# GBSync

Play your physical Game Boy, Game Boy Color, and Game Boy Advance cartridges on a Raspberry Pi — with automatic save sync back to the original cart.

GBSync reads ROMs and saves from cartridges using a **GBxCart RW v1.4a Pro**, launches them in **RetroArch**, and writes updated save data back to the cartridge when you're done playing.

## Hardware

- **Raspberry Pi Zero 2W** running Raspberry Pi OS Lite
- **GBxCart RW v1.4a Pro** (USB-C) — [insideGadgets](https://www.insidegadgets.com/)
- Game Boy / Game Boy Color / Game Boy Advance cartridges
- Display, controls, and battery (for handheld build)

## How It Works

1. Insert a cartridge into the GBxCart RW
2. GBSync detects the cart and reads the ROM header
3. ROM is dumped (first time only — cached for future sessions)
4. Save data is read from the cartridge
5. RetroArch launches with the correct core (Gambatte for GB/GBC, mGBA for GBA)
6. When you exit the game, GBSync compares save files
7. If save data changed, it's written back to the physical cartridge
8. Remove the cart and insert another — GBSync loops automatically

Save backups are kept locally so nothing is ever lost.

## Setup

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install retroarch python3-pip python3-venv usbutils
```

### 2. Install RetroArch cores

```bash
# Via RetroArch menu: Online Updater → Core Downloader
# Install: Gambatte (GB/GBC) and mGBA (GBA)
```

### 3. Install GBSync

```bash
git clone https://github.com/youruser/gbsync.git
cd gbsync
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run

```bash
python main.py
```

### 5. (Optional) Auto-start on boot

```bash
# Add to /etc/rc.local or create a systemd service
# See docs/autostart.md (coming soon)
```

## Project Structure

```
gbsync/
├── main.py          # Main loop — cart detection, orchestration
├── cart.py          # GBxCart RW / FlashGBX CLI wrapper
├── emulator.py      # RetroArch launch and save monitoring
├── saves.py         # Save diffing, backup, and sync logic
├── config.py        # Paths, settings, core mappings
├── requirements.txt
└── README.md
```

## Configuration

All paths and settings are in `config.py`:

- **ROM/save storage**: `~/.gbsync/roms/`, `~/.gbsync/saves/`
- **Save backups**: `~/.gbsync/backups/` (rolling, 10 per game)
- **RetroArch cores**: Gambatte (GB/GBC), mGBA (GBA)
- **USB detection**: GBxCart vendor/product IDs

## Roadmap

- [x] Core save sync loop (read → play → write back)
- [x] Automatic cart type detection (GB/GBC/GBA)
- [x] Save diffing to avoid unnecessary writes
- [x] Rolling save backups
- [ ] Auto-start systemd service
- [ ] OLED status display support
- [ ] GPIO button controls for menu navigation
- [ ] Wi-Fi save backup to cloud/NAS
- [ ] Multi-cart queue (swap carts without restarting)
- [ ] Custom vertical handheld enclosure design
- [ ] Battery management and safe shutdown

## License

MIT
