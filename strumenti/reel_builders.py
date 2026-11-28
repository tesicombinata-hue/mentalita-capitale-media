#!/usr/bin/env python3
"""Reel B in inglese "4 builders. 1 idea. 100 days." – 28/11.

EGO costruisce solo la facciata che si vede; ACTION TAKER costruisce veloce, crolla due volte e riparte;
PERFECTIONIST mette un mattone, lo toglie, lo rimette: la torre più bassa; OVERTHINKER resta seduto con i progetti.
Giorno 100: la tempesta. Cade la facciata, crolla la torre alta, volano via i progetti: resta solo quella del Perfectionist.
Elemento che fa commentare: vince l'archetipo che il pubblico considera perdente (contro "chi agisce vince sempre")
+ squadra da scegliere. Testi nel JSON. Uso: python3 reel_builders.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc
import motore_arch as A
from motore_arch import W, H, WHITE, BLUE, GREY, ease, lin

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C["durata"]
GY = 1330
XS = [175, 400, 625, 850]          # PERFECTIONIST, OVERTHINKER, EGO, ACTION TAKER
NAMES = C["nomi"]
BW, BH = 42, 21
T_D1, T_D100 = 1.0, 15.5
STORM = C["tempesta"]              # inizio della tempesta
COLL = C["crolli"]                 # crolli della torre di Action Taker (t)
T_EGO_FALL, T_ACT_FALL, T_PLANS = STORM + 0.5, STORM + 1.1, STORM + 0.2

def day(t): return int(lin(t, T_D1, T_D100, 1, 100))

def act_rows(t):
    a, b = COLL
    if t < a: return int(lin(t, 1.2, a - 0.1, 0, 16))
    if t < b: return int(lin(t, a + 0.8, b - 0.1, 0, 22))
    return int(lin(t, b + 0.8, T_D100, 0, 27))

def perf_rows(t): return int(lin(t, 1.5, T_D100, 0, 10))
def ego_h(t): return lin(t, 1.1, 5.0, 40, 640)
def plans(t): return int(lin(t, 1.3, T_D100, 1, 14))

def brick(d, v, cx, by, rot=0.0, col=(225, 225, 230), edge=(70, 70, 78)):
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    pts = [(-BW / 2, -BH / 2), (BW / 2, -BH / 2), (BW / 2, BH / 2), (-BW / 2, BH / 2)]
    P = [v.p(cx + x * ca - y * sa, by + x * sa + y * ca) for x, y in pts]
    d.polygon(P, fill=col, outline=edge)

def tower_pos(n, x0, messy, seed):
    """Posizioni (cx, cy, rot) dei mattoni di una torre di n file (2 mattoni per fila)."""
    rng = random.Random(seed); out = []
    for r in range(n):
        off = (BW / 2 if r % 2 else 0) - BW / 4
        jit = rng.uniform(-9, 9) * messy; tilt = rng.uniform(-6, 6) * messy
        for c in range(2):
            out.append((x0 + off + (c - 0.5) * BW + jit, GY - BH / 2 - r * BH, tilt))
    return out

def falling(d, v, bricks, t0, t, seed, side=1):
    rng = random.Random(seed)
    for i, (x, y, r) in enumerate(bricks):
        fx = x + side * rng.uniform(15, 105); fy = GY - BH / 2 - rng.choice([0, 0, 0, 1, 1, 2]) * BH * 0.9
        fr = rng.uniform(-80, 80)
        k = max(0.0, min(1.0, (t - t0 - (len(bricks) - i) * 0.006) / 0.6))
        e = k * k
        brick(d, v, x + (fx - x) * e, y + (fy - y) * e, r + (fr - r) * e)

def frame(t):
    img = Image.new("RGB", (W, H), A.BG); d = ImageDraw.Draw(img)
    z = 1.15 + 0.04 * ease(t / 2.0); v = A.V(z, 520, 915)
    storm = STORM <= t < STORM + 2.6
    # terreno
    G = v.p(0, GY); d.rectangle([0, G[1], W, H], fill=(14, 14, 18)); d.line([(0, G[1]), (W, G[1])], fill=(70, 70, 80), width=3)
    if storm:                                                           # pioggia
        rng = random.Random(int(t * 30))
        for _ in range(140):
            x = rng.uniform(-100, 1180); y = rng.uniform(300, 1700)
            d.line([(x, y), (x + 26, y + 70)], fill=(90, 100, 120), width=2)
    # PERFECTIONIST
    x = XS[0]; n = perf_rows(t)
    for bx, by, r in tower_pos(n, x + 40, 0, 1): brick(d, v, bx, by, r)
    fix = (int(t * 1.4) % 2 == 0) and t < T_D100
    if fix and n < 10:                                                   # il mattone che toglie e rimette
        brick(d, v, x + 40 + 10 * math.sin(t * 6), GY - BH / 2 - n * BH - 16 * abs(math.sin(t * 3)), 0)
    won = t >= C["fine0"]
    A.figure(d, v, x - 50, GY, "focus" if not won else "smile", BLUE if won else WHITE,
             arms=(0.0, 0.45 + 0.2 * math.sin(t * 5)) if not won else (0.55, 0.55))
    # OVERTHINKER
    x = XS[1]
    np_ = plans(t)
    if t < T_PLANS:
        for k in range(np_): d.rectangle([*v.p(x + 30, GY - 6 - k * 7), *v.p(x + 95, GY - 1 - k * 7)], fill=(200, 200, 205), outline=(90, 90, 95))
    else:
        for k in range(np_):
            q = t - T_PLANS - k * 0.04
            if q < 0: continue
            px = x + 60 + 700 * q + 40 * math.sin(q * 9 + k); py = GY - 10 - k * 7 - 350 * q + 60 * math.sin(q * 7 + k)
            d.polygon([v.p(px - 30, py - 4), v.p(px + 30, py - 12), v.p(px + 32, py + 4), v.p(px - 28, py + 10)], fill=(200, 200, 205))
    A.figure(d, v, x - 30, GY, "worried" if not storm else "scared", WHITE, arms=(0.3, 0.3), sit=1.0)
    # EGO: la facciata
    x = XS[2]; h = ego_h(t)
    ang = 0.0 if t < T_EGO_FALL else 88 * ease((t - T_EGO_FALL) / 0.6) ** 1.6
    a = math.radians(ang); px0, py0 = x + 95, GY
    rect = [(-100, 0), (0, 0), (0, -h), (-100, -h)]
    P = [v.p(px0 + rx * math.cos(a) - ry * math.sin(a), py0 + rx * math.sin(a) + ry * math.cos(a)) for rx, ry in rect]
    d.polygon(P, fill=(40, 40, 48), outline=(200, 200, 210))
    if ang < 10:
        for k in range(int(h // 70)):
            wy = GY - 50 - k * 70
            d.rectangle([*v.p(x + 10, wy - 18), *v.p(x + 75, wy)], fill=(230, 230, 120) if (k % 3) else (90, 90, 100))
    ego_kind = "smug" if t < STORM else ("scared" if t < STORM + 1.6 else "worried")
    A.figure(d, v, x - 40, GY, ego_kind, WHITE, arms=(0.9, 0.9) if t < STORM else (0.2, 0.2))
    # ACTION TAKER
    x = XS[3]
    for i, ct in enumerate(COLL):
        rows = int(lin(ct - 0.11, 1.2, COLL[0] - 0.1, 0, 16)) if i == 0 else int(lin(ct - 0.11, COLL[0] + 0.8, COLL[1] - 0.1, 0, 22))
        if t >= ct: falling(d, v, tower_pos(rows, x + 40, 1, 10 + i), ct, t, 20 + i, 1 if i == 0 else -1)
    if t < T_ACT_FALL:
        for bx, by, r in tower_pos(act_rows(t), x + 40, 1, 12 if t >= COLL[1] else (11 if t >= COLL[0] else 10)): brick(d, v, bx, by, r)
    else:
        falling(d, v, tower_pos(act_rows(T_ACT_FALL - 0.01), x + 40, 1, 12), T_ACT_FALL, t, 30, -1)
    busy = t < T_D100 and not any(0 <= t - ct < 0.9 for ct in COLL)
    A.figure(d, v, x - 45, GY, "focus" if busy else ("scared" if t < C["fine0"] else "tired"), WHITE,
             arms=(0.0, 0.5 + 0.3 * math.sin(t * 9)) if busy else (0.1, 0.1), legs=0.4 * math.sin(t * 9) if busy else 0)
    # lampi
    for ft in (STORM + 0.05, STORM + 0.75):
        if 0 <= t - ft < 0.12: img = Image.blend(img, Image.new("RGB", (W, H), (230, 235, 255)), 0.55 * (1 - (t - ft) / 0.12)); d = ImageDraw.Draw(img)
    # fumetti
    for i, s, a0, b0 in C["fumetti"]:
        if a0 <= t < b0:
            al = ease((t - a0) / 0.08) * (1 - ease((t - b0 + 0.08) / 0.08))
            A.bubble(d, v, (XS[i] - 40, GY - 470 - (60 if i == 0 else 0)), s, al)
    # etichette
    for i, nm in enumerate(NAMES):
        col = BLUE if (i == 0 and won) else (215, 215, 220)
        A.label(d, v, XS[i], GY + 40, nm, col)
    if t >= T_D1:
        A.counter(d, f"DAY {day(t)}/100", 1 - 0.6 * ease((t - C['fine0']) / 0.4))
    A.caption(d, C["testi"], t, DUR)
    A.question(d, C["domanda"][0], t, C["domanda_t"], 410, 46)
    A.question(d, C["domanda"][1], t, C["domanda_t"], 470, 46)
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    ev = [(0.0, mc.s_hum(DUR, 0.03))]
    for s, a, b in C["testi"]: ev.append((a, mc.s_pop(0.25, 800)))
    for k in range(int((T_D100 - 1.2) / 0.35)): ev.append((1.2 + k * 0.35, mc.s_tok(260, 0.05, 0.18)))
    for ct in COLL: ev += [(ct, mc.s_crack(0.7)), (ct + 0.35, mc.s_thud(0.8, 70)), (ct + 0.5, mc.s_tok(200, 0.06, 0.3))]
    ev += [(STORM, mc.s_whoosh(2.2, 0.5)), (STORM + 0.05, mc.s_thud(1.0, 40)), (STORM + 0.75, mc.s_thud(0.9, 38)),
           (T_EGO_FALL + 0.5, mc.s_thud(0.9, 60)), (T_ACT_FALL, mc.s_crack(0.9)), (T_ACT_FALL + 0.4, mc.s_thud(0.8, 70)),
           (C["fine0"], mc.s_rise(2.4, 0.4)), (C["domanda_t"], mc.s_chime(0.35, 660))]
    for i, s, a, b in C["fumetti"]: ev.append((a, mc.s_pop(0.2, 650)))
    A.finish(OUT, DUR, frame, ev)
