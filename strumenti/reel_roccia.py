#!/usr/bin/env python3
"""Reel B in inglese "One hit a day." – 28/11 (metafora della costanza, idea del titolare).

Un omino blu minuscolo davanti a una roccia gigante con scritto IMPOSSIBLE. Un colpo di piccone al giorno.
I giorni accelerano, le crepe crescono piano; due tizi seduti sulla roccia ridono. Giorno 251: il piccone si spezza,
lui cade in ginocchio. Si rialza e continua con il pezzo rotto. Giorno 365: ultimo colpo al rallentatore, le crepe si
accendono, la roccia si apre in due, entra la luce della città. I due che ridevano cadono; uno dice "LUCKY.".
Uso: python3 reel_roccia.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc
import motore_arch as A
from motore_arch import W, H, WHITE, BLUE, ease, lin, keys

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C["durata"]; T = C["tempi"]
GY = 1360
FX = 150                                   # dove sta l'omino
HIT = (262, 1120)                          # dove colpisce la roccia
ROCK = [(250, GY), (232, 1150), (262, 960), (300, 830), (380, 735), (520, 690), (660, 700), (800, 750), (905, 850),
        (965, 1000), (985, 1180), (1000, GY)]
SPLIT_X = [(620, 690), (600, 820), (640, 960), (595, 1090), (630, 1230), (610, GY)]    # linea di rottura

def crack_tree():
    rng = random.Random(11); segs = []
    def grow(x, y, ang, L, depth, t0):
        if depth == 0 or L < 14: return
        x2 = x + math.cos(ang) * L; y2 = y + math.sin(ang) * L
        segs.append((x, y, x2, y2, t0)); t1 = t0 + L
        grow(x2, y2, ang + rng.uniform(-0.45, 0.45), L * rng.uniform(0.78, 0.95), depth - 1, t1)
        if rng.random() < 0.45: grow(x2, y2, ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1), L * 0.6, depth - 2, t1)
    for a in (-0.55, -0.15, 0.2, 0.55, 0.0): grow(HIT[0], HIT[1], a, 70, 9, 0)
    for (x0, y0), (x1, y1) in zip(SPLIT_X, SPLIT_X[1:]): segs.append((x0, y0, x1, y1, 900 + (y0 - 690)))
    return segs
CRACKS = crack_tree()
MAXC = max(s[4] for s in CRACKS)

def day(t):
    return int(keys(t, [(0, 1), (T["acc0"], 1), (T["rotto"], 250), (T["rotto"] + 0.01, 251), (T["riparte"], 251), (T["ultimo"] - 1.0, 364), (T["ultimo"], 365)]))

def crack_amount(t):
    return keys(t, [(0, 0), (T["rotto"], 0.32 * MAXC), (T["ultimo"] - 1.0, 0.62 * MAXC), (T["ultimo"] + 0.6, 1.25 * MAXC)])

def hits(t):
    """Istanti dei colpi fino a t (per animazione e suoni)."""
    out = [0.45, 1.25, 2.0]
    k = T["acc0"]
    while k < T["rotto"]: out.append(k); k += max(0.17, 0.42 - 0.05 * (k - T["acc0"]))
    k = T["riparte"] + 0.3
    while k < T["ultimo"] - 1.0: out.append(k); k += 0.2
    out.append(T["ultimo"])
    return out
HITS = hits(DUR)

def rock_layer(t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon(ROCK, fill=(66, 66, 76, 255), outline=(120, 120, 132, 255))
    d.polygon([(300, 830), (380, 735), (520, 690), (560, 760), (430, 820), (330, 900)], fill=(84, 84, 96, 255))
    d.polygon([(905, 850), (965, 1000), (985, 1180), (1000, GY), (900, GY), (930, 1100)], fill=(52, 52, 60, 255))
    rng = random.Random(4)
    for _ in range(40):
        x = rng.uniform(320, 940); y = rng.uniform(780, 1330); r = rng.uniform(4, 12)
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(58, 58, 68, 255))
    fnt = mc.font(92, mc.INTER); s = "IMPOSSIBLE"; tw = mc.text_w(s, fnt)
    d.text((620 - tw / 2, 990), s, font=fnt, fill=(44, 44, 52, 255))
    amt = crack_amount(t)
    glow = ease((t - T["ultimo"] - 0.15) / 0.35)
    for x0, y0, x1, y1, t0 in CRACKS:
        if amt <= t0: continue
        L = math.hypot(x1 - x0, y1 - y0); k = min(1, (amt - t0) / L)
        col = tuple(int(c0 + (c1 - c0) * glow) for c0, c1 in zip((20, 20, 24), (255, 230, 160))) + (255,)
        d.line([(x0, y0), (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)], fill=col, width=4 if glow < 0.5 else 6)
    a = np.minimum(np.asarray(lay.split()[3]), ROCK_MASK); lay.putalpha(Image.fromarray(a))
    return lay

ROCK_MASK = np.asarray((lambda m: (ImageDraw.Draw(m).polygon(ROCK, fill=255), m)[1])(Image.new('L', (W, H), 0)))

def split_masks():
    left = [(0, 0), (SPLIT_X[0][0], 0)] + SPLIT_X + [(0, H)]
    right = [(SPLIT_X[0][0], 0), (W, 0), (W, H)] + SPLIT_X[::-1]
    ml = Image.new("L", (W, H), 0); ImageDraw.Draw(ml).polygon(left, fill=255)
    mr = Image.new("L", (W, H), 0); ImageDraw.Draw(mr).polygon(right, fill=255)
    return ml, mr
ML, MR = split_masks()

def skyline(d, a):
    if a <= 0: return
    rng = random.Random(2); x = 420
    while x < 820:
        w = rng.uniform(30, 60); h = rng.uniform(90, 260)
        d.rectangle([x, 1290 - h, x + w, 1290], fill=tuple(int(c * a) for c in (30, 60, 110)))
        for wy in range(int(1290 - h + 14), 1280, 26):
            for wx in range(int(x + 6), int(x + w - 8), 14):
                if rng.random() < 0.6: d.rectangle([wx, wy, wx + 6, wy + 10], fill=tuple(int(c * a) for c in (255, 220, 140)))
        x += w + rng.uniform(4, 14)

def pickaxe(d, v, hand, ang, broken=False):
    a = math.radians(ang); L = 120 if not broken else 0
    end = (hand[0] + math.cos(a) * L, hand[1] + math.sin(a) * L)
    if not broken:
        d.line([v.p(*hand), v.p(*end)], fill=(150, 110, 70), width=int(v.s(9)))
    hx, hy = end
    pa = a + math.pi / 2
    tip1 = (hx + math.cos(pa) * 46, hy + math.sin(pa) * 46); tip2 = (hx - math.cos(pa) * 30, hy - math.sin(pa) * 30)
    d.polygon([v.p(*tip1), v.p(hx + math.cos(a) * 9, hy + math.sin(a) * 9), v.p(*tip2), v.p(hx - math.cos(a) * 9, hy - math.sin(a) * 9)], fill=(190, 195, 205))

def frame(t):
    img = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
    dark = 0.35 * ease((t - T["rotto"]) / 0.4) * (1 - ease((t - T["riparte"]) / 0.6))
    for k in range(16):
        c = int((6 + min(k, 11) * 1.4) * (1 - dark)); d.rectangle([0, 120 * k, W, 120 * k + 120], fill=(c, c, c + 6))
    split = ease((t - T["ultimo"] - 0.55) / 0.9)
    # luce e città dietro la roccia
    if split > 0:
        light = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(light)
        ld.ellipse([620 - 520 * split, 1000 - 420, 620 + 520 * split, 1000 + 420], fill=(255, 214, 140))
        light = light.filter(ImageFilter.GaussianBlur(90))
        img = Image.fromarray(np.clip(np.asarray(img, dtype=int) + (np.asarray(light, dtype=int) * 0.8 * split).astype(int), 0, 255).astype("uint8")); d = ImageDraw.Draw(img)
        skyline(d, split)
    G = GY; d.rectangle([0, G, W, H], fill=(18, 18, 22)); d.line([(0, G), (W, G)], fill=(85, 85, 95), width=3)
    # roccia (intera o in due pezzi)
    lay = rock_layer(t)
    if split <= 0:
        img.paste(lay, (0, 0), lay)
    else:
        for m, sx, rot in ((ML, -260, 9), (MR, 300, -8)):
            piece = Image.new("RGBA", (W, H), (0, 0, 0, 0)); piece.paste(lay, (0, 0), Image.fromarray(np.minimum(np.asarray(lay.split()[3]), np.asarray(m))))
            piece = piece.rotate(rot * split, center=(620, GY), resample=Image.BICUBIC)
            img.paste(piece, (int(sx * split), int(30 * split)), piece)
    d = ImageDraw.Draw(img); v = A.V(1.0, 540, 960)
    # i due che ridono sopra la roccia, poi cadono
    for j, bx in enumerate((470, 660)):
        if split <= 0:
            by = 700 + (12 if j == 0 else -5)
            laugh = 0.5 + 0.5 * math.sin(t * 12 + j)
            kind = "big" if t < T["rotto"] else ("smug" if t < T["ultimo"] else "scared")
            A.figure(d, v, bx, by, kind, (170, 170, 180), arms=(0.3 + 0.4 * laugh * (t < T["rotto"]), 0.2), sit=1.0, k=0.62)
        else:
            k = min(1, (t - T["ultimo"] - 0.55) / 0.6)
            fx = bx + (-260 if j == 0 else 300) * split; fy = 700 + (GY - 700) * k * k
            rot = (-88 if j == 0 else 88) * min(1, k * 1.3)
            if k >= 1: fx += (110 if j == 0 else -110)
            A.figure(d, v, fx, fy, "ko" if k >= 1 and j == 0 else ("neutral" if k >= 1 else "scared"), (170, 170, 180), rot=rot if j == 0 or k < 1 else 0, arms=(0.2, 0.2), k=0.62)
    # l'omino con il piccone
    last = max([h for h in HITS if h <= t] or [-9])
    ph = t - last
    nxt = min([h for h in HITS if h > t] or [99]); per = max(0.17, nxt - last)
    swing = 1 - ease(min(1, ph / (per * 0.85))) if ph < per else 0
    ang = -60 + 70 * (1 - swing)                                              # -60 alzato, +10 sul colpo
    if T["ultimo"] - 1.0 <= t < T["ultimo"]: ang = keys(t, [(T["ultimo"] - 1.0, 0), (T["ultimo"] - 0.6, -80), (T["ultimo"], 10)])
    broken = T["rotto"] <= t
    kneel = T["rotto"] + 0.25 <= t < T["riparte"]
    fkind = "focus"
    if kneel: fkind = "tired"
    elif t >= T["ultimo"] + 0.6: fkind = "big"
    x = FX if t < T["ultimo"] + 1.2 else FX + (t - T["ultimo"] - 1.2) * 260
    if kneel:
        A.figure(d, v, x, GY, fkind, BLUE, arms=(0.05, 0.05), sit=1.0, k=0.8)
    elif t >= T["ultimo"] + 0.6:
        A.figure(d, v, x, GY, fkind, BLUE, arms=(0.9, 0.9), k=0.8, legs=0.5 * math.sin(t * 9) if t > T["ultimo"] + 1.2 else 0)
    else:
        A.figure(d, v, x, GY, fkind, BLUE, arms=(0.2, 0.55 if not broken else 0.5), k=0.8)
        hand = (x + 70, GY - 255 + (0 if not broken else 30))
        if t < T["rotto"]: pickaxe(d, v, hand, ang)
        elif t >= T["riparte"]: pickaxe(d, v, hand, ang * 0.6 + 20, broken=True)
    if T["rotto"] <= t < T["rotto"] + 1.0:                                     # il pezzo che vola via
        k = t - T["rotto"]; px_ = FX + 160 - 220 * k; py_ = GY - 300 - 300 * k + 700 * k * k
        if py_ < GY - 10: pickaxe(d, v, (px_, py_), 200 * k, broken=True)
        d.line([v.p(FX + 120 - 80 * k, GY - 180 + 400 * k * k), v.p(FX + 30 - 80 * k, GY - 140 + 400 * k * k)], fill=(150, 110, 70), width=9)
    # scintille sul colpo
    if ph < 0.12 and last > 0 and t < T["ultimo"] + 0.3:
        rng = random.Random(int(last * 100))
        for _ in range(9):
            a_ = rng.uniform(-2.6, -0.4); r = 30 + 160 * ph / 0.12
            d.line([(HIT[0] + math.cos(a_) * r * 0.5, HIT[1] + math.sin(a_) * r * 0.5), (HIT[0] + math.cos(a_) * r, HIT[1] + math.sin(a_) * r)], fill=(255, 230, 170), width=3)
    # fumetti
    for who, s, a0, b0 in C["fumetti"]:
        if a0 <= t < b0:
            al = ease((t - a0) / 0.06) * (1 - ease((t - b0 + 0.06) / 0.06))
            if who == "lui": p_ = (x + 10, GY - 360)
            elif who == "a": p_ = (470, 560) if split <= 0 else (470 - 260 + 110, GY - 260)
            else: p_ = (660, 560) if split <= 0 else (660 + 300 - 110, GY - 300)
            A.bubble(d, v, p_, s, al, size=28)
    A.counter(d, f"DAY {day(t)}", 1.0)
    A.caption(d, C["testi"], t, DUR)
    A.question(d, C["domanda"], t, C["domanda_t"], 420, 50)
    if T["ultimo"] + 0.5 <= t < T["ultimo"] + 0.9:                              # scossa
        img = Image.fromarray(np.roll(np.asarray(img), int(12 * math.sin(t * 90)), axis=1))
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    ev = [(0.0, mc.s_hum(DUR, 0.035))]
    for s, a, b in C["testi"]: ev.append((a, mc.s_pop(0.22, 800)))
    for h in HITS[:-1]: ev.append((h, mc.s_tok(520, 0.05, 0.35)))
    ev += [(T["rotto"], mc.s_crack(1.0)), (T["rotto"] + 0.5, mc.s_thud(0.5, 60)),
           (T["ultimo"] - 0.6, mc.s_whoosh(0.6, 0.3)), (T["ultimo"], mc.s_tok(420, 0.08, 0.9)), (T["ultimo"] + 0.02, mc.s_thud(0.8, 45)),
           (T["ultimo"] + 0.5, mc.s_crack(1.0)), (T["ultimo"] + 0.6, mc.s_thud(1.0, 40)), (T["ultimo"] + 0.7, mc.s_rise(2.6, 0.5)),
           (T["ultimo"] + 1.3, mc.s_thud(0.6, 70)), (C["domanda_t"], mc.s_chime(0.35, 660))]
    for w_, s, a, b in C["fumetti"]: ev.append((a, mc.s_pop(0.2, 650)))
    A.finish(OUT, DUR, frame, ev)
