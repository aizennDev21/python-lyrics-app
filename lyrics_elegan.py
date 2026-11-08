#!/usr/bin/env python3
"""
Lirik elegan di terminal: teks di tengah layar, baris lama meredup,
kursor ketik, header judul, dan progress bar. Tanpa library tambahan.

CARA PAKAI:
  1. Siapkan file  lyrics.lrc  di folder yang sama (format [mm:ss.xx] teks).
  2. Jalankan:  python3 lyrics_elegan.py
  3. Tekan Ctrl+C kapan saja untuk berhenti.

Alternatif: isi list `lyrics` di bawah dengan format (delay_detik, "teks").
"""

import os
import re
import shutil
import sys
import textwrap
import time

# Alternatif: tempel list (delay, teks) milik Anda di sini. Boleh dikosongkan.
lyrics = [
]

# ---------------- PENGATURAN ----------------
FILE_LRC = "lyrics.lrc"
JUDUL = "The World Is Ugly"
ARTIS = "My Chemical Romance"
COUNTDOWN = 3              # detik, 0 = mati
FRAKSI_KETIK = 0.85        # porsi waktu antar baris yang dipakai mengetik
MAX_JEDA_HURUF = 0.12      # jeda maksimal per huruf (detik)
DURASI_BARIS_TERAKHIR = 3.0
JUMLAH_RIWAYAT = 3         # berapa baris lama yang masih terlihat (meredup)
KURSOR = "▌"

# Palet warna (RGB)
TEKS_AKTIF = (245, 240, 228)                       # putih gading
REDUP = [(150, 142, 135), (100, 95, 92), (62, 59, 58)]
AKSEN = (158, 28, 48)                              # merah marun
GARIS = (70, 66, 64)
# --------------------------------------------

RESET = "\033[0m"
LRC_PATTERN = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")
# Bobot jeda: tanda baca membuat ketikan berhenti sejenak
BOBOT = {",": 4.0, ";": 4.0, ":": 4.0, ".": 6.0, "?": 6.0, "!": 6.0, ")": 2.0}


def warna(rgb, tebal=False):
    r, g, b = rgb
    return f"\033[{'1;' if tebal else ''}38;2;{r};{g};{b}m"


def ukuran():
    s = shutil.get_terminal_size((80, 24))
    return s.columns, s.lines


def fmt_waktu(detik):
    detik = int(max(detik, 0))
    return f"{detik // 60:02d}:{detik % 60:02d}"


# ---------------- DATA ----------------
def baca_lrc(path):
    hasil = []
    with open(path, "r", encoding="utf-8") as f:
        for baris in f:
            m = LRC_PATTERN.match(baris.strip())
            if m:
                menit, detik, teks = m.groups()
                hasil.append((int(menit) * 60 + float(detik), teks.strip()))
    hasil.sort(key=lambda x: x[0])
    return hasil


def dari_list_delay(daftar):
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
    t0 = timeline[0][0]
    return [(t - t0, teks) for t, teks in timeline]


# ---------------- TAMPILAN ----------------
def render(riwayat, aktif, tampil, mengetik, elapsed, total):
    cols, rows = ukuran()
    out = []

    def tulis(r, teks_polos, teks_berwarna):
        kol = max((cols - len(teks_polos)) // 2, 0) + 1
        out.append(f"\033[{r};{kol}H{teks_berwarna}{RESET}")

    # bersihkan layar baris demi baris (minim kedip)
    for r in range(1, rows + 1):
        out.append(f"\033[{r};1H\033[2K")

    # header
    if rows >= 12:
        tulis(2, JUDUL, warna(TEKS_AKTIF, True) + JUDUL)
        tulis(3, ARTIS, warna(REDUP[0]) + ARTIS)
        garis = "─" * min(max(cols - 10, 4), 28)
        tulis(4, garis, warna(GARIS) + garis)

    zona_atas = 6 if rows >= 12 else 1
    zona_bawah = rows - 4 if rows >= 10 else rows
    tengah = (zona_atas + zona_bawah) // 2

    # riwayat (meredup ke atas)
    for k, baris in enumerate(reversed(riwayat[-JUMLAH_RIWAYAT:]), start=1):
        r = tengah - k
        if r < zona_atas or not baris:
            continue
        if len(baris) > cols - 4:
            baris = baris[: cols - 5] + "…"
        tulis(r, baris, warna(REDUP[min(k - 1, len(REDUP) - 1)]) + baris)

    # baris aktif (dibungkus agar muat; posisi tiap baris tetap, tidak bergeser)
    if aktif:
        bungkus = textwrap.wrap(aktif, width=max(cols - 10, 20)) or [aktif]
        terpakai = 0
        kursor_ditaruh = False
        for idx, wl in enumerate(bungkus):
            ambil = max(0, min(len(wl), tampil - terpakai))
            bagian = wl[:ambil]
            kol = max((cols - len(wl)) // 2, 0) + 1
            teks = warna(TEKS_AKTIF, True) + bagian
            if mengetik and not kursor_ditaruh and tampil <= terpakai + len(wl):
                teks += warna(AKSEN, True) + KURSOR
                kursor_ditaruh = True
            if ambil > 0 or (mengetik and kursor_ditaruh and idx == 0):
                out.append(f"\033[{tengah + idx};{kol}H{teks}{RESET}")
            terpakai += len(wl) + 1

    # footer: progress bar
    if rows >= 10 and total > 0:
        lebar = max(min(40, cols - 18), 10)
        frac = min(max(elapsed / total, 0), 1)
        terisi = int(frac * lebar)
        if terisi < lebar:
            depan = "━" * terisi + "╸"
            belakang = "─" * (lebar - terisi - 1)
        else:
            depan, belakang = "━" * lebar, ""
        kiri, kanan = fmt_waktu(elapsed), fmt_waktu(total)
        polos = f"{kiri} {depan}{belakang} {kanan}"
        berwarna = (
            warna(REDUP[0]) + kiri + " "
            + warna(AKSEN) + depan
            + warna(GARIS) + belakang + " "
            + warna(REDUP[0]) + kanan
        )
        tulis(rows - 2, polos, berwarna)

    out.append(f"\033[{rows};1H")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def hitung_mundur(n):
    for i in range(n, 0, -1):
        cols, rows = ukuran()
        sys.stdout.write("\033[2J")
        kol = max(cols // 2, 1)
        sys.stdout.write(f"\033[{rows // 2};{kol}H{warna(AKSEN, True)}{i}{RESET}")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\033[2J")
    sys.stdout.flush()


# ---------------- PEMUTAR ----------------
def putar(timeline):
    total = timeline[-1][0] + DURASI_BARIS_TERAKHIR
    riwayat = []
    sekarang = ""   # baris terakhir yang sudah tampil penuh
    start = time.monotonic()

    def elapsed():
        return time.monotonic() - start

    def diam_sampai(target):
        while True:
            e = elapsed()
            if e >= target:
                return
            render(riwayat, sekarang, len(sekarang), False, e, total)
            time.sleep(min(0.1, target - e))

    for i, (t, teks) in enumerate(timeline):
        diam_sampai(t)

        if not teks:  # pemisah bait
            if sekarang:
                riwayat.append(sekarang)
            riwayat.append("")
            sekarang = ""
            continue

        if sekarang:
            riwayat.append(sekarang)
        sekarang = teks

        celah = (timeline[i + 1][0] - t) if i + 1 < len(timeline) else DURASI_BARIS_TERAKHIR
        jendela = max(celah * FRAKSI_KETIK, 0.5)

        bobot = [BOBOT.get(teks[j - 1], 1.0) if j > 0 else 1.0 for j in range(len(teks))]
        dasar = min(jendela / sum(bobot), MAX_JEDA_HURUF)

        mulai_baris = elapsed()
        kumulatif = 0.0
        for n in range(1, len(teks) + 1):
            render(riwayat, sekarang, n, True, elapsed(), total)
            kumulatif += dasar * bobot[n - 1]
            sisa = (mulai_baris + kumulatif) - elapsed()
            if sisa > 0:
                time.sleep(sisa)
        render(riwayat, sekarang, len(teks), False, elapsed(), total)

    diam_sampai(total)


def main():
    timeline = siapkan_timeline()
    os.system("")  # mengaktifkan ANSI di Windows
    sys.stdout.write("\033[?1049h\033[?25l")  # layar alternatif + sembunyikan kursor
    sys.stdout.flush()
    try:
        if COUNTDOWN > 0:
            hitung_mundur(COUNTDOWN)
        putar(timeline)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(f"{RESET}\033[?25h\033[?1049l")  # pulihkan terminal
        sys.stdout.flush()


if __name__ == "__main__":
    main()