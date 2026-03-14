#!/usr/bin/env bash
# GBSync — Pi Zero 2W Setup Script
# Run on a fresh Raspberry Pi OS Lite (64-bit) install.
# Usage: chmod +x setup.sh && sudo ./setup.sh

set -euo pipefail

# --- Must run as root ---
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run this script with sudo: sudo ./setup.sh"
    exit 1
fi

REAL_USER="${SUDO_USER:-pi}"
REAL_HOME=$(eval echo "~$REAL_USER")

echo "=== GBSync Setup ==="
echo "User: $REAL_USER"
echo "Home: $REAL_HOME"
echo ""

# --- System packages ---
echo "[1/6] Updating package lists..."
apt-get update

echo "[2/6] Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    retroarch \
    usbutils \
    git

# --- RetroArch cores ---
echo "[3/6] Installing RetroArch cores..."

CORE_DIR="/usr/lib/aarch64-linux-gnu/libretro"
# Fallback for 32-bit or other layouts
if [[ ! -d "$CORE_DIR" ]]; then
    CORE_DIR="/usr/lib/libretro"
    mkdir -p "$CORE_DIR"
fi

apt-get install -y libretro-mgba || true

# Gambatte may not be in apt — install via retroarch online updater or build
if ! ls "$CORE_DIR"/gambatte_libretro.so 2>/dev/null; then
    echo "NOTE: gambatte core not found in apt. Trying retroarch core downloader..."
    # retroarch --command 'DOWNLOAD_CORE gambatte' may work headless, but
    # it's more reliable to grab it manually:
    apt-get install -y libretro-gambatte 2>/dev/null || {
        echo "WARNING: Could not install gambatte core via apt."
        echo "  Install manually: RetroArch menu → Online Updater → Core Downloader → Gambatte"
        echo "  Or download from: https://buildbot.libretro.com/nightly/linux/aarch64/latest/"
    }
fi

echo "Installed cores:"
ls -1 "$CORE_DIR"/*.so 2>/dev/null || echo "  (none found in $CORE_DIR — check /usr/lib/*/libretro/)"

# --- Python venv + dependencies ---
echo "[4/6] Setting up Python virtual environment..."

GBSYNC_DIR="$REAL_HOME/gbsync"

if [[ ! -d "$GBSYNC_DIR" ]]; then
    echo "ERROR: gbsync project not found at $GBSYNC_DIR"
    echo "  Clone it first: git clone <repo-url> $GBSYNC_DIR"
    exit 1
fi

cd "$GBSYNC_DIR"

# Create venv as the real user (not root)
sudo -u "$REAL_USER" python3 -m venv .venv
sudo -u "$REAL_USER" .venv/bin/pip install --upgrade pip
sudo -u "$REAL_USER" .venv/bin/pip install -r requirements.txt

echo ""
echo "Installed Python packages:"
sudo -u "$REAL_USER" .venv/bin/pip list

# --- USB permissions for GBxCart ---
echo "[5/6] Setting up USB permissions for GBxCart RW..."

# GBxCart RW uses a CH340 USB-serial chip (vendor 1a86, product 7523)
# Grant the user access without needing sudo
UDEV_RULE="/etc/udev/rules.d/99-gbxcart.rules"
cat > "$UDEV_RULE" << 'UDEVRULE'
# GBxCart RW v1.4a Pro — CH340 USB-serial
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{idProduct}=="7523", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", SYMLINK+="gbxcart"
UDEVRULE

udevadm control --reload-rules
udevadm trigger

# Also add user to dialout group for serial port access
usermod -aG dialout "$REAL_USER"

# --- Create GBSync data directories ---
echo "[6/6] Creating GBSync data directories..."
sudo -u "$REAL_USER" mkdir -p \
    "$REAL_HOME/.gbsync/roms" \
    "$REAL_HOME/.gbsync/saves" \
    "$REAL_HOME/.gbsync/backups" \
    "$REAL_HOME/.gbsync/logs"

echo ""
echo "=== Setup complete ==="
echo ""
echo "RetroArch cores directory: $CORE_DIR"
echo "GBSync project: $GBSYNC_DIR"
echo "GBSync data:    $REAL_HOME/.gbsync/"
echo ""
echo "Next steps:"
echo "  1. Log out and back in (for dialout group to take effect)"
echo "  2. Plug in the GBxCart RW"
echo "  3. Run: lsusb | grep 1a86"
echo "  4. Activate venv: source $GBSYNC_DIR/.venv/bin/activate"
echo "  5. Test: python cart.py --info"
