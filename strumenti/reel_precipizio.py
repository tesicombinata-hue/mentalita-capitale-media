#!/usr/bin/env python3
"""Reel B "Il precipizio" (stile 3D, camera in movimento) – Mentalità Capitale, 26/11.

Una massa in giacca e cravatta cammina verso la camera, tra cartelloni "-50%", "RATA 0%", "COMPRA ORA". Lui (cravatta
blu, "TU") si ferma; gli altri lo superano. La camera si alza e arretra: la strada finisce in un precipizio e la massa
ci cade dentro, una fila dopo l'altra. Chi spinge da dietro trascina lui fino al bordo: barcolla. Si gira, risale
controcorrente in mezzo alla folla, esce di lato. Dall'alto: la fila che si getta nel vuoto e lui, da solo, su un
sentiero che porta alla città accesa.
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
V = 1.0                                   # velocità della massa (m/s), verso la camera (z che diminuisce)
COLS = [-2.7, -1.8, -0.9, 0.0, 0.9, 1.8, 2.7]
ROWS = 46
random.seed(21)
HE_Z0 = 5.0                               # lui parte a 5 m dal bordo, colonna centrale, prima fila
CROWD = [(cx + random.uniform(-0.18, 0.18), HE_Z0 + j * 1.05 + random.uniform(-0.15, 0.25), random.uniform(0, 6.28), random.uniform(0.93, 1.07))
         for j in range(ROWS) for cx in COLS if not (j == 0 and cx == 0.0)]
T_STOP = 1.9
T_REV0, T_REV1 = 3.2, 5.0                 # la camera si alza: il precipizio
T_PUSH0, T_PUSH1 = 5.0, 6.2               # la folla lo spinge fino al bordo
T_EDGE0, T_EDGE1 = 6.2, 7.3               # barcolla sul bordo (primo piano)
T_BACK0, T_BACK1 = 7.3, 8.6               # risale controcorrente
T_SIDE0, T_SIDE1 = 8.6, 9.3               # esce di lato
T_ANS = 9.4
BILLS = C["cartelloni"]                   # [testo, x, z]

def he_state(t):
    """posizione (x, z), posa, rotazione di lui."""
    zs = HE_Z0 - V * min(t, T_STOP)
    if t < T_STOP:
        return 0.0, zs, dict(facing="front", tie=BLUE, **walk_pose(t * 6.5))
    if t < T_PUSH0:
        look = math.sin((t - T_STOP) * 3) * 0.8
        return 0.0, zs, dict(facing="front", tie=BLUE, look=round(look, 1))
    if t < T_PUSH1:
        k = ease((t - T_PUSH0) / (T_PUSH1 - T_PUSH0))
        z = zs + (0.25 - zs) * k
        return 0.0, z, dict(facing="front", tie=BLUE, arml=35.0, armr=35.0, mouth=1, legl=round(0.05 * (math.sin(t * 14) > 0), 2))
    if t < T_EDGE1:
        p = (t - T_EDGE0) * 9
        return 0.0, 0.25, dict(facing="front", tie=BLUE, arml=round(110 + 50 * math.sin(p), 0), armr=round(110 - 50 * math.sin(p), 0), mouth=1)
    if t < T_BACK1:
        k = ease((t - T_BACK0) / (T_BACK1 - T_BACK0))
        return 0.0, 0.25 + 3.2 * k, dict(facing="back", **walk_pose(t * 7))
    if t < T_SIDE1:
        k = ease((t - T_SIDE0) / (T_SIDE1 - T_SIDE0))
        return -4.8 * k, 3.45, dict(facing="back", **walk_pose(t * 7))
    k = min(1.0, (t - T_SIDE1) / 2.5)
    return -4.8 - 1.6 * k, 3.45 + 3.0 * k, dict(facing="back", **walk_pose(t * 6))

def camera(t):
    hx, hz, _ = he_state(t)
    if t < T_STOP:
        return Cam(0.0, 1.1, hz - 4.0, 1040)
    if t < T_REV0:
        k = ease((t - T_STOP) / (T_REV0 - T_STOP))
        z0 = HE_Z0 - V * T_STOP
        return Cam(0.0, 1.1 + 0.25 * k, z0 - 4.0 + 0.8 * k, lerp(1040, 860, k))
    if t < T_PUSH1:
        k = ease((t - T_REV0) / (T_REV1 - T_REV0))
        z0 = HE_Z0 - V * T_STOP
        return Cam(0.0, lerp(1.35, 6.5, k), lerp(z0 - 3.2, -8.5, k), lerp(860, 560, k))
    if t < T_EDGE1:                                    # stacco: primo piano dal basso, dal vuoto
        k = (t - T_EDGE0) / (T_EDGE1 - T_EDGE0)
        return Cam(0.15 * math.sin(t * 2), lerp(0.55, 0.45, k), lerp(-2.6, -2.3, k), 1260)
    if t < T_SIDE1:                                    # lo segue alle spalle
        return Cam(lerp(0, hx, 0.85), 1.7, hz - 3.6 - (0 if t < T_SIDE0 else 0.8 * ease((t - T_SIDE0) / 0.7)), 880)
    k = ease((t - T_SIDE1) / 2.0)                      # gru: vista dall'alto
    return Cam(lerp(hx * 0.85, -3.0, k), lerp(1.7, 13.0, k), lerp(hz - 4.4, -13.0, k), lerp(880, 430, k))

def crowd_pos(t, x0, z0, ph, sp):
    """La massa: cammina verso z=0, poi cade. Chi è dietro a lui lo aggira dopo che si è fermato."""
    z = z0 - V * sp * t
    x = x0
    if t >= T_STOP and abs(x0) < 0.3:
        hx, hz, _ = he_state(t)
        if hz < z < hz + 1.4 and t < T_BACK0:              # lo aggirano
            x = x0 + (0.55 if (int(z0 * 7) % 2) else -0.55)
        if T_BACK0 <= t < T_SIDE0 and abs(z - hz) < 0.8:
            x = x0 + (0.6 if (int(z0 * 7) % 2) else -0.6)
    return x, z

def background(cam):
    img = Image.new("RGBA", (W, H), (10, 10, 13, 255)); d = ImageDraw.Draw(img)
    # pavimento: fasce di profondità, più chiare vicino (luce dall'alto), nebbia lontano
    zs = [0] + [0.5 * 1.25 ** i for i in range(30)]
    for za, zb in zip(zs if cam.y > 0 else [], zs[1:]):
        a = cam.proj(0, 0, max(za, cam.z + 0.2)); b = cam.proj(0, 0, zb)
        if a is None or b is None: continue
        zm = (za + zb) / 2; fog = math.exp(-zm / 30)
        c = int(18 + 52 * fog)
        d.rectangle([0, min(a[1], b[1]), W, max(a[1], b[1])], fill=(c, c, c + 4, 255))
    e = cam.proj(0, 0, 0)
    if e is not None:
        d.line([(0, e[1]), (W, e[1])], fill=(150, 150, 158, 255), width=max(2, int(e[2] * 0.03)))
        # parete del precipizio
        e2 = cam.proj(0, -8, 0)
        if e2 and e2[1] > e[1] + 2:
            for i in range(12):                    # parete di roccia che sfuma nel buio
                y0 = e[1] + 2 + (e2[1] - e[1]) * i / 12; y1 = e[1] + 2 + (e2[1] - e[1]) * (i + 1) / 12
                c = int(46 - 3 * i); d.rectangle([0, y0, W, y1], fill=(c, c, c + 3, 255))
    # luce dall'alto sulla strada (alone)
    return img

def bill(d, cam, s, x, z):
    p0 = cam.proj(x, 0, z); p1 = cam.proj(x, 3.4, z)
    if not p0 or not p1: return
    sc = p0[2]; w = 2.4 * sc; h = 1.0 * sc
    d.line([(p0[0], p0[1]), (p1[0], p1[1])], fill=(70, 70, 78), width=max(2, int(0.12 * sc)))
    x0, y0 = p1[0] - w / 2, p1[1] - h
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(235, 235, 238), outline=(40, 40, 46), width=max(1, int(0.05 * sc)))
    fs = int(h * 0.55)
    if fs >= 6:
        fnt = mc.font(fs, mc.INTER)
        d.text((p1[0] - mc.text_w(s, fnt) / 2, y0 + h * 0.16), s, font=fnt, fill=(20, 20, 24))

def frame(t):
    cam = camera(t)
    img = background(cam); d = ImageDraw.Draw(img)
    hx, hz, hpose = he_state(t)
    items = []                                         # (z, tipo, dati)
    for (x0, z0, ph, sp) in CROWD:
        x, z = crowd_pos(t, x0, z0, ph, sp)
        if z < 0:                                      # cade
            tf = -z / (V * sp)
            y = -4.9 * tf * tf; zz = -0.5 * tf
            if y < -25: continue
            if T_EDGE0 <= t < T_EDGE1 and abs(x) < 1.4: continue
            items.append((zz, "fall", (x, y, zz, min(55, tf * 110), ph)))
        else:
            items.append((z, "man", (x, z, ph)))
    for s, bx, bz in BILLS: items.append((bz, "bill", (s, bx, bz)))
    items.append((hz, "he", None))
    if t >= T_SIDE1 - 0.3:                             # sentiero illuminato verso la città
        for i in range(30):
            pz = 3.6 + i * 1.6; px = -5.2 - i * 0.55
            items.append((pz, "lamp", (px, pz)))
    items.sort(key=lambda it: -it[0])
    hhead = None
    for z, kind, data in items:
        if kind == "man":
            x, zz, ph = data
            if T_EDGE0 <= t < T_EDGE1 and zz < hz + 0.6 and abs(x) < 1.0: continue
            shadow(d, cam, x, zz)
            place(img, cam, x, 0, zz, dict(facing="front", **walk_pose(t * 6.5 + ph)))
        elif kind == "fall":
            x, y, zz, rot, ph = data
            place(img, cam, x, y, zz, dict(facing="front", arml=150.0, armr=150.0, mouth=1), rot=-rot if ph > 3.14 else rot)
        elif kind == "bill":
            bill(d, cam, *data)
        elif kind == "lamp":
            px, pz = data; p = cam.proj(px, 0, pz)
            if p:
                r = max(2, 0.12 * p[2]); a = ease((t - T_SIDE1 + 0.3) / 1.5)
                d.ellipse([p[0] - r, p[1] - r * 0.5, p[0] + r, p[1] + r * 0.5], fill=tuple(int(v * a + 20 * (1 - a)) for v in BLUE) + (255,))
        else:
            shadow(d, cam, hx, hz)
            if t >= T_EDGE1:                                # alone blu sotto di lui: si riconosce anche di spalle
                a_ = cam.proj(hx - 0.6, 0, hz); b_ = cam.proj(hx + 0.6, 0, hz)
                if a_ and b_:
                    hh = (b_[0] - a_[0]) * 0.25
                    d.ellipse([a_[0], a_[1] - hh, b_[0], a_[1] + hh], fill=(40, 90, 150, 255))
            rot = 9 * math.sin((t - T_EDGE0) * 7) if T_EDGE0 <= t < T_EDGE1 else 0
            r = place(img, cam, hx, 0, hz, hpose, rot=rot)
            if r: hhead = r
    # città accesa in fondo a sinistra (finale)
    if t >= T_SIDE1:
        a = ease((t - T_SIDE1) / 1.5)
        rng = random.Random(3)
        for i in range(90):
            bx, bz, bh = -28 + rng.uniform(-8, 8), 52 + rng.uniform(-4, 6), rng.uniform(1, 9)
            p = cam.proj(bx, bh, bz)
            if p and rng.random() < a:
                s = max(2, 0.4 * p[2]); col = BLUE if rng.random() < 0.6 else (220, 225, 240)
                d.rectangle([p[0], p[1], p[0] + s, p[1] + s * 1.3], fill=col + (255,))
    out = img.convert("RGB")
    # luce: vignetta e bagliore dei blu
    arr = np.asarray(out).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.55 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.55) / (H * 0.7)) ** 2, 0, 1)
    out = Image.fromarray(np.clip(arr * vig[..., None], 0, 255).astype(np.uint8))
    dd = ImageDraw.Draw(out)
    # "TU" sopra di lui
    if hhead and (t < T_REV0 or T_PUSH0 <= t < T_EDGE0):
        al = ease(t / 0.2) * (1 - ease((t - (T_REV0 - 0.3)) / 0.3)) if t < T_REV0 else ease((t - T_PUSH0) / 0.2) * (1 - ease((t - T_EDGE0 + 0.2) / 0.2))
        mc.bubble(dd, hhead[0], hhead[1] - 40, "TU", 34, al)
    for s, a, b, kind in C["fumetti"]:
        al = ease((t - a) / 0.15) * (1 - ease((t - (b - 0.15)) / 0.15))
        if al <= 0: continue
        if kind == "lui" and hhead: mc.bubble(dd, hhead[0], hhead[1] - 40, s, 36, al)
        elif kind != "lui": mc.bubble(dd, kind[0], kind[1], s, 36, al)
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
    if T_EDGE0 - 0.06 <= t < T_EDGE0 + 0.06 or T_EDGE1 - 0.06 <= t < T_EDGE1 + 0.06:      # stacchi
        out = Image.blend(out, Image.new("RGB", (W, H), (0, 0, 0)), 0.6)
    return out

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    mc.render(OUT, DUR, frame)
    ev = [(0.0, mc.s_hum(DUR, 0.04))]
    k = 0.0
    while k < T_EDGE0:                                  # passi della massa
        ev.append((k, mc.s_thud(0.3, 55))); k += math.pi / 6.5
    for s, a, b, kind in C["fumetti"]: ev.append((a, mc.s_pop(0.3)))
    ev += [(T_STOP, mc.s_thud(0.6, 90)), (T_REV0, mc.s_whoosh(1.6, 0.5)), (T_REV0 + 0.9, mc.s_rise(1.6, 0.25, 110, 160))]
    for k in range(6): ev.append((T_REV0 + 0.8 + k * 0.6, mc.s_whoosh(0.5, 0.25, False)))
    ev += [(T_PUSH0, mc.s_crack(0.4)), (T_EDGE0, mc.s_thud(0.8, 70)), (T_EDGE0 + 0.2, mc.s_crack(0.6))]
    for k in range(4): ev.append((T_EDGE0 + 0.1 + k * 0.28, mc.s_thud(0.35, 60)))
    ev += [(T_BACK0, mc.s_whoosh(0.6, 0.4)), (T_SIDE0, mc.s_whoosh(0.5, 0.3)), (T_ANS - 0.3, mc.s_rise(2.4, 0.45)), (T_ANS + 0.05, mc.s_chime(0.4))]
    for k in range(len(C["frase2"][0] + C["frase2"][1])): ev.append((T_ANS + k / 50, mc.s_type(0.1)))
    wav = OUT.replace(".mp4", "_audio.wav"); tmp = OUT.replace(".mp4", "_muto.mp4")
    os.rename(OUT, tmp); mc.mixdown(DUR, ev, wav); mc.mux(tmp, wav, OUT); os.remove(tmp); os.remove(wav)
    print("ok", OUT)
