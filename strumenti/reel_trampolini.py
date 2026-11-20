#!/usr/bin/env python3
"""Reel tipo B "Overthinker / Founder" (trampolini) - Mentalità Capitale.

Due omini su due trampolini sopra l'acqua, sfondo nero, scena grande che riempie lo schermo.
A destra il founder: cinque tuffi che migliorano piano piano (spanciata, di piedi goffo, di testa storto,
di testa pulito, capriola perfetta), nuota e risale veloce. Watermark con il nome della pagina. A sinistra l'overthinker: va sul bordo, guarda giù, torna indietro, ci pensa.
Il trampolino dell'overthinker non ha la scaletta. Video in loop.
Uso: python3 reel_trampolini.py contenuto.json uscita.mp4 [secondo]
contenuto.json: {"etichetta_sx": "OVERTHINKER", "etichetta_dx": "FOUNDER"}
"""
import json, math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 12.0
WHITE, BLUE, BG = (240, 240, 240), (77, 163, 255), (6, 6, 9)
K = 1.75                                     # scala degli omini
YB = 900                                     # piano dei trampolini (piedi)
YW = 1290                                    # linea dell'acqua
SEG = {k: v * K for k, v in dict(torso=62, neck=8, head=17, ua=34, fa=32, th=44, sh=44).items()}
LW = int(9 * K)
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
# geometria: torri ai bordi, trampolini verso il centro
TL = (0, 120); BL = (120, 430)               # torre e trampolino di sinistra (x)
TR = (960, 1080); BR = (655, 960)            # torre e trampolino di destra (x)
LADDER = (918, 950)                          # scaletta sul lato interno della torre di destra
TIP_R, START_R, SPLASH_X = 670, 905, 590

def P(**k):
    base = dict(torso=180, head=180, ua_l=8, fa_l=8, ua_r=-8, fa_r=-8, th_l=3, sh_l=3, th_r=-3, sh_r=-3)
    base.update(k); return base
STAND = P()
CROUCH = P(torso=150, head=160, ua_l=-50, fa_l=-30, ua_r=-60, fa_r=-40, th_l=75, sh_l=-15, th_r=70, sh_r=-20)
DIVE = P(torso=180, head=180, ua_l=178, fa_l=180, ua_r=182, fa_r=180, th_l=2, sh_l=0, th_r=-2, sh_r=0)
TUCK = P(torso=150, head=145, ua_l=70, fa_l=135, ua_r=80, fa_r=145, th_l=115, sh_l=0, th_r=110, sh_r=-5)
FLAIL = P(torso=175, head=200, ua_l=150, fa_l=200, ua_r=-130, fa_r=-170, th_l=40, sh_l=-40, th_r=-30, sh_r=-60)
FLAT = P(torso=180, head=200, ua_l=90, fa_l=90, ua_r=-90, fa_r=-90, th_l=0, sh_l=-20, th_r=0, sh_r=-25)
LOOK = P(torso=158, head=135, ua_l=12, fa_l=20, ua_r=-5, fa_r=10, th_l=4, sh_l=2, th_r=-4, sh_r=-2)
THINK = P(torso=180, head=172, ua_r=28, fa_r=168, ua_l=22, fa_l=95)
ALMOST = P(torso=165, head=150, ua_l=-30, fa_l=-20, ua_r=-35, fa_r=-25, th_l=35, sh_l=-10, th_r=30, sh_r=-12)

def walk(p):
    s = math.sin(p)
    return P(th_l=25 * s, sh_l=25 * s - 18 * max(0, -s), th_r=-25 * s, sh_r=-25 * s - 18 * max(0, s),
             ua_l=-18 * s, fa_l=-18 * s + 12, ua_r=18 * s, fa_r=18 * s + 12)

def swim(p):
    a = math.degrees(p) % 360
    return P(torso=180, head=190, ua_l=a, fa_l=a + 10, ua_r=a + 180, fa_r=a + 190,
             th_l=8 * math.sin(p * 2), sh_l=8 * math.sin(p * 2), th_r=-8 * math.sin(p * 2), sh_r=-8 * math.sin(p * 2))

def climb(p):
    s = math.sin(p)
    return P(torso=180, head=185, ua_l=160 + 18 * s, fa_l=178, ua_r=160 - 18 * s, fa_r=178,
             th_l=45 + 35 * s, sh_l=-15, th_r=45 - 35 * s, sh_r=-15)

def mix(a, b, k):
    k = max(0.0, min(1.0, k)); k = k * k * (3 - 2 * k)
    return {n: a[n] + (b[n] - a[n]) * k for n in a}

def dvec(a, f):
    r = math.radians(a); return (math.sin(r) * f, math.cos(r))

def skeleton(hip, pose, f, rot):
    hx, hy = hip; pts = {}
    def add(p, a, L): v = dvec(a, f); return (p[0] + v[0] * L, p[1] + v[1] * L)
    S = add((0, 0), pose["torso"], SEG["torso"]); N = add(S, pose["head"], SEG["neck"] + SEG["head"])
    pts["S"], pts["N"], pts["H"] = S, N, (0, 0)
    for s in "lr":
        e = add(S, pose["ua_" + s], SEG["ua"]); h = add(e, pose["fa_" + s], SEG["fa"])
        k = add((0, 0), pose["th_" + s], SEG["th"]); fo = add(k, pose["sh_" + s], SEG["sh"])
        pts["e" + s], pts["h" + s], pts["k" + s], pts["f" + s] = e, h, k, fo
    t = math.radians(rot) * f; c, s_ = math.cos(t), math.sin(t)
    return {n: (hx + x * c - y * s_, hy + x * s_ + y * c) for n, (x, y) in pts.items()}

def ground(x, pose, f, gy=YB):
    sk = skeleton((0, 0), pose, f, 0)
    return (x, gy - max(sk["fl"][1], sk["fr"][1]))

def draw_fig(dr, sk, col):
    for a, b in [("H", "S"), ("S", "el"), ("el", "hl"), ("S", "er"), ("er", "hr"), ("H", "kl"), ("kl", "fl"), ("H", "kr"), ("kr", "fr")]:
        dr.line([sk[a], sk[b]], fill=col, width=LW)
    for p in sk.values():
        dr.ellipse([p[0] - LW / 2, p[1] - LW / 2, p[0] + LW / 2, p[1] + LW / 2], fill=col)
    n = sk["N"]; r = SEG["head"]; dr.ellipse([n[0] - r, n[1] - r, n[0] + r, n[1] + r], fill=col)

# ---------- chi lo fa: 5 tuffi da 2,4 s che migliorano piano piano ----------
DIVES = ["spanciata", "piedi", "storto", "braccia", "capriola"]
SPLASH_SIZE = [1.4, 1.0, 0.75, 0.4, 0.12]
CYC = DUR / len(DIVES)
T_WALK, T_CROUCH, T_FLY, T_SWIM, T_CLIMB = 0.35, 0.15, 0.75, 0.55, 0.32     # + resto fermo in cima
FEET = P(torso=180, head=172, ua_l=125, fa_l=165, ua_r=-115, fa_r=-150, th_l=22, sh_l=-12, th_r=-12, sh_r=-22)
BENT = P(torso=168, head=168, ua_l=150, fa_l=168, ua_r=140, fa_r=160, th_l=62, sh_l=-30, th_r=55, sh_r=-38)

def doer(t):
    cyc = int(t // CYC) % len(DIVES); u = t % CYC; kind = DIVES[cyc]; f = -1
    t1 = T_WALK; t2 = t1 + T_CROUCH; t3 = t2 + T_FLY; t4 = t3 + T_SWIM; t5 = t4 + T_CLIMB
    if u < t1:
        k = u / T_WALK; pose = walk(k * 2 * math.pi * 1.2)
        return ground(START_R + (TIP_R - START_R) * k, pose, f), pose, f, 0
    if u < t2:
        pose = mix(STAND, CROUCH, (u - t1) / 0.1); return ground(TIP_R, pose, f), pose, f, 0
    if u < t3:
        k = (u - t2) / T_FLY
        h0 = ground(TIP_R, CROUCH, f)[1]; x = TIP_R - 10 + (SPLASH_X - TIP_R + 10) * k
        if kind == "spanciata":            # si sbilancia e cade piatto di pancia
            y = h0 + (YW - 10 - h0) * k * k - 140 * k * (1 - k)
            pose = mix(CROUCH, FLAIL, k / 0.3) if k < 0.75 else mix(FLAIL, FLAT, (k - 0.75) / 0.2)
            rot = 95 * min(1, k / 0.9) ** 1.5
        elif kind == "piedi":              # salta goffo di piedi, braccia che mulinano
            y = h0 + (YW + 40 - h0) * k * k - 220 * k * (1 - k)
            pose = mix(CROUCH, FEET, k / 0.3); rot = -18 * math.sin(k * math.pi * 2)
        elif kind == "storto":             # prova di testa ma si piega e non ruota abbastanza
            y = h0 + (YW + 40 - h0) * k * k - 480 * k * (1 - k)
            pose = mix(CROUCH, BENT, k / 0.3); rot = 125 * min(1, k / 0.6) ** 1.2
        elif kind == "braccia":            # tuffo di testa pulito
            y = h0 + (YW + 90 - h0) * k * k - 700 * k * (1 - k)
            pose = mix(CROUCH, DIVE, k / 0.3); rot = 175 * min(1, k / 0.55) ** 1.2
        else:                              # capriola raccolta e ingresso perfetto in verticale
            y = h0 + (YW + 120 - h0) * k * k - 620 * k * (1 - k)
            pose = mix(CROUCH, TUCK, k / 0.15) if k < 0.62 else mix(TUCK, DIVE, (k - 0.62) / 0.18)
            rot = 540 * min(1, k / 0.82) ** 1.1
        return (x, y), pose, f, rot
    if u < t4:
        k = (u - t3) / T_SWIM
        if kind == "spanciata" and k < 0.2:
            return (SPLASH_X + 10, YW + 8), mix(FLAT, swim(0), k / 0.2), -1, 90
        x = SPLASH_X + (LADDER[0] - 50 - SPLASH_X) * k
        return (x, YW + 14), swim(k * 2 * math.pi * 2.5), 1, 82
    if u < t5:
        k = (u - t4) / T_CLIMB
        hy = (YW + 40) + (ground(0, STAND, 1)[1] - (YW + 40)) * k
        return (LADDER[0] - 30 + 10 * k, hy), climb(k * 2 * math.pi * 2), 1, 0
    return ground(START_R, STAND, f), mix(climb(0), STAND, (u - t5) / 0.08), f, 0

# ---------- overthinker ----------
def thinker(t):
    f = 1
    def at(x, pose): return ground(x, pose, f), pose, f, 0
    def wk(x0, x1, t0, t1, back=False):
        k = (t - t0) / (t1 - t0); return at(x0 + (x1 - x0) * k, walk(k * 2 * math.pi * 2 * (-1 if back else 1)))
    if t < 1.2: return at(250, STAND)
    if t < 2.4: return wk(250, 395, 1.2, 2.4)
    if t < 3.6: return at(395, mix(STAND, LOOK, (t - 2.4) / 0.35))
    if t < 4.4: return wk(395, 320, 3.6, 4.4, back=True)
    if t < 6.0: return at(320, mix(STAND, THINK, (t - 4.4) / 0.35))
    if t < 7.0: return wk(320, 400, 6.0, 7.0)
    if t < 7.6: return at(400, mix(STAND, ALMOST, (t - 7.0) / 0.3))
    if t < 8.2: return at(400, mix(ALMOST, LOOK, (t - 7.6) / 0.3))
    if t < 9.2: return wk(400, 300, 8.2, 9.2, back=True)
    if t < 10.8: return at(300, mix(STAND, THINK, (t - 9.2) / 0.35))
    return wk(300, 250, 10.8, 12.0, back=True)

# ---------- scena ----------
def tower(dr, x0, x1, top, bottom):
    c = (205, 205, 210); step = 80
    dr.line([(x0, top), (x0, bottom)], fill=c, width=7); dr.line([(x1, top), (x1, bottom)], fill=c, width=7)
    y = top
    while y < bottom:
        dr.line([(x0, y), (x1, y + step)], fill=c, width=3); dr.line([(x1, y), (x0, y + step)], fill=c, width=3)
        dr.line([(x0, y), (x1, y)], fill=c, width=3); y += step
    dr.line([(x0, top - 70), (x1, top - 70)], fill=c, width=5)
    for xx in range(x0, x1 + 1, (x1 - x0) // 4): dr.line([(xx, top - 70), (xx, top)], fill=c, width=4)

def scene_static(lab_l, lab_r):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    tower(dr, TL[0] + 4, TL[1], YB + 14, YW + 60)
    dr.rectangle([BL[0], YB, BL[1], YB + 16], fill=(225, 225, 230)); dr.rectangle([BL[1] - 24, YB, BL[1], YB + 16], fill=BLUE)
    tower(dr, TR[0], TR[1] - 4, YB + 14, YW + 60)
    dr.rectangle([BR[0], YB, BR[1], YB + 16], fill=(225, 225, 230)); dr.rectangle([BR[0], YB, BR[0] + 24, YB + 16], fill=BLUE)
    c = (210, 210, 215)
    dr.line([(LADDER[0], YB - 60), (LADDER[0], YW + 30)], fill=c, width=6); dr.line([(LADDER[1], YB - 60), (LADDER[1], YW + 30)], fill=c, width=6)
    for y in range(YB + 30, YW + 30, 46): dr.line([(LADDER[0], y), (LADDER[1], y)], fill=c, width=4)
    fnt = ImageFont.truetype(FONT, 40)
    def label(s, cx, y):
        sp = 7; ws = [dr.textlength(ch, font=fnt) for ch in s]; x = cx - (sum(ws) + sp * (len(s) - 1)) / 2
        for ch, wch in zip(s, ws): dr.text((x, y), ch, font=fnt, fill=WHITE); x += wch + sp
    label(lab_l, 290, 470); label(lab_r, 770, 470)
    return im

def watermark(text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    fnt = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 44)
    tw = dr.textlength(text, font=fnt); dr.text((W / 2 - tw / 2, 1470), text, font=fnt, fill=(255, 255, 255, 70))
    return im

def ripple(arr, t, amp=7):
    out = np.empty_like(arr)
    for y in range(arr.shape[0]):
        out[y] = np.roll(arr[y], int(amp * math.sin(y * 0.08 + t * 6) * (0.4 + y / arr.shape[0])), axis=0)
    return out

class Splash:
    def __init__(s, x, t0, size):
        rnd = random.Random(int(x * 10 + t0 * 100)); s.x, s.t0, s.k = x, t0, size
        n = int(18 + 60 * size)
        s.p = [(rnd.uniform(-330, 330) * (0.5 + size), rnd.uniform(-950, -300) * (0.4 + 0.7 * size), rnd.uniform(3, 8)) for _ in range(n)]
    def draw(s, dr, t):
        a = t - s.t0
        if a < 0 or a > 1.6: return
        for vx, vy, r in s.p:
            if a > 0.9: break
            x = s.x + vx * a; y = YW + vy * a + 1700 * a * a
            if y > YW + 4: continue
            dr.ellipse([x - r, y - r, x + r, y + r], fill=(235, 235, 240, int(255 * (1 - a / 0.9))))
        for i in range(3):
            b = a - i * 0.2
            if 0 < b < 1.2:
                rw, rh = (40 + 300 * b) * (0.5 + s.k * 0.7), 10 + 30 * b; al = int(160 * (1 - b / 1.2))
                dr.ellipse([s.x - rw, YW + 8 - rh, s.x + rw, YW + 8 + rh], outline=(220, 220, 225, al), width=4)

def render(t, static, splashes):
    fig = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(fig)
    for fn in (thinker, doer):
        hip, pose, f, rot = fn(t % DUR); draw_fig(dr, skeleton(hip, pose, f, rot), WHITE + (255,))
    a = np.array(fig); a[YW + 4:, :, 3] = (a[YW + 4:, :, 3] * 0.28).astype(np.uint8); fig = Image.fromarray(a)
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dfx = ImageDraw.Draw(fx)
    for sp in splashes:
        for off in (-DUR, 0, DUR): sp.t0 += off; sp.draw(dfx, t); sp.t0 -= off
    top = Image.alpha_composite(Image.alpha_composite(static, fig), fx)
    band = np.array(top.crop((0, 560, W, YW)).transpose(Image.FLIP_TOP_BOTTOM))
    band = ripple(band, t); band[..., 3] = (band[..., 3] * 0.22).astype(np.uint8)
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); refl.paste(Image.fromarray(band), (0, YW))
    bg = Image.new("RGBA", (W, H), BG + (255,)); bd = ImageDraw.Draw(bg)
    bd.rectangle([0, YW, W, H], fill=(10, 10, 15, 255)); bd.line([(0, YW), (W, YW)], fill=(40, 40, 48, 255), width=2)
    out = Image.alpha_composite(bg, refl)
    g = np.array(top.filter(ImageFilter.GaussianBlur(10))); g[..., 3] = (g[..., 3] * 0.55).astype(np.uint8)
    out = Image.alpha_composite(Image.alpha_composite(out, Image.fromarray(g)), top)
    out = Image.alpha_composite(out, WM)
    return out.convert("RGB")

def main():
    c = json.load(open(sys.argv[1])); out = sys.argv[2]
    global WM
    static = scene_static(c.get("etichetta_sx", "OVERTHINKER"), c.get("etichetta_dx", "FOUNDER"))
    WM = watermark(c.get("watermark", "@mentalita.capitale"))
    te = T_WALK + T_CROUCH + T_FLY
    splashes = [Splash(SPLASH_X, te + CYC * i, sz) for i, sz in enumerate(SPLASH_SIZE)]
    if len(sys.argv) > 3:
        render(float(sys.argv[3]), static, splashes).save(out); return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(render(i / FPS, static, splashes).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
