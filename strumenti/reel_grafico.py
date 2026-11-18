#!/usr/bin/env python3
"""Reel "grafico che cresce" - Mentalità Capitale.
Bande nere, grafico del prezzo che si disegna mese per mese, anno grande sotto,
etichette sugli eventi. Uso: python3 reel_grafico.py out.mp4"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/inter/InterDisplay-"
F = lambda n, s: ImageFont.truetype(FD + n + ".otf", s)
BLUE = (77, 163, 255); WHITE = (255, 255, 255); GREY = (140, 140, 140); DARK = (40, 40, 40)
MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]

data = [(x.split()[0], float(x.split()[1])) for x in open("data.txt").read().strip().split(";")]
eventi = {"2001-10": "GTA III", "2002-10": "Vice City", "2004-10": "San Andreas",
          "2008-04": "GTA IV", "2013-09": "GTA V", "2018-10": "Red Dead 2"}

# tempo: ogni mese 1 unità, i mesi di uscita +14 (pausa); 13 s di grafico, poi 4 s finali
w = [1 + (14 if d in eventi else 0) for d, _ in data]
T_CHART, T_END = 13.0, 4.5
cum = [0]
for x in w: cum.append(cum[-1] + x)
tot = cum[-1]

def idx_at(t):  # indice frazionario del mese mostrato al tempo t
    u = min(t / T_CHART, 1) * tot
    for i in range(len(w)):
        if cum[i + 1] >= u:
            return i + min(1, (u - cum[i]) / w[i]) if w[i] == 1 else i + (1 if u - cum[i] > 0.5 else 0.999)
    return len(data) - 1

# area grafico
X0, X1, Y0, Y1 = 90, 990, 640, 1240

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for wd in text.split():
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) > maxw and cur: out.append(cur); cur = wd
        else: cur = t
    return out + [cur]

def frame(t):
    im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    # titolo (banda alta)
    ft = F("Bold", 60)
    lines = ["L'andamento di Take-Two,", "la società di GTA,", "dal 2001 a oggi"]
    y = 300
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=ft); d.text(((W - tw) / 2, y), l, font=ft, fill=WHITE if i != 1 else BLUE); y += 76
    sub = "Prezzo di un'azione, in dollari"
    d.text(((W - d.textlength(sub, font=F("Regular", 32))) / 2, y + 14), sub, font=F("Regular", 32), fill=GREY)

    fi = idx_at(t); n = int(fi)
    pts = data[: n + 1]
    vmax = max(v for _, v in pts) * 1.18
    vmax = max(vmax, 30)
    xs = lambda i: X0 + (X1 - X0) * (i / max(fi, 12))
    ys = lambda v: Y1 - (Y1 - Y0) * (v / vmax)
    # griglia leggera
    for k in range(1, 4):
        gv = vmax * k / 4; gy = ys(gv)
        d.line([X0, gy, X1, gy], fill=(25, 25, 25), width=2)
        lab = f"{gv:,.0f} $".replace(",", ".")
        d.text((X0, gy - 34), lab, font=F("Regular", 24), fill=(90, 90, 90))
    d.line([X0, Y1, X1, Y1], fill=DARK, width=2)
    # eventi già passati: linee verticali + etichette su 2 righe, senza sovrapposizioni
    fe = F("SemiBold", 26)
    evs = [(xs(i), eventi[dt]) for i, (dt, v) in enumerate(pts) if dt in eventi]
    for x, _ in evs:
        for yy in range(int(Y0), int(Y1), 18): d.line([x, yy, x, yy + 9], fill=(60, 60, 60), width=2)
    rows = [[], []]
    for x, lab in reversed(evs):
        lw = d.textlength(lab, font=fe); a = min(max(x - lw / 2, 10), W - lw - 10); b = a + lw
        for r in range(2):
            if all(b + 14 < a2 or a - 14 > b2 for a2, b2 in rows[r]):
                rows[r].append((a, b)); d.text((a, Y1 + 12 + r * 34), lab, font=fe, fill=GREY); break
    if t >= T_CHART:  # GTA 6 in arrivo
        x = X1
        for yy in range(int(Y0), int(Y1), 18): d.line([x, yy, x, yy + 9], fill=BLUE, width=3)
    # linea
    poly = [(xs(i), ys(v)) for i, (_, v) in enumerate(pts)]
    if n + 1 < len(data):  # interpolazione fino al punto corrente
        a = fi - n; v = pts[-1][1] + (data[n + 1][1] - pts[-1][1]) * a
        poly.append((xs(fi), ys(v)))
    else:
        v = pts[-1][1]
    if len(poly) > 1: d.line(poly, fill=WHITE, width=6, joint="curve")
    cx, cy = poly[-1]
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=BLUE)
    pl = f"{pts[-1][1]:.2f} $".replace(".", ",")
    fp = F("Bold", 40); pw = d.textlength(pl, font=fp)
    lx, ly = cx - pw - 26, max(cy - 70, Y0 - 60)
    d.rectangle([lx - 10, ly - 4, lx + pw + 10, ly + 50], fill=(0, 0, 0))
    d.text((lx, ly), pl, font=fp, fill=WHITE)

    # banda bassa: anno grande + evento
    cur = data[min(n, len(data) - 1)][0]
    yy, mm = cur.split("-")
    fy = F("Bold", 150); yw = d.textlength(yy, font=fy)
    d.text(((W - yw) / 2, 1320), yy, font=fy, fill=WHITE)
    if cur in eventi and t < T_CHART:
        ev = "Esce " + eventi[cur]; fv = F("Bold", 54); vw = d.textlength(ev, font=fv)
        d.text(((W - vw) / 2, 1500), ev, font=fv, fill=BLUE)
    # finale
    if t >= T_CHART:
        fz = F("Bold", 52); msg = "Giovedì 19 novembre esce GTA 6."
        d.text(((W - d.textlength(msg, font=fz)) / 2, 1500), msg, font=fz, fill=BLUE)
        s2 = "Ott. 2001: 9,29 $  →  Nov. 2026: 227,82 $"
        f2 = F("SemiBold", 38); d.text(((W - d.textlength(s2, font=f2)) / 2, 1580), s2, font=f2, fill=WHITE)
    fs = F("Regular", 22)
    src = "Fonte: Yahoo Finance, chiusure mensili rettificate per gli split. I rendimenti passati non sono indicativi di quelli futuri."
    y = 1760
    for l in wrap(d, src, fs, W - 160):
        d.text(((W - d.textlength(l, font=fs)) / 2, y), l, font=fs, fill=(110, 110, 110)); y += 30
    return im

def main(out):
    N = int((T_CHART + T_END) * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for f in range(N):
        p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()
    for t in (2.0, 8.5, 16.5):
        frame(t).resize((360, 640)).save(f"anteprima_{t}.png")

if __name__ == "__main__":
    main(sys.argv[1])
