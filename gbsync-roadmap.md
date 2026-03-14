# GBSync — Project Roadmap & Vision

> **Working title:** GBSync  
> **Concept:** A vertical GBC-style open source handheld that reads, plays, and syncs saves between physical GB/GBC/GBA cartridges and original hardware — seamlessly.  
> **Target price:** ~$150 prebuilt | ~$99 DIY kit | TBD drop-in board

---

## The Pitch

You own physical carts. You want to play them on a modern pocketable device. When you're done, you pull the cart out and play on your original hardware — save intact, no syncing, no PC, no fuss. GBSync makes that workflow completely automatic.

Nobody else does this. Not the Analogue Pocket. Not the ModRetro Chromatic. Not anything at any price.

---

## Product Tiers (Long-Term Vision)

| Tier | Description | Target Price |
|------|-------------|-------------|
| **Prebuilt** | Complete assembled unit, ready to play | ~$150 |
| **DIY Kit** | All PCBs + components, you source/print shell | ~$99 |
| **Drop-in Board** | Board only, fits original GBC shell with no modification | TBD |

The drop-in tier targets collectors who have a shell they love — limited color variants, custom paint, pristine originals — and just want modern guts inside it.

---

## Development Stages

### ✅ Stage 0 — Inventory & Research (DONE)
- Identified GBxCart RW v1.4a Pro as proven cart interface
- Identified Pi Zero 2W as compute platform
- Confirmed open source software stack (GBxCart CLI + RetroArch)
- Claude Code project scaffold created (`gbsync/` Python project)

---

### 🔄 Stage 1 — Proof of Concept (IN PROGRESS)
**Goal:** Prove the full save sync loop works on a desk, ugly wires everywhere, no form factor concerns.

**Hardware:**
- GBxCart RW v1.4a Pro (USB-C) → Pi Zero 2W via USB OTG
- Pi Zero 2W → monitor via mini HDMI
- USB gamepad for input

**Software milestones:**
- [ ] Pi Zero 2W boots Raspberry Pi OS Lite
- [ ] GBxCart CLI runs on Pi ARM — dumps FFTA ROM successfully
- [ ] RetroArch installed, runs dumped ROM with correct GBA core
- [ ] Save file written back to cart after play session
- [ ] Full loop automated: insert cart → game launches → save syncs on exit

**Definition of done:** Insert FFTA, play, save, pull cart, insert into real GBA, continue from same save point.

---

### Stage 2 — Software Polish
**Goal:** The software loop is reliable, automatic, and handles edge cases.

- Cart detection (polling GBxCart for insertion/removal)
- Correct core auto-selection (GB vs GBC vs GBA)
- Save diff logic — only write back if save actually changed
- Graceful handling of: no cart, unrecognized cart, corrupt save
- Simple on-screen UI (cart info, battery, save status)
- Auto-launch on boot (systemd service)
- [ ] STRETCH: Companion app / web UI for cart management over WiFi

---

### Stage 3 — Hardware Prototype v1
**Goal:** Replace GBxCart + Pi Zero with a single custom PCB. Still ugly, still on a bench, but integrated.

- Design PCB combining:
  - Cart interface circuit (based on GBxCart open source design)
  - Pi Zero 2W compute (or CM4 lite if performance needed)
  - Display connector
  - Button inputs
  - Battery management
- Order 5x from JLCPCB, assemble by hand
- 3D print a test enclosure — purely functional, not pretty

---

### Stage 4 — Handheld Prototype v1
**Goal:** A working handheld. Functional over pretty.

- Vertical GBC-style enclosure (3D printed, SLA resin)
- IPS display integrated
- Physical buttons wired
- Battery + charging circuit
- Everything fits, everything works

---

### Stage 5 — Refinement & Multiple Form Factors
**Goal:** Polish the v1 handheld. Begin second form factor design.

- Tighten tolerances based on v1 learnings
- Improve button feel (DSi silicone membranes or custom)
- Begin drop-in board design for original GBC shell
- Investigate injection molding vs continued 3D printing at scale

---

### Stage 6 — Open Source Release & Community
**Goal:** Publish everything. Build the community.

- GitHub release: schematics, firmware, STLs, BOM, build guide
- Crowd Supply campaign for prebuilt units
- DIY build guide with beginner-friendly instructions
- Community Discord / forum

---

## Feature Tracker

### Core Features (Stage 1–3)
- [x] GB cartridge read/write
- [x] GBC cartridge read/write  
- [x] GBA cartridge read/write
- [ ] Automatic save sync (ROM dump → emulate → write back)
- [ ] Auto cart detection and core selection
- [ ] RetroArch integration
- [ ] Battery powered

### Mid-Priority Features (Stage 3–5)
- [ ] **IR transceiver** — GBC IR communication (Pokemon trades without link cable)
- [ ] **Link cable port** — multiplayer between GBSync units or original hardware
- [ ] **WiFi save sync** — wireless save transfer, no cable required
- [ ] **Blank cart flashing** — flash homebrew or ROM backups to blank carts from the device
- [ ] **Full GBxCart feature parity** — expose all GBxCart functions through device UI
- [ ] **USB-C** — charging and data

### Stretch / Future Features (Stage 5+)
- [ ] **UV/light sensor** — authentic Boktai solar sensor emulation (VEML6070 or similar over I2C, ~$2-3 part). Take it outside on a sunny day and Boktai works exactly as intended.
- [ ] **Capacitive touch L/R triggers** — flush touch-sensitive strips on back/upper edges. Maintains clean GBC vertical form factor for GB/GBC games, fully supports GBA shoulder buttons. ESP32 supports this natively via GPIO touch pins — no extra chip needed for prototyping.
- [ ] **Multiple form factors** — same software stack, different shells (vertical pocket, horizontal landscape, desktop dock)
- [ ] **Drop-in board for original GBC shell** — ultrasonic-fit board designed to drop into original GBC shell with no cutting or modification, same approach as aftermarket IPS kits. Ship with foam tape for tolerance variation between shell production runs.
- [ ] **Wireless link cable emulation** — two GBSync units doing multiplayer over local WiFi, emulating the link cable protocol
- [ ] **GameCube link cable support** — via GBA-GCN link protocol
- [ ] **Companion mobile app** — ROM library management, save backup to cloud, cart dumping over WiFi
- [ ] **Game Boy Camera support** — dump camera photos, use as actual camera
- [ ] **RTC (real-time clock)** — for Pokemon Gold/Silver/Crystal, time-based events

---

## Hardware Stack (Current Thinking)

| Component | Current Plan | Notes |
|-----------|-------------|-------|
| Cart interface | GBxCart RW circuit (open source) | Proven, handles 5V/3.3V switching |
| Compute | Pi Zero 2W | Runs RetroArch, Linux ecosystem |
| Cart bridge MCU | RP2040 Pico | Handles cart bus timing if needed |
| Wireless | ESP32 (on hand) or Pi Zero 2W built-in WiFi | ESP32 for BT Classic controller support |
| Touch triggers | ESP32 capacitive touch GPIO | No extra chip for prototyping |
| UV sensor | VEML6070 (I2C) | ~$2-3, Boktai support |
| Power | 7-12V in, 3.3V/5V out modules (on hand) | Replace with custom PMU in final design |
| Display | IPS, TBD size | ~3.0-3.5" target |

---

## Scope Creep Parking Lot

*Great ideas that are NOT happening until Stage 5 or later. Captured here so they don't derail Stage 1.*

- FPGA-based cart execution (running code on actual cart hardware)
- SNES/N64/other system support
- Haptic feedback
- Rechargeable AA form factor
- Dock accessory with HDMI out
- Built-in flasher for blank GBA carts without a PC
- NFC for cart identification
- E-ink secondary display for battery/game info

---

## Anti-Scope-Creep Rules

1. **Stage 1 is done when the save sync loop works.** Not when it's pretty. Not when it has WiFi. When you can insert FFTA, play, and continue on a real GBA.
2. **No new hardware purchases until current hardware is proven.** You have everything you need for Stage 1.
3. **Every idea goes in the parking lot first.** If it's still exciting after Stage 1 ships, it goes on the roadmap.
4. **The Pi Zero 2W arriving is the starting gun for Stage 1.** Not for designing PCBs.

---

## What You Can Do Right Now (While Waiting for Pi Zero 2W)

1. **Let Claude Code flesh out the gbsync Python project** — get `cart.py`, `emulator.py`, `saves.py` stubbed out with TODOs
2. **Read the GBxCart RW CLI documentation** — understand all the commands you'll be scripting
3. **Install RetroArch on your PC** — get familiar with core selection, config files, save paths
4. **Look up RetroArch headless/CLI launch flags** — you'll need these to launch games from Python
5. **Read the insideGadgets GBxCart source code** — understand the cart interface circuit for when you design your own PCB later
6. **Start a GitHub repo** — even if it's just the README and roadmap for now

---

*Last updated: Stage 0 complete, Stage 1 in progress. Pi Zero 2W ordered.*
