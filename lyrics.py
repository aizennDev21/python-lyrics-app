#!/usr/bin/env python3
"""
Lirik per huruf di terminal.

CARA PAKAI (paling mudah):
  1. Di folder yang sama dengan file ini, buat file teks bernama  lyrics.lrc
  2. Tempel lirik berformat LRC ke dalamnya, contoh baris:  [02:58.34]teks lirik
  3. Jalankan:  python3 lyrics.py

CARA ALTERNATIF:
  Isi list `lyrics` di bawah dengan format (delay_detik, "teks").
  Kalau list ini terisi, file lyrics.lrc diabaikan.
"""

import os
import re
import sys
import time

# Alternatif: tempel list (delay, teks) milik Anda di sini. Boleh dikosongkan.
lyrics = [
]

# ---------------- PENGATURAN ----------------
FILE_LRC = "lyrics.lrc"
COUNTDOWN = 3            # hitung mundur sebelum mulai (detik), 0 = mati
FRAKSI_KETIK = 0.85      # porsi waktu antar baris yang dipakai mengetik
MAX_JEDA_HURUF = 0.12    # jeda maksimal per huruf (detik)
DURASI_BARIS_TERAKHIR = 2.0
# --------------------------------------------

LRC_PATTERN = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")


def baca_lrc(path):
    """Baca file LRC -> list (waktu_absolut_detik, teks)."""
    hasil = []
    with open(path, "r", encoding="utf-8") as f:
        for baris in f:
            m = LRC_PATTERN.match(baris.strip())
            if not m:
                continue
            menit, detik, teks = m.groups()
            hasil.append((int(menit) * 60 + float(detik), teks.strip()))
    hasil.sort(key=lambda x: x[0])
    return hasil


def dari_list_delay(daftar):
    """Ubah list (delay, teks) -> list (waktu_absolut, teks)."""
    hasil, t = [], 0.0
    for delay, teks in daftar:
        t += delay
        hasil.append((t, teks))
    return hasil


def siapkan_timeline():
    if lyrics:
        timeline = dari_list_delay(lyrics)
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(folder, FILE_LRC)
        if not os.path.exists(path):
            print(f"File '{FILE_LRC}' tidak ditemukan di folder:\n  {folder}")
            print("Buat file tersebut dan tempel lirik berformat [mm:ss.xx] ke dalamnya.")
            sys.exit(1)
        timeline = baca_lrc(path)
        if not timeline:
            print(f"Tidak ada baris berformat [mm:ss.xx] di '{FILE_LRC}'.")
            sys.exit(1)

    # Mulai dari lirik pertama (jeda intro dilewati)
    t0 = timeline[0][0]
    return [(t - t0, teks) for t, teks in timeline]


def tunggu_sampai(start, target):
    while True:
        sisa = target - (time.monotonic() - start)
        if sisa <= 0:
            return
        time.sleep(min(sisa, 0.01))


def ketik(teks, durasi):
    jeda = min(durasi / len(teks), MAX_JEDA_HURUF)
    for huruf in teks:
        sys.stdout.write(huruf)
        sys.stdout.flush()
        time.sleep(jeda)
    sys.stdout.write("\n")
    sys.stdout.flush()


def hitung_mundur(n):
    for i in range(n, 0, -1):
        sys.stdout.write(f"\rMulai dalam {i}... ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 20 + "\r")
    sys.stdout.flush()


def main():
    timeline = siapkan_timeline()

    try:
        if COUNTDOWN > 0:
            hitung_mundur(COUNTDOWN)

        start = time.monotonic()
        sebelumnya_teks = False

        for i, (t, teks) in enumerate(timeline):
            tunggu_sampai(start, t)

            if not teks:  # baris kosong = pemisah bait
                if sebelumnya_teks:
                    print()
                sebelumnya_teks = False
                continue

            if i + 1 < len(timeline):
                celah = timeline[i + 1][0] - t
                durasi = max(celah * FRAKSI_KETIK, 0.5)
            else:
                durasi = DURASI_BARIS_TERAKHIR

            ketik(teks, durasi)
            sebelumnya_teks = True

    except KeyboardInterrupt:
        print("\n\nDihentikan.")


if __name__ == "__main__":
    main()