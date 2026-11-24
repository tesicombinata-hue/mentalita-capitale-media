#!/usr/bin/env python3
"""Reel B "Il ponte" (24/11) – Mentalità Capitale.

Due amici costruiscono un ponte asse dopo asse sopra un burrone, verso una città illuminata.
La folla grigia sul bordo li prende in giro. Un'asse cede: uno cade, l'altro lo afferra.
Arrivano dall'altra parte e la frase in alto cambia: la folla attraversa il ponte costruito da loro.
Uso: python3 reel_ponte.py contenuto.json uscita.mp4
"""
import json, math, sys, random
from PIL import Image, ImageDraw
sys.path.insert(0, __import__("os").path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 11.8)
G = 1200                      # piano dei bordi
L_EDGE, R_EDGE = 290, 808     # bordi del burrone
PW = 74                       # larghezza di un'asse
KF = 2.0                      # scala dei protagonisti
KC = 1.6                      # scala della folla
random.seed(3)
STARS = [(random.randint(0, W), random.randint(560, 1000), random.random()) for _ in range(70)]
CITY = []
x = 560
while x < W:
    w = random.randint(80, 140); h = random.randint(260, 560)
    wins = [(x + 10 + i * 22, G - h + 14 + j * 30) for i in range((w - 14) // 22) for j in range((h - 30) // 30)]
    CITY.append((x, w, h, [(a, b, random.random()) for a, b in wins])); x += w + 6

# asse i: (tempo di posa, indice di posizione)
PLANKS = [(0.30, 0), (1.10, 1), (1.90, 2), (2.70, 3), (3.50, 4), (7.10, 4), (7.55, 5), (8.00, 6)]
T_CRACK, T_BREAK, T_GRAB, T_PULL0, T_PULL1 = 4.45, 4.75, 4.98, 6.05, 6.85
T_ARRIVE, T_ANS, T_CROWD = 8.75, 8.80, 9.10

def plank_x(i): return L_EDGE + PW * i

def a_pos(t):
    """Posizione (x) dell'amico davanti (A), che posa le assi."""
    xs = [(0.0, plank_x(0) - 40), (0.85, plank_x(1) - 40), (1.65, plank_x(2) - 40), (2.45, plank_x(3) - 40),
          (3.25, plank_x(4) - 40), (4.35, plank_x(4) + 40), (T_PULL1, plank_x(4) - 10), (7.30, plank_x(5) - 40),
          (7.75, plank_x(6) - 40), (T_ARRIVE, R_EDGE + 90)]
    for (t0, x0), (t1, x1) in zip(xs, xs[1:]):
        if t < t1:
            wd = min(0.4, t1 - t0)
            if t >= t1 - wd and x1 > x0:        # cammina nell'ultimo tratto
                return x0 + (x1 - x0) * ease((t - (t1 - wd)) / wd), True
            return x0, False
    return R_EDGE + 90, False

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit)
    city = 0.35 + 0.65 * ease(seg(t, T_ANS - 0.2, T_ANS + 0.8))
    for sx, sy, b in STARS:
        c = int(60 + 80 * b); d.point((sx, sy), fill=(c, c, c + 10))
    for bx, bw, bh, wins in CITY:
        d.rectangle([bx, G - bh, bx + bw, G], fill=(16, 18, 26))
        for wx, wy, r in wins:
            if r < city:
                col = BLUE if r < 0.5 else (200, 215, 240)
                dl.rectangle([wx, wy, wx + 10, wy + 14], fill=tuple(int(v * (0.55 + 0.45 * city)) for v in col))
    # bordi del burrone
    d.polygon([(0, G), (L_EDGE, G), (L_EDGE - 30, H), (0, H)], fill=(30, 30, 36))
    d.polygon([(R_EDGE, G), (W, G), (W, H), (R_EDGE + 30, H)], fill=(30, 30, 36))
    d.line([(0, G), (L_EDGE, G)], fill=(90, 90, 100), width=4); d.line([(R_EDGE, G), (W, G)], fill=(90, 90, 100), width=4)
    # assi
    for n, (tp, i) in enumerate(PLANKS):
        if t < tp - 0.25: continue
        x0 = plank_x(i); y = G
        if n == 4 and t >= T_BREAK:          # l'asse che cede e cade
            k = t - T_BREAK; y = G + 900 * k * k; ang = min(80, 160 * k)
            cx, cy = x0 + PW / 2, y
            pts = [(-PW / 2, -7), (PW / 2, -7), (PW / 2, 7), (-PW / 2, 7)]
            a = math.radians(ang)
            d.polygon([(cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)) for px, py in pts], fill=(170, 170, 178))
            continue
        drop = 1 - ease(seg(t, tp - 0.25, tp))
        wob = 3 * math.sin(t * 40) if (n == 4 and T_CRACK <= t < T_BREAK) else 0
        d.rectangle([x0 + 2, y - 9 - 60 * drop + wob, x0 + PW - 2, y + 9 - 60 * drop + wob], fill=(185, 185, 192))
        if n == 4 and t >= T_CRACK:
            d.line([(x0 + 25, y - 7), (x0 + 33, y + 7)], fill=BG, width=3)
    # folla
    crowd_x = [25, 75, 125, 175, 225]
    for j, cx in enumerate(crowd_x):
        if t < T_CROWD:
            if t < T_PULL1:
                pose = laugh(t * 9 + j) if (j + int(t * 1.4)) % 3 else POINT
            else:
                pose = SAD if t > T_ANS else STAND
            d_ = 1
            hip = on_ground(cx, G, pose, KC)
        else:                                # attraversano il ponte, testa bassa
            k = t - T_CROWD; px = cx + 190 * k
            pose = walk(k * 7 + j, 18); pose["head"] = 150
            hip = on_ground(px, G, pose, KC); d_ = 1
        draw_fig(d, hip, pose, GREY, d_, 0, KC)
    # fumetti della folla
    for s, a, b, bx in [("SEI PAZZO", 1.0, 2.3, 170), ("CADRAI", 2.2, 3.5, 130), ("TORNA INDIETRO", 3.3, 4.6, 220), ("TE L'AVEVO DETTO", 5.0, 6.4, 240)]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        bubble(d, bx, 790, s, 42, al)
    # i due amici
    ax, walking = a_pos(t)
    holding = any(tp - 0.6 < t < tp - 0.25 for tp, _ in PLANKS)
    placing = any(tp - 0.25 <= t < tp + 0.05 for tp, _ in PLANKS)
    if t < T_BREAK or t >= T_PULL1:
        if t >= T_ARRIVE:
            pa = STAND; fa = -1 if t > T_ANS + 0.3 else 1
        elif placing: pa = PLACE; fa = 1
        elif walking: pa = walk(t * 9); fa = 1
        else: pa = CARRY if holding else STAND; fa = 1
        if T_PULL1 <= t < T_PULL1 + 0.01: pass
        a_hip = on_ground(ax, G, pa, KF)
    bx = ax - 115 if t < T_ARRIVE else ax - 130
    b_grab_x = plank_x(4) - 55
    if T_BREAK <= t < T_PULL1:
        bx = b_grab_x
        pb = mix(STAND, REACH, seg(t, T_BREAK, T_GRAB)) if t < T_PULL0 else mix(REACH, STAND, seg(t, T_PULL0, T_PULL1))
        b_hip = on_ground(bx, G, pb, KF)
        bsk = draw_fig(dl, b_hip, pb, BLUE, 1, 0, KF)
        hand = bsk["hr"]
        rel, _ = skeleton((0, 0), HANG, -1, 0, KF)
        hang_hip = (hand[0] - rel["hr"][0], hand[1] - rel["hr"][1])
        start = on_ground(plank_x(4) + 40, G, STAND, KF)
        if t < T_GRAB:
            k = seg(t, T_BREAK, T_GRAB); pa = mix(STAND, HANG, k)
            a_hip = (start[0] + (hang_hip[0] - start[0]) * k, start[1] + (hang_hip[1] - start[1]) * k * k)
        elif t < T_PULL0:
            sw = 4 * math.sin((t - T_GRAB) * 5)
            pa = HANG; a_hip = (hang_hip[0] + sw, hang_hip[1])
        else:
            k = seg(t, T_PULL0, T_PULL1); end = on_ground(plank_x(4) - 10, G, STAND, KF)
            pa = mix(HANG, STAND, k); a_hip = (hang_hip[0] + (end[0] - hang_hip[0]) * ease(k), hang_hip[1] + (end[1] - hang_hip[1]) * ease(k))
        draw_fig(dl, a_hip, pa, BLUE, -1, 0, KF)
    else:
        if t < T_ARRIVE:
            pb = walk_carry(t * 9) if walking else CARRY
        else:
            pb = STAND
        fb = -1 if t > T_ANS + 0.3 else 1
        draw_fig(dl, on_ground(bx, G, pb, KF), pb, BLUE, fb, 0, KF)
        sk = draw_fig(dl, a_hip, pa, BLUE, fa, 0, KF)
        if holding and t < T_ARRIVE:          # asse tra le mani di A
            h = sk["hr"]; d.rectangle([h[0] - 14, h[1] - 8, h[0] + PW - 14, h[1] + 10], fill=(185, 185, 192))
    # testi
    if t < T_ANS:
        phrase(d, [(C["frase1"][0], WHITE), (C["frase1"][1], BLUE)])
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, cps=45)
        al = ease(seg(t, T_ANS + 0.6, T_ANS + 0.9))
        if al > 0:
            c = tuple(int(BG[i] + (210 - BG[i]) * al) for i in range(3))
            fnt = font(40); s = C["invito"]; d.text(((W - text_w(s, fnt)) / 2, 470), s, font=fnt, fill=c)
    watermark(d)
    return glow(img, lit, 22, 1.1)

if __name__ == "__main__":
    S = C.get("velocita", 1.0)                 # >1 = più veloce (M6: risposta entro ~7 s)
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03))]
    for tp, i in PLANKS: ev.append((tp, s_tok(170 + i * 8)))
    for a in (1.0, 2.2, 3.3, 5.0): ev.append((a, s_pop(0.35)))
    ev += [(T_CRACK, s_crack(0.9)), (T_BREAK, s_whoosh(0.7, 0.5, False)), (T_GRAB, s_thud(0.7, 90)),
           (T_PULL0, s_whoosh(0.8, 0.3)), (T_ANS - 0.3, s_rise(2.2, 0.5)), (T_ANS + 0.1, s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])):
        ev.append((T_ANS + k / 45, s_type(0.12)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    import os; os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
