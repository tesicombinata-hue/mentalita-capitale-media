#!/usr/bin/env python3
"""Reel B "Il giro" (massa che marcia, tu esci dal gruppo) – Mentalità Capitale, 26/11.

Una massa grigia marcia a passo unico sotto cartelli che si ripetono (STIPENDIO, RATE, SPESE, ZERO). Lui (blu) si
ferma: gli altri lo urtano e lo superano ("CAMMINA", "DOVE VAI?", "TORNA IN FILA"). Esce dalla fila, esita, guarda
indietro. Un'amica nella fila rallenta: lui le tende la mano e anche lei esce. Vista dall'alto: la massa cammina in
cerchio e non va da nessuna parte; i due escono dall'anello verso la città accesa.
Uso: python3 reel_giro.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 11.0)
V = 150                                   # velocità della massa (px/s)
STEP = 7.0                                # frequenza del passo
T_STOP = 1.9                              # lui si ferma
T_OUT0, T_OUT1 = 3.0, 3.6                 # esce dalla fila
T_LOOK0, T_LOOK1 = 4.1, 4.8               # guarda indietro, esita
T_HAND0, T_HAND1 = 5.0, 5.9               # tende la mano all'amica
T_FOUT0, T_FOUT1 = 5.9, 6.4               # lei esce
T_GO = 6.5                                # se ne vanno insieme
T_TOP = 7.3                               # vista dall'alto
T_ANS = 7.7
ROWS = [  # (y piedi, scala, colore, passo tra gli omini, sfasamento)
    (1060, 1.05, (70, 70, 80), 70, 0),
    (1160, 1.4, (100, 100, 112), 92, 30),
    (1290, 1.85, (150, 150, 160), 125, 0),
]
FRONT = 2
FRIEND_I = 3                              # l'amica: la quarta della fila davanti, dietro di lui
LEI = (125, 185, 255)
SIGNS = C["cartelli"]
random.seed(4)

def cam(t):
    return V * min(t, T_STOP)

def he_world(t):
    return 540 + V * min(t, T_STOP)

def frame_side(t, d, dl, late):
    cx = cam(t)
    # strada e cartelli (fissi nel mondo)
    d.rectangle([0, 1000, W, 1330], fill=(18, 18, 24))
    for k in range(-2, 40):
        wx = k * 420
        sx = wx - cx + 100
        if -300 < sx < W + 300:
            d.line([(sx, 1000), (sx, 700)], fill=(60, 60, 70), width=6)
            s = SIGNS[k % len(SIGNS)]
            fnt = font(40); tw = text_w(s, fnt)
            d.rectangle([sx - tw / 2 - 18, 630, sx + tw / 2 + 18, 700], fill=(36, 36, 44), outline=(90, 90, 100), width=3)
            d.text((sx - tw / 2, 645), s, font=fnt, fill=(200, 200, 210))
    for x in range(-200, W + 200, 160):
        xx = x - (cx * 1.0) % 160
        d.line([(xx, 1340), (xx + 70, 1340)], fill=(40, 40, 48), width=4)
    ph = t * STEP
    hx_world = he_world(t)
    for ri, (gy, k, col, gap, off) in enumerate(ROWS):
        n0 = int((cx - 600) // gap) - 2
        for i in range(n0, n0 + int(W / gap) + 8):
            wx = i * gap + off + V * t                           # la massa marcia sempre
            if ri == FRONT:
                base_i = i - int(V * t // gap)
            sx = wx - cx
            if sx < -150 or sx > W + 150: continue
            if ri == FRONT:
                # il posto di lui nella fila resta vuoto dopo che è uscito; l'amica è una del gruppo
                slot = round((wx - V * t - off) / gap)
                if slot == 540 // gap + 0: pass
                me_slot = round((540 - off) / gap)
                if slot == me_slot: continue                     # quello è lui, disegnato a parte
                if slot == me_slot - FRIEND_I:                   # l'amica (arriva da dietro)
                    continue
            pose = walk(ph + (0 if ri != 1 else 0.0), 20); pose["head"] = 172
            draw_fig(d, on_ground(sx, gy, pose, k), pose, col, 1, 0, k)
    # l'amica
    gy, k, col, gap, off = ROWS[FRONT]
    me_slot = round((540 - off) / gap)
    fw = (me_slot - FRIEND_I) * gap + off + V * min(t, T_HAND0 - 0.6) if t < T_FOUT0 else None
    if t < T_FOUT0:
        fsx = fw - cx
        if t < T_HAND0 - 0.6: fp = walk(ph, 20)
        else: fp = STAND; fp = dict(fp); fp["head"] = 200 if t < T_HAND0 else 185
        fy = gy; kk = k
    else:
        q = ease(seg(t, T_FOUT0, T_FOUT1))
        fw0 = (me_slot - FRIEND_I) * gap + off + V * (T_HAND0 - 0.6)
        fsx = fw0 - cx + (he_world(t) - 110 - fw0 + cx - cx) * 0 if False else (fw0 - cx) + ((he_world(t) - cx - 120) - (fw0 - cx)) * q
        fy = gy + 170 * q; kk = k + 0.25 * q
        fp = walk(t * 7, 18) if q < 1 else STAND
        if t >= T_GO: fp = walk(t * 7, 18)
    fdir = 1
    if t >= T_GO:
        fsx -= 170 * (t - T_GO); fdir = -1
    q2 = ease(seg(t, T_HAND0 - 0.5, T_HAND0 + 0.2))
    fcol = tuple(int(col[j] + (LEI[j] - col[j]) * q2) for j in range(3))
    fsk = draw_fig(dl if q2 > 0 else d, on_ground(fsx, fy, fp, kk), fp, fcol, fdir, 0, kk)
    # lui
    q = ease(seg(t, T_OUT0, T_OUT1))
    hsx = he_world(t) - cx
    hy = gy + 170 * q; hk = k + 0.25 * q
    if t < T_STOP: hp = walk(ph, 20); hdir = 1
    elif t < T_OUT0: hp = STAND; hdir = 1
    elif t < T_OUT1: hp = walk(t * 7, 18); hdir = 1
    elif T_LOOK0 <= t < T_LOOK1: hp = P(head=160); hdir = -1
    elif T_HAND0 <= t < T_FOUT1: hp = P(ua_r=-95, fa_r=-90); hdir = 1      # mano tesa verso di lei
    elif t >= T_GO: hp = walk(t * 7, 18); hdir = -1
    else: hp = STAND; hdir = 1
    if T_STOP <= t < T_OUT0:                                               # gli altri lo urtano
        hsx += 8 * math.sin(t * 30) * (1 - seg(t, T_STOP, T_STOP + 0.6))
    if t >= T_GO: hsx -= 170 * (t - T_GO)
    draw_fig(dl, on_ground(hsx, hy, hp, hk), hp, BLUE, hdir, 0, hk)
    # fumetti
    for s, a, b, bx, by in C["fumetti"]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        late.append((bx, by, s, al))

def frame_top(t, d, dl, late):
    k = ease(seg(t, T_TOP, T_TOP + 0.7))
    R = 1700 * (1 - k) + 390 * k
    cx0, cy0 = 540, 1080
    rot = t * 0.35
    n = 220
    for i in range(n):
        a = rot + 2 * math.pi * i / n
        for ring in (-26, -9, 9, 26):
            x = cx0 + (R + ring) * math.cos(a); y = cy0 + (R + ring) * math.sin(a) * 0.72
            if -10 < x < W + 10 and 0 < y < H:
                r = 7 if R < 600 else 11
                d.ellipse([x - r, y - r, x + r, y + r], fill=(150, 150, 160))
    if k > 0.6:
        al = ease(seg(t, T_TOP + 0.5, T_TOP + 0.9))
        c = tuple(int(BG[j] + (190 - BG[j]) * al) for j in range(3))
        for s, a in zip(SIGNS, (-math.pi / 2, 0, math.pi / 2, math.pi)):
            x = cx0 + (R - 120) * math.cos(a); y = cy0 + (R - 80) * math.sin(a) * 0.72
            fnt = font(34); d.text((x - text_w(s, fnt) / 2, y - 18), s, font=fnt, fill=c)
        # frecce: il giro
        for a in (-math.pi / 4, math.pi / 4, 3 * math.pi / 4, -3 * math.pi / 4):
            x = cx0 + (R + 50) * math.cos(a); y = cy0 + (R + 50) * math.sin(a) * 0.72
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=c)
        # la città accesa e i due che escono
        city = ease(seg(t, T_ANS, T_ANS + 1.2))
        for j in range(40):
            wx = 50 + (j % 8) * 30; wy = 1580 - (j // 8) * 42 - (j % 3) * 14
            dl.rectangle([wx, wy, wx + 16, wy + 22], fill=tuple(int(v * city) for v in (BLUE if j % 3 else (220, 225, 240))))
        sx, sy = cx0 + R * math.cos(2.3), cy0 + R * math.sin(2.3) * 0.72
        ex, ey = 170, 1500
        q = ease(seg(t, T_TOP + 0.6, DUR - 0.6))
        px_, py_ = sx + (ex - sx) * q, sy + (ey - sy) * q
        dl.line([(sx, sy), (px_, py_)], fill=(60, 120, 200), width=6)
        for dx, col in ((-15, BLUE), (15, LEI)):
            dl.ellipse([px_ + dx - 14, py_ - 14, px_ + dx + 14, py_ + 14], fill=col)

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit); late = []
    if t < T_TOP: frame_side(t, d, dl, late)
    else: frame_top(t, d, dl, late)
    if t < T_ANS:
        phrase(d, [(C["frase1"][0], WHITE), (C["frase1"][1], BLUE)], size=C.get("size1", 58))
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, size=C.get("size2", 50), cps=50)
        al = ease(seg(t, T_ANS + 0.8, T_ANS + 1.1))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            for n_, s in enumerate(C["invito"]):
                fnt = font(38); d.text(((W - text_w(s, fnt)) / 2, 470 + n_ * 48), s, font=fnt, fill=c)
    watermark(d)
    out = glow(img, lit, 22, 1.0); do = ImageDraw.Draw(out)
    for bx, by, s, al in late: bubble(do, bx, by, s, 36, al)
    if T_TOP - 0.15 <= t < T_TOP + 0.15:                        # stacco
        a = 1 - abs(t - T_TOP) / 0.15
        out = Image.blend(out, Image.new("RGB", (W, H), BG), a * 0.8)
    return out

if __name__ == "__main__":
    S = C.get("velocita", 1.0)
    if len(sys.argv) > 3:
        frame(float(sys.argv[3]) * S).save(OUT); sys.exit()
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03))]
    k = 0.0
    while k < T_TOP:                                            # passo unico della massa
        ev.append((k, s_thud(0.35, 55))); k += math.pi / STEP
    for s, a, b, bx, by in C["fumetti"]: ev.append((a, s_pop(0.3)))
    ev += [(T_STOP, s_thud(0.6, 90)), (T_OUT0, s_whoosh(0.5, 0.3)), (T_LOOK0, s_whoosh(0.4, 0.15)),
           (T_HAND0 + 0.3, s_chime(0.3, 660)), (T_FOUT0, s_whoosh(0.5, 0.3)),
           (T_TOP - 0.2, s_whoosh(1.0, 0.6, False)), (T_ANS - 0.3, s_rise(2.4, 0.45)), (T_ANS + 0.05, s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 50, s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
