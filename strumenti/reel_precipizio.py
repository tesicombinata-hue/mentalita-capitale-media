#!/usr/bin/env python3
"""Reel B "Il precipizio" v2 (stile 3D, camera in movimento) – Mentalità Capitale, 26/11.

Una massa ordinata in giacca e cravatta cammina verso la camera tra cartelloni "-50%", "RATA 0%", "COMPRA ORA".
Lui (cravatta blu, "TU") cammina nella colonna più esterna a destra. Entro 2 s la camera sale e mostra tutta la folla.
Torna su di lui; davanti la strada finisce: la massa cade nel precipizio, fila dopo fila. Lui esce di lato dalla fila
(è sul bordo esterno: non attraversa nessuno), si ferma a un passo dal vuoto, si gira e cammina nella direzione
opposta: sotto i suoi piedi compaiono piastrelle d'oro, la strada giusta.
Uso: python3 reel_precipizio.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from motore_3d import *
import motore_mc as mc

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C.get("durata", 12.0)
BLUE = (77, 163, 255)
GOLD, GOLD_HI, GOLD_LO = (225, 178, 55), (255, 222, 120), (150, 108, 25)
V = 1.3                                   # velocità della massa (m/s), verso la camera
GAPX, GAPZ = 0.95, 1.15
COLS = [round(-3 * GAPX + i * GAPX, 2) for i in range(7)]      # -2.85 … 2.85
HX0 = COLS[-1]                            # lui: colonna esterna a destra
HE_Z0 = 8.0                               # lui è in testa alla sua colonna (la più esterna)
FRONT_Z = HE_Z0
ROWS = 60
random.seed(21)
CROWD = [(cx + random.uniform(-0.05, 0.05), FRONT_Z + j * GAPZ + random.uniform(-0.05, 0.05), random.uniform(0, 6.28))
         for j in range(-4, ROWS) for cx in COLS if not (cx == HX0 and j <= 0)]

T_OUT0, T_OUT1 = 4.15, 4.95               # esce di lato dalla fila rallentando
T_LOOKL = 5.5                             # guarda a sinistra: la massa che cade
T_LOOKR = 6.0                             # guarda indietro la fila: dubbio
T_BACKSTEP = 6.45                         # mezzo passo verso la fila
T_TURN = 6.95                             # decide: si gira (stacco sull'inquadratura laterale)
T_WALK = 7.1
T_ANS = 9.6
X_OUT = HX0 + 1.5
TILE = 0.62
SPEED = 1.05

def z_stop():
    return HE_Z0 - V * T_OUT0 - V * (T_OUT1 - T_OUT0) * 0.5

def he_state(t):
    """(x, z, direzione del corpo (hx, hz), posa senza facing)."""
    if t < T_OUT0:
        return HX0, HE_Z0 - V * t, (0, -1), dict(tie=BLUE, **walk_pose(t * 6.5))
    z_out0 = HE_Z0 - V * T_OUT0
    zs = z_stop()
    if t < T_OUT1:
        k = (t - T_OUT0) / (T_OUT1 - T_OUT0)
        z = z_out0 - V * (T_OUT1 - T_OUT0) * (k - k * k / 2)
        x = HX0 + (X_OUT - HX0) * ease(k)
        return x, z, (0, -1), dict(tie=BLUE, look=0.4, **walk_pose(t * 6.5))
    if t < T_LOOKL:                                       # guarda la massa che cade, spaventato
        return X_OUT, zs, (0, -1), dict(tie=BLUE, look=-0.9, mouth=1, arml=22.0, armr=22.0)
    if t < T_LOOKR:                                       # si volta verso la fila: e se avessero ragione?
        return X_OUT, zs, (0, -1), dict(tie=BLUE, look=0.9, arml=12.0, armr=12.0)
    if t < T_BACKSTEP:                                    # mezzo passo verso la fila, incerto
        k = ease((t - T_LOOKR) / (T_BACKSTEP - T_LOOKR))
        pose = walk_pose((t - T_LOOKR) * 7) if k < 0.95 else {}
        return X_OUT - 0.5 * k, zs, (0, -1), dict(tie=BLUE, look=0.6, **pose)
    if t < T_TURN:                                        # si ferma, scuote la testa
        lk = round(0.8 * math.sin((t - T_BACKSTEP) * 22), 1)
        return X_OUT - 0.5, zs, (0, -1), dict(tie=BLUE, look=lk, arml=10.0, armr=10.0)
    tw = t - T_WALK
    if tw < 0:
        return X_OUT - 0.5, zs, (0, 1), dict(tie=BLUE)
    x = X_OUT - 0.5 + 0.5 * ease(tw / 0.6)                # torna sul suo lato e cammina
    return x, zs + SPEED * tw, (0, 1), dict(tie=BLUE, **walk_pose(tw * 6.5 + 1.57))

def camera(t):
    hx, hz, _, _ = he_state(t)
    zs = z_stop()
    keys = [
        (0.0, HX0 + 0.5, 1.2, HE_Z0 - 4.0, 1040),
        (0.8, HX0 + 0.5, 1.4, HE_Z0 - V * 0.8 - 4.0, 1010),
        (2.0, 0.6, 7.5, -2.2, 330),                    # gru: tutta la folla
        (3.0, 0.4, 7.8, -2.4, 320),
        (3.9, HX0 + 0.9, 1.5, HE_Z0 - V * 3.9 - 3.6, 1000),   # di nuovo su di lui, dal lato esterno
        (4.6, HX0 + 0.6, 2.6, -4.6, 820),              # si apre: il precipizio
        (5.2, X_OUT - 0.4, 1.6, zs - 2.8, 1010),       # primo piano: il dubbio
        (T_TURN, X_OUT - 0.5, 1.6, zs - 2.6, 1010),
    ]
    if t < T_TURN:
        return cam_keys(t, keys)
    # inquadratura laterale da destra: lo si vede di profilo che va nella direzione opposta alla massa
    cz = hz - 0.4
    if t < T_ANS - 0.3:
        return Cam(X_OUT + 4.2, 1.45, cz, 1020, yaw=-90)
    k = ease((t - (T_ANS - 0.3)) / 2.2)
    return Cam(X_OUT + lerp(4.2, 6.0, k), lerp(1.45, 3.6, k), cz + 0.5 * k, lerp(1020, 820, k), yaw=-90)

def background(cam):
    img = Image.new("RGBA", (W, H), (10, 10, 13, 255)); d = ImageDraw.Draw(img)
    if cam.y > 0:                                       # pavimento: fasce di profondità (vale per ogni direzione)
        ds = [0.7 * 1.22 ** i for i in range(34)]
        for da, db in zip(ds, ds[1:]):
            ya = cam.hz + cam.f * cam.y / da; yb = cam.hz + cam.f * cam.y / db
            fog = math.exp(-(da + db) / 60)
            c = int(18 + 52 * fog)
            d.rectangle([0, min(ya, yb), W, max(ya, yb)], fill=(c, c, c + 4, 255))
    if cam.yaw != 0:
        xn, xf = cam.x - 1.0, cam.x - 120
        pts = [cam.proj(xn, 0, 0), cam.proj(xf, 0, 0), cam.proj(xf, 0, -150), cam.proj(xn, 0, -150)]
        if all(pts):
            d.polygon([(p[0], p[1]) for p in pts], fill=(9, 9, 11, 255))
            d.line([(pts[0][0], pts[0][1]), (pts[1][0], pts[1][1])], fill=(165, 165, 172, 255), width=4)
        return img
    if cam.z + 0.7 > 0:                                 # la camera è sopra la strada: niente bordo davanti
        return img
    e = cam.proj(0, 0, 0)
    if e is not None:
        e2 = cam.proj(0, -8, 0)
        if e2 and e2[1] > e[1] + 2:
            for i in range(12):
                y0 = e[1] + 2 + (e2[1] - e[1]) * i / 12; y1 = e[1] + 2 + (e2[1] - e[1]) * (i + 1) / 12
                c = int(44 - 3 * i); d.rectangle([0, y0, W, y1], fill=(c, c, c + 3, 255))
        d.line([(0, e[1]), (W, e[1])], fill=(165, 165, 172, 255), width=max(2, int(e[2] * 0.03)))
    return img

def bill(d, cam, s, x, z):
    p0 = cam.proj(x, 0, z); p1 = cam.proj(x, 3.4, z)
    if not p0 or not p1: return
    sc = p0[2]; w = 2.4 * sc; h = 1.0 * sc
    if w > 2000: return
    d.line([(p0[0], p0[1]), (p1[0], p1[1])], fill=(70, 70, 78), width=max(2, int(0.12 * sc)))
    x0, y0 = p1[0] - w / 2, p1[1] - h
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(235, 235, 238), outline=(40, 40, 46), width=max(1, int(0.05 * sc)))
    fs = int(h * 0.55)
    if fs >= 6:
        fnt = mc.font(fs, mc.INTER)
        d.text((p1[0] - mc.text_w(s, fnt) / 2, y0 + h * 0.16), s, font=fnt, fill=(20, 20, 24))

def tiles(d, lit, cam, t):
    """Piastrelle d'oro sotto i suoi passi dopo che si è girato."""
    if t < T_WALK: return
    hx, hz, _, _ = he_state(t)
    z0 = z_stop() - TILE / 2
    n = int((hz - z0) / TILE) + 2
    for i in range(n):
        zc = z0 + i * TILE
        born = T_WALK + (zc - z0) / SPEED - 0.1
        k = ease((t - born) / 0.35)
        if k <= 0: continue
        s = TILE * 0.47 * (0.6 + 0.4 * k)
        pts = [cam.proj(X_OUT + dx, 0.005, zc + dz) for dx, dz in ((-s, -s), (s, -s), (s, s), (-s, s))]
        if any(p is None for p in pts): continue
        q = [(p[0], p[1]) for p in pts]
        col = tuple(int(c * k + 30 * (1 - k)) for c in GOLD)
        d.polygon(q, fill=col + (255,), outline=GOLD_LO + (255,))
        # riflesso
        hi = [q[3], q[2], ((q[2][0] + q[1][0]) / 2, (q[2][1] + q[1][1]) / 2), ((q[3][0] + q[0][0]) / 2, (q[3][1] + q[0][1]) / 2)]
        d.polygon(hi, fill=tuple(int(c * k + 30 * (1 - k)) for c in GOLD_HI) + (255,))
        lit.polygon(q, fill=tuple(int(c * 0.35 * k) for c in GOLD))

def frame(t):
    cam = camera(t)
    img = background(cam); d = ImageDraw.Draw(img)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); dg = ImageDraw.Draw(glow)
    tiles(d, dg, cam, t)
    hx, hz, hdir, hpose = he_state(t)
    hpose = dict(hpose, facing=cam.facing(*hdir))
    cf = cam.facing(0, -1)
    items = []
    for (x0, z0, ph) in CROWD:
        z = z0 - V * t
        if z < 0:
            tf = -z / V
            y = -4.9 * tf * tf; zz = -0.45 * tf
            if y < -30: continue
            items.append((cam.depth(x0, zz), "fall", (x0, y, zz, min(50, tf * 100), ph)))
        else:
            items.append((cam.depth(x0, z), "man", (x0, z, ph)))
    for s, bx, bz in C["cartelloni"]: items.append((cam.depth(bx, bz), "bill", (s, bx, bz)))
    items.append((cam.depth(hx, hz), "he", None))
    items.sort(key=lambda it: -it[0])
    hhead = None
    for z, kind, data in items:
        if kind == "man":
            x, zz, ph = data
            shadow(d, cam, x, zz)
            place(img, cam, x, 0, zz, dict(facing=cf, **walk_pose(t * 6.5 + ph)))
        elif kind == "fall":
            x, y, zz, rot, ph = data
            place(img, cam, x, y, zz, dict(facing=cf, arml=150.0, armr=150.0, mouth=1), rot=-rot if ph > 3.14 else rot)
        elif kind == "bill":
            bill(d, cam, *data)
        else:
            shadow(d, cam, hx, hz)
            r = place(img, cam, hx, 0, hz, hpose)
            if r: hhead = r
    out = img.convert("RGB")
    arr = np.asarray(out).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.5 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.55) / (H * 0.7)) ** 2, 0, 1)
    out = Image.fromarray(np.clip(arr * vig[..., None], 0, 255).astype(np.uint8))
    if t >= T_TURN: out = mc.glow(out, glow, 26, 1.2)
    dd = ImageDraw.Draw(out)
    if hhead and t < 1.0:
        mc.bubble(dd, hhead[0], hhead[1] - 40, "TU", 34, ease(t / 0.2) * (1 - ease((t - 0.8) / 0.2)))
    for s, a, b, where in C["fumetti"]:
        al = ease((t - a) / 0.15) * (1 - ease((t - (b - 0.15)) / 0.15))
        if al <= 0: continue
        if where == "lui":
            if hhead: mc.bubble(dd, hhead[0], hhead[1] - 40, s, 36, al)
        else: mc.bubble(dd, where[0], where[1], s, 36, al)
    if t < T_ANS:
        mc.phrase(dd, [(C["frase1"][0], (240, 240, 240)), (C["frase1"][1], BLUE)], size=C.get("size1", 58))
    else:
        mc.phrase(dd, [(C["frase2"][0], (240, 240, 240)), (C["frase2"][1], BLUE)], t0=T_ANS, t=t, size=C.get("size2", 50), cps=50)
        al = ease((t - T_ANS - 0.8) / 0.3)
        if al > 0:
            c = tuple(int(10 + (215 - 10) * al) for _ in range(3))
            for n, s in enumerate(C["invito"]):
                fnt = mc.font(38); dd.text(((W - mc.text_w(s, fnt)) / 2, 470 + n * 48), s, font=fnt, fill=c)
    mc.watermark(dd)
    return out

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    mc.render(OUT, DUR, frame)
    ev = [(0.0, mc.s_hum(DUR, 0.04))]
    k = 0.0
    while k < DUR:                                       # passi della massa
        ev.append((k, mc.s_thud(0.25 if k < T_TURN else 0.12, 55))); k += math.pi / 6.5
    for s, a, b, where in C["fumetti"]: ev.append((a, mc.s_pop(0.3)))
    ev += [(0.0, mc.s_pop(0.35, 900)), (0.8, mc.s_whoosh(1.2, 0.45)), (3.0, mc.s_whoosh(0.9, 0.35, False)),
           (3.9, mc.s_rise(1.5, 0.25, 110, 160)), (4.4, mc.s_whoosh(1.2, 0.45))]
    for k in range(8): ev.append((4.5 + k * 0.55, mc.s_whoosh(0.45, 0.22, False)))
    ev += [(T_OUT1, mc.s_thud(0.6, 80)), (T_LOOKR, mc.s_whoosh(0.4, 0.2)), (T_TURN, mc.s_whoosh(0.6, 0.4))]
    for k in range(4): ev.append((T_BACKSTEP + k * 0.12, mc.s_click(0.12)))
    tw = 0.0
    while T_WALK + tw < DUR - 0.3:                 # ogni piastrella d'oro: un rintocco
        ev.append((T_WALK + tw, mc.s_chime(0.18, 1320 + 60 * int(tw / TILE * 1.05) % 400)))
        tw += TILE / 1.05
    ev += [(T_ANS - 0.3, mc.s_rise(2.4, 0.45)), (T_ANS + 0.05, mc.s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 50, mc.s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mc.mixdown(DUR, ev, wav); mc.mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
