#!/usr/bin/env python3
"""Reel B in inglese "One hit a day." v2 – 28/11 (note del titolare: piccone tenuto davvero con due mani e picconate vere,
contatore dei giorni grande e dinamico, inquadratura più stretta).

Scena disegnata in coordinate "mondo", poi inquadrata da una camera con zoom (camera_keys) e infine i testi sopra.
Uso: python3 reel_roccia2.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc
import motore_arch as A
from motore_arch import W, H, WHITE, BLUE, RED, ease, lin, keys

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C["durata"]; T = C["tempi"]
GY = 1360
OX = 95                                                   # spostamento della roccia verso destra
SV = 0.78                                                  # roccia un po' più bassa (lascia spazio al contatore)
def sy(y): return GY - (GY - y) * SV
SX_ = 0.8                                                  # roccia più stretta (rientra tutta)
def hx(x): return 250 + (x - 250) * SX_ + OX
def sh(pts): return [(hx(x), sy(y)) for x, y in pts]
ROCK = sh([(250, GY), (232, 1150), (262, 960), (300, 830), (380, 735), (520, 690), (660, 700), (800, 750), (905, 850),
           (965, 1000), (985, 1180), (1000, GY)])
SPLIT_X = sh([(620, 690), (600, 820), (640, 960), (595, 1090), (630, 1230), (610, GY)])
HIT = (hx(243), 1135)
BYX = (hx(470), hx(640))                                   # i due seduti in cima
T_PUGNO = C["pugno"]
K = 0.95                                                   # scala del minatore
FX = HIT[0] - 200                                          # piedi del minatore
def top_y(x):
    ys = []
    for (x0, y0), (x1, y1) in zip(ROCK, ROCK[1:]):
        if min(x0, x1) <= x <= max(x0, x1) and x0 != x1: ys.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return min(ys)
LUCKY_X = BYX[1] + 200 + 40

# ---------------- crepe ----------------
def crack_tree():
    rng = random.Random(11); segs = []
    def grow(x, y, ang, L, depth, t0):
        if depth == 0 or L < 14: return
        x2 = x + math.cos(ang) * L; y2 = y + math.sin(ang) * L
        segs.append((x, y, x2, y2, t0)); t1 = t0 + L
        grow(x2, y2, ang + rng.uniform(-0.45, 0.45), L * rng.uniform(0.78, 0.95), depth - 1, t1)
        if rng.random() < 0.45: grow(x2, y2, ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1), L * 0.6, depth - 2, t1)
    for a in (-0.55, -0.15, 0.2, 0.55, 0.0): grow(HIT[0], HIT[1], a, 70, 9, 0)
    for (x0, y0), (x1, y1) in zip(SPLIT_X, SPLIT_X[1:]): segs.append((x0, y0, x1, y1, 900 + (y0 - sy(690))))
    return segs
CRACKS = crack_tree(); MAXC = max(s[4] for s in CRACKS)

def day(t):
    if t < T["acc0"]: return 1 + sum(1 for h in HITS if 0 < h <= t)
    return int(keys(t, [(T["acc0"], 1 + sum(1 for h in HITS if h < T["acc0"])), (T["rotto"], 250), (T["rotto"] + 0.01, 251), (T["riparte"], 251), (T["ultimo"] - 1.2, 364), (T["ultimo"], 365)]))
def crack_amount(t):
    return keys(t, [(0, 0), (T["rotto"], 0.32 * MAXC), (T["ultimo"] - 1.2, 0.62 * MAXC), (T["ultimo"] + 0.6, 1.25 * MAXC)])

def make_hits():
    out = [0.3 + 0.3 * i for i in range(8)]                         # subito un ritmo serrato
    k = T["acc0"]
    while k < T["rotto"] - 0.05: out.append(k); k += max(0.2, 0.5 - 0.06 * (k - T["acc0"]))
    out.append(T["rotto"])
    k = T["riparte"] + 0.45
    while k < T["ultimo"] - 1.3: out.append(k); k += 0.24
    out.append(T["ultimo"])
    return out
HITS = make_hits()

def swing_angle(t):
    """Angolo delle braccia (gradi, 0 = avanti orizzontale, -130 = sopra la testa dietro)."""
    if T["ultimo"] - 1.2 <= t < T["ultimo"] + 0.6:
        return keys(t, [(T["ultimo"] - 1.2, 5), (T["ultimo"] - 0.35, -150), (T["ultimo"] - 0.2, -150), (T["ultimo"], 8), (T["ultimo"] + 0.6, 8)])
    prev = max([h for h in HITS if h <= t] or [-1]); nxt = min([h for h in HITS if h > t] or [99])
    if nxt > 90: return 8
    per = min(nxt - max(prev, 0), 1.0)
    q = 1 - (nxt - t) / per
    if q < 0: return 8
    if q < 0.62: return 8 - 138 * ease(q / 0.62)                 # carica
    return -130 + 138 * ((q - 0.62) / 0.38) ** 2                    # colpo veloce

# ---------------- disegno ----------------
def limb(d, a, b, w, col):
    d.line([a, b], fill=col, width=int(w))
    for P in (a, b): d.ellipse([P[0] - w / 2, P[1] - w / 2, P[0] + w / 2, P[1] + w / 2], fill=col)

def pick_head(d, end, ang, scale=1.0):
    a = math.radians(ang); pa = a + math.pi / 2
    hx, hy = end
    tip_f = (hx + math.cos(pa) * 62 * scale + math.cos(a) * 10, hy + math.sin(pa) * 62 * scale + math.sin(a) * 10)   # punta
    tip_b = (hx - math.cos(pa) * 40 * scale + math.cos(a) * 6, hy - math.sin(pa) * 40 * scale + math.sin(a) * 6)
    d.polygon([tip_f, (hx + math.cos(a) * 12, hy + math.sin(a) * 12), tip_b, (hx - math.cos(a) * 12, hy - math.sin(a) * 12)], fill=(200, 205, 215), outline=(110, 115, 125))

def miner(d, t, x, kind, col=BLUE):
    """Il minatore con il piccone in mano (due mani sul manico)."""
    ang = swing_angle(t)
    broken = T["rotto"] + 0.02 <= t
    lean = 18 * (1 - (ang + 130) / 138) * -1 + 8                    # si piega in avanti sul colpo
    hip = (x, GY - 150 * K); S = (x + lean, GY - 290 * K); head = (x + lean * 1.2, GY - 332 * K)
    w = 20 * K
    limb(d, S, hip, w, col)
    limb(d, hip, (x - 40 * K, GY - 4), 14 * K, col); limb(d, hip, (x + 48 * K, GY - 4), 14 * K, col)
    a = math.radians(ang); dv = (math.cos(a), math.sin(a))
    R = 100 * K
    h1 = (S[0] + dv[0] * R, S[1] + dv[1] * R)                       # mano davanti
    h2 = (S[0] + dv[0] * (R - 26 * K), S[1] + dv[1] * (R - 26 * K))   # mano dietro
    for hh, off in ((h2, -10), (h1, 10)):
        el = ((S[0] + hh[0]) / 2 - dv[1] * off * K, (S[1] + hh[1]) / 2 + dv[0] * off * K)
        limb(d, S, el, 14 * K, col); limb(d, el, hh, 14 * K, col)
    if not broken or t >= T["riparte"]:
        L = 118 * K if not broken else 36 * K
        start = (h2[0] - dv[0] * 14 * K, h2[1] - dv[1] * 14 * K)
        end = (h1[0] + dv[0] * L, h1[1] + dv[1] * L)
        if not broken: d.line([start, end], fill=(156, 112, 70), width=int(10 * K))
        pick_head(d, end, ang, K if not broken else K * 0.85)
    elif t < T["rotto"] + 0.25:
        d.line([h2, (h1[0] + dv[0] * 50 * K, h1[1] + dv[1] * 50 * K)], fill=(156, 112, 70), width=int(10 * K))
    A.face(d, A.V(1, 540, 960), head, 36 * K, kind, col)
    return head

def rock_layer(t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon(ROCK, fill=(66, 66, 76, 255), outline=(120, 120, 132, 255))
    d.polygon(sh([(300, 830), (380, 735), (520, 690), (560, 760), (430, 820), (330, 900)]), fill=(84, 84, 96, 255))
    d.polygon(sh([(905, 850), (965, 1000), (985, 1180), (1000, GY), (900, GY), (930, 1100)]), fill=(52, 52, 60, 255))
    rng = random.Random(4)
    for _ in range(40):
        xx = hx(rng.uniform(320, 940)); yy = sy(rng.uniform(780, 1330)); r = rng.uniform(4, 12)
        d.ellipse([xx - r, yy - r * 0.6, xx + r, yy + r * 0.6], fill=(58, 58, 68, 255))
    fnt = mc.font(76, mc.INTER); s = "IMPOSSIBLE"; tw = mc.text_w(s, fnt)
    d.text((hx(600) - tw / 2, sy(1030)), s, font=fnt, fill=(44, 44, 52, 255))
    amt = crack_amount(t); glow = ease((t - T["ultimo"] - 0.15) / 0.35)
    for x0, y0, x1, y1, t0 in CRACKS:
        if amt <= t0: continue
        L = math.hypot(x1 - x0, y1 - y0); k = min(1, (amt - t0) / L)
        col = tuple(int(c0 + (c1 - c0) * glow) for c0, c1 in zip((20, 20, 24), (255, 230, 160))) + (255,)
        d.line([(x0, y0), (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k)], fill=col, width=4 if glow < 0.5 else 7)
    lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.split()[3]), ROCK_MASK)))
    return lay
ROCK_MASK = np.asarray((lambda m: (ImageDraw.Draw(m).polygon(ROCK, fill=255), m)[1])(Image.new('L', (W, H), 0)))

def split_masks():
    left = [(0, 0), (SPLIT_X[0][0], 0)] + SPLIT_X + [(0, H)]
    right = [(SPLIT_X[0][0], 0), (W, 0), (W, H)] + SPLIT_X[::-1]
    ml = Image.new("L", (W, H), 0); ImageDraw.Draw(ml).polygon(left, fill=255)
    mr = Image.new("L", (W, H), 0); ImageDraw.Draw(mr).polygon(right, fill=255)
    return np.asarray(ml), np.asarray(mr)
ML, MR = split_masks()

def skyline(d, a):
    rng = random.Random(2); x = hx(410)
    while x < hx(840):
        w = rng.uniform(30, 60); h = rng.uniform(90, 260)
        d.rectangle([x, 1290 - h, x + w, 1290], fill=tuple(int(c * a) for c in (30, 60, 110)))
        for wy in range(int(1290 - h + 14), 1280, 26):
            for wx in range(int(x + 6), int(x + w - 8), 14):
                if rng.random() < 0.6: d.rectangle([wx, wy, wx + 6, wy + 10], fill=tuple(int(c * a) for c in (255, 220, 140)))
        x += w + rng.uniform(4, 14)

def scene(t):
    img = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
    dark = 0.4 * ease((t - T["rotto"]) / 0.4) * (1 - ease((t - T["riparte"]) / 0.6))
    for k in range(16):
        c = int((8 + min(k, 11) * 1.4) * (1 - dark)); d.rectangle([0, 120 * k, W, 120 * k + 120], fill=(c, c, c + 7))
    split = ease((t - T["ultimo"] - 0.55) / 0.9)
    if split > 0:
        light = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(light)
        ld.ellipse([hx(620) - 520 * split, 1000 - 440, hx(620) + 520 * split, 1000 + 440], fill=(255, 214, 140))
        light = light.filter(ImageFilter.GaussianBlur(90))
        img = Image.fromarray(np.clip(np.asarray(img, dtype=int) + (np.asarray(light, dtype=int) * 0.85 * split).astype(int), 0, 255).astype("uint8")); d = ImageDraw.Draw(img)
        skyline(d, split)
    d.rectangle([0, GY, W, H], fill=(18, 18, 22)); d.line([(0, GY), (W, GY)], fill=(85, 85, 95), width=3)
    lay = rock_layer(t)
    if split <= 0: img.paste(lay, (0, 0), lay)
    else:
        al = np.asarray(lay.split()[3])
        for m, sx, rot in ((ML, -170, 7), (MR, 200, -7)):
            piece = Image.new("RGBA", (W, H), (0, 0, 0, 0)); piece.paste(lay, (0, 0), Image.fromarray(np.minimum(al, m)))
            piece = piece.rotate(rot * split, center=(hx(620), GY), resample=Image.BICUBIC)
            img.paste(piece, (int(sx * split), int(30 * split)), piece)
    d = ImageDraw.Draw(img); v = A.V(1.0, 540, 960)
    # i due sopra la roccia
    for j, bx in enumerate(BYX):
        if split <= 0:
            by = top_y(bx) + 82 * 0.72; laugh = 0.5 + 0.5 * math.sin(t * 12 + j)
            kind = "big" if t < T["rotto"] else ("smug" if t < T["ultimo"] else "scared")
            A.figure(d, v, bx, by, kind, (175, 175, 185), arms=(0.3 + 0.45 * laugh * (t < T["rotto"] + 1.5), 0.2), sit=1.0, k=0.72)
        else:
            k = min(1, (t - T["ultimo"] - 0.55) / 0.6)
            fx = bx + (-170 if j == 0 else 200) * split; y0 = top_y(bx) + 60; fy = y0 + (GY - y0) * k * k
            if k >= 1: fx += (90 if j == 0 else 40)
            rot = (-88 * min(1, k * 1.3)) if j == 0 else (88 * min(1, k * 1.3) if k < 1 else 0)
            if j == 1 and t >= T_PUGNO:                                                     # il pugno: vola via girando
                q = t - T_PUGNO; fx = LUCKY_X + 620 * q; fy = GY - 1050 * q + 520 * q * q; rot = 540 * q
                A.figure(d, v, fx, fy, "ko", (175, 175, 185), rot=rot, arms=(0.9, 0.9), k=0.72)
                continue
            A.figure(d, v, fx, fy, ("ko" if k >= 1 else "scared") if j == 0 else ("smug" if k >= 1 else "scared"), (175, 175, 185), rot=rot, arms=(0.2, 0.2), k=0.72)
    # il minatore
    kneel = T["rotto"] + 0.3 <= t < T["riparte"]
    x = keys(t, [(0, FX), (T["ultimo"] + 1.4, FX), (T_PUGNO - 0.15, LUCKY_X - 150), (DUR, LUCKY_X - 150)])
    if kneel:
        A.figure(d, v, x, GY, "tired", BLUE, arms=(0.05, 0.05), sit=1.0, k=K)
        d.polygon([(x + 120, GY - 6), (x + 170, GY - 22), (x + 190, GY - 6)], fill=(200, 205, 215))     # la testa del piccone a terra
    elif T_PUGNO - 0.35 <= t < T_PUGNO + 0.45:                                               # carica e tira il pugno
        A.figure(d, v, x, GY, "angry", BLUE, arms=(0.2, 0.0 if t < T_PUGNO - 0.05 else 0.5), k=K)
    elif t >= T["ultimo"] + 0.7:
        walking = T["ultimo"] + 1.4 < t < T_PUGNO - 0.35
        A.figure(d, v, x, GY, "focus" if walking else "big", BLUE, arms=(0.1, 0.1) if walking else (0.92, 0.92), k=K, legs=0.6 * math.sin(t * 12) if walking else 0)
    else:
        kind = "strain" if abs(swing_angle(t) - 8) < 20 else "focus"
        if T["riparte"] <= t < T["riparte"] + 0.45: kind = "angry"
        miner(d, t, x, kind)
    if T["rotto"] <= t < T["rotto"] + 1.0:                                                   # la testa che vola
        k = t - T["rotto"]; px_ = HIT[0] - 30 + 160 * k; py_ = HIT[1] - 60 - 380 * k + 900 * k * k
        if py_ < GY - 10: pick_head(d, (px_, py_), 400 * k, K)
        mx = HIT[0] - 90 - 120 * k; my = HIT[1] + 30 - 200 * k + 800 * k * k
        if my < GY - 6: d.line([(mx, my), (mx - 70 * math.cos(6 * k), my - 70 * math.sin(6 * k))], fill=(156, 112, 70), width=9)
    if 0 <= t - T_PUGNO < 0.28:
        q = t - T_PUGNO; cxp, cyp = LUCKY_X - 20, GY - 250 * 0.72 - 40; rr = 40 + 200 * q; a_ = 1 - q / 0.28
        pts = [(cxp + (rr if j % 2 == 0 else rr * 0.45) * math.cos(j * math.pi / 8), cyp + (rr if j % 2 == 0 else rr * 0.45) * math.sin(j * math.pi / 8)) for j in range(16)]
        d.polygon(pts, fill=tuple(int(255 * a_) for _ in range(3)))
    last = max([h for h in HITS if h <= t] or [-9]); ph = t - last
    if 0 <= ph < 0.14 and last > 0 and t < T["ultimo"] + 0.3:                               # scintille e schegge
        rng = random.Random(int(last * 100)); big = 1.8 if abs(last - T["ultimo"]) < 0.01 or abs(last - T["rotto"]) < 0.01 else 1.0
        for _ in range(int(12 * big)):
            a_ = rng.uniform(-2.8, -0.3); r = (30 + 170 * ph / 0.14) * big
            d.line([(HIT[0] + math.cos(a_) * r * 0.5, HIT[1] + math.sin(a_) * r * 0.5), (HIT[0] + math.cos(a_) * r, HIT[1] + math.sin(a_) * r)], fill=(255, 230, 170), width=4)
    return img, x

def camera(t):
    """(zoom, cx, cy) in coordinate mondo; il punto (cx, cy) va sullo schermo in (540, 1200)."""
    tl = [(0, 1.16, 500, 1090), (T["acc0"], 1.16, 500, 1090), (T["rotto"] - 0.2, 1.2, 500, 1095),
          (T["rotto"] + 0.15, 1.62, 330, 1170), (T["riparte"] - 0.1, 1.62, 330, 1170), (T["riparte"] + 0.6, 1.16, 500, 1090),
          (T["ultimo"] - 1.2, 1.16, 500, 1090), (T["ultimo"] - 0.1, 1.62, HIT[0], 1150), (T["ultimo"] + 0.5, 1.62, HIT[0], 1150),
          (T["ultimo"] + 1.5, 1.05, 560, 1080), (T_PUGNO - 0.3, 1.25, LUCKY_X - 80, 1120), (T_PUGNO + 0.6, 1.25, LUCKY_X - 80, 1120), (DUR, 1.05, 560, 1080)]
    return tuple(keys(t, [(row[0], row[i + 1]) for row in tl]) for i in range(3))

def to_screen(p, cam):
    z, cx, cy = cam; return ((p[0] - cx) * z + 540, (p[1] - cy) * z + 1200)

def counter(d, t):
    dd = day(t)
    if t >= T["ultimo"] + 1.2: return
    prev = day(t - 1 / 30)
    pop = 1.0
    last_change = None
    for k in range(1, 8):
        if day(t - k / 30) != dd: last_change = (k - 1) / 30; break
    if last_change is not None: pop = 1 + (0.35 if t < T['acc0'] else 0.2) * (1 - min(1, last_change / 0.14))
    col = WHITE
    if T["rotto"] <= t < T["riparte"]: col = RED
    if dd == 365: col = BLUE
    fade = 1 - ease((t - T["ultimo"] - 0.6) / 0.5)
    base = 112; fnt = mc.font(int(base * pop), mc.INTER)
    s = f"DAY {dd}"; tw = mc.text_w(s, fnt)
    d.text(((W - tw) / 2, 318 - (pop - 1) * 40), s, font=fnt, fill=tuple(int(c * fade) for c in col))
    # barra dell'anno
    p = dd / 365; y = 452
    d.rounded_rectangle([190, y, 890, y + 12], radius=6, fill=tuple(int(c * fade) for c in (45, 45, 55)))
    d.rounded_rectangle([190, y, 190 + 700 * p, y + 12], radius=6, fill=tuple(int(c * fade) for c in (BLUE if dd < 365 else (255, 214, 140))))

def frame(t):
    sc, mx = scene(t)
    cam = camera(t); z, cx, cy = cam
    # trasformazione affine: punto schermo -> punto mondo
    img = sc.transform((W, H), Image.AFFINE, (1 / z, 0, cx - 540 / z, 0, 1 / z, cy - 1200 / z), resample=Image.BILINEAR, fillcolor=(18, 18, 22))
    if T["ultimo"] + 0.5 <= t < T["ultimo"] + 0.9 or T["rotto"] <= t < T["rotto"] + 0.25:
        img = Image.fromarray(np.roll(np.asarray(img), int(14 * math.sin(t * 90)), axis=1))
    d = ImageDraw.Draw(img); v = A.V(1, 540, 960)
    for who, s, a0, b0 in C["fumetti"]:
        if a0 <= t < b0:
            al = ease((t - a0) / 0.06) * (1 - ease((t - b0 + 0.06) / 0.06))
            split = ease((t - T["ultimo"] - 0.55) / 0.9)
            if who == "lui": wp = (mx + 20, GY - 430)
            elif who == "a": wp = (BYX[0], top_y(BYX[0]) - 190)
            else: wp = (BYX[1], top_y(BYX[1]) - 190) if split <= 0 else (LUCKY_X, GY - 330)
            P = to_screen(wp, cam)
            mc.bubble(d, min(max(P[0], 170), W - 170), max(P[1], 540), s, size=34, alpha=al)
    counter(d, t)
    A.caption(d, C["testi"], t, DUR, y=150, size=54)
    A.question(d, C["domanda"], t, C["domanda_t"], 350, 56)
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    ev = [(0.0, mc.s_hum(DUR, 0.035))]
    for s, a, b in C["testi"]: ev.append((a, mc.s_pop(0.22, 800)))
    for h in HITS[:-1]: ev += [(h, mc.s_tok(560, 0.05, 0.4)), (h - 0.12, mc.s_whoosh(0.15, 0.08))]
    for dd_t in [k / 30 for k in range(int(DUR * 30))]:
        if day(dd_t) != day(dd_t - 1 / 30) and dd_t > T["acc0"] and int(dd_t * 30) % 2 == 0: ev.append((dd_t, mc.s_click(0.12)))
    ev += [(T["rotto"], mc.s_crack(1.0)), (T["rotto"] + 0.02, mc.s_thud(0.7, 70)), (T["rotto"] + 0.75, mc.s_tok(300, 0.05, 0.4)),
           (T["riparte"], mc.s_rise(1.0, 0.25, 180, 260)),
           (T["ultimo"] - 0.6, mc.s_whoosh(0.6, 0.35)), (T["ultimo"], mc.s_tok(420, 0.08, 1.0)), (T["ultimo"] + 0.02, mc.s_thud(0.9, 45)),
           (T["ultimo"] + 0.5, mc.s_crack(1.0)), (T["ultimo"] + 0.6, mc.s_thud(1.0, 40)), (T["ultimo"] + 0.7, mc.s_rise(2.6, 0.5)),
           (T["ultimo"] + 1.3, mc.s_thud(0.6, 70)), (T_PUGNO, mc.s_thud(1.0, 80)), (T_PUGNO + 0.02, mc.s_crack(0.7)), (T_PUGNO + 0.05, mc.s_whoosh(0.8, 0.35)),
           (C["domanda_t"], mc.s_chime(0.35, 660))]
    for w_, s, a, b in C["fumetti"]: ev.append((a, mc.s_pop(0.2, 650)))
    A.finish(OUT, DUR, frame, ev)
