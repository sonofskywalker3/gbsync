#!/usr/bin/env python3
"""
GBSync — Game Boy cartridge save sync for Raspberry Pi
Reads physical Game Boy/GBC/GBA carts, plays them in RetroArch,
and syncs save data back to the cartridge when done.
"""

import logging
import signal
import sys
import time
from pathlib import Path

from config import (
    ROM_DIR,
    SAVE_DIR,
    LOG_DIR,
    CART_POLL_INTERVAL,
    CORE_MAP,
    ensure_directories,
)
from cart import Cart, CartError, CartInfo
from emulator import Emulator, EmulatorError
from saves import SaveManager, SaveError

logger = logging.getLogger("gbsync")


class GBSync:
    """Main application: cart detection, emulation, and save sync loop."""

    def __init__(self):
        self._running = False
        self._cart = Cart()
        self._emulator = Emulator()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Handle graceful shutdown on SIGINT/SIGTERM."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._shutdown)

    def _shutdown(self, signum: int, frame) -> None:
        logger.info("Shutdown signal received")
        self._running = False
        self._emulator.stop()

    def run(self) -> None:
        """Main loop: wait for cart, play, sync, repeat."""
        logger.info("GBSync started — waiting for cartridge")
        self._running = True

        while self._running:
            if not self._cart.is_connected():
                time.sleep(CART_POLL_INTERVAL)
                continue

            try:
                self._handle_cart_session()
            except CartError as e:
                logger.error("Cart error: %s", e)
            except EmulatorError as e:
                logger.error("Emulator error: %s", e)
            except SaveError as e:
                logger.error("Save error: %s", e)

            if self._running:
                logger.info("Session complete — waiting for next cartridge")
                self._wait_for_cart_removal()

    def _handle_cart_session(self) -> None:
        """Full session: read cart → launch emulator → sync save back."""
        # Step 1: Identify the cartridge
        logger.info("Cartridge detected — reading header")
        info = self._cart.read_header()
        logger.info("Game: %s (%s)", info.title, info.cart_type)

        if info.cart_type not in CORE_MAP:
            logger.error("Unsupported cart type: %s", info.cart_type)
            return

        game_dir = ROM_DIR / info.safe_title
        game_dir.mkdir(parents=True, exist_ok=True)
        save_dir = SAVE_DIR / info.safe_title
        save_dir.mkdir(parents=True, exist_ok=True)

        # Determine file extension from core config
        core = self._emulator.get_core(info.cart_type)
        rom_ext = core.extensions[0] if core.extensions else ".gb"
        rom_path = game_dir / (info.safe_title + rom_ext)
        cart_save_path = save_dir / (info.safe_title + "_cart.sav")

        # Step 2: Dump ROM (skip if we already have it)
        if rom_path.exists():
            logger.info("ROM already dumped: %s", rom_path)
        else:
            logger.info("Dumping ROM...")
            self._cart.read_rom(rom_path, mode=info.cart_type)

        # Step 3: Read save from cart
        logger.info("Reading save from cartridge...")
        cart_save = self._cart.read_save(cart_save_path, mode=info.cart_type)

        # Step 4: Prepare emulator save
        save_manager = SaveManager(info.safe_title)
        emu_save_path = save_dir / (rom_path.stem + core.save_extension)
        save_manager.prepare_emulator_save(cart_save, emu_save_path)

        # Step 5: Launch RetroArch
        logger.info("Launching emulator...")
        self._emulator.launch(rom_path, info.cart_type, save_dir)

        # Step 6: Wait for player to finish
        exit_code = self._emulator.wait_for_exit()
        logger.info("RetroArch exited (code %d)", exit_code)

        # Step 7: Sync save back to cart if changed
        if save_manager.sync_save_to_cart(emu_save_path, cart_save):
            if self._cart.is_connected():
                logger.info("Writing updated save to cartridge...")
                self._cart.write_save(emu_save_path, mode=info.cart_type)
                logger.info("Save synced to cartridge successfully")
            else:
                logger.warning(
                    "Cart disconnected before save sync! "
                    "Save is backed up locally — reinsert cart to sync."
                )
        else:
            logger.info("No save changes to sync")

    def _wait_for_cart_removal(self) -> None:
        """Wait until the current cart is removed before starting a new session."""
        logger.info("Remove cartridge to start a new session")
        while self._running and self._cart.is_connected():
            time.sleep(CART_POLL_INTERVAL)


def setup_logging() -> None:
    """Configure logging to both console and file."""
    ensure_directories()

    log_file = LOG_DIR / "gbsync.log"
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def main() -> None:
    setup_logging()
    logger.info("=== GBSync v0.1.0 ===")

    try:
        app = GBSync()
        app.run()
    except CartError as e:
        logger.critical("Failed to initialize: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        logger.info("GBSync stopped")


if __name__ == "__main__":
    main()
