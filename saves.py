"""
GBSync Save Manager
Handles save file diffing, backups, and sync logic between emulator and cartridge.
"""

import hashlib
import logging
import shutil
from datetime import datetime
from pathlib import Path

from config import BACKUP_DIR, MAX_SAVE_BACKUPS

logger = logging.getLogger(__name__)


class SaveError(Exception):
    """Raised when a save sync operation fails."""


class SaveManager:
    """Manages save file comparison, backup, and sync between emulator and cart."""

    def __init__(self, game_title: str):
        self.game_title = game_title
        self._game_backup_dir = BACKUP_DIR / game_title
        self._game_backup_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def file_hash(path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def saves_differ(self, path_a: Path, path_b: Path) -> bool:
        """Check if two save files have different content.

        Args:
            path_a: First save file.
            path_b: Second save file.

        Returns:
            True if files differ or one doesn't exist.
        """
        if not path_a.exists() or not path_b.exists():
            return True

        if path_a.stat().st_size != path_b.stat().st_size:
            return True

        return self.file_hash(path_a) != self.file_hash(path_b)

    def backup_save(self, save_path: Path, label: str = "") -> Path:
        """Create a timestamped backup of a save file.

        Args:
            save_path: Save file to back up.
            label: Optional label (e.g., "cart", "emu") added to filename.

        Returns:
            Path to the backup file.
        """
        if not save_path.exists():
            raise SaveError(f"Cannot backup: file not found: {save_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        backup_name = f"{save_path.stem}{suffix}_{timestamp}{save_path.suffix}"
        backup_path = self._game_backup_dir / backup_name

        shutil.copy2(save_path, backup_path)
        logger.info("Backed up save: %s", backup_path)

        self._prune_backups()
        return backup_path

    def _prune_backups(self) -> None:
        """Remove oldest backups when exceeding MAX_SAVE_BACKUPS."""
        backups = sorted(self._game_backup_dir.iterdir(), key=lambda p: p.stat().st_mtime)
        while len(backups) > MAX_SAVE_BACKUPS:
            oldest = backups.pop(0)
            oldest.unlink()
            logger.debug("Pruned old backup: %s", oldest.name)

    def prepare_emulator_save(self, cart_save: Path | None, emu_save_path: Path) -> None:
        """Set up the emulator save file before launching.

        If a cart save exists and the emulator already has a save, compare them.
        The cart save is considered the source of truth.

        Args:
            cart_save: Save file read from the cartridge (None if cart has no save).
            emu_save_path: Where RetroArch expects the save file.
        """
        if cart_save is None:
            logger.info("Cart has no save data — emulator starts fresh")
            return

        if emu_save_path.exists():
            if self.saves_differ(cart_save, emu_save_path):
                # Cart save differs from emulator save — back up both, use cart's
                logger.info("Cart save differs from emulator save — using cart version")
                self.backup_save(emu_save_path, label="emu_pre_sync")
                self.backup_save(cart_save, label="cart")
                shutil.copy2(cart_save, emu_save_path)
            else:
                logger.info("Cart and emulator saves match — no sync needed")
        else:
            # No existing emulator save — copy cart save in
            logger.info("Copying cart save to emulator save location")
            emu_save_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cart_save, emu_save_path)

    def sync_save_to_cart(self, emu_save: Path, cart_save: Path | None) -> bool:
        """Determine if the emulator save should be written back to the cart.

        Compares the current emulator save against the original cart save.
        If they differ, the emulator save has new progress to sync.

        Args:
            emu_save: Current emulator save file (post-play).
            cart_save: Original save read from cart before play (None if no cart save).

        Returns:
            True if the emulator save has changes that should be written to cart.
        """
        if not emu_save.exists():
            logger.info("No emulator save file exists — nothing to sync")
            return False

        if cart_save is None:
            # Cart had no save, but emulator created one — new save data
            logger.info("New save data created during play")
            self.backup_save(emu_save, label="emu_new")
            return True

        if self.saves_differ(emu_save, cart_save):
            logger.info("Emulator save differs from cart — sync needed")
            self.backup_save(emu_save, label="emu_post_play")
            return True

        logger.info("Save unchanged during play — no sync needed")
        return False
