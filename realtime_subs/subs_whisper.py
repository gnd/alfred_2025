#!/usr/bin/env python3
"""
Realtime 5‑second chunk transcription with **whisper.cpp**
---------------------------------------------------------

•   **CLI flags** override values in *config.ini*.
•   *config.ini* overrides the built‑in sane defaults below.

Sample *config.ini*::

    [whisper]
    sample_rate   = 16000
    channels      = 1
    chunk_seconds = 5
    whisper_bin   = ./main
    whisper_model = ggml-base.en.bin

Prerequisites
~~~~~~~~~~~~~
1. Build whisper.cpp and download a model, or point to them in *config.ini*.
2. ``pip install sounddevice numpy``
3. ``python realtime_whisper_poc.py`` (or pass flags like ``--rate 8000``)
"""
import argparse
import configparser
import os
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULTS = {
    "sample_rate":   16_000,
    "channels":      1,
    "chunk_seconds": 5,
    "whisper_bin":   "./main",  # whisper.cpp executable
    "whisper_model": os.environ.get("WHISPER_MODEL", "ggml-base.en.bin"),
}
CONFIG_FILE = "config.ini"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(path: str = CONFIG_FILE) -> dict:
    """Return a config dict, falling back to :pydata:`DEFAULTS`."""
    cfg = DEFAULTS.copy()
    parser = configparser.ConfigParser()
    if parser.read(path) and parser.has_section("whisper"):
        sec = "whisper"
        cfg["sample_rate"]   = parser.getint(sec, "sample_rate",   fallback=cfg["sample_rate"])
        cfg["channels"]      = parser.getint(sec, "channels",      fallback=cfg["channels"])
        cfg["chunk_seconds"] = parser.getint(sec, "chunk_seconds", fallback=cfg["chunk_seconds"])
        cfg["whisper_bin"]   = parser.get(sec,    "whisper_bin",   fallback=cfg["whisper_bin"])
        cfg["whisper_model"] = parser.get(sec,    "whisper_model", fallback=cfg["whisper_model"])
    return cfg


def transcribe_to_txt(input_filename: str, output_stem: str, bin_path: str, model_path: str) -> None:
    """Call whisper.cpp to transcribe *input_filename* → ``output_stem.txt``."""
    print("Running whisper transcription…", flush=True)
    cmd = [
        bin_path,
        "-m", model_path,
        "-f", input_filename,
        "-otxt",
        "-of", output_stem,
        "-np",  # no progress bar
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr or "Whisper exited with non‑zero code", file=sys.stderr)
    else:
        print("Successful run.")


def build_callback(cfg: dict):
    """Factory that returns the sounddevice callback bound to *cfg*."""
    sample_rate = cfg["sample_rate"]
    channels = cfg["channels"]

    def callback(indata: np.ndarray, frames: int, time_info, status):
        if status:
            print(status, flush=True)

        # 1. Save the raw buffer to a temporary WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", prefix="audio_", dir=".") as tmpwav:
            with wave.open(tmpwav, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 16‑bit samples → 2 bytes
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(indata.tobytes())
            tmpwav_path = Path(tmpwav.name)

        # 2. Transcribe
        stem = tmpwav_path.with_suffix("").name
        transcribe_to_txt(tmpwav_path.as_posix(), stem, cfg["whisper_bin"], cfg["whisper_model"])

        # 3. Print result
        txt_path = Path(f"{stem}.txt")
        if txt_path.exists():
            with txt_path.open() as fh:
                print(fh.read().strip())
            txt_path.unlink(missing_ok=True)
        tmpwav_path.unlink(missing_ok=True)

    return callback

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    cfg = load_config()

    parser = argparse.ArgumentParser(description="Realtime whisper.cpp transcription")
    parser.add_argument("--rate",        type=int, help="Sample rate (Hz)")
    parser.add_argument("--seconds",     type=int, dest="chunk_seconds", help="Chunk length in seconds")
    parser.add_argument("--channels",    type=int, help="Number of audio channels")
    parser.add_argument("--bin",         dest="whisper_bin",   help="Path to whisper.cpp executable")
    parser.add_argument("--model",       dest="whisper_model", help="Path to whisper model file")
    args = parser.parse_args()

    # Override config with CLI flags that were actually provided
    for k, v in vars(args).items():
        if v is not None:
            cfg[k] = v

    sample_rate   = cfg["sample_rate"]
    channels      = cfg["channels"]
    chunk_seconds = cfg["chunk_seconds"]
    blocksize     = sample_rate * chunk_seconds

    print("Recording… Press Ctrl+C to stop.")
    try:
        with sd.InputStream(
            callback=build_callback(cfg),
            dtype="int16",
            channels=channels,
            samplerate=sample_rate,
            blocksize=blocksize,
        ):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Recording stopped.")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
