#!/usr/bin/env python3
"""Reel B "Chi resta acceso?" v2 (24/11) – Mentalità Capitale.

Notte, tempesta. Quattro omini piegati contro il vento proteggono una fiammella tra le mani:
HYPE, VOGLIA, MOTIVAZIONE, IL TUO PERCHÉ. Ogni raffica ne spegne uno: HYPE molla subito e se ne va,
VOGLIA cade in ginocchio, MOTIVAZIONE resiste, scivola, poi finisce a terra. Anche IL TUO PERCHÉ cade,
la fiamma diventa una brace: si rannicchia sopra per proteggerla, si rialza, e la brace diventa un fuoco
che illumina tutto. Frase fissa: "LA MOTIVAZIONE È UN FIAMMIFERO." → "IL PERCHÉ È UN FUOCO."
Uso: python3 reel_acceso.py contenuto.json uscita.mp4
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 9.5)
G = 1220
K = 1.85
XS = [185, 420, 655, 885]
LAB = C["etichette"]
T_LAB = [1.05, 1.25, 1.45, 1.65]
GUSTS = [1.9, 3.5, 5.2]
T_HYPE, T_VOGLIA, T_MOT0, T_MOT1 = 1.9, 3.5, 4.4, 5.2
T_P_FALL, T_P_CURL, T_P_UP0, T_P_UP1 = 5.2, 5.5, 6.3, 6.9
T_ANS = 7.0
FLAME = (255, 228, 170)
random.seed(4)
import numpy as np
_yy, _xx = np.mgrid[0:H, 0:W]
RAD = np.exp(-(((_xx - 885) ** 2 + (_yy - 700) ** 2) / 520.0 ** 2))[..., None] * np.array([77, 163, 255]) * 0.45
RAIN = [(random.uniform(0, W + 600), random.uniform(0, H), random.uniform(0.7, 1.3)) for _ in range(140)]

LEAN = P(torso=150, head=150, ua_l=60, fa_l=115, ua_r=55, fa_r=120, th_l=28, sh_l=12, th_r=-25, sh_r=-35)
STRAIN = P(torso=135, head=140, ua_l=55, fa_l=110, ua_r=50, fa_r=118, th_l=40, sh_l=20, th_r=-35, sh_r=-50)
KNEEL = P(torso=168, head=125, ua_l=10, fa_l=10, ua_r=5, fa_r=5, th_l=5, sh_l=-90, th_r=-5, sh_r=-88)
KNEEL_HOLD = P(torso=160, head=145, ua_l=55, fa_l=110, ua_r=50, fa_r=118, th_l=5, sh_l=-90, th_r=-5, sh_r=-88)
CURL = P(torso=100, head=90, ua_l=30, fa_l=80, ua_r=25, fa_r=85, th_l=5, sh_l=-90, th_r=0, sh_r=-88)
RAISE = P(torso=180, head=185, ua_r=165, fa_r=172, ua_l=20, fa_l=20)

def flame(dr, x, y, s, t, col=FLAME):
    if s <= 0.5: return
    f = 1 + 0.18 * math.sin(t * 31 + x) + 0.1 * math.sin(t * 17)
    h = s * 2.4 * f
    dr.ellipse([x - s, y - s, x + s, y + s], fill=col)
    dr.polygon([(x - s * 0.95, y - s * 0.2), (x + s * 0.95, y - s * 0.2), (x + 3 * math.sin(t * 20), y - h)], fill=col)

def smoke(dr, x, y, t0, t):
    k = t - t0
    if 0 <= k < 1.2:
        for n in range(4):
            c = int(110 * (1 - k / 1.2))
            r = 10 + 14 * k + n * 3
            dr.ellipse([x + 20 * n * k - r, y - 120 * k - n * 25 - r, x + 20 * n * k + r, y - 120 * k - n * 25 + r], fill=(c, c, c + 5))

def wind(t):
    base = 6 * math.sin(t * 7)
    for g in GUSTS:
        base += 30 * math.exp(-((t - g - 0.15) ** 2) / 0.03)
    return base if t < T_ANS else 0

def person(i, t):
    """(pose, x, rot, fiamma, colore) per l'omino i."""
    w = wind(t); x = XS[i] + w * 0.6
    if i == 0:                                   # HYPE: molla alla prima raffica e se ne va
        if t < T_HYPE: return LEAN, x, 0, 16, GREY
        k = t - T_HYPE
        if k < 0.35: return mix(LEAN, STAND, k / 0.35), x, 0, 0, GREY
        return walk(k * 9), XS[0] - 190 * (k - 0.35), 0, 0, GREY
    if i == 1:                                   # VOGLIA: cade in ginocchio
        if t < T_VOGLIA: return LEAN, x, 0, 18, GREY
        return mix(LEAN, KNEEL, seg(t, T_VOGLIA, T_VOGLIA + 0.3)), XS[1] + 25 * seg(t, T_VOGLIA, T_VOGLIA + 0.3), 0, 0, GREY
    if i == 2:                                   # MOTIVAZIONE: resiste, scivola, poi a terra
        if t < T_MOT0: return LEAN, x, 0, 22, GREY
        if t < T_MOT1:
            k = seg(t, T_MOT0, T_MOT1)
            return STRAIN, XS[2] + 55 * k + w, 0, 22 * (1 - 0.6 * k) * (0.3 if 4.75 < t < 4.9 else 1), GREY
        k = seg(t, T_MOT1, T_MOT1 + 0.35)
        return mix(STRAIN, STAND, k), XS[2] + 55 + 60 * k, 85 * ease(k), 0, GREY
    # IL TUO PERCHÉ
    if t < T_P_FALL: return LEAN, x, 0, 24, BLUE
    if t < T_P_CURL: return mix(LEAN, KNEEL_HOLD, seg(t, T_P_FALL, T_P_FALL + 0.2)), XS[3] + 30, 0, 7, BLUE
    if t < T_P_UP0: return CURL, XS[3] + 30, 0, 4 + 2 * math.sin(t * 9), BLUE
    if t < T_P_UP1:
        k = seg(t, T_P_UP0, T_P_UP1); return mix(CURL, LEAN, k), XS[3] + 30 - 30 * k, 0, 4 + 22 * k, BLUE
    if t < T_ANS: return LEAN, XS[3], 0, 26, BLUE
    k = seg(t, T_ANS, T_ANS + 0.35)
    return mix(LEAN, RAISE, k), XS[3], 0, 26 + 50 * ease(seg(t, T_ANS, T_ANS + 0.6)), BLUE

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit)
    burst = ease(seg(t, T_ANS, T_ANS + 0.8))
    d.rectangle([0, G, W, H], fill=(20, 20, 26)); d.line([(0, G), (W, G)], fill=(80, 80, 92), width=4)
    rain = 1 - seg(t, T_ANS, T_ANS + 0.5)
    if rain > 0:
        sp = 1500
        for rx, ry, v in RAIN:
            y = (ry + t * sp * v) % H; x = (rx - y * 0.35 - t * 260) % (W + 600) - 300
            c = int(95 * rain); d.line([(x, y), (x - 14, y + 42)], fill=(c, c, c + 12), width=3)
    for g in GUSTS:                                  # raffiche visibili
        k = seg(t, g - 0.2, g + 0.5)
        if 0 < k < 1:
            for n in range(6):
                xx = -400 + (W + 800) * k + n * 60; yy = 760 + n * 85
                d.line([(xx, yy), (xx + 260, yy)], fill=(170, 170, 185), width=5)
    for i in range(4):
        pose, x, rot, fs, col = person(i, t)
        tgt = dl if col == BLUE else d
        hip = on_ground(x, G, pose, K)
        if rot: hip = (hip[0], hip[1] + 110 * ease(seg(t, T_MOT1, T_MOT1 + 0.35)))
        sk = draw_fig(tgt, hip, pose, col, -1, rot, K)
        hm = ((sk["hl"][0] + sk["hr"][0]) / 2, (sk["hl"][1] + sk["hr"][1]) / 2)
        if i == 3 and t >= T_ANS: hm = sk["hr"]
        col_f = FLAME if not (i == 3 and t >= T_ANS) else (200, 230, 255)
        if i == 3 and T_P_CURL <= t < T_P_UP0: hm = (sk["H"][0] - 95, G - 22)
        flame(dl, hm[0], hm[1] - 8, fs, t, col_f)
    smoke(d, XS[0] - 60, G - 400, T_HYPE, t); smoke(d, XS[1] - 50, G - 380, T_VOGLIA, t); smoke(d, XS[2] + 30, G - 390, T_MOT1, t)
    out = glow(img, lit, 24, 1.1)
    if burst > 0:                                   # il fuoco illumina la scena
        out = Image.fromarray(np.clip(np.asarray(out, dtype=np.float32) + RAD * burst, 0, 255).astype(np.uint8))
    do = ImageDraw.Draw(out)
    for i in range(4):
        al = ease(seg(t, T_LAB[i], T_LAB[i] + 0.15))
        if al <= 0: continue
        on = (i == 3) or t < [T_HYPE, T_VOGLIA, T_MOT1][i]
        lc = BLUE if i == 3 else (WHITE if on else (110, 110, 120))
        lc = tuple(int(BG[c] + (lc[c] - BG[c]) * al) for c in range(3))
        label(do, XS[i], G + 26, LAB[i], lc, 30)
    phrase(do, [(C["frase"][0], WHITE)], y=270, size=50)
    if t >= T_ANS:
        phrase(do, [(C["frase"][1], BLUE)], t0=T_ANS, t=t, y=270 + 65, size=58, cps=40)
        al = ease(seg(t, T_ANS + 0.7, T_ANS + 1.0))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            s = C["invito"]; fnt = font(38); do.text(((W - text_w(s, fnt)) / 2, 450), s, font=fnt, fill=c)
    watermark(do)
    return out

if __name__ == "__main__":
    S = C.get("velocita", 1.0)
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_whoosh(DUR, 0.10))]
    for k in range(int(DUR * 8)): ev.append((k / 8 + 0.03, s_clap(0.04)))       # pioggia
    for g in GUSTS: ev.append((g - 0.25, s_whoosh(0.9, 0.7)))
    for a in T_LAB: ev.append((a, s_pop(0.25)))
    ev += [(T_HYPE + 0.1, s_click(0.4)), (T_VOGLIA + 0.25, s_thud(0.5, 80)), (T_MOT1 + 0.35, s_thud(0.8, 70)),
           (T_P_FALL + 0.2, s_thud(0.5, 85))]
    for k in range(3): ev.append((T_P_CURL + 0.2 + k * 0.3, s_thud(0.3, 55)))     # battito
    ev += [(T_ANS - 0.3, s_rise(2.0, 0.55, 196, 392)), (T_ANS, s_whoosh(0.6, 0.5)), (T_ANS + 0.1, s_chime(0.45, 784))]
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
