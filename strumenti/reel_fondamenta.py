#!/usr/bin/env python3
"""Reel B "Applausi o fondamenta" (24/11) – Mentalità Capitale.

Due lotti uguali. A alza in fretta una torre di scatoloni (HYPE) e la folla applaude; B scava sottoterra e nessuno lo guarda.
Arriva la CRISI: la torre crolla e gli applausi vanno a zero. Sulle fondamenta di B il palazzo sale in un attimo.
Uso: python3 reel_fondamenta.py contenuto.json uscita.mp4
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 12.0)
G = 1150
KF, KC = 1.6, 1.1
TX = 315                       # centro della torre di A
BW_, BH_ = 120, 60             # scatolone
NB = 7
T_BOX = [0.8 + 0.62 * i for i in range(NB)]
HX0, HX1 = 660, 900            # buca di B
T_DIG0, T_DIG1, T_FOUND1 = 0.8, 5.2, 6.8
T_WIND, T_FALL, T_ANS = 7.0, 7.8, 8.7
APPL = C.get("applausi", 12480)
random.seed(9)
FALL = [(random.uniform(-260, 120), random.uniform(-200, 200), random.uniform(0.9, 1.2)) for _ in range(NB)]
FWIN = [(HX0 + 18 + c * 44, r, random.random()) for c in range(5) for r in range(11)]

def depth(t): return 300 * ease(seg(t, T_DIG0, T_DIG1))

def applause_l(t):
    n = sum(1 for tb in T_BOX if t >= tb)
    v = int(APPL * (n / NB) ** 1.6)
    return int(v * (1 - ease(seg(t, T_FALL + 0.1, T_FALL + 0.7))))

def applause_r(t): return int(APPL * 1.4 * ease(seg(t, T_ANS + 0.3, T_ANS + 1.4)))

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit)
    d.rectangle([0, G, W, H], fill=(22, 20, 25)); d.line([(0, G), (W, G)], fill=(90, 90, 100), width=4)
    # buca e fondamenta di B
    dp = depth(t)
    if dp > 1:
        d.rectangle([HX0, G, HX1, G + dp], fill=BG)
        pile = dp / 300
        d.polygon([(HX1 + 10, G), (HX1 + 60 + 70 * pile, G - 90 * pile), (HX1 + 150, G)], fill=(40, 37, 44))
    if t > T_DIG1:                                       # blocchi delle fondamenta, dal fondo in su
        rows = int(5 * seg(t, T_DIG1, T_FOUND1) + 0.999)
        for r in range(rows):
            for c in range(4):
                x0 = HX0 + 6 + c * 58; y1 = G + 300 - r * 60
                dl.rectangle([x0, y1 - 54, x0 + 52, y1 - 4], fill=(30, 75, 125))
    # palazzo di B che sale
    bh = 530 * ease(seg(t, T_ANS, T_ANS + 1.0))
    if bh > 0:
        d.rectangle([HX0, G - bh, HX1, G], fill=(24, 26, 36))
        for wx, r, rnd in FWIN:
            wy = G - 40 - r * 48
            if wy > G - bh + 10 and rnd < 0.25 + seg(t, T_ANS + 0.4, T_ANS + 1.6):
                dl.rectangle([wx, wy - 26, wx + 26, wy], fill=BLUE if rnd < 0.6 else (190, 210, 240))
    # torre di A
    sway = 0.0
    if t >= T_WIND: sway = 6 * math.sin((t - T_WIND) * 9) * seg(t, T_WIND, T_FALL)
    for i, tb in enumerate(T_BOX):
        if t < tb - 0.3: continue
        if t < tb:                                       # lo scatolone vola su
            k = ease((t - (tb - 0.3)) / 0.3); y = G - 60 - (i * BH_) * k - 40 * math.sin(k * math.pi); x = TX + 120 * (1 - k)
            ang = 0
        elif t < T_FALL:
            h = i * BH_; y = G - BH_ / 2 - h; ang = sway * (i / NB) * 1.4
            x = TX + math.sin(math.radians(ang)) * h * 0.6 + (2 * math.sin(t * 3 + i) if i > 4 else 0)
        else:                                            # crollo
            k = t - T_FALL; fx, fy, sp = FALL[i]
            y0 = G - BH_ / 2 - i * BH_; x = TX + fx * min(1, k * 1.6) * sp
            y = min(G - BH_ / 2 - (i % 3) * 8, y0 + 1400 * k * k); ang = (fx / 3) * min(1, k * 1.5)
        a = math.radians(ang); cx, cy = x, y
        pts = [(-BW_ / 2, -BH_ / 2), (BW_ / 2, -BH_ / 2), (BW_ / 2, BH_ / 2), (-BW_ / 2, BH_ / 2)]
        poly = [(cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
        d.polygon(poly, fill=(118, 104, 86), outline=(70, 60, 50))
        if i == NB // 2 and t < T_FALL:
            label(d, cx, cy - 16, "HYPE", (40, 32, 24), 28)
    # vento della crisi
    if T_WIND <= t < T_FALL + 1.0:
        k = seg(t, T_WIND, T_FALL + 1.0)
        for n in range(9):
            yy = 640 + n * 55; xx = -300 + (W + 600) * ((k * 1.6 + n * 0.13) % 1)
            d.line([(xx, yy), (xx + 220, yy)], fill=(150, 150, 165), width=4)
        al = ease(seg(t, T_WIND, T_WIND + 0.2)) * (1 - ease(seg(t, T_FALL + 0.6, T_FALL + 1.0)))
        if al > 0:
            fnt = font(80); s = C["crisi"]; c = tuple(int(BG[q] + (235 - BG[q]) * al) for q in range(3))
            d.text((-150 + 500 * k, 700), s, font=fnt, fill=c)
    # A
    if t < T_FALL:
        pa = CHEER if any(tb - 0.3 <= t < tb + 0.15 for tb in T_BOX) else STAND
    else:
        pa = mix(STAND, SAD, seg(t, T_FALL + 0.6, T_FALL + 1.0))
    draw_fig(d, on_ground(470, G, pa, KF), pa, WHITE, -1, 0, KF)
    # B: scava, posa i blocchi, poi esce
    if t < T_ANS:
        pb = dig(t * 10) if t < T_DIG1 else PLACE
        floor = G + (dp if t < T_DIG1 else 300 - 60 * int(5 * seg(t, T_DIG1, T_FOUND1)))
        if t >= T_FOUND1: floor = G
        hip = on_ground(780, floor, pb, KF)
        sk = draw_fig(dl, hip, pb, BLUE, 1, 0, KF)
        if t < T_DIG1:                                   # pala
            h = sk["hr"]; dl.line([(h[0] - 20, h[1] - 30), (h[0] + 40, h[1] + 60)], fill=(150, 160, 175), width=6)
    else:
        pb = STAND; sk = draw_fig(dl, on_ground(HX0 - 60, G, pb, KF), pb, BLUE, 1, 0, KF)
    # folla
    for j, cx in enumerate([40, 85, 130, 175, 220]):
        if t < 0.8: pose, f = STAND, 1
        elif t < T_FALL: pose, f = (laugh(t * 9 + j) if (3.6 <= t < 5.0 and j == 4) else clap(t * 16 + j)), 1
        elif t < T_ANS + 0.2: pose, f = SAD, 1
        else: pose, f = clap(t * 16 + j), 1
        x = cx + (110 * ease(seg(t, T_ANS + 0.2, T_ANS + 1.2)) if t > T_ANS else 0)
        draw_fig(d, on_ground(x, G, pose, KC), pose, GREY, f, 0, KC)
    for s, a, b, bx in [(C["fumetti"][0], 2.0, 3.4, 170), (C["fumetti"][1], 3.6, 5.0, 300)]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        bubble(d, bx, 890, s, 36, al)
    # contatori
    for cx, val, col in [(TX, applause_l(t), WHITE), ((HX0 + HX1) / 2, applause_r(t), BLUE)]:
        al = ease(seg(t, 1.3, 1.5))
        if al > 0:
            c = tuple(int(BG[q] + (col[q] - BG[q]) * al) for q in range(3))
            label(d, cx, 488, "APPLAUSI", (int(150 * al), int(150 * al), int(160 * al)), 26)
            label(d, cx, 520, f"{val:,}".replace(",", "."), c, 50)
    # testi
    if t < T_ANS:
        phrase(d, [(C["frase1"], WHITE)], y=270, size=60)
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, y=250, size=44, cps=55)
        al = ease(seg(t, T_ANS + 0.7, T_ANS + 1.0))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            for n, s in enumerate(C["invito"]):
                fnt = font(36); d.text(((W - text_w(s, fnt)) / 2, 375 + n * 44), s, font=fnt, fill=c)
    watermark(d)
    return glow(img, lit, 22, 1.0)

if __name__ == "__main__":
    S = C.get("velocita", 1.0)                 # >1 = più veloce (M6: risposta entro ~7 s)
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03))]
    for tb in T_BOX:
        ev.append((tb - 0.3, s_whoosh(0.3, 0.15))); ev.append((tb, s_tok(140, 0.08, 0.5)))
        for k in range(5): ev.append((tb + 0.05 + k * 0.07, s_clap(0.18)))
    for k in range(int((T_DIG1 - T_DIG0) / 0.63)): ev.append((T_DIG0 + 0.3 + k * 0.63, s_thud(0.25, 110)))
    for r in range(5): ev.append((T_DIG1 + r * 0.32, s_tok(90, 0.12, 0.6)))
    ev += [(2.0, s_pop(0.35)), (3.6, s_pop(0.35)), (T_WIND, s_whoosh(1.6, 0.6)), (T_FALL, s_crack(0.7))]
    for i in range(NB): ev.append((T_FALL + 0.15 + i * 0.06, s_thud(0.35, 80 + i * 6)))
    ev += [(T_ANS - 0.3, s_rise(2.0, 0.5, 220, 440)), (T_ANS + 0.2, s_chime(0.4, 880))]
    for k in range(18): ev.append((T_ANS + 0.4 + k * 0.06, s_clap(0.2)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
