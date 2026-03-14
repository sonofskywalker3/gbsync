"""
GBSync Emulator Manager
Launches RetroArch with the correct core and monitors for save changes.
"""

import logging
import subprocess
import time
from pathlib import Path

from config import (
    RETROARCH_BIN,
    RETROARCH_CORES_DIR,
    RETROARCH_CONFIG,
    RETROARCH_LAUNCH_TIMEOUT,
    SAVE_POLL_INTERVAL,
    CORE_MAP,
    CoreConfig,
)

logger = logging.getLogger(__name__)


class EmulatorError(Exception):
    """Raised when the emulator fails to launch or run."""


class Emulator:
    """Manages RetroArch lifecycle and save file monitoring."""

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._save_path: Path | None = None
        self._last_save_mtime: float = 0.0

    @property
    def is_running(self) -> bool:
        """Check if RetroArch is currently running."""
        return self._process is not None and self._process.poll() is None

    def get_core(self, cart_type: str) -> CoreConfig:
        """Look up the RetroArch core config for a cartridge type.

        Args:
            cart_type: "GB", "GBC", or "GBA".

        Returns:
            CoreConfig with core file path and save extension.
        """
        if cart_type not in CORE_MAP:
            raise EmulatorError(f"Unknown cart type: {cart_type}")
        return CORE_MAP[cart_type]

    def launch(self, rom_path: Path, cart_type: str, save_dir: Path) -> Path:
        """Launch RetroArch with the appropriate core.

        Args:
            rom_path: Path to the ROM file.
            cart_type: "GB", "GBC", or "GBA".
            save_dir: Directory where RetroArch should store saves.

        Returns:
            Expected save file path.
        """
        if self.is_running:
            raise EmulatorError("RetroArch is already running")

        core = self.get_core(cart_type)
        core_path = RETROARCH_CORES_DIR / core.core_file

        if not core_path.exists():
            raise EmulatorError(
                f"Core not found: {core_path}. "
                f"Install the {core.core_name} core in RetroArch."
            )

        # RetroArch save file: same name as ROM with .srm extension, in save_dir
        self._save_path = save_dir / (rom_path.stem + core.save_extension)

        # Record current save mtime for change detection
        if self._save_path.exists():
            self._last_save_mtime = self._save_path.stat().st_mtime

        cmd = [
            RETROARCH_BIN,
            "--libretro", str(core_path),
            "--config", str(RETROARCH_CONFIG),
            "--savefile-directory", str(save_dir),
            str(rom_path),
        ]

        # TODO: Test RetroArch launch flags on Pi Zero 2W — may need
        # --set-shader, --fullscreen, or performance flags for smooth playback
        logger.info("Launching RetroArch: %s with %s core", rom_path.name, core.core_name)
        logger.debug("Command: %s", " ".join(cmd))

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise EmulatorError(
                f"RetroArch not found at '{RETROARCH_BIN}'. "
                "Install with: sudo apt install retroarch"
            )

        # Brief wait to catch immediate launch failures
        time.sleep(1)
        if self._process.poll() is not None:
            stderr = self._process.stderr.read().decode() if self._process.stderr else ""
            raise EmulatorError(f"RetroArch exited immediately: {stderr.strip()}")

        logger.info("RetroArch running (PID %d)", self._process.pid)
        return self._save_path

    def wait_for_exit(self) -> int:
        """Block until RetroArch exits.

        Returns:
            RetroArch exit code.
        """
        if not self._process:
            raise EmulatorError("RetroArch is not running")

        logger.info("Waiting for RetroArch to exit...")
        return self._process.wait()

    def save_changed(self) -> bool:
        """Check if the save file has been modified since last check.

        Returns:
            True if the save file was created or modified.
        """
        if not self._save_path or not self._save_path.exists():
            return False

        current_mtime = self._save_path.stat().st_mtime
        if current_mtime > self._last_save_mtime:
            self._last_save_mtime = current_mtime
            return True
        return False

    def get_save_path(self) -> Path | None:
        """Return the path to the current emulator save file."""
        return self._save_path

    def stop(self) -> None:
        """Gracefully stop RetroArch if running."""
        if not self.is_running:
            return

        logger.info("Stopping RetroArch (PID %d)", self._process.pid)

        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("RetroArch did not terminate, killing")
            self._process.kill()
            self._process.wait()

        logger.info("RetroArch stopped")
        self._process = None
