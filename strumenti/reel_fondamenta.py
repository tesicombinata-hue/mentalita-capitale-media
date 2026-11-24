#!/usr/bin/env python3
"""Reel B "Apparire o essere" v2 (24/11) – Mentalità Capitale (file: reel_fondamenta).

Due lotti uguali con due etichette: APPARIRE (bianco) ed ESSERE (blu).
APPARIRE alza in fretta una facciata luminosa, si fa i selfie, la folla scatta foto e manda cuori.
ESSERE scava: colpisce una roccia e cade, si rialza, si asciuga il sudore, porta i blocchi pesanti delle fondamenta; la folla lo prende in giro.
Arriva la CRISI: la facciata cade e si vede che era solo un pannello. Sulle fondamenta il palazzo vero sale.
Uso: python3 reel_fondamenta.py contenuto.json uscita.mp4
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 9.4)
G = 1150
KF, KC = 1.6, 1.1
FX0, FX1 = 200, 430           # facciata di APPARIRE
FL = 72                       # altezza di un piano della facciata
NF = 6
T_FLOOR = [0.35 + 0.5 * i for i in range(NF)]
HX0, HX1 = 660, 900           # buca di ESSERE
T_ROCK, T_UP0, T_UP1, T_WIPE0, T_WIPE1 = 1.55, 2.05, 2.5, 3.1, 3.5
T_DIG1, T_FOUND1 = 3.9, 5.5
T_WIND, T_FALL, T_ANS = 5.6, 6.0, 6.7
random.seed(9)
FWIN = [(HX0 + 18 + c * 44, r, random.random()) for c in range(5) for r in range(11)]
FLASH = [(random.uniform(0, 3.4), random.choice([40, 85, 130, 175])) for _ in range(9)]
HEARTS = [(random.uniform(0.4, 5.4), random.uniform(30, 190)) for _ in range(14)]

PHONE = P(ua_r=135, fa_r=150, ua_l=10, fa_l=10, head=185)          # selfie
SIT_BACK = P(torso=200, head=200, ua_l=-40, fa_l=-20, ua_r=-30, fa_r=-10, th_l=90, sh_l=10, th_r=85, sh_r=5)
WIPE = P(torso=165, head=160, ua_r=150, fa_r=230, ua_l=10, fa_l=10)
HEAVY = P(torso=150, head=150, ua_l=20, fa_l=40, ua_r=15, fa_r=35, th_l=25, sh_l=-25, th_r=-15, sh_r=-25)
SHOOT = P(ua_r=100, fa_r=110, ua_l=95, fa_l=115, head=175)          # la folla fa foto

def depth(t):
    if T_ROCK <= t <= T_UP1: t = T_ROCK                  # dopo la roccia la buca si ferma un attimo
    return 300 * ease(seg(t, 0.3, T_DIG1))

def heart(dr, x, y, s, col):
    dr.ellipse([x - s, y - s * 0.6, x, y + s * 0.4], fill=col); dr.ellipse([x, y - s * 0.6, x + s, y + s * 0.4], fill=col)
    dr.polygon([(x - s * 0.98, y), (x + s * 0.98, y), (x, y + s * 1.1)], fill=col)

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit)
    d.rectangle([0, G, W, H], fill=(22, 20, 25)); d.line([(0, G), (W, G)], fill=(90, 90, 100), width=4)
    dp = depth(t)
    if dp > 1:
        d.rectangle([HX0, G, HX1, G + dp], fill=BG)
        pile = dp / 300
        d.polygon([(HX1 + 10, G), (HX1 + 60 + 70 * pile, G - 90 * pile), (HX1 + 150, G)], fill=(40, 37, 44))
    if T_ROCK - 0.1 < t < T_UP1 + 0.6:                     # la roccia
        d.ellipse([760, G + dp - 30, 840, G + dp + 18], fill=(70, 70, 80))
    if t > T_DIG1:
        rows = int(5 * seg(t, T_DIG1, T_FOUND1) + 0.999)
        for r in range(rows):
            for c in range(4):
                x0 = HX0 + 6 + c * 58; y1 = G + 300 - r * 60
                dl.rectangle([x0, y1 - 54, x0 + 52, y1 - 4], fill=(30, 75, 125))
    bh = 520 * ease(seg(t, T_ANS, T_ANS + 0.9))
    if bh > 0:
        d.rectangle([HX0, G - bh, HX1, G], fill=(24, 26, 36))
        for wx, r, rnd in FWIN:
            wy = G - 40 - r * 46
            if wy > G - bh + 10 and rnd < 0.3 + seg(t, T_ANS + 0.3, T_ANS + 1.4):
                dl.rectangle([wx, wy - 26, wx + 26, wy], fill=BLUE if rnd < 0.6 else (190, 210, 240))
    # facciata: pannello sottile che sale a piani, poi cade a terra
    nf = sum(1 for tf in T_FLOOR if t >= tf)
    fh = nf * FL + (FL * ease(seg(t, T_FLOOR[nf] - 0.2, T_FLOOR[nf])) if nf < NF else 0)
    if fh > 0:
        ang = 0.0
        if T_WIND <= t < T_FALL: ang = 4 * math.sin((t - T_WIND) * 14)
        if t >= T_FALL: ang = -90 * min(1, ((t - T_FALL) / 0.55) ** 2)
        a = math.radians(ang); ox, oy = FX0, G
        def R(px_, py_): return (ox + px_ * math.cos(a) - py_ * math.sin(a), oy + px_ * math.sin(a) + py_ * math.cos(a))
        wdt = FX1 - FX0
        d.polygon([R(0, 0), R(wdt, 0), R(wdt, -fh), R(0, -fh)], fill=(70, 66, 60))
        bright = 1 - 0.7 * seg(t, T_FALL, T_FALL + 0.5)
        for fl in range(int(fh // FL)):
            for c in range(3):
                x0 = 28 + c * 66; y0 = -(fl * FL) - 22
                dl.polygon([R(x0, y0), R(x0 + 40, y0), R(x0 + 40, y0 - 34), R(x0, y0 - 34)], fill=tuple(int(v * bright) for v in (240, 225, 180)))
        if t >= T_FALL + 0.3:                              # dietro non c'era niente: solo un paletto
            d.line([(FX0 + 115, G), (FX0 + 115, G - 90)], fill=(60, 56, 50), width=8)
    if T_WIND <= t < T_FALL + 1.0:
        k = seg(t, T_WIND, T_FALL + 1.0)
        for n in range(9):
            yy = 640 + n * 55; xx = -300 + (W + 600) * ((k * 1.6 + n * 0.13) % 1)
            d.line([(xx, yy), (xx + 220, yy)], fill=(150, 150, 165), width=4)
        al = ease(seg(t, T_WIND, T_WIND + 0.2)) * (1 - ease(seg(t, T_FALL + 0.6, T_FALL + 1.0)))
        if al > 0:
            c = tuple(int(BG[q] + (235 - BG[q]) * al) for q in range(3))
            d.text((-150 + 500 * k, 680), C["crisi"], font=font(80), fill=c)
    for j, cx in enumerate([40, 85, 130, 175]):
        if t < 0.3: pose = STAND
        elif t < T_FALL: pose = laugh(t * 9 + j) if (2.2 <= t < 3.4 and j == 3) else SHOOT
        elif t < T_ANS + 0.2: pose = SAD
        else: pose = SHOOT
        x = cx + (110 * ease(seg(t, T_ANS + 0.2, T_ANS + 1.2)) if t > T_ANS else 0)
        draw_fig(d, on_ground(x, G, pose, KC), pose, GREY, 1, 0, KC)
    for tf, fx in FLASH:
        if tf <= t < tf + 0.12 and t < T_FALL:
            dl.ellipse([fx + 30, 975, fx + 70, 1015], fill=(255, 255, 255))
    for th, hx in HEARTS:
        if th <= t < min(th + 1.4, T_FALL + 0.3):
            k = t - th; heart(d, hx + 15 * math.sin(k * 5), 960 - 260 * k, 16, (230, 230, 235))
    if t < T_FALL: pa = PHONE if int(t * 2.2) % 3 else CHEER
    else: pa = mix(STAND, SAD, seg(t, T_FALL + 0.3, T_FALL + 0.7))
    ask = draw_fig(d, on_ground(490, G, pa, KF), pa, WHITE, -1, 0, KF)
    if pa is PHONE:
        h = ask["hr"]; d.rounded_rectangle([h[0] - 14, h[1] - 26, h[0] + 8, h[1] + 8], radius=4, fill=(200, 200, 210))
    if t < T_ANS:
        if T_ROCK <= t < T_UP0: pb = mix(dig(t * 10), SIT_BACK, seg(t, T_ROCK, T_ROCK + 0.15))
        elif T_UP0 <= t < T_UP1: pb = mix(SIT_BACK, STAND, seg(t, T_UP0, T_UP1))
        elif T_WIPE0 <= t < T_WIPE1: pb = WIPE
        elif t < T_DIG1: pb = dig(t * (10 if t < 2.8 else 7))
        else: pb = HEAVY if int((t - T_DIG1) * 3) % 2 == 0 else PLACE
        floor = G + (dp if t < T_DIG1 else 300 - 60 * int(5 * seg(t, T_DIG1, T_FOUND1)))
        if t >= T_FOUND1: floor = G
        bx = 780 - (30 if T_ROCK <= t < T_UP1 else 0)
        sk = draw_fig(dl, on_ground(bx, floor, pb, KF), pb, BLUE, 1, 0, KF)
        if t < T_DIG1 and not (T_WIPE0 <= t < T_WIPE1):
            h = sk["hr"]
            if T_ROCK <= t < T_UP1:                        # la pala vola via e ricade
                k = t - T_ROCK; dl.line([(840 + 120 * k, G + dp - 120 - 200 * k + 500 * k * k), (900 + 120 * k, G + dp - 60 - 200 * k + 500 * k * k)], fill=(150, 160, 175), width=6)
            else:
                dl.line([(h[0] - 20, h[1] - 30), (h[0] + 40, h[1] + 60)], fill=(150, 160, 175), width=6)
        if pb is HEAVY:
            h = sk["hr"]; dl.rectangle([h[0] - 30, h[1] - 10, h[0] + 30, h[1] + 30], fill=(30, 75, 125))
        if T_WIPE0 <= t < T_WIPE1:
            n = sk["N"]; d.ellipse([n[0] + 30, n[1] - 10 + 60 * (t - T_WIPE0), n[0] + 40, n[1] + 6 + 60 * (t - T_WIPE0)], fill=(160, 200, 255))
    else:
        draw_fig(dl, on_ground(HX0 - 50, G, STAND, KF), STAND, BLUE, 1, 0, KF)
    label(d, 315, 540, C["etichette"][0], WHITE, 54)
    label(d, 780, 540, C["etichette"][1], BLUE, 54)
    if t >= T_ANS:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, y=250, size=50, cps=55)
        al = ease(seg(t, T_ANS + 0.6, T_ANS + 0.9))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            for n, s in enumerate(C["invito"]):
                fnt = font(36); d.text(((W - text_w(s, fnt)) / 2, 400 + n * 44), s, font=fnt, fill=c)
    watermark(d)
    out = glow(img, lit, 22, 1.0); do = ImageDraw.Draw(out)       # fumetti sopra le luci
    for s, a, b, bx in C["fumetti"]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        bubble(do, bx, 890, s, 36, al)
    return out

if __name__ == "__main__":
    S = C.get("velocita", 1.0)
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03))]
    for tf in T_FLOOR: ev.append((tf, s_tok(150, 0.08, 0.45)))
    for tf, fx in FLASH: ev.append((tf, s_click(0.35)))
    for k in range(int((T_DIG1 - 0.3) / 0.6)): ev.append((0.4 + k * 0.6, s_thud(0.22, 110)))
    ev += [(T_ROCK, s_tok(900, 0.05, 0.9)), (T_ROCK + 0.05, s_thud(0.6, 70)), (T_WIPE0, s_whoosh(0.4, 0.12))]
    for r in range(5): ev.append((T_DIG1 + r * 0.32, s_thud(0.6, 60)))
    for s, a, b, bx in C["fumetti"]: ev.append((a, s_pop(0.35)))
    ev += [(T_WIND, s_whoosh(1.4, 0.6)), (T_FALL + 0.5, s_thud(0.8, 65)), (T_ANS - 0.3, s_rise(2.0, 0.5, 220, 440)), (T_ANS + 0.2, s_chime(0.4, 880))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 55, s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
