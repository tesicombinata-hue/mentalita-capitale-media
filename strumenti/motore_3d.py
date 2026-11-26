#!/usr/bin/env python3
"""Motore "3D" dei Reel di Mentalità Capitale (26/11): omini in giacca e cravatta con volume (testa sferica ombreggiata,
giacca con lato in luce e lato in ombra, contorni scuri), visti di fronte o di spalle, proiettati con una camera
prospettica che si muove (carrellata, gru, panoramica). Stile ispirato ai reel animati in scala di grigi con un solo
colore di accento.

Coordinate del mondo in metri: x a destra, y in alto, z in profondità (lontano dalla camera = z grande).
"""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
SPR_H = 420                       # altezza dello sprite di base in pixel (1,8 m + margini)
PM = 200                          # pixel per metro nello sprite
OUTL = (32, 32, 38)
SUIT_L, SUIT_M, SUIT_D = (176, 176, 184), (150, 150, 158), (118, 118, 126)
PANTS, SHOE = (92, 92, 100), (40, 40, 46)
SKIN_HI, SKIN_LO = (252, 252, 252), (170, 172, 180)

# ---------------- camera ----------------
class Cam:
    def __init__(self, x, y, z, hz, f=1100):
        self.x, self.y, self.z, self.hz, self.f = x, y, z, hz, f
    def proj(self, x, y, z):
        d = z - self.z
        if d <= 0.6: return None
        return (W / 2 + self.f * (x - self.x) / d, self.hz - self.f * (y - self.y) / d, self.f / d)

def lerp(a, b, k): return a + (b - a) * k
def ease(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

def cam_keys(t, keys):
    """keys: lista di (t, x, y, z, hz). Interpolazione morbida; un tempo ripetuto = stacco."""
    if t <= keys[0][0]: return Cam(*keys[0][1:])
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t < b[0]:
            if b[0] - a[0] < 1e-6: return Cam(*b[1:])
            k = ease((t - a[0]) / (b[0] - a[0]))
            return Cam(*[lerp(p, q, k) for p, q in zip(a[1:], b[1:])])
    return Cam(*keys[-1][1:])

# ---------------- sprite dell'omino ----------------
def _sphere(r):
    s = 2 * r + 4
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    cx = cy = s / 2
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    lx, ly = (xx - cx + r * 0.35) / r, (yy - cy + r * 0.4) / r
    l = np.clip(1 - np.sqrt(lx ** 2 + ly ** 2) * 0.55, 0, 1)
    rgb = np.zeros((s, s, 4), np.uint8)
    for i in range(3):
        rgb[..., i] = (SKIN_LO[i] + (SKIN_HI[i] - SKIN_LO[i]) * l).astype(np.uint8)
    rgb[..., 3] = (np.clip((1 - d) * r, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGBA")

def _pt(x, y):
    return (SPR_W / 2 + x * PM, SPR_H - 12 - y * PM)

SPR_W = 300

def _limb(d, a, b, w, col):
    d.line([a, b], fill=OUTL, width=int(w + 6))
    d.line([a, b], fill=col, width=int(w))
    for p in (a, b):
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)

@lru_cache(maxsize=4096)
def sprite(facing="front", legl=0.0, legr=0.0, arml=8.0, armr=8.0, look=0.0, tie=(60, 60, 66), lean=0.0, mouth=0):
    """facing: front/back. legl/legr: sollevamento del piede (m). arml/armr: angolo del braccio dal basso (gradi, + verso
    l'esterno/alto). look: -1..1 sposta gli occhi. lean: inclinazione del busto (gradi)."""
    im = Image.new("RGBA", (SPR_W, SPR_H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    front = facing == "front"
    # gambe
    for sx, lift in ((-0.1, legl), (0.1, legr)):
        hip = _pt(sx, 0.95); foot = _pt(sx * 1.05, 0.1 + lift)
        _limb(d, hip, foot, 0.16 * PM, PANTS)
        fx, fy = foot; sw = 0.13 * PM; sh = 0.07 * PM * (1.3 if front else 1.0)
        d.ellipse([fx - sw - 3, fy - sh + 6, fx + sw + 3, fy + sh + 12], fill=OUTL)
        d.ellipse([fx - sw, fy - sh + 8, fx + sw, fy + sh + 9], fill=SHOE)
    # busto (con inclinazione)
    def T(x, y):
        a = math.radians(lean); y0 = 0.95
        return _pt(x * math.cos(a) + (y - y0) * math.sin(a), y0 + (y - y0) * math.cos(a) - x * math.sin(a) * 0)
    sh_l, sh_r = T(-0.28, 1.46), T(0.28, 1.46)
    hp_l, hp_r = T(-0.23, 0.86), T(0.23, 0.86)
    mid_t, mid_b = T(0, 1.46), T(0, 0.86)
    d.polygon([sh_l, sh_r, hp_r, hp_l], fill=OUTL)
    inset = 4
    d.polygon([(sh_l[0] + inset, sh_l[1] + inset), (mid_t[0], mid_t[1] + inset), (mid_b[0], mid_b[1] - inset), (hp_l[0] + inset, hp_l[1] - inset)], fill=SUIT_L if front else SUIT_M)
    d.polygon([(mid_t[0], mid_t[1] + inset), (sh_r[0] - inset, sh_r[1] + inset), (hp_r[0] - inset, hp_r[1] - inset), (mid_b[0], mid_b[1] - inset)], fill=SUIT_M if front else SUIT_D)
    if front:
        v1, v2, v3 = T(-0.1, 1.45), T(0.1, 1.45), T(0, 1.18)
        d.polygon([v1, v2, v3], fill=(235, 235, 238))
        t1, t2, t3, t4 = T(-0.035, 1.43), T(0.035, 1.43), T(0.05, 1.1), T(-0.05, 1.1)
        d.polygon([t1, t2, (t3[0], t3[1]), (0.5 * (t3[0] + t4[0]), t3[1] + 10), t4], fill=tie, outline=OUTL)
        d.line([v1, v3], fill=OUTL, width=3); d.line([v2, v3], fill=OUTL, width=3)
        for by in (1.02, 0.93):
            b = T(0, by); d.ellipse([b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4], fill=OUTL)
    else:
        d.line([T(0, 1.4), T(0, 0.88)], fill=OUTL, width=3)
        c = T(0, 1.46); d.rectangle([c[0] - 0.1 * PM, c[1] - 2, c[0] + 0.1 * PM, c[1] + 10], fill=(225, 225, 228))
    # braccia
    for side, ang in ((-1, arml), (1, armr)):
        sh = T(0.26 * side, 1.4)
        a = math.radians(ang)
        el = (sh[0] + side * math.sin(a) * 0.27 * PM, sh[1] + math.cos(a) * 0.27 * PM)
        a2 = math.radians(ang * 1.15)
        hd = (el[0] + side * math.sin(a2) * 0.25 * PM, el[1] + math.cos(a2) * 0.25 * PM)
        _limb(d, sh, el, 0.12 * PM, SUIT_M if side < 0 else SUIT_D)
        _limb(d, el, hd, 0.11 * PM, SUIT_M if side < 0 else SUIT_D)
        r = 0.065 * PM
        d.ellipse([hd[0] - r - 3, hd[1] - r - 3, hd[0] + r + 3, hd[1] + r + 3], fill=OUTL)
        d.ellipse([hd[0] - r, hd[1] - r, hd[0] + r, hd[1] + r], fill=(245, 245, 245))
    # testa
    hc = T(0, 1.68); r = int(0.2 * PM)
    d.ellipse([hc[0] - r - 3, hc[1] - r - 3, hc[0] + r + 3, hc[1] + r + 3], fill=OUTL)
    sp = _sphere(r); im.alpha_composite(sp, (int(hc[0] - sp.width / 2), int(hc[1] - sp.height / 2)))
    if front:
        for ex in (-0.065, 0.065):
            e = (hc[0] + (ex + look * 0.06) * PM, hc[1] - 0.01 * PM); er = 0.024 * PM
            d.ellipse([e[0] - er, e[1] - er * 1.25, e[0] + er, e[1] + er * 1.25], fill=OUTL)
        if mouth:
            m = (hc[0] + look * 0.06 * PM, hc[1] + 0.09 * PM)
            d.ellipse([m[0] - 7, m[1] - 9, m[0] + 7, m[1] + 9], fill=OUTL)
    return im

def walk_pose(p, swing=1.0):
    s = math.sin(p)
    return dict(legl=round(max(0, s) * 0.13, 3), legr=round(max(0, -s) * 0.13, 3),
                arml=round(8 + 10 * s * swing, 1), armr=round(8 - 10 * s * swing, 1))

_scaled = {}
def scaled(spr, h):
    """Sprite ridimensionata a h pixel di altezza (cache)."""
    h = max(4, int(h))
    k = (id(spr), h)
    if k not in _scaled:
        if len(_scaled) > 6000: _scaled.clear()
        w = max(2, int(spr.width * h / spr.height))
        _scaled[k] = spr.resize((w, h), Image.BILINEAR)
    return _scaled[k]

def q(v, step):
    return round(v / step) * step

def place(canvas, cam, x, y, z, pose, rot=0.0):
    """Disegna un omino con i piedi in (x, y, z). Ritorna (sx, sy_testa, scala) o None."""
    p = cam.proj(x, y, z)
    if p is None: return None
    sx, sy, sc = p
    h = SPR_H / PM * sc
    if h < 3 or h > 2600 or sy < -h or sy > H + h or sx < -h or sx > W + h: return None
    spr = sprite(**pose)
    img = scaled(spr, h)
    foot_off = 12 / SPR_H * img.height
    if rot:
        pad = Image.new("RGBA", (img.width * 2, img.height * 2), (0, 0, 0, 0))
        pad.alpha_composite(img, (img.width // 2, int(img.height - img.height + foot_off)))
        # i piedi sono nel centro del riquadro: si ruota attorno ai piedi
        pad2 = Image.new("RGBA", pad.size, (0, 0, 0, 0)); pad2.alpha_composite(img, (img.width // 2, int(foot_off)))
        pad = pad2.rotate(rot, resample=Image.BILINEAR, center=(img.width, img.height))
        canvas.alpha_composite(pad, (int(sx - img.width), int(sy - img.height)))
    else:
        canvas.alpha_composite(img, (int(sx - img.width / 2), int(sy - img.height + foot_off)))
    return sx, sy - 1.9 * sc, sc

def shadow(d, cam, x, z, r=0.32, y=0.0):
    a = cam.proj(x - r, y, z); b = cam.proj(x + r, y, z)
    if a is None or b is None: return
    hh = max(1, (b[0] - a[0]) * 0.22)
    d.ellipse([a[0], a[1] - hh, b[0], a[1] + hh], fill=(30, 30, 36))
