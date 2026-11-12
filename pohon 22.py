"""
Pohon Natal 3D berputar di terminal (tanpa library tambahan).

Teknik yang menciptakan ilusi 3D:
  1. Proyeksi perspektif  -> yang dekat tampak besar, yang jauh kecil
  2. Z-buffer             -> titik yang dekat menutupi titik yang jauh
  3. Shading kedalaman    -> yang dekat terang & tebal, yang jauh gelap & tipis
  4. Rotasi + kemiringan  -> kamera sedikit melihat dari atas
  5. Salju paralaks       -> butiran dekat jatuh tampak lebih besar

Jalankan : python pohon3d.py
Berhenti : Ctrl+C
"""
import math
import random
import shutil
import sys
import time

RESET = "\033[0m"


def warna(n):
    return f"\033[38;5;{n}m"


random.seed(7)

TINGGI = 10.0          # tinggi kerucut pohon
JARAK_KAMERA = 16.0    # jarak kamera dari pusat pohon
GESER_Y = -(TINGGI / 2) + 1


def radius(y):
    """Radius pohon di ketinggian y, berbentuk tingkat bergerigi."""
    t = y / TINGGI
    tingkat = 4
    lokal = (t * tingkat) % 1.0
    return (4.6 * (1 - t) + 0.4) * (1 - 0.35 * lokal)


# Setiap titik: [x, y, z, tipe, warna_dasar, id]
titik = []


def tambah(x, y, z, tipe, w=0):
    titik.append([x, y + GESER_Y, z, tipe, w, len(titik)])


# Daun
for _ in range(2800):
    y = TINGGI * random.random() ** 0.9
    a = random.uniform(0, 2 * math.pi)
    r = radius(y) * random.uniform(0.9, 1.0)
    tambah(r * math.cos(a), y, r * math.sin(a), "daun")

# Batang
for _ in range(220):
    y = random.uniform(-2.2, 0.2)
    a = random.uniform(0, 2 * math.pi)
    r = 0.7 * random.uniform(0.85, 1.0)
    tambah(r * math.cos(a), y, r * math.sin(a), "batang")

# Untaian lampu spiral (emas)
for i in range(420):
    t = i / 420
    y = t * TINGGI * 0.97
    a = t * 16 * math.pi
    r = radius(y) * 1.04
    tambah(r * math.cos(a), y, r * math.sin(a), "emas")

# Bola hias
WARNA_HIAS = [196, 21, 201, 51, 226, 208]
for _ in range(55):
    y = random.uniform(0.4, TINGGI * 0.9)
    a = random.uniform(0, 2 * math.pi)
    r = radius(y) * 1.05
    tambah(r * math.cos(a), y, r * math.sin(a), "hias", random.choice(WARNA_HIAS))

# Bintang di puncak
for _ in range(90):
    a = random.uniform(0, 2 * math.pi)
    b = random.uniform(0, math.pi)
    r = random.uniform(0.15, 0.45)
    tambah(r * math.sin(b) * math.cos(a),
           TINGGI + 0.5 + r * math.cos(b),
           r * math.sin(b) * math.sin(a), "bintang")

# Salju
SALJU = []
for _ in range(170):
    SALJU.append([random.uniform(-9, 9), random.uniform(-7, 9),
                  random.uniform(-9, 9), random.uniform(0.05, 0.14)])

HIJAU = [22, 28, 34, 40, 46, 83]
CHAR_DAUN = ".:+*#@"


def render(sudut, miring, w, h, frame):
    cs, sn = math.cos(sudut), math.sin(sudut)
    ct, st = math.cos(miring), math.sin(miring)
    fokus = JARAK_KAMERA * h * 0.82 / 13.5
    buf = [[None] * w for _ in range(h)]

    def taruh(x, y, z, ch, warna_kode):
        # putar mengelilingi sumbu Y
        xr = x * cs + z * sn
        zr = -x * sn + z * cs
        # miringkan kamera (sumbu X)
        yr = y * ct - zr * st
        zr2 = y * st + zr * ct
        kedalaman = zr2 + JARAK_KAMERA
        if kedalaman < 1:
            return
        f = fokus / kedalaman
        sx = int(w / 2 + xr * f * 2)      # x2 karena karakter lebih tinggi dari lebar
        sy = int(h / 2 - yr * f)
        if 0 <= sx < w and 0 <= sy < h:
            sel = buf[sy][sx]
            if sel is None or kedalaman < sel[0]:
                buf[sy][sx] = (kedalaman, ch, warna_kode)

    def dekat(x, y, z):
        """0 (jauh) .. 1 (dekat), dipakai untuk shading."""
        zr = -x * sn + z * cs
        zr2 = y * st + (zr * ct)
        k = (zr2 + JARAK_KAMERA - (JARAK_KAMERA - 5.5)) / 11.0
        return 1 - min(max(k, 0), 1)

    for x, y, z, tipe, w0, idx in titik:
        n = dekat(x, y, z)
        if tipe == "daun":
            i = min(int(n * 6), 5)
            taruh(x, y, z, CHAR_DAUN[i], HIJAU[i])
        elif tipe == "batang":
            taruh(x, y, z, "#" if n > 0.4 else ":", 94 if n > 0.4 else 58)
        elif tipe == "emas":
            taruh(x, y, z, "*" if n > 0.5 else "+", 220 if n > 0.5 else 136)
        elif tipe == "hias":
            kedip = (frame // 4 + idx) % 4 == 0
            taruh(x, y, z, "O" if n > 0.45 else "o", 231 if kedip else w0)
        elif tipe == "bintang":
            kedip = (frame // 3) % 2 == 0
            taruh(x, y, z, "@" if n > 0.5 else "*", 226 if kedip else 229)

    # salju: butiran dekat tampak lebih besar & terang
    for s in SALJU:
        s[1] -= s[3]
        if s[1] < -7:
            s[1] = 9
        n = dekat(s[0], s[1], s[2])
        taruh(s[0], s[1], s[2], "*" if n > 0.75 else ".", 255 if n > 0.5 else 244)

    baris = []
    for row in buf:
        out = []
        for sel in row:
            if sel is None:
                out.append(" ")
            else:
                out.append(f"{warna(sel[2])}{sel[1]}{RESET}")
        baris.append("".join(out))
    return "\n".join(baris)


def main():
    kolom, baris = shutil.get_terminal_size((80, 30))
    w = min(kolom, 100)
    h = max(baris - 3, 15)
    sys.stdout.write("\033[?25l\033[2J")
    try:
        frame = 0
        while True:
            sudut = frame * 0.05
            miring = 0.35 + 0.12 * math.sin(frame * 0.03)
            sys.stdout.write("\033[H" + render(sudut, miring, w, h, frame))
            teks = "Merry Christmas!"
            sys.stdout.write(f"\n{' ' * max((w - len(teks)) // 2, 0)}"
                             f"{warna(226)}{teks}{RESET}\n")
            sys.stdout.flush()
            frame += 1
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h" + RESET + "\nSelamat Natal!\n")


if __name__ == "__main__":
    main()