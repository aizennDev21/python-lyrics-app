#!/usr/bin/env python3
"""
Typewriter Lyrics - menampilkan lirik per huruf di terminal sesuai timestamp LRC.

Cara pakai:
  1. Simpan lirik berformat LRC (contoh baris: [02:58.34]teks lirik) ke file
     bernama  lyrics.lrc  di folder yang sama dengan skrip ini.
  2. Jalankan:
         python typewriter_lyrics.py
     atau dengan opsi:
         python typewriter_lyrics.py mylyrics.lrc --speed 1.2 --no-skip

Opsi:
  file         path file .lrc (default: lyrics.lrc)
  --speed X    pengali kecepatan mengetik (default 1.0, lebih besar = lebih cepat)
  --no-skip    jangan lewati jeda awal; tunggu sesuai timestamp pertama
                (berguna kalau Anda memutar lagunya dari awal bersamaan)
  --max-delay  jeda maksimal per huruf dalam detik (default 0.12)
"""

import argparse
import os
import re
import sys
import time

LRC_PATTERN = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")


def parse_lrc(path):
    """Baca file LRC -> list of (detik, teks)."""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            m = LRC_PATTERN.match(raw.strip())
            if not m:
                continue
            minutes, seconds, text = m.groups()
            t = int(minutes) * 60 + float(seconds)
            entries.append((t, text.strip()))
    entries.sort(key=lambda e: e[0])
    return entries


def wait_until(start, target):
    """Tunggu sampai waktu berjalan mencapai target (detik sejak start)."""
    while True:
        remaining = target - (time.monotonic() - start)
        if remaining <= 0:
            return
        time.sleep(min(remaining, 0.01))


def type_line(text, window, speed, max_delay):
    """Ketik satu baris huruf demi huruf dalam rentang waktu 'window'."""
    delay = min(window / max(len(text), 1) / speed, max_delay)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def play(entries, speed, skip_intro, max_delay):
    base = entries[0][0] if skip_intro else 0.0
    start = time.monotonic()
    last_was_text = False

    for i, (t, text) in enumerate(entries):
        target = t - base
        wait_until(start, target)

        if not text:
            # baris kosong = pemisah bait
            if last_was_text:
                print()
            last_was_text = False
            continue

        if i + 1 < len(entries):
            gap = (entries[i + 1][0] - base) - target
        else:
            gap = len(text) * 0.08
        window = max(0.3, gap * 0.85)

        type_line(text, window, speed, max_delay)
        last_was_text = True


def main():
    parser = argparse.ArgumentParser(description="Lirik muncul per huruf di terminal.")
    parser.add_argument("file", nargs="?", default="lyrics.lrc", help="file .lrc")
    parser.add_argument("--speed", type=float, default=1.0, help="kecepatan mengetik")
    parser.add_argument("--no-skip", action="store_true", help="jangan lewati jeda awal")
    parser.add_argument("--max-delay", type=float, default=0.12, help="jeda maks per huruf")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"File '{args.file}' tidak ditemukan.")
        print("Simpan lirik berformat LRC (mis. [02:58.34]teks) ke file tersebut, lalu jalankan lagi.")
        sys.exit(1)

    entries = parse_lrc(args.file)
    if not entries:
        print("Tidak ada baris berformat [mm:ss.xx] di file tersebut.")
        sys.exit(1)

    print("Mulai dalam 2 detik... (Ctrl+C untuk berhenti)\n")
    time.sleep(2)

    try:
        play(entries, args.speed, not args.no_skip, args.max_delay)
    except KeyboardInterrupt:
        print("\n\nDihentikan.")


if __name__ == "__main__":
    main()