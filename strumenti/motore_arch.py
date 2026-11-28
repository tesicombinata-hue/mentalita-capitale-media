#!/usr/bin/env python3
"""Motore comune dei Reel in inglese con archetipi (28/11).

Omini piatti su fondo nero (stesso stile di reel_paycheck.py) con rotazione attorno ai piedi
(cadere, stare a terra, rialzarsi), braccia libere, facce, fumetti, scritte in alto, contatore.
Audio e video con motore_mc.
"""
import math, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc

W, H = 1080, 1920
BG = (0, 0, 0)
WHITE = (245, 245, 245); GREY = (105, 105, 112); BLUE = (77, 163, 255); RED = (225, 50, 45)
DIM = (80, 80, 88)

def ease(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)
def lin(x, x0, x1, y0, y1):
    if x <= x0: return y0
    if x >= x1: return y1
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
def keys(t, kf):
    """Interpolazione dolce su una lista di (t, valore)."""
    if t <= kf[0][0]: return kf[0][1]
    for (a, va), (b, vb) in zip(kf, kf[1:]):
        if a <= t < b: return va + (vb - va) * ease((t - a) / (b - a))
    return kf[-1][1]

class V:
    def __init__(self, z=1.0, cx=540, cy=960):
        self.z, self.cx, self.cy = z, cx, cy
    def p(self, x, y): return ((x - self.cx) * self.z + W / 2, (y - self.cy) * self.z + H / 2)
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
    def eye(ex, half=False, closed=False, x_=False):
        if x_:
            d.line([(ex - er * 1.3, ey - er * 1.3), (ex + er * 1.3, ey + er * 1.3)], fill=dark, width=lw)
            d.line([(ex - er * 1.3, ey + er * 1.3), (ex + er * 1.3, ey - er * 1.3)], fill=dark, width=lw)
        elif closed: d.line([(ex - er * 1.4, ey), (ex + er * 1.4, ey)], fill=dark, width=lw)
        elif half:
            d.ellipse([ex - er, ey - er * 0.5, ex + er, ey + er * 1.1], fill=dark)
            d.line([(ex - er * 1.6, ey - er * 0.6), (ex + er * 1.6, ey - er * 0.6)], fill=dark, width=lw)
        else: d.ellipse([ex - er, ey - er * 1.2, ex + er, ey + er * 1.2], fill=dark)
    brow = lambda up: (d.line([(lx - er * 2, ey - er * (3.2 if up else 2.6)), (lx + er * 1.6, ey - er * (1.8 if up else 3.4))], fill=dark, width=lw),
                       d.line([(rx - er * 1.6, ey - er * (1.8 if up else 3.4)), (rx + er * 2, ey - er * (3.2 if up else 2.6))], fill=dark, width=lw))
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
    elif kind == "worried":
        eye(lx); eye(rx); brow(False); d.arc([X - R * 0.28, my - R * 0.05, X + R * 0.28, my + R * 0.35], 200, 340, fill=dark, width=lw)
    elif kind == "angry":
        eye(lx); eye(rx); brow(True); d.line([(X - R * 0.25, my), (X + R * 0.25, my)], fill=dark, width=lw)
    elif kind == "strain":
        eye(lx, closed=True); eye(rx, closed=True); brow(True)
        d.arc([X - R * 0.3, my - R * 0.05, X + R * 0.3, my + R * 0.4], 200, 340, fill=dark, width=lw)
    elif kind == "scared":
        eye(lx); eye(rx); d.ellipse([X - R * 0.14, my - R * 0.12, X + R * 0.14, my + R * 0.22], fill=dark)
    elif kind == "ko":
        eye(lx, x_=True); eye(rx, x_=True); d.ellipse([X - R * 0.12, my - R * 0.05, X + R * 0.12, my + R * 0.18], fill=dark)
    elif kind == "focus":
        eye(lx, half=True); eye(rx, half=True); d.line([(X - R * 0.22, my), (X + R * 0.22, my)], fill=dark, width=lw)

def figure(d, v, x, gy, kind="neutral", col=WHITE, rot=0.0, arms=(0.0, 0.0), legs=0.0, k=1.0, sway=0.0, sit=0.0):
    """Omino con i piedi in (x, gy). rot = gradi di rotazione attorno ai piedi (90 = steso a destra).
    arms = (sinistro, destro) 0 giù .. 1 su; legs = passo (-1..1); sit 0..1 seduto. Ritorna la testa."""
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    def R(px, py):                                  # coordinate locali (0,0) = piedi, y verso l'alto negativo
        return (x + (px * ca - py * sa) * k, gy + (px * sa + py * ca) * k)
    hipy = -150 + 70 * sit
    hip = R(sway * 0.3, hipy); sh = R(sway, hipy - 140); head = R(sway, hipy - 180)
    limb(d, v, sh, hip, 20 * k, col)
    for side, up in ((-1, arms[0]), (1, arms[1])):
        th = math.radians(15 + 140 * up)
        hx = sway + side * 14 + side * math.sin(th) * 130
        hy = hipy - 135 + math.cos(th) * 130
        limb(d, v, R(sway + side * 14, hipy - 135), R(hx, hy), 14 * k, col)
        if sit > 0:
            kn = R(side * 18 + 60 * sit, hipy + 10); limb(d, v, hip, kn, 14 * k, col); limb(d, v, kn, R(side * 18 + 60 * sit, -5), 14 * k, col)
        else:
            limb(d, v, hip, R(side * 24 + side * 22 * legs, -5), 14 * k, col)
    face(d, v, head, 36 * k, kind, col)
    return head

def bubble(d, v, xy, s, a=1.0, size=26):
    if a <= 0: return
    P = v.p(*xy); mc.bubble(d, min(max(P[0], 160), W - 160), P[1], s, size=size, alpha=a)

def caption(d, testi, t, dur, y=240, size=56):
    for s, a, b in testi:
        if not (a <= t < b): continue
        al = (1.0 if a == 0 else ease((t - a) / 0.2)) * ((1 - ease((t - (b - 0.2)) / 0.2)) if b < dur - 0.05 else 1.0)
        fnt = mc.font(size, mc.INTER); yy = y
        for ln in s.split("|"):
            d.text(((W - mc.text_w(ln, fnt)) / 2, yy), ln, font=fnt, fill=tuple(int(c * al) for c in WHITE)); yy += int(size * 1.28)

def question(d, s, t, t0, y, size=50):
    if t < t0: return
    al = ease((t - t0) / 0.3); fnt = mc.font(size, mc.INTER)
    d.text(((W - mc.text_w(s, fnt)) / 2, y), s, font=fnt, fill=tuple(int(c * al) for c in BLUE))

def counter(d, s, a=1.0, y=165):
    fnt = mc.font(34); d.text(((W - mc.text_w(s, fnt)) / 2, y), s, font=fnt, fill=tuple(int(c * a) for c in (150, 150, 160)))

def label(d, v, x, y, s, col):
    fnt = mc.font(28); P = v.p(x, y); d.text((P[0] - mc.text_w(s, fnt) / 2, P[1]), s, font=fnt, fill=col)

def finish(out, dur, frame, ev):
    mc.render(out, dur, frame)
    wav = out.replace(".mp4", "_audio.wav"); tmp = out.replace(".mp4", "_muto.mp4")
    os.rename(out, tmp); mc.mixdown(dur, ev, wav); mc.mux(tmp, wav, out); os.remove(tmp); os.remove(wav)
    print("ok", out)
