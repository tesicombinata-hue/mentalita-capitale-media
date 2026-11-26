#!/usr/bin/env python3
"""Reel B "Chi resiste più a lungo?" (la sbarra sul fossato dei coccodrilli) – Mentalità Capitale, 26/11.

Struttura e movimenti ripresi dal reel di @stikmindset (20/11) su richiesta del titolare, testi in italiano riscritti,
più il fossato con i coccodrilli sotto la sbarra. Quattro omini appesi: MOTIVAZIONE, DISCIPLINA, EGO, OSSESSIONE.
- Motivazione fa trazioni piena di energia, si spegne, molla e cade: il coccodrillo lo prende.
- Disciplina fa una trazione, poi si sposta mano dopo mano fino alla fine della sbarra e scende sulla riva.
- Ego resiste solo finché qualcuno guarda: si accorge che nessuno lo guarda, molla, coccodrillo.
- Ossessione resta appeso con il braccio che diventa rosso; i coccodrilli sotto.
Uso: python3 reel_sbarra.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
W, H = 1080, 1920
DUR = C.get("durata", 58.0)
BG = (0, 0, 0)
WHITE = (245, 245, 245)
GREY = (110, 110, 115)
BLUE = (77, 163, 255)
RED = (225, 50, 45)
WATER, WATER_HI = (8, 20, 34), (40, 70, 100)
CROC, CROC_D, CROC_L = (74, 96, 66), (48, 64, 44), (110, 135, 96)

BAR_Y = 700
BAR_X0, BAR_X1 = 50, 1030
GROUND = 1250
MOAT_X0, MOAT_X1 = 150, 990            # il fossato tra le due rive
WATER_Y = 1310
XS = [250, 450, 650, 850]              # motivazione, disciplina, ego, ossessione
NAMES = C["nomi"]

# ---------------- tempi ----------------
T = C["tempi"]

def ease(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)
def seg(t, a, b):
    if b <= a: return 1.0 if t >= b else 0.0
    return max(0.0, min(1.0, (t - a) / (b - a)))
def lerp(a, b, k): return a + (b - a) * k

# ---------------- camera 2D ----------------
CAM_KEYS = [  # (t, cx, cy, zoom)
    (0.0, 540, 1010, 1.0), (T["zoom0"], 540, 1010, 1.0),
    (T["zoom0"] + 0.9, XS[0] + 20, 930, 1.9), (T["pan1"], XS[3] - 20, 930, 1.9),
    (T["mot0"], 360, 960, 1.75), (T["mot_fall"], 360, 960, 1.75), (T["mot_fall"] + 0.6, 330, 1080, 1.55),
    (T["dis0"], 400, 980, 1.75), (T["dis_move"], 400, 980, 1.75), (T["dis_drop"] - 0.8, 250, 1000, 1.6), (T["dis_drop"] + 1.2, 290, 1020, 1.5),
    (T["ego0"], 560, 990, 1.65), (T["ego_fall"], 560, 990, 1.65), (T["ego_fall"] + 0.6, 600, 1090, 1.5),
    (T["oss0"], 800, 960, 1.9), (T["oss_close"], 800, 930, 2.3), (T["fin0"] - 0.6, 800, 930, 2.3),
    (T["fin0"], 540, 1010, 1.0), (DUR, 540, 1010, 0.97),
]

def camera(t):
    for a, b in zip(CAM_KEYS, CAM_KEYS[1:]):
        if a[0] <= t < b[0]:
            k = ease((t - a[0]) / (b[0] - a[0])) if b[0] > a[0] else 1
            return tuple(lerp(p, q, k) for p, q in zip(a[1:], b[1:]))
    return CAM_KEYS[-1][1:]

class V:
    def __init__(self, cam):
        self.cx, self.cy, self.z = cam
    def p(self, x, y):
        return ((x - self.cx) * self.z + W / 2, (y - self.cy) * self.z + H / 2 + 120)
    def s(self, v): return v * self.z

# ---------------- omino piatto ----------------
def limb(d, v, a, b, w, col):
    A, B = v.p(*a), v.p(*b); ww = max(2, v.s(w))
    d.line([A, B], fill=col, width=int(ww))
    for P in (A, B): d.ellipse([P[0] - ww / 2, P[1] - ww / 2, P[0] + ww / 2, P[1] + ww / 2], fill=col)

def face(d, v, c, r, kind, col=WHITE, dark=(0, 0, 0)):
    X, Y = v.p(*c); R = v.s(r)
    d.ellipse([X - R, Y - R, X + R, Y + R], fill=col)
    lw = max(2, int(R * 0.12)); er = R * 0.1
    ey = Y - R * 0.12
    def eye(ex, closed=False, half=False):
        if closed: d.line([(ex - er * 1.4, ey), (ex + er * 1.4, ey)], fill=dark, width=lw)
        elif half:
            d.ellipse([ex - er, ey - er * 0.5, ex + er, ey + er * 1.1], fill=dark); d.line([(ex - er * 1.6, ey - er * 0.6), (ex + er * 1.6, ey - er * 0.6)], fill=dark, width=lw)
        else: d.ellipse([ex - er, ey - er * 1.2, ex + er, ey + er * 1.2], fill=dark)
    lx, rx = X - R * 0.36, X + R * 0.36
    my = Y + R * 0.38
    if kind == "smile":
        eye(lx); eye(rx); d.arc([X - R * 0.4, my - R * 0.35, X + R * 0.4, my + R * 0.15], 20, 160, fill=dark, width=lw)
    elif kind == "big":
        eye(lx); eye(rx); d.chord([X - R * 0.42, my - R * 0.3, X + R * 0.42, my + R * 0.28], 0, 180, fill=dark)
    elif kind == "neutral":
        eye(lx); eye(rx); d.line([(X - R * 0.25, my), (X + R * 0.25, my)], fill=dark, width=lw)
    elif kind == "tired":
        eye(lx, half=True); eye(rx, half=True); d.arc([X - R * 0.3, my - R * 0.05, X + R * 0.3, my + R * 0.4], 200, 340, fill=dark, width=lw)
    elif kind == "smug":
        eye(lx, half=True); eye(rx, half=True)
        d.arc([X - R * 0.1, my - R * 0.3, X + R * 0.45, my + R * 0.1], 20, 150, fill=dark, width=lw)
    elif kind == "worried":
        eye(lx); eye(rx)
        d.line([(lx - er * 2, ey - er * 2.6), (lx + er * 1.5, ey - er * 3.4)], fill=dark, width=lw)
        d.line([(rx - er * 1.5, ey - er * 3.4), (rx + er * 2, ey - er * 2.6)], fill=dark, width=lw)
        d.arc([X - R * 0.28, my - R * 0.05, X + R * 0.28, my + R * 0.35], 200, 340, fill=dark, width=lw)
    elif kind == "angry":
        eye(lx); eye(rx)
        d.line([(lx - er * 2, ey - er * 3.2), (lx + er * 1.6, ey - er * 1.8)], fill=dark, width=lw)
        d.line([(rx - er * 1.6, ey - er * 1.8), (rx + er * 2, ey - er * 3.2)], fill=dark, width=lw)
        d.line([(X - R * 0.25, my), (X + R * 0.25, my)], fill=dark, width=lw)
    elif kind == "strain":
        eye(lx, closed=True); eye(rx, closed=True)
        d.line([(lx - er * 2, ey - er * 3.2), (lx + er * 1.6, ey - er * 1.8)], fill=dark, width=lw)
        d.line([(rx - er * 1.6, ey - er * 1.8), (rx + er * 2, ey - er * 3.2)], fill=dark, width=lw)
        d.rectangle([X - R * 0.32, my - R * 0.1, X + R * 0.32, my + R * 0.16], fill=dark)
        for k in range(4): d.line([(X - R * 0.32 + k * R * 0.21, my - R * 0.1), (X - R * 0.32 + k * R * 0.21, my + R * 0.16)], fill=col, width=max(1, lw // 2))
    elif kind == "scared":
        eye(lx); eye(rx); d.ellipse([X - R * 0.14, my - R * 0.12, X + R * 0.14, my + R * 0.22], fill=dark)

def hanging(d, v, hx, face_kind, pull=0.0, sway=0.0, col=WHITE, red=0.0, legs_up=0.0, hands=None, dy=0.0, arms_up=False):
    """Omino appeso alla sbarra. hands: (xl, xr) delle mani (default ±30 da hx)."""
    xl, xr = hands if hands else (hx - 46, hx + 46)
    by = BAR_Y + dy
    up = 90 * pull
    sh_y = by + 105 - up
    bx = hx + sway
    head = (bx, by + 62 - up)
    hip = (bx, by + 245 - up)
    # braccia (con gomito che si piega nella trazione)
    for hxx, side in ((xl, -1), (xr, 1)):
        sh = (bx + side * 22, sh_y)
        if arms_up:
            el = ((hxx + sh[0]) / 2 + side * 6, (by + sh_y) / 2)
        else:
            el = ((hxx + sh[0]) / 2 + side * 38 * pull, (by + sh_y) / 2 + 10 * pull)
        c = col
        if side == 1 and red > 0:
            c = tuple(int(col[i] + (RED[i] - col[i]) * red) for i in range(3))
        limb(d, v, (hxx, by), el, 15, c); limb(d, v, el, sh, 15, c)
    limb(d, v, (bx, sh_y), hip, 22, col)
    for side in (-1, 1):
        kx = bx + side * (8 + 18 * legs_up); ky = hip[1] + 70 - 45 * legs_up
        fx = bx + side * (10 + 10 * legs_up); fy = hip[1] + 145 - 105 * legs_up
        limb(d, v, hip, (kx, ky), 15, col); limb(d, v, (kx, ky), (fx, fy), 15, col)
    face(d, v, head, 36, face_kind, col)
    return head

def standing(d, v, x, gy, face_kind, col=WHITE):
    hip = (x, gy - 170); sh = (x, gy - 330); head = (x, gy - 375)
    limb(d, v, sh, hip, 22, col)
    for side in (-1, 1):
        limb(d, v, (x + side * 16, sh[1] + 5), (x + side * 34, sh[1] + 150), 15, col)
        limb(d, v, hip, (x + side * 26, gy - 6), 15, col)
    face(d, v, head, 40, face_kind, col)
    return head

# ---------------- coccodrilli ----------------
def croc(d, v, x, t, phase, attack=None, facing=1):
    """Coccodrillo nel fossato. attack = k 0..1 dell'assalto (sale, apre, chiude, torna giù)."""
    bob = 6 * math.sin(t * 1.6 + phase)
    if attack is None or attack <= 0 or attack >= 1:
        # solo occhi e muso sopra l'acqua
        y = WATER_Y + bob * 0.3
        P = lambda dx, dy: v.p(x + dx * facing, y + dy)
        d.polygon([P(-120, 6), P(-60, -12), P(60, -10), P(150, -4), P(160, 6)], fill=CROC)
        for ex in (-40, -5):
            e = P(ex, -18); r = v.s(13)
            d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=CROC_L)
            d.ellipse([e[0] - r * 0.55, e[1] - r * 0.7, e[0] + r * 0.55, e[1] + r * 0.4], fill=(235, 215, 90))
            d.line([(e[0], e[1] - r * 0.6), (e[0], e[1] + r * 0.3)], fill=(0, 0, 0), width=max(1, int(r * 0.3)))
        return None
    # assalto: il muso esce verticale dall'acqua, le fauci si aprono e si chiudono
    rise = math.sin(min(1, attack / 0.35) * math.pi / 2) if attack < 0.7 else 1 - ease((attack - 0.7) / 0.3)
    opening = ease(attack / 0.3) * (1 - ease((attack - 0.42) / 0.08))
    top = WATER_Y - 330 * rise
    P = lambda dx, dy: v.p(x + dx, dy)
    d.polygon([P(-55, WATER_Y + 10), P(-42, top + 60), P(42, top + 60), P(55, WATER_Y + 10)], fill=CROC)        # collo
    ang = 0.55 * opening
    for side in (-1, 1):                                                                                       # mascelle
        L = 150
        base = (x + side * 8, top + 70)
        tip = (base[0] + side * math.sin(ang) * L, base[1] - math.cos(ang) * L)
        w_ = 34
        nx, ny = math.cos(ang) * side, math.sin(ang)
        poly = [base, (base[0] + side * w_, base[1]), (tip[0] + side * w_ * 0.4, tip[1] + 10), tip]
        d.polygon([v.p(*q) for q in poly], fill=CROC if side < 0 else CROC_D)
        for k in range(1, 6):                                                                                  # denti
            q = k / 6
            px_ = base[0] + (tip[0] - base[0]) * q; py_ = base[1] + (tip[1] - base[1]) * q
            a_ = v.p(px_, py_); b_ = v.p(px_ - side * 16 * math.cos(ang), py_ + 4); c_ = v.p(px_ - side * 4, py_ - 12)
            d.polygon([a_, b_, c_], fill=(240, 240, 230))
    e = v.p(x - 30, top + 110); r = v.s(14)
    d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=(235, 215, 90))
    return (x, top + 60)

def splash(d, v, x, t, t0):
    k = t - t0
    if k < 0 or k > 1.2: return
    rng = random.Random(int(x))
    for i in range(22):
        a = rng.uniform(-2.6, -0.5); sp = rng.uniform(250, 600)
        px_ = x + math.cos(a) * sp * k; py_ = WATER_Y + math.sin(a) * sp * k + 900 * k * k
        if py_ > WATER_Y + 5: continue
        P = v.p(px_, py_); r = v.s(rng.uniform(5, 11) * (1 - k * 0.6))
        d.ellipse([P[0] - r, P[1] - r, P[0] + r, P[1] + r], fill=(200, 225, 245))
    for j in range(3):                                                                   # cerchi nell'acqua
        rr = 40 + 260 * k + j * 50
        A = v.p(x - rr, WATER_Y - rr * 0.08); B = v.p(x + rr, WATER_Y + rr * 0.08)
        d.ellipse([A[0], A[1], B[0], B[1]], outline=WATER_HI, width=max(1, int(v.s(3))))

# ---------------- scena ----------------
def scene(t):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    v = V(camera(t))
    # rive, fossato, pali, sbarra
    d.polygon([v.p(-2000, GROUND), v.p(MOAT_X0, GROUND), v.p(MOAT_X0 + 20, WATER_Y + 600), v.p(-2000, WATER_Y + 600)], fill=(22, 22, 25))
    d.polygon([v.p(MOAT_X1, GROUND), v.p(3000, GROUND), v.p(3000, WATER_Y + 600), v.p(MOAT_X1 - 20, WATER_Y + 600)], fill=(22, 22, 25))
    d.line([v.p(-2000, GROUND), v.p(MOAT_X0, GROUND)], fill=WHITE, width=max(2, int(v.s(5))))
    d.line([v.p(MOAT_X1, GROUND), v.p(3000, GROUND)], fill=WHITE, width=max(2, int(v.s(5))))
    d.polygon([v.p(MOAT_X0 + 2, WATER_Y), v.p(MOAT_X1 - 2, WATER_Y), v.p(MOAT_X1 - 20, WATER_Y + 600), v.p(MOAT_X0 + 20, WATER_Y + 600)], fill=WATER)
    for i in range(7):                                                                   # riflessi sull'acqua
        xx = MOAT_X0 + 60 + ((i * 113 + t * 18) % (MOAT_X1 - MOAT_X0 - 120))
        d.line([v.p(xx, WATER_Y + 18 + i % 3 * 22), v.p(xx + 50, WATER_Y + 18 + i % 3 * 22)], fill=(25, 45, 65), width=max(1, int(v.s(3))))
    d.line([v.p(MOAT_X0, WATER_Y), v.p(MOAT_X1, WATER_Y)], fill=WATER_HI, width=max(1, int(v.s(3))))
    for px_ in (BAR_X0, BAR_X1):
        d.line([v.p(px_, BAR_Y - 10), v.p(px_, GROUND)], fill=WHITE, width=max(2, int(v.s(9))))
    d.line([v.p(BAR_X0 - 10, BAR_Y), v.p(BAR_X1 + 10, BAR_Y)], fill=WHITE, width=max(2, int(v.s(9))))
    # coccodrilli che aspettano
    crocs = [(330, 0.0, 1), (560, 2.0, -1), (760, 4.0, 1), (880, 1.0, -1)]
    attacks = {0: (T["mot_fall"] + 0.45, XS[0]), 2: (T["ego_fall"] + 0.45, XS[2])}
    croc_x = {0: XS[0], 2: XS[2]}
    snap_oss = (T["oss_snap"], XS[3])
    for i, (cx_, ph, f) in enumerate(crocs):
        att = None; x_draw = cx_
        if i == 0:
            a0 = attacks[0][0]; att = (t - (a0 - 0.25)) / 1.3; x_draw = lerp(cx_, XS[0], ease((t - (a0 - 1.5)) / 1.2))
            if t > a0 + 1.1: x_draw = XS[0]
        if i == 1:
            a0 = attacks[2][0]; att = (t - (a0 - 0.25)) / 1.3; x_draw = lerp(cx_, XS[2], ease((t - (a0 - 1.5)) / 1.2))
            if t > a0 + 1.1: x_draw = XS[2]
        if i == 3:
            a0 = snap_oss[0]; att = (t - a0) / 1.6
            x_draw = lerp(cx_, XS[3], ease((t - (a0 - 1.5)) / 1.2)) if t < a0 + 2 else lerp(XS[3], cx_, ease((t - a0 - 2) / 2))
        croc(d, v, x_draw, t, ph, att, f)
    # gli omini
    heads = {}
    # MOTIVAZIONE
    mf = T["mot_fall"]
    if t < mf:
        pull = 0.0; fk = "smile"
        if T["mot_pull0"] <= t < T["mot_pull1"]:
            ph = (t - T["mot_pull0"]) / (T["mot_pull1"] - T["mot_pull0"]) * 3
            pull = ease(1 - abs((ph % 1) * 2 - 1)); fk = "big"
        elif t >= T["mot_pull1"]:
            fk = "tired"
        sway = 4 * math.sin(t * 2) if t < T["mot_pull1"] else 6 * math.sin(t * 7) * seg(t, mf - 1.2, mf)
        heads[0] = hanging(d, v, XS[0], fk, pull, sway)
    else:
        k = t - mf; dy = 1200 * k * k
        if T["mot_fall"] + 0.45 + 0.35 > t:
            hanging(d, v, XS[0], "scared", 0, 0, dy=dy, legs_up=0.3, arms_up=True, hands=(XS[0] - 46, XS[0] + 46))
    # DISCIPLINA
    dm, dd_ = T["dis_move"], T["dis_drop"]
    if t < dm:
        pull = 0.0
        if T["dis_pull0"] <= t < T["dis_pull1"]:
            pull = ease(1 - abs(((t - T["dis_pull0"]) / (T["dis_pull1"] - T["dis_pull0"])) * 2 - 1))
        heads[1] = hanging(d, v, XS[1], "neutral", pull, 2 * math.sin(t * 2))
    elif t < dd_:
        k = (t - dm) / (dd_ - dm); x = lerp(XS[1], BAR_X0 + 60, k)
        stp = math.sin(k * math.pi * 7)
        heads[1] = hanging(d, v, x, "neutral", 0.1, 5 * stp, hands=(x - 46 + 22 * stp, x + 46 + 22 * stp))
    else:
        k = seg(t, dd_, dd_ + 0.45)
        x = BAR_X0 + 60
        if k < 1:
            hanging(d, v, x, "neutral", 0, 0, dy=(GROUND - (BAR_Y + 395)) * k * k, arms_up=True, hands=(x - 46, x + 46))
        else:
            heads[1] = standing(d, v, x, GROUND, "smile" if t > dd_ + 1.2 else "neutral")
    # EGO
    ef = T["ego_fall"]
    if t < ef:
        fk = "smug"
        if T["ego_look"] <= t < ef: fk = "worried"
        sway = 2 * math.sin(t * 2)
        hh = hanging(d, v, XS[2], fk, 0.15 if t < T["ego_look"] else 0, sway)
        heads[2] = hh
    else:
        k = t - ef; dy = 1200 * k * k
        if ef + 0.8 > t:
            hanging(d, v, XS[2], "scared", 0, 0, dy=dy, legs_up=0.3, arms_up=True, hands=(XS[2] - 46, XS[2] + 46))
    # OSSESSIONE
    red = ease(seg(t, T["oss0"] + 1.5, T["oss_close"] + 3.0))
    legs = ease(seg(t, T["oss_snap"] - 0.2, T["oss_snap"] + 0.2)) * (1 - ease(seg(t, T["oss_snap"] + 1.2, T["oss_snap"] + 1.8)))
    shake = 3 * math.sin(t * 40) * red
    heads[3] = hanging(d, v, XS[3], "angry" if red < 0.5 else "strain", 0, shake, red=red, legs_up=legs)
    if T["oss0"] + 2.5 <= t < T["fin0"] + 6:                                               # freccia verso il braccio
        a = ease(seg(t, T["oss0"] + 2.5, T["oss0"] + 2.9))
        tip = v.p(XS[3] + 70, BAR_Y + 60); tail = v.p(XS[3] + 160, BAR_Y + 120)
        tip2 = (tail[0] + (tip[0] - tail[0]) * a, tail[1] + (tip[1] - tail[1]) * a)
        d.line([tail, tip2], fill=WHITE, width=max(2, int(v.s(5))))
        if a > 0.9:
            ang = math.atan2(tip[1] - tail[1], tip[0] - tail[0]); L = v.s(22)
            for s in (-0.5, 0.5):
                d.line([tip, (tip[0] - L * math.cos(ang + s), tip[1] - L * math.sin(ang + s))], fill=WHITE, width=max(2, int(v.s(5))))
    # l'acqua copre chi è caduto dentro
    d.polygon([v.p(MOAT_X0 + 2, WATER_Y + 4), v.p(MOAT_X1 - 2, WATER_Y + 4), v.p(MOAT_X1 - 20, WATER_Y + 600), v.p(MOAT_X0 + 20, WATER_Y + 600)], fill=WATER)
    d.line([v.p(MOAT_X0, WATER_Y + 3), v.p(MOAT_X1, WATER_Y + 3)], fill=WATER_HI, width=max(1, int(v.s(3))))
    # schizzi
    splash(d, v, XS[0], t, mf + 0.42)
    splash(d, v, XS[2], t, ef + 0.42)
    # etichette sotto la riva
    gone = {0: mf + 0.5, 1: 1e9, 2: ef + 0.5, 3: 1e9}
    for i, n in enumerate(NAMES):
        lx = XS[i] if i != 1 or t < dd_ else BAR_X0 + 60
        P = v.p(lx, GROUND + 70 if i == 1 and t >= dd_ else WATER_Y + 90)
        fnt = mc.font(max(9, int(v.s(23))), mc.INTER)
        col = GREY if t > gone[i] else WHITE
        if i == 1 and t >= dd_: col = BLUE
        d.text((P[0] - mc.text_w(n, fnt) / 2, P[1]), n, font=fnt, fill=col)
    return img

def caption(d, t):
    """Testi in alto, come nel reel di riferimento: bianco grassetto centrato."""
    for s, a, b, *rest in C["testi"]:
        if not (a <= t < b): continue
        al = ease((t - a) / 0.25) * (1 - ease((t - (b - 0.25)) / 0.25))
        lines = s.split("|")
        fnt = mc.font(56, mc.INTER)
        hi = rest[0] if rest else None
        y = 250
        for ln in lines:
            if hi is not None:                                     # parole che si accendono una alla volta
                words = ln.split("·"); x = (W - sum(mc.text_w(w_, fnt) for w_ in words) - 20 * (len(words) - 1)) / 2
                for w_ in words:
                    idx = C["parole"].index(w_.strip()) if w_.strip() in C["parole"] else -1
                    on = idx >= 0 and t >= hi[idx]
                    c = WHITE if on else (95, 95, 100)
                    d.text((x, y), w_, font=fnt, fill=tuple(int(cc * al) for cc in c)); x += mc.text_w(w_, fnt) + 20
            else:
                c = tuple(int(cc * al) for cc in WHITE)
                d.text(((W - mc.text_w(ln, fnt)) / 2, y), ln, font=fnt, fill=c)
            y += 72

def frame(t):
    if t >= T["end0"]:                                                             # schermata finale
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        al = ease((t - T["end0"]) / 0.4)
        fnt = mc.font(78, mc.INTER)
        for n, s in enumerate(C["domanda"]):
            d.text(((W - mc.text_w(s, fnt)) / 2, 760 + n * 96), s, font=fnt, fill=tuple(int(c * al) for c in WHITE))
        d.line([(W / 2 - 40, 990), (W / 2 + 40, 990)], fill=tuple(int(c * al) for c in GREY), width=3)
        f2 = mc.font(36, mc.INTER)
        for n, s in enumerate(NAMES):
            a2 = ease((t - T["end0"] - 0.4 - n * 0.25) / 0.3)
            d.text(((W - mc.text_w(s, f2)) / 2, 1030 + n * 58), s, font=f2, fill=tuple(int(c * a2) for c in (BLUE if n == 1 else (200, 200, 205))))
        f3 = mc.font(34)
        for n, s in enumerate(C["invito"]):
            a3 = ease((t - T["end0"] - 1.6) / 0.4)
            d.text(((W - mc.text_w(s, f3)) / 2, 1330 + n * 46), s, font=f3, fill=tuple(int(c * a3) for c in (215, 215, 215)))
        mc.watermark(d)
        return img
    img = scene(t); d = ImageDraw.Draw(img)
    caption(d, t)
    mc.watermark(d)
    if T["fin0"] - 0.6 <= t < T["fin0"]:
        img = Image.blend(img, Image.new("RGB", (W, H), BG), ease((t - (T["fin0"] - 0.6)) / 0.6) * 0.0)
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    mc.render(OUT, DUR, frame)
    ev = [(0.0, mc.s_hum(DUR, 0.03))]
    for s, a, b, *rest in C["testi"]: ev.append((a, mc.s_pop(0.25, 800)))
    for w_t in C["tempi_parole"]: ev.append((w_t, mc.s_click(0.3)))
    # trazioni
    for k in range(3): ev.append((T["mot_pull0"] + (k + 0.5) * (T["mot_pull1"] - T["mot_pull0"]) / 3, mc.s_whoosh(0.3, 0.2)))
    ev.append(((T["dis_pull0"] + T["dis_pull1"]) / 2, mc.s_whoosh(0.4, 0.15)))
    for fall in (T["mot_fall"], T["ego_fall"]):
        ev += [(fall, mc.s_whoosh(0.5, 0.45, False)), (fall + 0.42, mc.s_thud(0.9, 60)), (fall + 0.45, mc.s_crack(0.5)),
               (fall + 0.62, mc.s_crack(1.0)), (fall + 0.7, mc.s_thud(0.6, 45))]
    k = T["dis_move"]
    while k < T["dis_drop"]: ev.append((k, mc.s_tok(300, 0.05, 0.25))); k += (T["dis_drop"] - T["dis_move"]) / 7
    ev += [(T["dis_drop"] + 0.45, mc.s_thud(0.5, 110))]
    ev += [(T["oss_snap"] + 0.4, mc.s_crack(0.9)), (T["oss_snap"] + 0.3, mc.s_whoosh(0.5, 0.3))]
    for k in range(12): ev.append((T["oss_close"] + k * 0.55, mc.s_thud(0.25 + 0.02 * k, 55)))   # battito
    ev += [(T["fin0"], mc.s_rise(2.6, 0.4)), (T["end0"], mc.s_chime(0.4))]
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mc.mixdown(DUR, ev, wav); mc.mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
