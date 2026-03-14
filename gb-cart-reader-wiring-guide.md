# GB/GBC/GBA Cart Reader — Wiring Guide
## Raspberry Pi Pico ↔ Cartridge ↔ Pi Zero 2W

---

## The Voltage Situation (Read This First)

| Cart Type | Cart Voltage | Pico Voltage | Level Shifting Needed? |
|-----------|-------------|--------------|----------------------|
| GBA       | **3.3V**    | 3.3V         | ❌ None — wire directly |
| GB / GBC  | **5V**      | 3.3V         | ✅ Yes — bidirectional shifters |

**Start with GBA.** It's the easiest wiring because the Pico is native 3.3V — same as the GBA cart. No extra chips. Once GBA is working, adding GB/GBC just means wiring in level shifters.

---

## What You Need

| Item | Where to Buy | ~Cost |
|------|-------------|-------|
| Raspberry Pi Pico (you have one) | — | — |
| Raspberry Pi Zero 2W | [pishop.us](https://www.pishop.us/product/raspberry-pi-zero-2-w/) | $15 |
| GB/GBC/GBA cartridge breakout board | [Tindie - Driptronics](https://www.tindie.com/products/driptronics/cartridge-breakout-board-for-gameboy/) | ~$10 |
| Bidirectional logic level shifter (4-ch, BSS138-based) x3 | [Amazon search](https://www.amazon.com/s?k=bidirectional+logic+level+shifter+5v+3.3v) | ~$1 each |
| Mini HDMI to HDMI adapter | [Amazon search](https://www.amazon.com/s?k=mini+hdmi+to+hdmi+adapter) | ~$5 |
| Micro USB OTG cable (for Pico→Pi Zero) | [Amazon search](https://www.amazon.com/s?k=micro+usb+otg+cable) | ~$4 |
| Breadboard + jumper wires (you have these) | — | — |
| microSD card (16GB+) | Amazon / anywhere | ~$8 |

---

## Phase A: GBA Cart Wiring (No Level Shifting)

### The GBA Cart Bus

The GBA connector has 32 pins. The breakout board exposes them all with labels.
Key thing to understand: GBA **multiplexes** address and data on the same pins.
The first 16 pins (AD0–AD15) carry the address first, then switch to data.
The upper 8 address pins (A16–A23) are always address.

### GBA Breakout → Pico GPIO Wiring

| Breakout Label | Pico GPIO | Notes |
|---------------|-----------|-------|
| VDD (pin 1)   | 3V3 (pin 36) | Power to cart — 3.3V from Pico |
| GND (pin 32)  | GND (pin 38) | Common ground |
| AD0           | GPIO0     | Multiplexed addr/data |
| AD1           | GPIO1     | |
| AD2           | GPIO2     | |
| AD3           | GPIO3     | |
| AD4           | GPIO4     | |
| AD5           | GPIO5     | |
| AD6           | GPIO6     | |
| AD7           | GPIO7     | |
| AD8           | GPIO8     | |
| AD9           | GPIO9     | |
| AD10          | GPIO10    | |
| AD11          | GPIO11    | |
| AD12          | GPIO12    | |
| AD13          | GPIO13    | |
| AD14          | GPIO14    | |
| AD15          | GPIO15    | |
| A16           | GPIO16    | Upper address (output only) |
| A17           | GPIO17    | |
| A18           | GPIO18    | |
| A19           | GPIO19    | |
| A20           | GPIO20    | |
| A21           | GPIO21    | |
| A22           | GPIO22    | |
| A23           | GPIO26    | (skip GPIO23-25 — used internally) |
| /CS (pin 5)   | GPIO27    | ROM chip select, active LOW |
| /RD (pin 4)   | GPIO28    | Read enable, active LOW |
| /WR (pin 3)   | GPIO24    | Write enable, active LOW |
| /CS2 (pin 30) | GPIO25    | RAM chip select (for save data) |

> **⚠️ Important:** The GBA cart must share GND with both the Pico and eventually the Pi Zero.
> Run a GND wire to your breadboard's negative rail and connect everything to it.

---

## Phase B: GB/GBC Cart Wiring (With Level Shifting)

GB/GBC carts run at 5V. Sending 5V into the Pico's 3.3V GPIO pins **will damage it**.
You need bidirectional level shifters between the Pico and the cart.

### Level Shifter Wiring (per chip)

Each cheap BSS138 level shifter module has two sides:
- **LV side** (Low Voltage = 3.3V) → connects to Pico
- **HV side** (High Voltage = 5V) → connects to cart

Power the shifter:
- LV pin → Pico 3V3
- HV pin → 5V (use Pico VBUS pin 40 — this is USB 5V)
- GND → GND (common rail)

### GB/GBC Cart Breakout → Level Shifter → Pico

You need 3x 4-channel shifters (12 channels) for the first batch of signals:

**Shifter #1 — Data bus D0–D3:**
| Cart Pin | Shifter HV | Shifter LV | Pico GPIO |
|----------|-----------|-----------|-----------|
| D0       | B1        | A1        | GPIO16    |
| D1       | B2        | A2        | GPIO17    |
| D2       | B3        | A3        | GPIO18    |
| D3       | B4        | A4        | GPIO19    |

**Shifter #2 — Data bus D4–D7:**
| Cart Pin | Shifter HV | Shifter LV | Pico GPIO |
|----------|-----------|-----------|-----------|
| D4       | B1        | A1        | GPIO20    |
| D5       | B2        | A2        | GPIO21    |
| D6       | B3        | A3        | GPIO22    |
| D7       | B4        | A4        | GPIO26    |

**Shifter #3 — Control lines:**
| Cart Pin | Shifter HV | Shifter LV | Pico GPIO |
|----------|-----------|-----------|-----------|
| /RD      | B1        | A1        | GPIO27    |
| /WR      | B2        | A2        | GPIO28    |
| /CS      | B3        | A3        | GPIO24    |
| /RST     | B4        | A4        | GPIO25    |

**Address lines A0–A15 (output only, Pico → cart):**
These can use simple unidirectional shifters or the same bidirectional ones.
Connect A0–A15 to GPIO0–GPIO15 through 4 more level shifter channels.
(You can buy a second set of 3 shifters for this, or get an 8-channel TXB0108 chip.)

**Power the GB/GBC cart:**
| Cart Pin | Connect To |
|----------|-----------|
| VCC (pin 1) | Pico VBUS (pin 40) = 5V from USB |
| GND (pin 32) | Common GND rail |

---

## Pico → Pi Zero 2W Connection

The simplest connection is **USB**. The Pico shows up as a serial device over USB.

```
Pico micro-USB port
        ↓
  micro-USB OTG cable
        ↓
Pi Zero 2W USB OTG port (the data USB port, not the power port)
```

On the Pi Zero, the Pico will appear as `/dev/ttyACM0` (or similar).
The Pico sends ROM data and save data over USB serial.
The Pi receives it, writes it to a file, and passes it to RetroArch.

> **Pi Zero has two micro-USB ports:**
> - The one labeled **PWR** → power only, for your power supply
> - The one labeled **USB** → data, plug the OTG cable here

---

## The Full Picture

```
[GB/GBC cart]          [GBA cart]
      |                      |
[Level shifters]        (direct)
      |                      |
      +----------+----------+
                 |
          [Pico GPIO]
          (reads cart bus,
           handles timing)
                 |
           [USB serial]
                 |
          [Pi Zero 2W]
          (runs RetroArch,
           manages save files)
                 |
          [HDMI → monitor]
```

---

## First Test Goal (Before Hooking Up the Pi)

Before connecting the Pi Zero at all, just prove the Pico can read a cart.

1. Wire up GBA cart to Pico per Phase A above
2. Flash this firmware to the Pico: **[gba-cart-reader for RP2040](https://github.com/arl/gba-cart)** (or search GitHub for "RP2040 GBA cart reader")
3. Open Arduino Serial Monitor or any serial terminal at 115200 baud
4. Insert a GBA cart and power up
5. You should see ROM header data printing — game title, checksum, etc.

If you see garbage or nothing, double-check GND connections first (most common issue), then check VDD is actually 3.3V.

---

## Common Mistakes

- **No common GND between Pico, cart, and Pi Zero** → nothing works
- **Plugging 5V GB cart directly into Pico GPIO** → fried Pico
- **Using PWR port on Pi Zero for OTG** → won't work, needs the USB data port
- **Forgetting VBUS isn't available without USB** → if powering Pico from battery later, you'll need a separate 5V boost converter for GB/GBC carts
- **Level shifter not powered** → signals don't shift, looks like bad wiring

---

## Next Steps After Proof of Concept Works

1. Install **RetroPie** or **Batocera** on the Pi Zero 2W microSD
2. Write a small Python script on the Pi that:
   - Listens on `/dev/ttyACM0`
   - Receives ROM dump from Pico
   - Saves it to `/home/pi/roms/gba/game.gba`
   - Launches RetroArch with that ROM
   - Monitors the save file for changes
   - Sends updated save back to Pico to write to cart
3. That's the full loop — insert cart, play, pull cart, play on original hardware, progress intact
