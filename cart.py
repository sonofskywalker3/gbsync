"""
GBSync Cart Interface
Wrapper around FlashGBX CLI for reading/writing ROMs and saves via GBxCart RW.

Run directly to check cart status:
    python cart.py --info
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from config import (
    FLASHGBX_BIN,
    FLASHGBX_TIMEOUT,
    GBXCART_USB_VENDOR_ID,
    GBXCART_USB_PRODUCT_ID,
)

logger = logging.getLogger(__name__)


class CartError(Exception):
    """Raised when a cart operation fails."""


class CartInfo:
    """Parsed cartridge header information."""

    def __init__(self, title: str, cart_type: str, rom_size: str, save_type: str):
        self.title = title
        self.cart_type = cart_type  # "GB", "GBC", or "GBA"
        self.rom_size = rom_size
        self.save_type = save_type

    def __repr__(self) -> str:
        return f"CartInfo({self.title!r}, type={self.cart_type}, rom={self.rom_size}, save={self.save_type})"

    @property
    def safe_title(self) -> str:
        """Filesystem-safe version of the cart title."""
        return "".join(c if c.isalnum() or c in "._- " else "_" for c in self.title).strip()


class Cart:
    """Interface to a Game Boy cartridge via GBxCart RW and FlashGBX CLI."""

    def __init__(self):
        self._verify_flashgbx()

    def _verify_flashgbx(self) -> None:
        """Check that FlashGBX is installed and reachable."""
        try:
            result = subprocess.run(
                [FLASHGBX_BIN, "--help"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode not in (0, 1):
                raise CartError(f"FlashGBX returned unexpected code: {result.returncode}")
        except FileNotFoundError:
            raise CartError(
                f"FlashGBX not found at '{FLASHGBX_BIN}'. "
                "Install with: pip install FlashGBX"
            )

    # Map cart types to FlashGBX mode flags
    MODE_MAP = {"GB": "dmg", "GBC": "dmg", "GBA": "agb"}

    def _run_flashgbx(self, args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
        """Run a FlashGBX CLI command and return the result."""
        timeout = timeout or FLASHGBX_TIMEOUT
        cmd = [FLASHGBX_BIN, "--cli"] + args
        logger.debug("Running: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise CartError(f"FlashGBX timed out after {timeout}s: {' '.join(cmd)}")

        if result.returncode != 0:
            raise CartError(
                f"FlashGBX failed (code {result.returncode}): {result.stderr.strip()}"
            )

        return result

    def is_connected(self) -> bool:
        """Check if a GBxCart RW device is connected via USB."""
        # TODO: Test USB detection on real hardware — pyudev is Linux-only,
        # may need to fall back to parsing lsusb output on Pi
        try:
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=5,
            )
            search = f"{GBXCART_USB_VENDOR_ID}:{GBXCART_USB_PRODUCT_ID}"
            return search in result.stdout.lower()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("lsusb not available, assuming cart is connected")
            return True

    def read_header(self, mode: str | None = None) -> CartInfo:
        """Read and parse the cartridge header to identify the game.

        Args:
            mode: Force a specific mode ("GB", "GBC", "GBA").
                  If None, tries GBA first, then GB/GBC.

        Returns:
            CartInfo with title, type, ROM size, and save type.
        """
        if mode:
            flashgbx_mode = self.MODE_MAP.get(mode, mode)
            result = self._run_flashgbx(["--action", "info", "--mode", flashgbx_mode])
            return self._parse_header(result.stdout, hint=mode)

        # Try GBA first, then DMG
        for try_mode, hint in [("agb", "GBA"), ("dmg", "GB")]:
            try:
                result = self._run_flashgbx(["--action", "info", "--mode", try_mode])
                return self._parse_header(result.stdout, hint=hint)
            except CartError:
                continue

        raise CartError("Could not read cartridge header in any mode")

    def _parse_header(self, output: str, hint: str = "GB") -> CartInfo:
        """Parse FlashGBX header output into a CartInfo.

        Actual FlashGBX output format:
            Game Title:           POKEMON LEAF
            ROM Size:             16 MiB
            Save Type:            1M FLASH (128 KiB)
            Cartridge Mode:       Game Boy Advance
        """
        title = ""
        cart_type = hint
        rom_size = ""
        save_type = ""

        for line in output.splitlines():
            line_lower = line.strip().lower()
            if "game title:" in line_lower:
                title = line.split(":", 1)[1].strip()
            elif "game name:" in line_lower and not title:
                title = line.split(":", 1)[1].strip()
            elif "cartridge mode:" in line_lower:
                value = line.split(":", 1)[1].strip()
                if "advance" in value.lower():
                    cart_type = "GBA"
                elif "color" in value.lower():
                    cart_type = "GBC"
                else:
                    cart_type = "GB"
            elif "rom size:" in line_lower:
                rom_size = line.split(":", 1)[1].strip()
            elif "save type:" in line_lower:
                save_type = line.split(":", 1)[1].strip()

        if not title:
            raise CartError("Could not parse cart title from header output")

        return CartInfo(title=title, cart_type=cart_type, rom_size=rom_size, save_type=save_type)

    def read_rom(self, output_path: Path, mode: str = "auto") -> Path:
        """Dump the cartridge ROM to a file.

        Args:
            output_path: Where to write the ROM file.
            mode: Cart mode — "GB", "GBC", "GBA", or "auto".

        Returns:
            Path to the written ROM file.
        """
        args = ["--action", "backup-rom", "--path", str(output_path)]
        if mode != "auto":
            args += ["--mode", self.MODE_MAP.get(mode, mode)]

        logger.info("Reading ROM to %s", output_path)
        self._run_flashgbx(args)

        if not output_path.exists():
            raise CartError(f"ROM file was not created at {output_path}")

        logger.info("ROM read complete: %s (%d bytes)", output_path, output_path.stat().st_size)
        return output_path

    def read_save(self, output_path: Path, mode: str = "auto") -> Path | None:
        """Read the save data from the cartridge.

        Args:
            output_path: Where to write the save file.
            mode: Cart mode — "GB", "GBC", "GBA", or "auto".

        Returns:
            Path to the save file, or None if the cart has no save data.
        """
        args = ["--action", "backup-save", "--path", str(output_path)]
        if mode != "auto":
            args += ["--mode", self.MODE_MAP.get(mode, mode)]

        logger.info("Reading save to %s", output_path)
        try:
            self._run_flashgbx(args)
        except CartError as e:
            if "no save" in str(e).lower() or "not supported" in str(e).lower():
                logger.info("Cart has no save data")
                return None
            raise

        if not output_path.exists():
            logger.warning("Save file was not created — cart may not have save capability")
            return None

        logger.info("Save read complete: %s (%d bytes)", output_path, output_path.stat().st_size)
        return output_path

    def write_save(self, save_path: Path, mode: str = "auto") -> None:
        """Write save data back to the cartridge.

        Args:
            save_path: Path to the save file to write.
            mode: Cart mode — "GB", "GBC", "GBA", or "auto".
        """
        if not save_path.exists():
            raise CartError(f"Save file not found: {save_path}")

        args = ["--action", "restore-save", "--path", str(save_path)]
        if mode != "auto":
            args += ["--mode", self.MODE_MAP.get(mode, mode)]

        logger.info("Writing save from %s to cart", save_path)
        self._run_flashgbx(args)
        logger.info("Save write complete")


def cli_info() -> None:
    """Print GBxCart connection status and cartridge info."""
    print("=== GBSync Cart Info ===\n")

    # Check USB connection
    print("[USB] Checking for GBxCart RW...")
    try:
        result = subprocess.run(
            ["lsusb"], capture_output=True, text=True, timeout=5,
        )
        search = f"{GBXCART_USB_VENDOR_ID}:{GBXCART_USB_PRODUCT_ID}"
        usb_lines = [
            line for line in result.stdout.splitlines()
            if search in line.lower()
        ]
        if usb_lines:
            print(f"  FOUND: {usb_lines[0].strip()}")
        else:
            print(f"  NOT FOUND (looking for vendor:product {search})")
            print("  Tip: Is the GBxCart plugged in via USB OTG?")
            print("\n  All USB devices:")
            for line in result.stdout.strip().splitlines():
                print(f"    {line.strip()}")
            sys.exit(1)
    except FileNotFoundError:
        print("  ERROR: lsusb not available (install usbutils)")
        sys.exit(1)

    # Check serial device
    print("\n[Serial] Checking for serial device...")
    import glob
    serial_devs = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    if serial_devs:
        for dev in serial_devs:
            print(f"  FOUND: {dev}")
    else:
        print("  No serial devices found (/dev/ttyUSB* or /dev/ttyACM*)")
        print("  Tip: Check USB cable and try: sudo dmesg | tail -20")

    # Check FlashGBX
    print(f"\n[FlashGBX] Checking for {FLASHGBX_BIN}...")
    try:
        result = subprocess.run(
            [FLASHGBX_BIN, "--help"],
            capture_output=True, text=True, timeout=10,
        )
        print(f"  OK: FlashGBX is installed")
    except FileNotFoundError:
        print(f"  NOT FOUND: {FLASHGBX_BIN}")
        print("  Install with: pip install FlashGBX")
        sys.exit(1)

    # Try to read cart header
    print("\n[Cart] Reading cartridge header...")
    try:
        cart = Cart()
        info = cart.read_header()
        print(f"  Title:     {info.title}")
        print(f"  Type:      {info.cart_type}")
        print(f"  ROM Size:  {info.rom_size}")
        print(f"  Save Type: {info.save_type}")
    except CartError as e:
        print(f"  ERROR: {e}")
        print("  Tip: Make sure a cartridge is inserted in the GBxCart")
        sys.exit(1)

    print("\nEverything looks good!")


def cli_dump() -> None:
    """Dump the ROM and save from the inserted cartridge."""
    from config import ROM_DIR, SAVE_DIR, CORE_MAP, ensure_directories
    ensure_directories()

    cart = Cart()
    print("Reading cartridge header...")
    info = cart.read_header()
    print(f"  Game:      {info.title}")
    print(f"  Type:      {info.cart_type}")
    print(f"  ROM Size:  {info.rom_size}")
    print(f"  Save Type: {info.save_type}")

    core = CORE_MAP[info.cart_type]
    rom_ext = core.extensions[0] if core.extensions else ".gb"
    rom_path = ROM_DIR / (info.safe_title + rom_ext)

    if rom_path.exists():
        print(f"\nROM already exists: {rom_path}")
        print(f"  Size: {rom_path.stat().st_size:,} bytes")
    else:
        print(f"\nDumping ROM to {rom_path}...")
        cart.read_rom(rom_path, mode=info.cart_type)
        print(f"  Done! {rom_path.stat().st_size:,} bytes")

    # Also dump save
    save_path = SAVE_DIR / (info.safe_title + "_cart.sav")
    print(f"\nReading save data to {save_path}...")
    result = cart.read_save(save_path, mode=info.cart_type)
    if result:
        print(f"  Done! {save_path.stat().st_size:,} bytes")
    else:
        print("  No save data on cartridge (or save type not supported)")

    print(f"\nROM path: {rom_path}")
    if result:
        print(f"Save path: {save_path}")


def cli_write_save() -> None:
    """Write a save file back to the inserted cartridge."""
    from config import SAVE_DIR, CORE_MAP, ensure_directories
    ensure_directories()

    cart = Cart()
    print("Reading cartridge header...")
    info = cart.read_header()
    print(f"  Game: {info.title} ({info.cart_type})")

    core = CORE_MAP[info.cart_type]

    # Look for the emulator save file (what RetroArch writes)
    emu_save = SAVE_DIR / (info.safe_title + core.save_extension)
    # Fall back to cart save
    cart_save = SAVE_DIR / (info.safe_title + "_cart.sav")

    save_to_write = None
    if emu_save.exists():
        save_to_write = emu_save
        print(f"\nFound emulator save: {emu_save}")
        print(f"  Size: {emu_save.stat().st_size:,} bytes")
    elif cart_save.exists():
        save_to_write = cart_save
        print(f"\nFound cart save: {cart_save}")
        print(f"  Size: {cart_save.stat().st_size:,} bytes")
    else:
        print(f"\nNo save file found in {SAVE_DIR}")
        print(f"  Looked for: {emu_save.name} or {cart_save.name}")
        sys.exit(1)

    print(f"\nWriting save to cartridge...")
    cart.write_save(save_to_write, mode=info.cart_type)
    print("  Done! Save written to cartridge.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GBSync cart interface")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--info", action="store_true",
        help="Print GBxCart connection status and cartridge info",
    )
    group.add_argument(
        "--dump", action="store_true",
        help="Dump ROM and save from inserted cartridge",
    )
    group.add_argument(
        "--write-save", action="store_true",
        help="Write save file back to inserted cartridge",
    )
    args = parser.parse_args()

    if args.info:
        cli_info()
    elif args.dump:
        cli_dump()
    elif args.write_save:
        cli_write_save()
    else:
        parser.print_help()
