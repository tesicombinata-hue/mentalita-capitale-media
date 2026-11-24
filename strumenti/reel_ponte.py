#!/usr/bin/env python3
"""Reel B "Il ponte" v2 (24/11) – Mentalità Capitale.

Lui costruisce un ponte asse dopo asse sopra un burrone, verso la casa che vogliono; lei gli passa le assi.
La folla grigia prende in giro lui e poi lei ("E TU GLI CREDI?"). Lui esita guardando giù: lei gli mette una mano sulla spalla.
Un'asse cede: lui cade, lei si butta a terra, lo afferra e scivola verso il bordo, poi lo tira su. Si abbracciano,
finiscono il ponte insieme. Dall'altra parte la casa si accende e la folla attraversa il ponte che criticava.
Uso: python3 reel_ponte.py contenuto.json uscita.mp4
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 10.4)
G = 1200
L_EDGE, R_EDGE = 345, 807
PW = 66
KF, KL, KC = 2.0, 1.8, 1.6
LEI = (125, 185, 255)                 # lei: azzurro più chiaro, coda di cavallo
random.seed(3)
STARS = [(random.randint(0, W), random.randint(560, 1000), random.random()) for _ in range(70)]
CITY = []
x = 560
while x < W:
    w = random.randint(80, 140); h = random.randint(300, 560)
    wins = [(x + 10 + i * 22, G - h + 14 + j * 30) for i in range((w - 14) // 22) for j in range((h - 30) // 30)]
    CITY.append((x, w, h, [(a, b, random.random()) for a, b in wins])); x += w + 6
HOUSE = (850, 1030)                   # la loro casa, sul bordo di destra

PLANKS = [(0.30, 0), (0.95, 1), (1.60, 2), (2.25, 3), (2.90, 4), (6.75, 4), (7.05, 5), (7.35, 6)]
T_LOOK0, T_LOOK1 = 3.05, 3.65         # lui esita guardando giù, lei gli tocca la spalla
T_CRACK, T_BREAK, T_GRAB = 3.95, 4.20, 4.42
T_SLIDE1, T_PULL0, T_PULL1 = 5.00, 5.35, 6.15
T_HUG0, T_HUG1 = 6.15, 6.55
T_ARRIVE, T_ANS, T_CROWD = 7.70, 7.75, 8.15

def px(i): return L_EDGE + PW * i

LOOK = P(torso=168, head=125, ua_l=20, fa_l=15, ua_r=10, fa_r=5)
SHOULDER = P(ua_r=110, fa_r=95)                                   # mano sulla spalla di lui
LIE = P(torso=90, head=90, ua_r=90, fa_r=90, ua_l=70, fa_l=80, th_l=-90, sh_l=-90, th_r=-95, sh_r=-95)
PULL = P(torso=110, head=100, ua_r=40, fa_r=20, ua_l=50, fa_l=30, th_l=-30, sh_l=-80, th_r=-50, sh_r=-100)
HUG = P(ua_l=80, fa_l=150, ua_r=75, fa_r=150, head=170)
HAND = P(ua_l=25, fa_l=25)                                        # mano nella mano

def lui_x(t):
    xs = [(0.0, px(0) - 40), (0.70, px(1) - 40), (1.35, px(2) - 40), (2.00, px(3) - 40), (2.65, px(4) - 40),
          (T_LOOK1 + 0.25, px(4) + 40), (T_PULL1, px(4) - 10), (6.90, px(5) - 40), (7.20, px(6) - 40), (T_ARRIVE, R_EDGE + 70)]
    for (t0, x0), (t1, x1) in zip(xs, xs[1:]):
        if t < t1:
            wd = min(0.35, t1 - t0)
            if t >= t1 - wd and x1 != x0:
                return x0 + (x1 - x0) * ease((t - (t1 - wd)) / wd), True
            return x0, False
    return R_EDGE + 70, False

def hair(dr, sk, f, col, k, skirt=True):
    h = sk["H"]
    if skirt:                                   # gonna corta: si capisce che è lei
        dr.polygon([(h[0] - 6 * k, h[1] - 14 * k), (h[0] + 6 * k, h[1] - 14 * k), (h[0] + 24 * k, h[1] + 30 * k), (h[0] - 24 * k, h[1] + 30 * k)], fill=col)
    n = sk["N"]; r = 17 * k
    dr.line([(n[0] - f * r * 0.6, n[1] - r * 0.4), (n[0] - f * r * 1.7, n[1] + r * 0.9)], fill=col, width=int(8 * k))

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit)
    city = 0.3 + 0.7 * ease(seg(t, T_ANS - 0.2, T_ANS + 0.8))
    for sx, sy, b in STARS:
        c = int(60 + 80 * b); d.point((sx, sy), fill=(c, c, c + 10))
    for bx, bw, bh, wins in CITY:
        d.rectangle([bx, G - bh, bx + bw, G], fill=(16, 18, 26))
        for wx, wy, r in wins:
            if r < city:
                col = BLUE if r < 0.5 else (200, 215, 240)
                dl.rectangle([wx, wy, wx + 10, wy + 14], fill=tuple(int(v * (0.5 + 0.5 * city)) for v in col))
    # la casa che vogliono, davanti alla città
    hx0, hx1 = HOUSE
    d.rectangle([hx0, G - 150, hx1, G], fill=(26, 28, 38)); d.polygon([(hx0 - 15, G - 150), ((hx0 + hx1) / 2, G - 240), (hx1 + 15, G - 150)], fill=(26, 28, 38))
    hw = 0.25 + 0.75 * ease(seg(t, T_ANS, T_ANS + 0.5))
    dl.rectangle([hx0 + 30, G - 120, hx0 + 75, G - 70], fill=tuple(int(c * hw) for c in (230, 215, 170)))
    dl.rectangle([hx1 - 75, G - 120, hx1 - 30, G - 70], fill=tuple(int(c * hw) for c in (230, 215, 170)))
    # bordi
    d.polygon([(0, G), (L_EDGE, G), (L_EDGE - 30, H), (0, H)], fill=(30, 30, 36))
    d.polygon([(R_EDGE, G), (W, G), (W, H), (R_EDGE + 30, H)], fill=(30, 30, 36))
    d.line([(0, G), (L_EDGE, G)], fill=(90, 90, 100), width=4); d.line([(R_EDGE, G), (W, G)], fill=(90, 90, 100), width=4)
    # assi
    for n, (tp, i) in enumerate(PLANKS):
        if t < tp - 0.2: continue
        x0 = px(i); y = G
        if n == 4 and t >= T_BREAK:
            k = t - T_BREAK; cy = G + 900 * k * k; a = math.radians(min(80, 160 * k)); cx = x0 + PW / 2
            pts = [(-PW / 2, -9), (PW / 2, -9), (PW / 2, 9), (-PW / 2, 9)]
            d.polygon([(cx + a1 * math.cos(a) - b1 * math.sin(a), cy + a1 * math.sin(a) + b1 * math.cos(a)) for a1, b1 in pts], fill=(170, 170, 178))
            continue
        drop = 1 - ease(seg(t, tp - 0.2, tp))
        wob = 3 * math.sin(t * 40) if (n == 4 and T_CRACK <= t < T_BREAK) else 0
        d.rectangle([x0 + 2, y - 9 - 60 * drop + wob, x0 + PW - 2, y + 9 - 60 * drop + wob], fill=(185, 185, 192))
        if n == 4 and t >= T_CRACK: d.line([(x0 + 30, y - 9), (x0 + 40, y + 9)], fill=BG, width=4)
    # folla
    for j, cx in enumerate([12, 55, 98, 141]):
        if t < T_CROWD:
            if t < T_PULL1: pose = laugh(t * 9 + j) if (j + int(t * 1.4)) % 3 else POINT
            else: pose = SAD if t > T_ANS else STAND
            hip = on_ground(cx, G, pose, KC)
        else:
            k = t - T_CROWD; pose = walk(k * 7 + j, 18); pose["head"] = 150
            hip = on_ground(cx + 150 * k, G, pose, KC)
        draw_fig(d, hip, pose, GREY, 1, 0, KC)
    for s, a, b, bx in C["fumetti"]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        bubble(d, bx, 790, s, 42, al)
    # LUI e LEI
    lx, walking = lui_x(t)
    holding = any(tp - 0.55 < t < tp - 0.2 for tp, _ in PLANKS)
    placing = any(tp - 0.2 <= t < tp + 0.05 for tp, _ in PLANKS)
    gx = px(4) - 60                                   # dove lei si butta a terra
    if T_BREAK <= t < T_PULL1:
        # lei: si butta a terra, scivola verso il bordo, poi tira
        if t < T_GRAB: pb = mix(STAND, LIE, seg(t, T_BREAK, T_GRAB)); slide = 0
        elif t < T_SLIDE1: pb = LIE; slide = 38 * ease(seg(t, T_GRAB, T_SLIDE1))
        elif t < T_PULL0: pb = LIE; slide = 38
        else: pb = mix(LIE, PULL, seg(t, T_PULL0, T_PULL0 + 0.25)); slide = 38 - 30 * seg(t, T_PULL0, T_PULL1)
        k = seg(t, T_BREAK, T_GRAB)
        hipy = G - feet_offset(STAND, KL) * (1 - k) - 22 * k
        if t >= T_PULL0: hipy = G - 22 - 60 * seg(t, T_PULL0 + 0.2, T_PULL1)
        lsk = draw_fig(dl, (gx + slide, hipy), pb, LEI, 1, 0, KL); hair(dl, lsk, 1, LEI, KL, False)
        hand = lsk["hr"]
        rel, _ = skeleton((0, 0), HANG, -1, 0, KF)
        hang = (hand[0] - rel["hr"][0], hand[1] - rel["hr"][1])
        start = on_ground(px(4) + 40, G, STAND, KF)
        if t < T_GRAB:
            k = seg(t, T_BREAK, T_GRAB); pa = mix(LOOK, HANG, k)
            a_hip = (start[0] + (hang[0] - start[0]) * k, start[1] + (hang[1] - start[1]) * k * k)
        elif t < T_PULL0:
            pa = HANG; a_hip = (hang[0] + 5 * math.sin((t - T_GRAB) * 6), hang[1])
        else:
            k = ease(seg(t, T_PULL0, T_PULL1)); end = on_ground(px(4) - 10, G, STAND, KF)
            pa = mix(HANG, STAND, k); a_hip = (hang[0] + (end[0] - hang[0]) * k, hang[1] + (end[1] - hang[1]) * k)
        draw_fig(dl, a_hip, pa, BLUE, -1, 0, KF)
    else:
        after = t >= T_ARRIVE
        fa = -1 if t > T_ANS + 0.3 else 1
        if T_HUG0 <= t < T_HUG1: pa = HUG; fa = -1
        elif after: pa = HAND
        elif T_LOOK0 <= t < T_LOOK1: pa = LOOK
        elif placing: pa = PLACE
        elif walking: pa = walk(t * 9)
        else: pa = CARRY if holding else STAND
        a_hip = on_ground(lx, G, pa, KF)
        # lei: dietro di lui, passa le assi; mano sulla spalla quando lui esita
        bx = lx - (95 if after or (T_HUG0 <= t < T_HUG1) else 88)
        if T_HUG0 <= t < T_HUG1: pb = HUG; fb = 1; bx = lx - 70
        elif after: pb = P(ua_r=-25, fa_r=-25); fb = -1 if t > T_ANS + 0.3 else 1
        elif T_LOOK0 + 0.15 <= t < T_LOOK1 + 0.1: pb = SHOULDER; fb = 1
        else: pb = walk_carry(t * 9) if walking else CARRY; fb = 1
        if after and t > T_ANS + 0.3: bx = lx + 95          # girati verso la folla, lei alla sua destra
        lsk = draw_fig(dl, on_ground(bx, G, pb, KL), pb, LEI, fb, 0, KL); hair(dl, lsk, fb, LEI, KL)
        if not after and pb is not SHOULDER and not (T_HUG0 <= t < T_HUG1) and t < T_ARRIVE - 0.4:
            h = lsk["hr"]; d.rectangle([h[0] - 14, h[1] - 8, h[0] + PW - 14, h[1] + 10], fill=(185, 185, 192))
        draw_fig(dl, a_hip, pa, BLUE, fa, 0, KF)
    # testi
    if t < T_ANS:
        phrase(d, [(C["frase1"][0], WHITE), (C["frase1"][1], BLUE)])
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, size=C.get("size2", 52), cps=55)
        al = ease(seg(t, T_ANS + 0.6, T_ANS + 0.9))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            for n, s in enumerate(C["invito"]):
                fnt = font(38); d.text(((W - text_w(s, fnt)) / 2, 460 + n * 48), s, font=fnt, fill=c)
    watermark(d)
    return glow(img, lit, 22, 1.1)

if __name__ == "__main__":
    S = C.get("velocita", 1.0)
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03))]
    for tp, i in PLANKS: ev.append((tp, s_tok(170 + i * 8)))
    for s, a, b, bx in C["fumetti"]: ev.append((a, s_pop(0.35)))
    ev += [(T_LOOK0, s_whoosh(0.6, 0.2)), (T_CRACK, s_crack(0.9)), (T_BREAK, s_whoosh(0.7, 0.5, False)),
           (T_GRAB, s_thud(0.8, 90))]
    for k in range(4): ev.append((T_GRAB + 0.3 + k * 0.38, s_thud(0.35, 55)))      # battito mentre è appeso
    ev += [(T_PULL0, s_whoosh(0.8, 0.3)), (T_ANS - 0.3, s_rise(2.2, 0.5)), (T_ANS + 0.1, s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 55, s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
