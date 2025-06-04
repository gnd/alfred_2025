#!/usr/bin/env python3
"""
midimix_monitor.py — *super‑minimal* MIDI monitor for the Akai MIDImix (or any
controller).

•   Lists every incoming MIDI event in plain text so you can see which **CC** or
    **note** number each button/knob sends.
•   No dependencies beyond *mido* + *python‑rtmidi*.

    pip install mido python-rtmidi

Run it and start twiddling knobs / pressing buttons — numbers will scroll in the
terminal.  Press **Ctrl‑C** to quit.
"""
import sys
import mido


def open_default_port():
    """Pick the first available MIDI‑IN port (quick & dirty)."""
    names = mido.get_input_names()
    if not names:
        sys.exit("No MIDI input ports detected.")
    print("Opening MIDI port:", names[1])
    return mido.open_input(names[1])


def pretty_print(msg: mido.Message) -> None:
    """Print a human‑readable one‑liner for the incoming MIDI message."""
    if msg.type == "control_change":
        # Akai MIDImix uses only CC messages (0‑119)
        print(f"CC  {msg.control:3}  value={msg.value}")
    elif msg.type == "note_on":
        print(f"NOTE ON  {msg.note:3}  vel={msg.velocity}")
    elif msg.type == "note_off":
        print(f"NOTE OFF {msg.note:3}")
    else:
        print(msg)


def main() -> None:
    with open_default_port() as inport:
        print("Listening…  Ctrl‑C to exit.")
        try:
            for msg in inport:  # this loop blocks until a message arrives
                pretty_print(msg)
        except KeyboardInterrupt:
            print("\nExiting.")


if __name__ == "__main__":
    main()
