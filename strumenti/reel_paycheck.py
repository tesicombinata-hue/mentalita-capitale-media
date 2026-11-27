#!/usr/bin/env python3
"""Reel B in inglese "Same paycheck. 30 days. Who's still standing?" – 27/11.

Quattro omini in piedi su una colonna di monete (lo stipendio) sopra un fiume di coccodrilli.
Ogni giorno la colonna sale o scende a seconda del carattere:
- EGO spende per farsi vedere: la colonna finisce al giorno 8, coccodrillo.
- MOTIVATION risparmia la prima settimana, poi "I deserve it": cade al giorno 15.
- OBSESSION non spende niente: la torre più alta, ma sempre più stanco.
- DISCIPLINE mette da parte per primo (vasetto blu) e vive con il resto: colonna bassa, sorride.
Finale sulla scena (niente schermata nera): "One has the most money. / One still has a life." + "Who really won?".
Tutti i testi nel JSON. Uso: python3 reel_paycheck.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
W, H = 1080, 1920
DUR = C.get("durata", 23.5)
BG = (0, 0, 0)
WHITE = (245, 245, 245); GREY = (105, 105, 112); BLUE = (77, 163, 255)
WATER, WATER_HI = (8, 20, 34), (40, 70, 100)
CROC, CROC_D, CROC_L = (74, 96, 66), (48, 64, 44), (110, 135, 96)
COIN, COIN_E = (205, 205, 210), (125, 125, 135)
WATER_Y = 1400
CH = 9                                     # altezza di una moneta
XS = [180, 388, 596, 800]                   # MOTIVATION, EGO, OBSESSION, DISCIPLINE
NAMES = C["nomi"]
T0, DAYLEN = C.get("t_giorno1", 1.0), C.get("durata_giorno", 0.63)

def ease(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)
def lin(x, x0, x1, y0, y1):
    if x <= x0: return y0
    if x >= x1: return y1
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

def day(t): return min(30.0, 1 + max(0.0, t - T0) / DAYLEN)
def t_of_day(dd): return T0 + (dd - 1) * DAYLEN

def counts(t):
    """Monete di ognuno (colonna) e del vasetto di Discipline."""
    pay = lin(t, 0.2, 0.95, 3, 20)               # giorno di paga: le colonne salgono
    if t < 0.95: return [pay] * 4, 0
    d = day(t)
    mot = lin(d, 1, 5, 20, 26) if d < 7 else lin(d, 7, 15, 26, 0)
    ego = lin(d, 2, 8, 20, 0)
    obs = lin(d, 1, 30, 20, 40)
    jar = lin(t, 1.1, 1.9, 0, 4) + sum(1 for k in (8, 15, 22, 29) if d >= k)
    dis = lin(t, 1.1, 1.9, 20, 16) - lin(d, 1.5, 30, 0, 6) - sum(1 for k in (8, 15, 22, 29) if d >= k) + 4 * 0
    return [mot, ego, obs, max(dis, 0)], jar

FALL = {0: t_of_day(15), 1: t_of_day(8)}       # chi cade e quando

# ---------------- camera fissa con piccola spinta ----------------
class V:
    def __init__(self, t):
        if t < 1.0: self.z = 1.07 + 0.08 * ease(t / 1.0)
        elif t < C["fine0"]: self.z = 1.15
        else: self.z = 1.15 - 0.04 * ease((t - C["fine0"]) / 1.5)
        self.cx, self.cy = 565, 939
    def p(self, x, y): return ((x - self.cx) * self.z + W / 2, (y - self.cy) * self.z + H / 2 - 50)
    def s(self, v): return v * self.z

def limb(d, v, a, b, w, col):
    A, B = v.p(*a), v.p(*b); ww = max(2, v.s(w))
    d.line([A, B], fill=col, width=int(ww))
    for P in (A, B): d.ellipse([P[0] - ww / 2, P[1] - ww / 2, P[0] + ww / 2, P[1] + ww / 2], fill=col)

def face(d, v, c, r, kind, col=WHITE, dark=(0, 0, 0)):
    X, Y = v.p(*c); R = v.s(r)
    d.ellipse([X - R, Y - R, X + R, Y + R], fill=col)
    lw = max(2, int(R * 0.12)); er = R * 0.1; ey = Y - R * 0.12
    lx, rx = X - R * 0.36, X + R * 0.36; my = Y + R * 0.38
    def eye(ex, half=False, closed=False):
        if closed: d.line([(ex - er * 1.4, ey), (ex + er * 1.4, ey)], fill=dark, width=lw)
        elif half:
            d.ellipse([ex - er, ey - er * 0.5, ex + er, ey + er * 1.1], fill=dark)
            d.line([(ex - er * 1.6, ey - er * 0.6), (ex + er * 1.6, ey - er * 0.6)], fill=dark, width=lw)
        else: d.ellipse([ex - er, ey - er * 1.2, ex + er, ey + er * 1.2], fill=dark)
    if kind == "smile":
        eye(lx); eye(rx); d.arc([X - R * 0.4, my - R * 0.35, X + R * 0.4, my + R * 0.15], 20, 160, fill=dark, width=lw)
    elif kind == "big":
        eye(lx); eye(rx); d.chord([X - R * 0.42, my - R * 0.3, X + R * 0.42, my + R * 0.28], 0, 180, fill=dark)
    elif kind == "neutral":
        eye(lx); eye(rx); d.line([(X - R * 0.25, my), (X + R * 0.25, my)], fill=dark, width=lw)
    elif kind == "smug":
        eye(lx, half=True); eye(rx, half=True); d.arc([X - R * 0.1, my - R * 0.3, X + R * 0.45, my + R * 0.1], 20, 150, fill=dark, width=lw)
    elif kind == "tired":
        eye(lx, half=True); eye(rx, half=True); d.arc([X - R * 0.3, my - R * 0.05, X + R * 0.3, my + R * 0.4], 200, 340, fill=dark, width=lw)
    elif kind == "strain":
        eye(lx, closed=True); eye(rx, closed=True)
        d.line([(lx - er * 2, ey - er * 3.2), (lx + er * 1.6, ey - er * 1.8)], fill=dark, width=lw)
        d.line([(rx - er * 1.6, ey - er * 1.8), (rx + er * 2, ey - er * 3.2)], fill=dark, width=lw)
        d.arc([X - R * 0.3, my - R * 0.05, X + R * 0.3, my + R * 0.4], 200, 340, fill=dark, width=lw)
    elif kind == "scared":
        eye(lx); eye(rx); d.ellipse([X - R * 0.14, my - R * 0.12, X + R * 0.14, my + R * 0.22], fill=dark)

def standing(d, v, x, gy, kind, col=WHITE, arms=0.0, sway=0.0):
    """Omino in piedi con i piedi a gy. arms 0..1 = braccia alzate (esulta / lancia)."""
    hip = (x + sway * 0.3, gy - 150); sh = (x + sway, gy - 290); head = (x + sway, gy - 330)
    limb(d, v, sh, hip, 20, col)
    for side in (-1, 1):
        hand = (x + sway + side * (30 + 40 * arms), sh[1] + 130 - 230 * arms)
        limb(d, v, (x + sway + side * 14, sh[1] + 5), hand, 14, col)
        limb(d, v, hip, (x + side * 24, gy - 5), 14, col)
    face(d, v, head, 36, kind, col)
    return head

def coin(d, v, x, y, col=COIN, edge=COIN_E, w=62):
    A = v.p(x - w, y - CH * 0.55); B = v.p(x + w, y + CH * 0.55)
    d.ellipse([A[0], A[1] + v.s(4), B[0], B[1] + v.s(4)], fill=edge)
    d.ellipse([A[0], A[1], B[0], B[1]], fill=col, outline=edge, width=max(1, int(v.s(2))))

def column(d, v, x, n, col=COIN, edge=COIN_E):
    k = int(n)
    for i in range(k): coin(d, v, x, WATER_Y - 6 - i * CH, col, edge)
    return WATER_Y - 6 - k * CH - 4

def croc(d, v, x, t, phase, attack=None):
    bob = 6 * math.sin(t * 1.6 + phase)
    if attack is None or attack <= 0 or attack >= 1:
        y = WATER_Y + 40 + bob * 0.3
        P = lambda dx, dy: v.p(x + dx, y + dy)
        d.polygon([P(-90, 6), P(-45, -10), P(45, -8), P(110, -3), P(118, 6)], fill=CROC)
        for ex in (-30, -2):
            e = P(ex, -15); r = v.s(10)
            d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=CROC_L)
            d.ellipse([e[0] - r * 0.55, e[1] - r * 0.7, e[0] + r * 0.55, e[1] + r * 0.4], fill=(235, 215, 90))
            d.line([(e[0], e[1] - r * 0.6), (e[0], e[1] + r * 0.3)], fill=(0, 0, 0), width=max(1, int(r * 0.3)))
        return
    rise = math.sin(min(1, attack / 0.35) * math.pi / 2) if attack < 0.7 else 1 - ease((attack - 0.7) / 0.3)
    opening = ease(attack / 0.3) * (1 - ease((attack - 0.42) / 0.08))
    top = WATER_Y + 40 - 300 * rise
    P = lambda dx, dy: v.p(x + dx, dy)
    d.polygon([P(-50, WATER_Y + 60), P(-38, top + 60), P(38, top + 60), P(50, WATER_Y + 60)], fill=CROC)
    ang = 0.55 * opening
    for side in (-1, 1):
        L = 140; base = (x + side * 8, top + 70)
        tip = (base[0] + side * math.sin(ang) * L, base[1] - math.cos(ang) * L)
        poly = [base, (base[0] + side * 32, base[1]), (tip[0] + side * 13, tip[1] + 10), tip]
        d.polygon([v.p(*q) for q in poly], fill=CROC if side < 0 else CROC_D)
        for k in range(1, 6):
            q = k / 6; px_ = base[0] + (tip[0] - base[0]) * q; py_ = base[1] + (tip[1] - base[1]) * q
            d.polygon([v.p(px_, py_), v.p(px_ - side * 15 * math.cos(ang), py_ + 4), v.p(px_ - side * 4, py_ - 12)], fill=(240, 240, 230))
    e = v.p(x - 28, top + 105); r = v.s(13)
    d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=(235, 215, 90))

def splash(d, v, x, t, t0):
    k = t - t0
    if k < 0 or k > 1.2: return
    rng = random.Random(int(x))
    for i in range(20):
        a = rng.uniform(-2.6, -0.5); sp = rng.uniform(250, 550)
        px_ = x + math.cos(a) * sp * k; py_ = WATER_Y + 40 + math.sin(a) * sp * k + 900 * k * k
        if py_ > WATER_Y + 45: continue
        P = v.p(px_, py_); r = v.s(rng.uniform(5, 10) * (1 - k * 0.6))
        d.ellipse([P[0] - r, P[1] - r, P[0] + r, P[1] + r], fill=(200, 225, 245))

# monete che volano via quando si spende (Ego, Motivation dal giorno 7)
def spent_coins(i, t):
    out = []
    if i not in (0, 1): return out
    for tt in [k / 30 for k in range(int(t * 30) - 15, int(t * 30) + 1) if k > 30]:
        a = counts(tt)[0][i]; b = counts(tt - 1 / 30)[0][i]
        if int(a) < int(b):
            out.append((tt, int(b)))
    return out

FACES = {
    0: lambda d_, n: "big" if d_ < 7 else ("smug" if n > 6 else "scared"),
    1: lambda d_, n: "smug" if n > 5 else "scared",
    2: lambda d_, n: "neutral" if d_ < 12 else ("tired" if d_ < 22 else "strain"),
    3: lambda d_, n: "smile",
}

def caption(d, t):
    for s, a, b in C["testi"]:
        if not (a <= t < b): continue
        al = (1.0 if a == 0 else ease((t - a) / 0.25)) * ((1 - ease((t - (b - 0.25)) / 0.25)) if b < DUR else 1.0)
        fnt = mc.font(56, mc.INTER); y = 240
        for ln in s.split("|"):
            d.text(((W - mc.text_w(ln, fnt)) / 2, y), ln, font=fnt, fill=tuple(int(c * al) for c in WHITE)); y += 72
    if t >= C["domanda_t"]:                                            # domanda sulla scena finale
        al = ease((t - C["domanda_t"]) / 0.35); fnt = mc.font(50, mc.INTER)
        s = C["domanda"]; d.text(((W - mc.text_w(s, fnt)) / 2, 420), s, font=fnt, fill=tuple(int(c * al) for c in BLUE))
    if T0 <= t:                                                        # contatore dei giorni
        dd = int(day(t)); s = f"DAY {dd}/30"; fnt = mc.font(34)
        al = ease((t - T0) / 0.3) * (1 - 0.6 * ease((t - C["fine0"]) / 0.4))
        d.text(((W - mc.text_w(s, fnt)) / 2, 165), s, font=fnt, fill=tuple(int(c * al) for c in (150, 150, 160)))

def frame(t):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); v = V(t)
    cs, jar = counts(t); dd = day(t)
    # acqua
    A = v.p(-200, WATER_Y + 30); d.rectangle([0, A[1], W, H], fill=WATER)
    d.line([(0, A[1]), (W, A[1])], fill=WATER_HI, width=3)
    for i, x in enumerate(XS):
        gy = column(d, v, x, cs[i])
        fall = FALL.get(i)
        if i == 3:                                                     # vasetto blu accanto a Discipline
            jx = x + 105; jy = WATER_Y - 6
            for k in range(int(jar)): coin(d, v, jx, jy - k * CH, (120, 185, 255), (50, 110, 200), w=36)
        if fall is not None and t >= fall:
            k = t - fall
            if k < 0.5:
                gy2 = gy + 900 * k * k
                standing(d, v, x, gy2, "scared", WHITE, arms=1.0)
            splash(d, v, x, t, fall + 0.35)
            continue
        kind = FACES[i](dd, cs[i])
        arms = 0.0; sway = 0.0
        if t < 1.0: arms = 0.6 * math.sin(min(1, t / 1.0) * math.pi)          # giorno di paga: esultano
        if i == 2 and dd > 22: sway = 6 * math.sin(t * 9)                      # Obsession trema
        col = BLUE if i == 3 else WHITE
        if t >= C["fine0"] and i == 3: arms = 0.35 * ease((t - C["fine0"]) / 0.5)
        standing(d, v, x, gy, kind, col, arms, sway)
    # monete che volano via
    for i in (0, 1):
        for tt, n in spent_coins(i, t):
            k = (t - tt) / 0.5
            if 0 <= k <= 1:
                x0 = XS[i]; y0 = WATER_Y - 6 - n * CH
                side = -1 if i == 0 else 1
                coin(d, v, x0 + side * 260 * k, y0 - 160 * math.sin(k * math.pi) + 120 * k)
    # coccodrilli
    for j, x in enumerate([60, 280, 510, 740, 980]):
        croc(d, v, x, t, j * 1.3)
    for i, ft in FALL.items():
        a = (t - ft - 0.15) / 1.1
        if 0 < a < 1: croc(d, v, XS[i], t, 0, a)
    # etichette
    fnt = mc.font(28)
    for i, x in enumerate(XS):
        gone = FALL.get(i) is not None and t >= FALL[i] + 0.4
        col = (80, 80, 88) if gone else (BLUE if i == 3 else (215, 215, 220))
        P = v.p(x, WATER_Y + 110); d.text((P[0] - mc.text_w(NAMES[i], fnt) / 2, P[1]), NAMES[i], font=fnt, fill=col)
    # fumetti (indice, testo, da, a)
    for i, s, a, b in C["fumetti"]:
        if a <= t < b and not (FALL.get(i) is not None and t >= FALL[i]):
            gy = WATER_Y - 6 - int(cs[i]) * CH - 4
            P = v.p(XS[i], gy - 425)
            al = ease((t - a) / 0.08) * (1 - ease((t - b + 0.08) / 0.08))
            mc.bubble(d, min(max(P[0], 150), W - 150), P[1], s, size=26, alpha=al)
    caption(d, t)
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    mc.render(OUT, DUR, frame)
    ev = [(0.0, mc.s_hum(DUR, 0.03)), (0.25, mc.s_chime(0.35, 880))]
    for k in range(8): ev.append((0.25 + k * 0.09, mc.s_click(0.25)))            # monete del giorno di paga
    for s, a, b in C["testi"]: ev.append((a, mc.s_pop(0.25, 800)))
    for dd in range(2, 31): ev.append((t_of_day(dd), mc.s_tok(420, 0.04, 0.12)))  # orologio dei giorni
    for i in (0, 1):
        last = 0
        for k in range(int(DUR * 30)):
            tt = k / 30
            if int(counts(tt)[0][i]) < int(counts(tt - 1 / 30)[0][i]) and tt > 1.0 and tt - last > 0.12:
                ev.append((tt, mc.s_click(0.35))); last = tt
    for i, ft in FALL.items():
        ev += [(ft, mc.s_whoosh(0.5, 0.45, False)), (ft + 0.35, mc.s_thud(0.9, 60)), (ft + 0.5, mc.s_crack(0.6)), (ft + 0.65, mc.s_crack(1.0))]
    for i, s, a, b in C["fumetti"]: ev.append((a, mc.s_pop(0.2, 650)))
    ev += [(C["fine0"], mc.s_rise(2.4, 0.4)), (C["domanda_t"], mc.s_chime(0.35, 660))]
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mc.mixdown(DUR, ev, wav); mc.mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
