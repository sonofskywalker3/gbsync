"""
GBSync Configuration
Paths, settings, timeouts, and RetroArch core mappings.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field


# --- Paths ---

HOME = Path.home()
GBSYNC_DIR = HOME / ".gbsync"
ROM_DIR = GBSYNC_DIR / "roms"
SAVE_DIR = GBSYNC_DIR / "saves"
LOG_DIR = GBSYNC_DIR / "logs"
BACKUP_DIR = GBSYNC_DIR / "backups"

# RetroArch paths (Raspberry Pi OS defaults)
RETROARCH_BIN = "/usr/bin/retroarch"
RETROARCH_CORES_DIR = next(
    (p for p in [
        Path("/usr/lib/aarch64-linux-gnu/libretro"),
        Path("/usr/lib/arm-linux-gnueabihf/libretro"),
        Path("/usr/lib/libretro"),
    ] if p.is_dir()),
    Path("/usr/lib/libretro"),
)
RETROARCH_CONFIG = HOME / ".config/retroarch/retroarch.cfg"

# FlashGBX CLI binary
# TODO: Confirm install path on Pi — may be ~/.local/bin/FlashGBX or via pip entry point
FLASHGBX_BIN = "FlashGBX"


# --- RetroArch Core Mappings ---

@dataclass(frozen=True)
class CoreConfig:
    """RetroArch core configuration for a cartridge type."""
    core_name: str
    core_file: str
    save_extension: str
    extensions: tuple[str, ...] = field(default_factory=tuple)


CORE_MAP: dict[str, CoreConfig] = {
    "GB": CoreConfig(
        core_name="Gambatte",
        core_file="gambatte_libretro.so",
        save_extension=".srm",
        extensions=(".gb",),
    ),
    "GBC": CoreConfig(
        core_name="Gambatte",
        core_file="gambatte_libretro.so",
        save_extension=".srm",
        extensions=(".gbc",),
    ),
    "GBA": CoreConfig(
        core_name="mGBA",
        core_file="mgba_libretro.so",
        save_extension=".srm",
        extensions=(".gba",),
    ),
}


# --- Timeouts & Polling ---

CART_POLL_INTERVAL = 2.0       # Seconds between cart detection checks
SAVE_POLL_INTERVAL = 5.0      # Seconds between save file change checks
FLASHGBX_TIMEOUT = 300        # Max seconds for a FlashGBX read/write operation
RETROARCH_LAUNCH_TIMEOUT = 10 # Seconds to wait for RetroArch process to start

# --- USB Detection ---

# TODO: Confirm vendor/product IDs on real GBxCart RW v1.4a Pro hardware
GBXCART_USB_VENDOR_ID = "1a86"
GBXCART_USB_PRODUCT_ID = "7523"


# --- Save Backup ---

MAX_SAVE_BACKUPS = 10  # Rolling backup count per game


def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    for d in (GBSYNC_DIR, ROM_DIR, SAVE_DIR, LOG_DIR, BACKUP_DIR):
        d.mkdir(parents=True, exist_ok=True)
