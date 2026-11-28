#!/usr/bin/env python3
"""Reel B in inglese "4 climbers. 1 mountain." – 28/11.

Quattro archetipi scalano la stessa montagna, ognuno sulla sua via; sotto, la folla con i telefoni li guarda.
MOTIVATION si ferma presto ("TOMORROW."). EGO è il più veloce finché la folla guarda: quando la folla se ne va,
si ferma, guarda giù ("WHERE IS EVERYONE?") e torna indietro. OBSESSION e DISCIPLINE arrivano in cima al buio.
Elemento che fa commentare: l'Ego molla (contro il meme "Ego accepts death but not defeat") + squadra da scegliere.
Uso: python3 reel_climbers.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc
import motore_arch as A
from motore_arch import W, H, WHITE, BLUE, ease, lin, keys

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C["durata"]
BASE_Y = 1440
PEAK = (540, 900)
BASES = [(200, BASE_Y), (400, BASE_Y), (660, BASE_Y), (880, BASE_Y)]     # MOTIVATION, EGO, OBSESSION, DISCIPLINE
NAMES = C["nomi"]
P = C["percorsi"]                                                       # keyframe (t, progresso) per ognuno
T_LEAVE = C["folla_via"]
STARS = [(random.Random(i).uniform(0, 1080), random.Random(i * 7).uniform(120, 1200)) for i in range(90)]

def pos(i, p):
    bx, by = BASES[i]
    ex = 380 + i * 95
    return (bx + (ex - bx) * p, by + (PEAK[1] - by) * p)

def frame(t):
    img = Image.new("RGB", (W, H), A.BG); d = ImageDraw.Draw(img)
    v = A.V(1.0 + 0.04 * ease(t / 3), 540, 1010)
    dark = ease((t - T_LEAVE) / 1.5)
    for x, y in STARS:                                                    # stelle (più visibili quando è buio)
        c = int(60 + 120 * dark); Q = v.p(x, y); d.ellipse([Q[0] - 2, Q[1] - 2, Q[0] + 2, Q[1] + 2], fill=(c, c, c + 10))
    # luci della folla
    for k, sx in enumerate((240, 540, 840)):
        a = (1 - dark) * (0.55 + 0.1 * math.sin(t * 3 + k))
        if a > 0.02:
            tip = (PEAK[0] + (sx - 540) * 0.2, PEAK[1] + 120)
            poly = [v.p(sx - 30, 1560), v.p(sx + 30, 1560), v.p(tip[0] + 160, tip[1]), v.p(tip[0] - 160, tip[1])]
            layer = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(layer).polygon(poly, fill=(int(60 * a), int(60 * a), int(48 * a)))
            img = Image.fromarray(__import__("numpy").clip(__import__("numpy").asarray(img, dtype=int) + __import__("numpy").asarray(layer, dtype=int), 0, 255).astype("uint8")); d = ImageDraw.Draw(img)
    # montagna
    d.polygon([v.p(-60, BASE_Y + 20), v.p(350, PEAK[1]), v.p(700, PEAK[1]), v.p(1140, BASE_Y + 20)], fill=(30, 30, 38), outline=(110, 110, 122))
    d.polygon([v.p(350, PEAK[1]), v.p(700, PEAK[1]), v.p(680, PEAK[1] + 26), v.p(370, PEAK[1] + 26)], fill=(210, 210, 220))
    for i in range(4):                                                    # le vie
        for s in range(0, 40):
            if s % 2: continue
            a_, b_ = pos(i, s / 40), pos(i, (s + 1) / 40)
            d.line([v.p(*a_), v.p(*b_)], fill=(70, 70, 82), width=3)
    # terreno e folla
    G = v.p(0, BASE_Y + 20); d.rectangle([0, G[1], W, H], fill=(12, 12, 16))
    leave = ease((t - T_LEAVE) / 1.6)
    for k in range(14):
        cx = 60 + k * 72 - leave * (1300 + 30 * k)
        if cx < -60: continue
        cheer = 0.5 + 0.5 * math.sin(t * 7 + k) if t < T_LEAVE else 0.0
        A.figure(d, v, cx, 1640, "big" if t < T_LEAVE else "neutral", (150, 150, 160), arms=(0.2, 0.75 + 0.2 * cheer), k=0.42,
                 legs=0.5 * math.sin(t * 10 + k) if t >= T_LEAVE else 0)
        if t < T_LEAVE and (int(t * 4) + k) % 5 == 0:                   # flash dei telefoni
            Q = v.p(cx + 30, 1640 - 135); d.ellipse([Q[0] - 7, Q[1] - 7, Q[0] + 7, Q[1] + 7], fill=(255, 255, 230))
    # scalatori
    for i in range(4):
        p = keys(t, P[i]); x, y = pos(i, p)
        moving = abs(keys(t + 0.1, P[i]) - p) > 0.002
        down = keys(t + 0.1, P[i]) < p - 0.002
        if i == 0 and t > C["mot_stop"]:
            kind, arms, sit = "tired", (0.2, 0.2), 1.0
        elif i == 1 and t >= T_LEAVE + 0.3:
            kind = "worried" if not down else "tired"; arms = (0.3, 0.3); sit = 1.0 if t > C["ego_seduto"] else 0.0
        else:
            ph = math.sin(t * 9 + i)
            kind = {0: "big", 1: "smug", 2: "strain", 3: "focus"}[i]
            arms = (0.55 + 0.35 * ph, 0.55 - 0.35 * ph) if moving else (0.2, 0.2)
            sit = 0.0
        top = p > 0.985
        if top: kind, arms = "big", (0.9, 0.9)
        col = BLUE if i == 3 else WHITE
        A.figure(d, v, x, y, kind, col, rot=-8 if (moving and not down) else 0, arms=arms, k=0.58, sit=sit,
                 legs=0.6 * math.sin(t * 9 + i) if moving else 0)
        A.label(d, v, x, y + (10 if i % 2 == 0 else 40), NAMES[i], (BLUE if i == 3 else (205, 205, 210)))
    # fumetti
    for i, s, a0, b0 in C["fumetti"]:
        if a0 <= t < b0:
            al = ease((t - a0) / 0.08) * (1 - ease((t - b0 + 0.08) / 0.08))
            x, y = pos(i, keys(t, P[i])); A.bubble(d, v, (x, y - 280), s, al)
    hrs = int(lin(t, 1.0, C["vetta"], 1, 12))
    A.counter(d, f"HOUR {hrs}/12", 1 - 0.6 * ease((t - C['fine0']) / 0.4))
    A.caption(d, C["testi"], t, DUR)
    A.question(d, C["domanda"][0], t, C["domanda_t"], 410, 46)
    A.question(d, C["domanda"][1], t, C["domanda_t"], 470, 46)
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    ev = [(0.0, mc.s_hum(DUR, 0.03))]
    for k in range(int(T_LEAVE / 0.18)): ev.append((k * 0.18, mc.s_clap(0.18)))
    for s, a, b in C["testi"]: ev.append((a, mc.s_pop(0.25, 800)))
    for k in range(int(C["vetta"] / 0.4)): ev.append((0.6 + k * 0.4, mc.s_tok(330, 0.04, 0.12)))
    ev += [(T_LEAVE, mc.s_whoosh(1.4, 0.35, False)), (C["ego_giu"], mc.s_whoosh(0.8, 0.25, False)),
           (C["vetta"] - 0.6, mc.s_chime(0.35, 990)), (C["vetta"] + 0.2, mc.s_chime(0.35, 1320)),
           (C["fine0"], mc.s_rise(2.4, 0.4)), (C["domanda_t"], mc.s_chime(0.35, 660))]
    for i, s, a, b in C["fumetti"]: ev.append((a, mc.s_pop(0.2, 650)))
    A.finish(OUT, DUR, frame, ev)
