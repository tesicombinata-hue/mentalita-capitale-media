#!/usr/bin/env python3
"""Reel B "Il secchio bucato" (serie Stesso stipendio, piccole spese) – Mentalità Capitale, 25/11.

Due amici camminano con lo stesso secchio pieno di monete (lo stipendio). Dal secchio di lui (bianco) si aprono
buchi piccoli, ognuno con il nome di una spesa piccola, e le monete cadono ("SONO SOLO 2 EURO"). L'amico (blu) si
ferma, posa il suo secchio e tappa i buchi uno a uno. Risposta: "NON TI SVUOTANO LE SPESE GRANDI. / TI SVUOTANO I
BUCHI PICCOLI."
Uso: python3 reel_secchio.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_mc import *

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 8.6)
G = 1260
K = 2.8
XA, XB = 380, 780
COIN = (110, 180, 255)
HOLES = C["buchi"]                       # [nome, t, dx, dy (rispetto al centro del secchio)]
T_STOP = 4.3                             # l'amico si ferma e posa il secchio
T_FIX0, T_FIXD = 4.75, 0.3               # tappa un buco ogni 0,3 s
T_ANS = 5.95
CARRY1 = P(ua_r=12, fa_r=12)             # braccio destro giù che regge il secchio
random.seed(9)

def walking(t, ph0=0.0, stop=None):
    if stop is not None and t >= stop: return STAND
    w = walk(t * 7 + ph0, 18); w.update(ua_r=12, fa_r=12); return w

def bucket(d, dl, cx, top, level, col_out, glow_coins=True):
    """Secchio: bordo superiore a y=top, centro cx. level 0-1."""
    w0, w1, h = 124, 92, 112
    d.polygon([(cx - w0 / 2, top), (cx + w0 / 2, top), (cx + w1 / 2, top + h), (cx - w1 / 2, top + h)], fill=(34, 34, 42), outline=col_out)
    d.arc([cx - w0 / 2 - 6, top - 70, cx + w0 / 2 + 6, top + 40], 200, 340, fill=col_out, width=5)      # manico
    if level > 0.02:
        y = top + h - h * level
        k = (y - top) / h; hw = (w0 + (w1 - w0) * k) / 2 - 6
        layer = dl if glow_coins else d
        layer.polygon([(cx - hw, y), (cx + hw, y), (cx + w1 / 2 - 6, top + h - 4), (cx - w1 / 2 + 6, top + h - 4)], fill=COIN)
        for i in range(5):
            ex = cx - hw + 16 + i * (2 * hw - 32) / 4
            layer.ellipse([ex - 18, y - 9, ex + 18, y + 7], fill=(170, 210, 255), outline=(60, 120, 200))
    return top + h

def frame(t):
    img = Image.new("RGB", (W, H), BG); lit = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img); dl = ImageDraw.Draw(lit); late = []
    # strada che scorre (camminano sul posto)
    d.line([(0, G), (W, G)], fill=(70, 70, 80), width=4)
    off = (t * 220) % 120 if t < T_STOP else (T_STOP * 220) % 120
    for x in range(-120, W + 120, 120):
        d.line([(x - off, G + 26), (x - off + 50, G + 26)], fill=(45, 45, 52), width=4)
    # quanti buchi sono aperti e quanti tappati
    opened = [h for h in HOLES if t >= h[1]]
    fixed = int(max(0, (t - T_FIX0) / T_FIXD) + 0.0001) if t >= T_FIX0 else 0
    leaking = len(opened) - min(fixed, len(opened))
    # livello di lui: scende finché ci sono buchi aperti
    lv = 0.92
    for h in HOLES:
        end = min(t, T_FIX0 + T_FIXD * (HOLES.index(h) + 1))
        if end > h[1]: lv -= 0.075 * (end - h[1])
    lv = max(0.08, lv)
    # LUI (bianco) con il secchio
    pa = walking(t, 0, T_STOP)
    if t >= T_ANS + 0.2: pa = mix(STAND, P(ua_l=150, fa_l=160, ua_r=12, fa_r=12), seg(t, T_ANS + 0.2, T_ANS + 0.5))
    ska = draw_fig(dl, on_ground(XA, G, pa, K), pa, WHITE, 1, 0, K)
    hand = ska["hr"]; top = hand[1] + 26
    bot = bucket(d, dl, hand[0] + 6, top, lv, (200, 200, 205))
    bx = hand[0] + 6
    # buchi, etichette, monete che cadono
    for i, (name, th, dx, dy) in enumerate(HOLES):
        if t < th: continue
        hx, hy = bx + dx * 0.7, top + 50 + dy * 0.8
        is_fixed = i < fixed
        if is_fixed:
            dl.rectangle([hx - 16, hy - 9, hx + 16, hy + 9], fill=(150, 190, 255))
        else:
            d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=BG, outline=(220, 220, 225), width=2)
            for k in range(4):                       # monete che cadono dal buco
                q = ((t - th) * 2.2 + k / 4) % 1
                cy = hy + q * (G - hy - 10); cx = hx + (8 if dx > 0 else -8) * q * 3
                dl.ellipse([cx - 10, cy - 5, cx + 10, cy + 5], fill=COIN)
        al = ease(seg(t, th, th + 0.15)) * (0.45 if is_fixed else 1.0)
        c = tuple(int(BG[j] + (225 - BG[j]) * al) for j in range(3))
        fnt = font(36); ly = G - 560 + i * 52
        d.text((40, ly), name, font=fnt, fill=c)
        lc = tuple(int(v * 0.5) for v in c); d.line([(50 + text_w(name, fnt) + 8, ly + 16), (hx - 10, hy)], fill=lc, width=2)
    # monete a terra
    n_ground = int(min(40, max(0, sum(max(0, min(t, T_FIX0 + T_FIXD * (i + 1)) - h[1]) for i, h in enumerate(HOLES)) * 6)))
    for j in range(n_ground):
        gx = bx - 110 + (j * 37) % 220; dl.ellipse([gx - 10, G - 9, gx + 10, G + 1], fill=(70, 120, 190))
    # L'AMICO (blu): cammina, si ferma, posa il secchio, tappa i buchi
    if t < T_STOP: xb = XB; pb = walking(t, 1.5)
    elif t < T_FIX0: xb = XB - (XB - (bx + 135)) * ease(seg(t, T_STOP, T_FIX0)); pb = walk(t * 7, 18)
    elif t < T_ANS: xb = bx + 135; pb = REACH
    else: xb = bx + 135; pb = mix(REACH, STAND, seg(t, T_ANS, T_ANS + 0.3))
    skb = draw_fig(dl, on_ground(xb, G, pb, K), pb, BLUE, -1 if t >= T_STOP else 1, 0, K)
    if t < T_STOP:
        hb = skb["hr"]; bucket(d, dl, hb[0] + 6, hb[1] + 26, 0.92, BLUE)
    else:
        bucket(d, dl, XB + 120, G - 112, 0.92, BLUE)             # il suo secchio, posato a terra
    # fumetti
    for s, a, b, fx, fy in C["fumetti"]:
        al = ease(seg(t, a, a + 0.15)) * (1 - ease(seg(t, b - 0.15, b)))
        late.append((fx, fy, s, al))
    # testi
    if t < T_ANS:
        phrase(d, [(C["frase1"][0], WHITE), (C["frase1"][1], BLUE)])
    else:
        phrase(d, [(C["frase2"][0], WHITE), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, size=C.get("size2", 48), cps=55)
        al = ease(seg(t, T_ANS + 0.6, T_ANS + 0.9))
        if al > 0:
            c = tuple(int(BG[i] + (215 - BG[i]) * al) for i in range(3))
            for n, s in enumerate(C["invito"]):
                fnt = font(38); d.text(((W - text_w(s, fnt)) / 2, 450 + n * 48), s, font=fnt, fill=c)
    watermark(d)
    out = glow(img, lit, 22, 1.0); do = ImageDraw.Draw(out)
    for fx, fy, s, al in late: bubble(do, fx, fy, s, 36, al)
    return out

if __name__ == "__main__":
    S = C.get("velocita", 1.0)
    if len(sys.argv) > 3:
        frame(float(sys.argv[3]) * S).save(OUT); sys.exit()
    render(OUT, DUR / S, lambda t: frame(t * S))
    ev = [(0.0, s_hum(DUR, 0.03)), (0.0, s_chime(0.25, 1320))]
    k = 0.0
    while k < T_STOP: ev.append((k, s_tok(120, 0.04, 0.2))); k += 0.45          # passi
    for name, th, dx, dy in HOLES:
        ev.append((th, s_pop(0.35, 500)))
        q = th + 0.25
        while q < min(DUR, T_FIX0 + T_FIXD * (HOLES.index([name, th, dx, dy]) + 1)):
            ev.append((q, s_click(0.18))); q += 0.23                             # monete che tintinnano
    for i in range(len(HOLES)): ev.append((T_FIX0 + T_FIXD * (i + 1) - 0.05, s_tok(260, 0.06, 0.4)))
    for s, a, b, fx, fy in C["fumetti"]: ev.append((a, s_pop(0.3)))
    ev += [(T_STOP, s_thud(0.4, 80)), (T_ANS - 0.3, s_rise(2.2, 0.45)), (T_ANS + 0.05, s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 55, s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mixdown(DUR / S, [(a / S, x) for a, x in ev], wav); mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
