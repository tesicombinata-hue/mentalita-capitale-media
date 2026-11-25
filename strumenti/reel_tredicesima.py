#!/usr/bin/env python3
"""Reel B "Chi arriva a dicembre?" (serie Stesso stipendio, Black Week) – Mentalità Capitale, 25/11.

Due amici, stesso stipendio, davanti allo stesso "-50%" che lampeggia. Lui (bianco) compra: i pacchi gli si
accumulano accanto ("TANTO ARRIVA LA TREDICESIMA"). L'altro (blu) mette via il telefono. Il calendario corre fino
a dicembre, arriva la busta della tredicesima a tutti e due: a lui le banconote volano via verso i pacchi (già spesa),
all'altro restano in mano e si impilano. Risposta: "LA TREDICESIMA SI SPENDE UNA VOLTA SOLA."
Uso: python3 reel_tredicesima.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 8.8)
G = 1250
K = 2.3
XA, XB = 360, 760
BOX_T = [0.75, 1.15, 1.55, 1.95, 2.35, 2.75, 3.15]
BOX_P = [(140, 0), (215, 0), (178, 1), (65, 0), (102, 1), (140, 2), (252, 1)]   # (x, piano)
BW, BH = 72, 56
T_OFF = 0.95                      # l'altro mette via il telefono
T_CAL0, T_CAL1 = 3.6, 4.7         # il calendario corre
T_ENV0, T_ENV1 = 4.75, 5.2        # la busta cade
T_FLY0, T_FLY1 = 5.3, 6.0         # le banconote di lui volano ai pacchi
T_ANS = 5.95
PAGES = ["27 NOV", "28 NOV", "29 NOV", "30 NOV", "1 DIC", "5 DIC", "10 DIC", "DICEMBRE"]
PHONE = P(ua_r=55, fa_r=150, ua_l=8, fa_l=8)
TAP = P(ua_r=55, fa_r=150, ua_l=40, fa_l=140)
ARMS = P(ua_l=35, fa_l=110, ua_r=-35, fa_r=-110)          # braccia conserte
HOLD = P(ua_l=60, fa_l=100, ua_r=-60, fa_r=-100)          # tiene la busta davanti
random.seed(5)
BILLS = [(random.uniform(-30, 30), random.uniform(-40, 10), random.uniform(0, 0.25)) for _ in range(9)]

def box(d, x, y, col=(150, 150, 158)):
    d.rectangle([x - BW / 2, y - BH, x + BW / 2, y], fill=col, outline=(70, 70, 78), width=3)
    d.line([(x, y - BH), (x, y)], fill=(110, 110, 118), width=6)

def envelope(d, cx, cy, col, s=1.0):
    w, h = 110 * s, 70 * s
    d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=col)
    d.line([(cx - w / 2, cy - h / 2), (cx, cy + 4), (cx + w / 2, cy - h / 2)], fill=BG, width=4)
    label(d, cx, cy + h / 2 - 32 * s, "13ª", BG, int(26 * s))

def bill(d, cx, cy, col, a=0):
    w, h = 64, 34; c, s = math.cos(a), math.sin(a)
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    d.polygon([(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts], fill=col)

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit)
    d.line([(0, G), (W, G)], fill=(70, 70, 80), width=4)
    # "-50%" che lampeggia, poi il calendario
    if t < T_CAL0:
        on = (int(t / 0.22) % 2 == 0) or t < 0.25
        k = ease(seg(t, 0, 0.18)); s = 0.6 + 0.4 * k
        if on:
            w, h = 330 * s, 150 * s
            dl.rounded_rectangle([W / 2 - w / 2, 640 - h / 2, W / 2 + w / 2, 640 + h / 2], radius=18, fill=WHITE)
            fnt = font(int(108 * s), INTER); s2 = "-50%"
            dl.text((W / 2 - text_w(s2, fnt) / 2, 640 - 70 * s), s2, font=fnt, fill=BG)
        else:
            w, h = 330 * s, 150 * s
            d.rounded_rectangle([W / 2 - w / 2, 640 - h / 2, W / 2 + w / 2, 640 + h / 2], radius=18, outline=(90, 90, 100), width=4)
    elif t < T_ENV0 + 0.4:
        i = min(len(PAGES) - 1, int(seg(t, T_CAL0, T_CAL1) * (len(PAGES) - 1) + 0.0001))
        flip = (seg(t, T_CAL0, T_CAL1) * (len(PAGES) - 1)) % 1 if t < T_CAL1 else 0
        al = 1 - ease(seg(t, T_ENV0, T_ENV0 + 0.4))
        c = tuple(int(BG[j] + (235 - BG[j]) * al) for j in range(3))
        d.rounded_rectangle([W / 2 - 170, 560 - 6 * flip, W / 2 + 170, 720], radius=14, fill=c)
        d.rectangle([W / 2 - 170, 560 - 6 * flip, W / 2 + 170, 600], fill=tuple(int(v * al) for v in BLUE))
        fnt = font(60 if len(PAGES[i]) < 8 else 50, INTER)
        d.text((W / 2 - text_w(PAGES[i], fnt) / 2, 625), PAGES[i], font=fnt, fill=BG)
    # pacchi di lui
    for tb, (bx, lv) in zip(BOX_T, BOX_P):
        if t < tb - 0.25: continue
        k = ease(seg(t, tb - 0.25, tb)); y = G - lv * BH
        box(d, bx, y - (1 - k) * 420)
    # LUI (bianco): compra
    if t < T_CAL0:
        pa = TAP if any(tb - 0.25 <= t < tb - 0.05 for tb in BOX_T) else PHONE
    elif t < T_ENV1: pa = STAND
    elif t < T_FLY1: pa = HOLD
    else: pa = mix(HOLD, SAD, seg(t, T_FLY1, T_FLY1 + 0.3))
    ska = draw_fig(dl, on_ground(XA, G, pa, K), pa, WHITE, -1, 0, K)
    if t < T_CAL0:
        h = ska["hr"]; dl.rectangle([h[0] - 18, h[1] - 44, h[0] + 8, h[1] + 4], fill=(150, 190, 255))
    # L'ALTRO (blu): mette via il telefono e aspetta
    if t < T_OFF: pb = PHONE
    elif t < T_OFF + 0.25: pb = mix(PHONE, STAND, seg(t, T_OFF, T_OFF + 0.25))
    elif t < T_ENV1: pb = ARMS
    elif t < T_ANS + 0.3: pb = HOLD
    else: pb = HOLD
    skb = draw_fig(dl, on_ground(XB, G, pb, K), pb, BLUE, -1, 0, K)
    if t < T_OFF:
        h = skb["hr"]; dl.rectangle([h[0] - 8, h[1] - 44, h[0] + 18, h[1] + 4], fill=(150, 190, 255))
    # buste della tredicesima
    if t >= T_ENV0:
        k = ease(seg(t, T_ENV0, T_ENV1))
        for x, sk, who in ((XA, ska, "a"), (XB, skb, "b")):
            hand = ((sk["hl"][0] + sk["hr"][0]) / 2, (sk["hl"][1] + sk["hr"][1]) / 2) if t >= T_ENV1 else (x, 980)
            cy = 300 + (hand[1] - 300) * k if t < T_ENV1 else hand[1]
            if who == "a" and t >= T_FLY0:
                if t < T_FLY1 + 0.3: envelope(d, hand[0], cy, (200, 200, 205), 1 - 0.5 * seg(t, T_FLY0, T_FLY1))
                for n, (dx, dy, dt) in enumerate(BILLS):
                    q = seg(t, T_FLY0 + dt, T_FLY0 + dt + 0.5)
                    if 0 < q < 1:
                        tx, ty = BOX_P[n % 7][0], G - BOX_P[n % 7][1] * BH - 30
                        bx = hand[0] + (tx - hand[0]) * ease(q) + dx; by = cy + (ty - cy) * q - 160 * math.sin(math.pi * q) + dy
                        bill(d, bx, by, (225, 225, 230), q * 6)
            elif who == "b":
                envelope(dl, hand[0], cy, BLUE if t >= T_ANS else (170, 200, 240))
            else:
                envelope(d, hand[0], cy, (225, 225, 230))
        # pila di banconote dell'altro
        if t >= T_ANS:
            n = int(min(8, (t - T_ANS) / 0.12))
            for j in range(n):
                bill(dl, XB + 130 + (8 if j % 2 else -8), G - 20 - j * 20, (110, 180, 255), 0.08 if j % 2 else -0.06)
    # fumetti
    for s, a, b, bx, by in C["fumetti"]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        bubble(d, bx, by, s, 36, al)
    if t >= T_FLY1 - 0.2:
        al = ease(seg(t, T_FLY1 - 0.2, T_FLY1 + 0.1))
        c = tuple(int(BG[j] + (200 - BG[j]) * al) for j in range(3))
        label(d, 190, G - 3 * BH - 70, C["etichetta_pacchi"], c, 34)
    # testi
    if t < T_ANS:
        phrase(d, [(C["frase1"][0], WHITE), (C["frase1"][1], BLUE)])
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, size=C.get("size2", 56), cps=50)
        al = ease(seg(t, T_ANS + 0.5, T_ANS + 0.8))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            for n, s in enumerate(C["invito"]):
                fnt = font(38); d.text(((W - text_w(s, fnt)) / 2, 470 + n * 48), s, font=fnt, fill=c)
    watermark(d)
    return glow(img, lit, 22, 1.0)

if __name__ == "__main__":
    S = C.get("velocita", 1.0)
    if len(sys.argv) > 3:
        frame(float(sys.argv[3]) * S).save(OUT); sys.exit()
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03)), (0.0, s_pop(0.5, 900))]
    for k in range(1, int(T_CAL0 / 0.44)): ev.append((k * 0.44, s_pop(0.12, 1200)))
    for tb in BOX_T: ev += [(tb - 0.25, s_click(0.35)), (tb, s_tok(140, 0.12, 0.6))]
    for s, a, b, bx, by in C["fumetti"]: ev.append((a, s_pop(0.3)))
    ev.append((T_OFF, s_click(0.4)))
    for k in range(len(PAGES)): ev.append((T_CAL0 + k * (T_CAL1 - T_CAL0) / len(PAGES), s_whoosh(0.18, 0.25)))
    ev += [(T_ENV0, s_whoosh(0.5, 0.3, False)), (T_ENV1, s_thud(0.5, 90)), (T_FLY0, s_whoosh(0.9, 0.45))]
    ev += [(T_ANS - 0.3, s_rise(2.2, 0.45)), (T_ANS + 0.05, s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 50, s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
