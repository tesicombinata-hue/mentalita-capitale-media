#!/usr/bin/env python3
"""Reel B "La salita" (mentalità, tandem) – Mentalità Capitale, 25/11.

Una salita. Tutti la fanno in bici da soli e a un terzo scendono e tornano indietro ("NON NE VALE LA PENA").
Due amici in tandem salgono piano; quello davanti si spegne e smette di pedalare, quello dietro pedala per due
("CI SONO IO"). Arrivano in cima e la discesa li lancia verso la città che si accende.
Risposta: "IN SALITA SCOPRI / CHI PEDALA CON TE."
Uso: python3 reel_salita.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 9.0)
PATH = [(-150, 1500), (640, 930), (1250, 1400)]       # salita, cima, discesa
KR = 1.55                                             # scala degli omini
WR = 34                                               # raggio delle ruote
T_TIRED0 = 2.6                                        # quello davanti si spegne
T_SUMMIT = 5.35
T_ANS = 5.9
T_END = 6.9
random.seed(11)
STARS = [(random.randint(0, W), random.randint(560, 1100), random.random()) for _ in range(80)]
CITY = []
x = 700
while x < W + 40:
    w = random.randint(60, 110); h = random.randint(320, 600)
    base = 1400 - (x - 640) * (470 / 610) + 60
    wins = [(x + 8 + i * 20, base - h + 12 + j * 26) for i in range((w - 12) // 20) for j in range((h - 26) // 26)]
    CITY.append((x, w, h, base, [(a, b, random.random()) for a, b in wins])); x += w + 5

SEGL = [math.dist(PATH[0], PATH[1]), math.dist(PATH[1], PATH[2])]

def point(s):
    """Punto e angolo sul percorso alla distanza s."""
    if s < SEGL[0]:
        a, b, k = PATH[0], PATH[1], s / SEGL[0]
    else:
        a, b, k = PATH[1], PATH[2], min(1.2, (s - SEGL[0]) / SEGL[1])
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k), math.atan2(b[1] - a[1], b[0] - a[0])

def ground_y(x):
    if x < PATH[1][0]: return PATH[0][1] + (x - PATH[0][0]) * (PATH[1][1] - PATH[0][1]) / (PATH[1][0] - PATH[0][0])
    return PATH[1][1] + (x - PATH[1][0]) * (PATH[2][1] - PATH[1][1]) / (PATH[2][0] - PATH[1][0])

def tandem_s(t):
    s_top = SEGL[0]
    if t < T_TIRED0: return 430 + 105 * t
    if t < T_SUMMIT: return 430 + 105 * T_TIRED0 + (s_top - 430 - 105 * T_TIRED0) * ease(seg(t, T_TIRED0, T_SUMMIT)) ** 1.15
    k = t - T_SUMMIT
    return min(s_top + 190, s_top + 260 * k + 330 * k * k)

def ride(ph, tired=False):
    s = math.sin(ph)
    if tired:
        return P(torso=150, head=115, ua_l=95, fa_l=95, ua_r=90, fa_r=92, th_l=70, sh_l=10, th_r=70, sh_r=10)
    return P(torso=165, head=170, ua_l=70, fa_l=95, ua_r=65, fa_r=92, th_l=60 + 30 * s, sh_l=0 + 25 * s, th_r=60 - 30 * s, sh_r=-25 * s)

def bike(d, dl, s, riders, ph, cols, fwd=1, length=150):
    """riders: lista di (offset lungo il telaio, colore, stanco). fwd=1 verso destra."""
    (cx, cy), ang = point(s)
    if fwd < 0: ang = ang  # percorso già orientato
    ca, sa = math.cos(ang), math.sin(ang)
    def at(u, v):              # u lungo il telaio, v verso l'alto (perpendicolare)
        return (cx + u * ca * fwd + v * sa, cy + u * sa * fwd - v * ca)
    r_w = at(-length / 2, WR); f_w = at(length / 2, WR)
    for w in (r_w, f_w):
        d.ellipse([w[0] - WR, w[1] - WR, w[0] + WR, w[1] + WR], outline=(150, 150, 160), width=5)
        a = ph * 2
        d.line([(w[0] - WR * math.cos(a), w[1] - WR * math.sin(a)), (w[0] + WR * math.cos(a), w[1] + WR * math.sin(a))], fill=(90, 90, 100), width=3)
    top_r, top_f = at(-length / 2 + 20, WR + 52), at(length / 2 - 10, WR + 52)
    d.line([r_w, top_r, top_f, f_w], fill=(150, 150, 160), width=6)
    d.line([at(length / 2 - 10, WR + 52), at(length / 2 + 6, WR + 78)], fill=(150, 150, 160), width=6)   # manubrio
    rot = math.degrees(ang) * fwd
    for off, col, tired in riders:
        hip = at(off, WR + 62)
        pose = ride(ph + off, tired)
        draw_fig(dl, hip, pose, col, fwd, rot, KR)

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit); late = []
    city = 0.15 + 0.85 * ease(seg(t, T_ANS - 0.2, T_ANS + 0.7))
    for sx, sy, b in STARS:
        c = int(50 + 80 * b); d.point((sx, sy), fill=(c, c, c + 10))
    for bx, bw, bh, base, wins in CITY:
        d.rectangle([bx, base - bh, bx + bw, base], fill=(16, 18, 26))
        for wx, wy, r in wins:
            if r < city:
                col = BLUE if r < 0.5 else (200, 215, 240)
                if wy + 13 >= ground_y(wx) - 4: continue
                dl.rectangle([wx, wy, wx + 9, wy + 13], fill=tuple(int(v * (0.5 + 0.5 * city)) for v in col))
    # collina
    d.polygon([PATH[0], PATH[1], PATH[2], (W + 200, H), (-200, H)], fill=(22, 22, 28))
    d.line(PATH, fill=(110, 110, 120), width=5)
    # gli altri: salgono da soli, poi scendono e tornano indietro
    for j, (s0, stop) in enumerate([(650, 0.9), (770, 1.4), (880, 1.9)]):
        if t < stop:
            s = s0 + 90 * t; fwd = 1; ph = t * 8 + j
        else:
            s = s0 + 90 * stop - 240 * (t - stop) ** 1.3; fwd = -1; ph = 0
        if s < 0: continue
        bike(d, d, s, [(0, GREY, t >= stop)], ph, None, fwd, 110)
    for txt, a, b, bx, by in C["fumetti_altri"]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        late.append((bx, by, txt, al))
    # il tandem
    s = tandem_s(t)
    ph = t * (9 if t < T_TIRED0 else 5) if t < T_SUMMIT else T_SUMMIT * 5
    tired = T_TIRED0 <= t < T_SUMMIT
    bike(d, dl, s, [(40, BLUE, tired), (-45, (125, 185, 255), False)], ph, None, 1, 150)
    (cx, cy), _ = point(s)
    for txt, a, b, dx, dy in C["fumetti_tandem"]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        late.append((cx + dx, cy + dy, txt, al))
    # testi
    if t < T_ANS:
        phrase(d, [(C["frase1"][0], WHITE), (C["frase1"][1], BLUE)])
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, size=C.get("size2", 62), cps=45)
        al = ease(seg(t, T_ANS + 0.5, T_ANS + 0.8))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            for n, s_ in enumerate(C["invito"]):
                fnt = font(38); d.text(((W - text_w(s_, fnt)) / 2, 470 + n * 48), s_, font=fnt, fill=c)
    watermark(d)
    out = glow(img, lit, 22, 1.0); do = ImageDraw.Draw(out)
    for bx, by, txt, al in late: bubble(do, bx, by, txt, 34, al)
    return out

if __name__ == "__main__":
    S = C.get("velocita", 1.0)
    if len(sys.argv) > 3:
        frame(float(sys.argv[3]) * S).save(OUT); sys.exit()
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03)), (0.0, s_whoosh(0.5, 0.3))]
    k = 0.0
    while k < T_SUMMIT:                                # pedalate: più lente quando uno si spegne
        ev.append((k, s_tok(110, 0.05, 0.25))); k += 0.35 if k < T_TIRED0 else 0.6
    for txt, a, b, bx, by in C["fumetti_altri"]: ev.append((a, s_pop(0.3)))
    for txt, a, b, dx, dy in C["fumetti_tandem"]: ev.append((a, s_pop(0.35, 900)))
    ev += [(T_TIRED0, s_thud(0.4, 60)), (T_SUMMIT, s_whoosh(1.4, 0.6)), (T_ANS - 0.3, s_rise(2.2, 0.45)), (T_ANS + 0.05, s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 45, s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
