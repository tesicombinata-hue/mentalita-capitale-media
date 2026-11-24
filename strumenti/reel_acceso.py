#!/usr/bin/env python3
"""Reel B "Chi resta acceso?" (24/11) – Mentalità Capitale.

Un palazzo di notte, quattro finestre accese con un omino al lavoro: HYPE, VOGLIA, MOTIVAZIONE, IL TUO PERCHÉ.
L'orologio corre, le finestre si spengono una alla volta; MOTIVAZIONE resiste e poi cede.
Resta acceso solo IL TUO PERCHÉ: passano i giorni, poi la sua luce accende tutto il palazzo.
Uso: python3 reel_acceso.py contenuto.json uscita.mp4
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 11.8)
BX0, BX1, BTOP = 230, 850, 690
WW, WH = 250, 250
WINS = [(BX0 + 45, 780), (BX0 + 325, 780), (BX0 + 45, 1130), (BX0 + 325, 1130)]
LAB = C["etichette"]
T_LAB = [1.3, 1.55, 1.8, 2.05]
T_OFF = [2.7, 4.4, 6.9, None]
T_DAYS0, T_DAYS1, T_ANS = 7.2, 8.8, 8.9
WARM = (150, 138, 105)
random.seed(5)
SMALL = []
for gx in range(BX0 + 22, BX1 - 30, 46):
    for gy in range(BTOP + 25, H - 40, 52):
        inside = any(wx - 25 < gx < wx + WW + 10 and wy - 30 < gy < wy + WH + 70 for wx, wy in WINS)
        if not inside: SMALL.append((gx, gy, random.random()))
PX, PY = WINS[3][0] + WW / 2, WINS[3][1] + WH / 2

def win_on(i, t):
    if T_OFF[i] is None: return 1.0
    if i == 2 and 5.6 <= t < T_OFF[i]:                 # MOTIVAZIONE resiste: tremola
        return 0.15 if (5.75 < t < 5.95 or 6.3 < t < 6.42 or 6.6 < t < 6.75) else 1.0
    return 1.0 if t < T_OFF[i] else 0.0

def clock(t):
    if t < T_DAYS0:
        m = int(23 * 60 + (5 * 60) * seg(t, 0, 7.0)) % (24 * 60)
        return f"{m // 60:02d}:{m % 60:02d}"
    return f"GIORNO {1 + int(364 * ease(seg(t, T_DAYS0, T_DAYS1)))}"

def worker(i, t):
    """Posa dell'omino nella finestra i: (pose, x relativo, visibile)."""
    if i == 0 and t > 2.0:                               # HYPE si alza e se ne va
        k = seg(t, 2.0, 2.4)
        if k < 1: return mix(SIT_TYPE, STAND, k), 0, True
        return walk((t - 2.4) * 10), 170 * (t - 2.4), t < 3.4
    if i == 1 and t > 3.7:                               # VOGLIA si addormenta
        return mix(type_(t * 14), SIT_SLEEP, seg(t, 3.7, 4.1)), 0, True
    if i == 2 and t > 5.6:                               # MOTIVAZIONE si accascia piano
        return mix(type_(t * 10), SIT_SLEEP, seg(t, 5.8, 6.8)), 0, True
    return type_(t * (14 + i * 2)), 0, True

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit)
    for sx in range(0, W, 9):                            # città lontana
        pass
    d.rectangle([BX0, BTOP, BX1, H], fill=(20, 21, 28))
    d.rectangle([BX0 - 12, BTOP - 18, BX1 + 12, BTOP], fill=(32, 33, 40))
    # finestre piccole: si accendono dalla finestra del perché verso l'esterno
    spread = seg(t, T_ANS, T_ANS + 1.3) * 1300
    for gx, gy, r in SMALL:
        dist = math.hypot(gx - PX, gy - PY)
        if dist < spread:
            a = min(1, (spread - dist) / 120)
            col = BLUE if r < 0.6 else (200, 220, 245)
            dl.rectangle([gx, gy, gx + 22, gy + 30], fill=tuple(int(c * a * 0.8) for c in col))
        else:
            d.rectangle([gx, gy, gx + 22, gy + 30], fill=(30, 31, 38))
    # le 4 finestre grandi
    for i, (wx, wy) in enumerate(WINS):
        on = win_on(i, t)
        if i == 3:
            k = seg(t, T_ANS, T_ANS + 0.4)
            col = tuple(int(WARM[c] + (BLUE[c] * 0.85 - WARM[c]) * k) for c in range(3))
        else:
            col = WARM
        if on > 0:
            dl.rectangle([wx, wy, wx + WW, wy + WH], fill=tuple(int(c * on) for c in col))
        else:
            d.rectangle([wx, wy, wx + WW, wy + WH], fill=(12, 12, 16))
        d.rectangle([wx - 6, wy - 6, wx + WW + 6, wy + WH + 6], outline=(45, 46, 55), width=6)
        # omino in controluce dentro la finestra
        win = Image.new("RGBA", (WW, WH), (0, 0, 0, 0)); wd = ImageDraw.Draw(win)
        pose, dx, vis = worker(i, t)
        if vis:
            fc = (8, 8, 12, 255) if on > 0 else (34, 34, 42, 255)
            seat = WH - 70
            wd.rectangle([150, seat - 10, 240, seat - 2], fill=fc)                 # scrivania
            wd.rectangle([200, seat - 2, 208, WH], fill=fc)
            if i != 0 or t < 2.4:
                wd.rectangle([60, seat + 8, 110, seat + 16], fill=fc)            # sedia
                wd.rectangle([82, seat + 16, 90, WH], fill=fc)
            hip = (95 + dx, seat + 4) if dx == 0 and not (i == 0 and t > 2.0 and seg(t, 2.0, 2.4) >= 1) else (95 + dx, 0)
            if i == 0 and t > 2.0:
                hip = (95 + dx, seat + 4 - 40 * seg(t, 2.0, 2.4)) if seg(t, 2.0, 2.4) < 1 else on_ground(95 + dx, WH - 4, pose, 0.95)
            draw_fig(wd, hip, pose, fc, 1, 0, 0.95)
            if i == 3 and t > T_DAYS0 - 0.6:                                        # il lavoro si accumula
                for n in range(int(9 * seg(t, T_DAYS0 - 0.6, T_DAYS1))):
                    wd.rectangle([212, seat - 16 - n * 9, 240, seat - 11 - n * 9], fill=fc)
            if i != 0 or t < 2.0:                                                   # portatile
                wd.polygon([(170, seat - 10), (205, seat - 10), (198, seat - 48), (176, seat - 48)], fill=fc)
        mask = Image.new("L", (W, H), 0); mask.paste(win.split()[3], (wx, wy))
        img.paste(Image.new("RGB", (W, H), (8, 8, 12) if on > 0 else (34, 34, 42)), (0, 0), mask)
        lit.paste((0, 0, 0), (0, 0), mask)
        al = ease(seg(t, T_LAB[i], T_LAB[i] + 0.15))
        if al > 0:
            lc = BLUE if (i == 3 and t >= T_ANS) else WHITE
            if on == 0 and i != 3: lc = (110, 110, 120)
            lc = tuple(int(BG[c] + (lc[c] - BG[c]) * al) for c in range(3))
            label(d, wx + WW / 2, wy + WH + 14, LAB[i], lc, 30)
    # testi
    if t < T_ANS:
        phrase(d, [(C["frase1"], WHITE)], y=260)
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, y=260, size=54, cps=50)
    fnt = font(64); s = clock(t); col = BLUE if t >= T_DAYS0 else (200, 200, 210)
    if t < T_ANS: d.text(((W - text_w(s, fnt)) / 2, 400), s, font=fnt, fill=col)
    al = ease(seg(t, T_ANS + 0.6, T_ANS + 0.9))
    if al > 0:
        c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
        for n, s in enumerate(C["invito"]):
            fnt = font(40); d.text(((W - text_w(s, fnt)) / 2, 470 + n * 52), s, font=fnt, fill=c)
    watermark(d)
    return glow(img, lit, 26, 0.9)

if __name__ == "__main__":
    S = C.get("velocita", 1.0)                 # >1 = più veloce (M6: risposta entro ~7 s)
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03))]
    for k in range(int(7.0 * 4)): ev.append((k / 4, s_type(0.10)))          # tasti nella notte
    for a in T_LAB: ev.append((a, s_pop(0.3)))
    ev += [(2.0, s_whoosh(0.4, 0.15)), (2.7, s_click(0.7)), (4.4, s_click(0.7)),
           (5.75, s_click(0.4)), (6.3, s_click(0.4)), (6.6, s_click(0.4)), (6.9, s_click(0.8))]
    for k in range(16): ev.append((T_DAYS0 + k * 0.1, s_tok(900 + k * 30, 0.03, 0.18)))
    ev += [(T_ANS - 0.4, s_rise(2.3, 0.5, 196, 392)), (T_ANS, s_chime(0.45, 784))]
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
