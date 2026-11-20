#!/usr/bin/env python3
"""Reel tipo B "Stesso stipendio, due scelte" - Mentalità Capitale.

Due omini con lo stesso stipendio; mese per mese il conto di uno si svuota, quello dell'altro cresce.
Uso: python3 reel_due_scelte.py contenuto.json uscita.mp4 [secondo]  (con il secondo salva un fotogramma .png)

contenuto.json: titolo[2], stipendio, sinistra{nome, sotto, picco, motivi[]}, destra{nome, sotto, mensile},
mesi, anni_finali, chiusura, invito[], nota
"""
import json, math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/inter/"
BLUE, WHITE, GREY, RED, BG = (77, 163, 255), (255, 255, 255), (150, 150, 150), (255, 90, 90), (10, 10, 12)

def F(n, s): return ImageFont.truetype(FD + n, s)
fT, fM, fN, fS, fV, fP, fC, fI, fNo = (F("Inter-Black.otf", 66), F("Inter-Black.otf", 54), F("Inter-Black.otf", 50),
    F("Inter-Bold.otf", 32), F("Inter-Black.otf", 60), F("Inter-Bold.otf", 34), F("Inter-ExtraBold.otf", 44),
    F("Inter-Black.otf", 36), F("Inter-Regular.otf", 24))

def eur(x): return f"{int(round(x)):,}".replace(",", ".") + " €"
def ease(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)

def ctext(d, y, s, f, fill, cx=W // 2):
    d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill)

def omino(d, cx, y, col, bounce=0):
    y -= bounce
    d.ellipse([cx - 42, y, cx + 42, y + 84], fill=col)
    d.rounded_rectangle([cx - 62, y + 96, cx + 62, y + 210], radius=46, fill=col)

def frame(c, t):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    T_MESI, T_SALTO, T_FINE = c["t_mesi"], c["t_salto"], c["t_fine"]
    mesi = c["mesi"]; dur_m = T_MESI / mesi
    L, R = c["sinistra"], c["destra"]
    xl, xr = 300, 740
    # titolo (fermo dal primo fotogramma, dentro la fascia 3:4)
    ctext(d, 250, c["titolo"][0], fT, WHITE)
    ctext(d, 328, c["titolo"][1], fT, BLUE)
    # fase
    if t < T_MESI:
        m = int(t // dur_m) + 1; fm = (t % dur_m) / dur_m
        ctext(d, 440, f"MESE {m}", fM, WHITE)
        vr = R["mensile"] * (m - 1 + ease(fm / 0.5))
        # sinistra: sale un po' e poi crolla a zero con un motivo
        up = L["picco"] * ease(fm / 0.45)
        vl = up if fm < 0.55 else L["picco"] * (1 - ease((fm - 0.55) / 0.3))
        motivo = L["motivi"][(m - 1) % len(L["motivi"])] if fm >= 0.5 else None
        scale = R["mensile"] * mesi
    else:
        k = ease((t - T_MESI) / (T_SALTO - T_MESI))
        ctext(d, 440, f"DOPO {c['anni_finali']} ANNI", fM, WHITE)
        vr = R["mensile"] * (mesi + k * (c["anni_finali"] * 12 - mesi))
        vl, motivo, scale = 0, None, R["mensile"] * mesi * (1 - k) + R["mensile"] * c["anni_finali"] * 12 * k
    # omini e nomi
    bounce = 10 * abs(math.sin(t * 6)) if t < T_SALTO else 0
    omino(d, xl, 540, (200, 200, 200), 0)
    omino(d, xr, 540, BLUE, bounce)
    for x, P in ((xl, L), (xr, R)):
        ctext(d, 772, P["nome"], fN, WHITE, x)
        for i, s in enumerate(P["sotto"]):
            ctext(d, 832 + i * 38, s, fS, GREY, x)
    # barre del conto
    top, bot, bw = 960, 1270, 170
    for x, v, col in ((xl, vl, (200, 200, 200)), (xr, vr, BLUE)):
        d.rounded_rectangle([x - bw / 2, top, x + bw / 2, bot], radius=18, outline=(70, 70, 75), width=4)
        h = (bot - top - 8) * min(1, v / scale)
        if h > 2: d.rounded_rectangle([x - bw / 2 + 4, bot - 4 - h, x + bw / 2 - 4, bot - 4], radius=14, fill=col)
        ctext(d, 1285, eur(v if t >= T_MESI or x == xr else (0 if v < 1 else v)), fV, col if x == xr else WHITE, x)
    if motivo:
        ctext(d, 912, motivo, fP, RED, xl)
    if t < T_MESI and fm < 0.5:
        ctext(d, 912, "+" + eur(R["mensile"]), fP, BLUE, xr)
    # finale
    if t >= T_SALTO:
        y = 1378
        s = c["chiusura"]; w = d.textlength(s, font=fC) + 56
        d.rounded_rectangle([W / 2 - w / 2, y, W / 2 + w / 2, y + 74], radius=16, fill=WHITE)
        ctext(d, y + 12, s, fC, (12, 12, 12))
        y += 90
        w = max(d.textlength(s, font=fI) for s in c["invito"]) + 52
        d.rounded_rectangle([W / 2 - w / 2, y, W / 2 + w / 2, y + 30 + 46 * len(c["invito"])], radius=16, fill=BLUE)
        for i, s in enumerate(c["invito"]):
            ctext(d, y + 14 + i * 46, s, fI, WHITE)
    ctext(d, 1556, c["nota"], fNo, (120, 120, 120))
    return im

frame_cache = {}

def main():
    c = json.load(open(sys.argv[1])); out = sys.argv[2]
    if len(sys.argv) > 3:
        frame(c, float(sys.argv[3])).save(out); return
    n = int(c["t_fine"] * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(frame(c, i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
