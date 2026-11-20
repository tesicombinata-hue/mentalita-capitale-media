#!/usr/bin/env python3
"""Reel tipo B "Chi ci pensa / Chi lo fa" (trampolini) - Mentalità Capitale.

Due omini su due trampolini sopra l'acqua, sfondo nero. Chi lo fa si tuffa in continuazione e risale
dalla scaletta; chi ci pensa va sul bordo, si ferma, torna indietro, ci pensa. Il trampolino di chi ci pensa
non ha la scaletta. Video in loop: l'ultimo fotogramma si raccorda con il primo.
Uso: python3 reel_trampolini.py contenuto.json uscita.mp4 [secondo]
contenuto.json: {"etichetta_sx": "CHI CI PENSA", "etichetta_dx": "CHI LO FA"}
"""
import json, math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 12.0
WHITE, BLUE, BG = (240, 240, 240), (77, 163, 255), (6, 6, 9)
YW = 1170                       # linea dell'acqua
YB = 900                        # piano dei trampolini (piedi)
LEG = 88                        # coscia + stinco
SEG = dict(torso=62, neck=8, head=17, ua=34, fa=32, th=44, sh=44)
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

# ---------- pose (angoli assoluti in gradi: 0 = verso il basso, positivo = in avanti) ----------
def P(**k):
    base = dict(torso=180, head=180, ua_l=8, fa_l=8, ua_r=-8, fa_r=-8, th_l=3, sh_l=3, th_r=-3, sh_r=-3)
    base.update(k); return base
STAND = P()
CROUCH = P(torso=150, head=160, ua_l=-50, fa_l=-30, ua_r=-60, fa_r=-40, th_l=75, sh_l=-15, th_r=70, sh_r=-20)
DIVE = P(torso=180, head=180, ua_l=178, fa_l=180, ua_r=182, fa_r=180, th_l=2, sh_l=0, th_r=-2, sh_r=0)
TUCK = P(torso=155, head=150, ua_l=70, fa_l=130, ua_r=80, fa_r=140, th_l=110, sh_l=0, th_r=105, sh_r=-5)
PENCIL = P(torso=180, head=180, ua_l=2, fa_l=0, ua_r=-2, fa_r=0, th_l=1, sh_l=0, th_r=-1, sh_r=0)
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

def d(a, f):  # direzione di un segmento
    r = math.radians(a); return (math.sin(r) * f, math.cos(r))

def skeleton(hip, pose, f, rot):
    hx, hy = hip
    pts = {}
    def add(p, a, L): v = d(a, f); return (p[0] + v[0] * L, p[1] + v[1] * L)
    S = add((0, 0), pose["torso"], SEG["torso"])
    N = add(S, pose["head"], SEG["neck"] + SEG["head"])
    pts["S"], pts["N"], pts["H"] = S, N, (0, 0)
    for side in "lr":
        e = add(S, pose["ua_" + side], SEG["ua"]); h = add(e, pose["fa_" + side], SEG["fa"])
        k = add((0, 0), pose["th_" + side], SEG["th"]); fo = add(k, pose["sh_" + side], SEG["sh"])
        pts["e" + side], pts["h" + side], pts["k" + side], pts["f" + side] = e, h, k, fo
    t = math.radians(rot) * f
    c, s = math.cos(t), math.sin(t)
    return {n: (hx + x * c - y * s, hy + x * s + y * c) for n, (x, y) in pts.items()}

def grounded_hip(x, ground, pose, f):
    sk = skeleton((0, 0), pose, f, 0)
    low = max(sk["fl"][1], sk["fr"][1])
    return (x, ground - low)

def draw_fig(dr, sk, col, w=9):
    lines = [("H", "S"), ("S", "el"), ("el", "hl"), ("S", "er"), ("er", "hr"),
             ("H", "kl"), ("kl", "fl"), ("H", "kr"), ("kr", "fr")]
    for a, b in lines:
        dr.line([sk[a], sk[b]], fill=col, width=w)
    for p in sk.values():
        dr.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)
    n = sk["N"]; r = SEG["head"]
    dr.ellipse([n[0] - r, n[1] - r, n[0] + r, n[1] + r], fill=col)

# ---------- chi lo fa: 3 cicli da 4 s (camminata, carica, tuffo, nuoto, scaletta) ----------
LADDER_X, TIP_R, START_R = 905, 668, 900
DIVES = ["swan", "flip", "pencil"]

def doer(t):
    cyc, u = int(t // 4) % 3, t % 4
    kind = DIVES[cyc]; f = -1
    if u < 0.6:
        k = u / 0.6; x = START_R + (TIP_R - START_R) * k
        pose = walk(k * 2 * math.pi * 1.5)
        return grounded_hip(x, YB, pose, f), pose, f, 0, None
    if u < 0.85:
        pose = mix(STAND, CROUCH, (u - 0.6) / 0.15)
        return grounded_hip(TIP_R, YB, pose, f), pose, f, 0, None
    if u < 1.85:
        k = (u - 0.85) / 1.0
        x0, x1 = TIP_R - 10, 530
        h0 = grounded_hip(TIP_R, YB, CROUCH, f)[1]
        x = x0 + (x1 - x0) * k
        y = h0 + (YW + 70 - h0) * k * k - 260 * k * (1 - k) * 1.6
        if kind == "swan":
            pose = mix(CROUCH, DIVE, k / 0.3); rot = -170 * k ** 1.3 * -1
        elif kind == "flip":
            pose = mix(CROUCH, TUCK, k / 0.2) if k < 0.7 else mix(TUCK, PENCIL, (k - 0.7) / 0.2)
            rot = 360 * min(1, k / 0.8)
        else:
            pose = mix(CROUCH, PENCIL, k / 0.25); rot = 0
        return (x, y), pose, f, rot, ("entry", 1.85) if k > 0.97 else None
    if u < 3.0:
        k = (u - 1.85) / 1.15
        x = 530 + (LADDER_X - 40 - 530) * k
        pose = swim(k * 2 * math.pi * 2.5)
        return (x, YW + 12), pose, 1, 82, None
    k = (u - 3.0) / 1.0
    pose = climb(k * 2 * math.pi * 2)
    hy = (YW + 40) + (grounded_hip(0, YB, STAND, 1)[1] - (YW + 40)) * k
    if k > 0.85:
        pose = mix(pose, STAND, (k - 0.85) / 0.15)
    return (LADDER_X - 6 * (1 - k), hy), pose, 1, 0, None

# ---------- chi ci pensa ----------
def thinker(t):
    f = 1
    def at(x, pose): return grounded_hip(x, YB, pose, f), pose, f, 0, None
    def wk(x0, x1, t0, t1, back=False):
        k = (t - t0) / (t1 - t0); x = x0 + (x1 - x0) * k
        return at(x, walk(k * 2 * math.pi * 2 * (-1 if back else 1)))
    if t < 1.2: return at(250, STAND)
    if t < 2.4: return wk(250, 398, 1.2, 2.4)
    if t < 3.6: return at(398, mix(STAND, LOOK, (t - 2.4) / 0.35))
    if t < 4.4: return wk(398, 330, 3.6, 4.4, back=True)
    if t < 6.0: return at(330, mix(STAND, THINK, (t - 4.4) / 0.35))
    if t < 7.0: return wk(330, 404, 6.0, 7.0)
    if t < 7.6: return at(404, mix(STAND, ALMOST, (t - 7.0) / 0.3))
    if t < 8.2: return at(404, mix(ALMOST, LOOK, (t - 7.6) / 0.3))
    if t < 9.2: return wk(404, 300, 8.2, 9.2, back=True)
    if t < 10.8: return at(300, mix(STAND, THINK, (t - 9.2) / 0.35))
    return wk(300, 250, 10.8, 12.0, back=True)

# ---------- scena fissa ----------
def tower(dr, x0, x1, top, bottom, rail=True):
    c = (200, 200, 205)
    dr.line([(x0, top), (x0, bottom)], fill=c, width=5); dr.line([(x1, top), (x1, bottom)], fill=c, width=5)
    y = top
    while y < bottom:
        dr.line([(x0, y), (x1, y + 60)], fill=c, width=2); dr.line([(x1, y), (x0, y + 60)], fill=c, width=2)
        dr.line([(x0, y), (x1, y)], fill=c, width=2); y += 60
    if rail:
        dr.line([(x0, top - 50), (x1, top - 50)], fill=c, width=4)
        for xx in range(x0, x1 + 1, (x1 - x0) // 4): dr.line([(xx, top - 50), (xx, top)], fill=c, width=3)

def scene_static(lab_l, lab_r):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    tower(dr, 30, 130, YB + 8, YW + 40)
    dr.rectangle([130, YB, 430, YB + 10], fill=(225, 225, 230)); dr.rectangle([415, YB, 432, YB + 10], fill=BLUE)
    tower(dr, 950, 1050, YB + 8, YW + 40)
    dr.rectangle([650, YB, 950, YB + 10], fill=(225, 225, 230)); dr.rectangle([648, YB, 665, YB + 10], fill=BLUE)
    lx0, lx1 = LADDER_X + 18, LADDER_X + 40         # scaletta solo sul trampolino di destra
    dr.line([(lx0, YB - 40), (lx0, YW + 20)], fill=(210, 210, 215), width=4)
    dr.line([(lx1, YB - 40), (lx1, YW + 20)], fill=(210, 210, 215), width=4)
    for y in range(YB + 20, YW + 20, 34): dr.line([(lx0, y), (lx1, y)], fill=(210, 210, 215), width=3)
    fnt = ImageFont.truetype(FONT, 34)
    def label(s, cx, y):
        sp = 6; ws = [dr.textlength(ch, font=fnt) for ch in s]; tw = sum(ws) + sp * (len(s) - 1); x = cx - tw / 2
        for ch, wch in zip(s, ws): dr.text((x, y), ch, font=fnt, fill=WHITE); x += wch + sp
    label(lab_l, 290, 610); label(lab_r, 760, 650)
    return im

def ripple(arr, t, amp=6):
    out = np.empty_like(arr)
    for y in range(arr.shape[0]):
        s = int(amp * math.sin(y * 0.09 + t * 6) * (0.4 + y / arr.shape[0]))
        out[y] = np.roll(arr[y], s, axis=0)
    return out

class Splash:
    def __init__(s, x, t0, n=46):
        rnd = random.Random(int(x * 10 + t0 * 100))
        s.x, s.t0 = x, t0
        s.p = [(rnd.uniform(-260, 260), rnd.uniform(-820, -260), rnd.uniform(2.5, 6)) for _ in range(n)]
    def draw(s, dr, t):
        a = t - s.t0
        if a < 0 or a > 1.6: return
        for vx, vy, r in s.p:
            if a > 0.9: break
            x = s.x + vx * a; y = YW + vy * a + 1500 * a * a
            if y > YW + 4: continue
            al = int(255 * (1 - a / 0.9)); dr.ellipse([x - r, y - r, x + r, y + r], fill=(235, 235, 240, al))
        for i in range(3):
            b = a - i * 0.2
            if 0 < b < 1.2:
                rw, rh = 40 + 260 * b, 8 + 26 * b; al = int(160 * (1 - b / 1.2))
                dr.ellipse([s.x - rw, YW + 6 - rh, s.x + rw, YW + 6 + rh], outline=(220, 220, 225, al), width=3)

def render(c, t, static, splashes):
    fig = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(fig)
    for fn, col in ((thinker, WHITE), (doer, WHITE)):
        hip, pose, f, rot, _ = fn(t % DUR)
        draw_fig(dr, skeleton(hip, pose, f, rot), col + (255,))
    # sotto l'acqua l'omino si vede appena
    a = np.array(fig); a[YW + 4:, :, 3] = (a[YW + 4:, :, 3] * 0.28).astype(np.uint8); fig = Image.fromarray(a)
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dfx = ImageDraw.Draw(fx)
    for sp in splashes:
        for k in (-DUR, 0, DUR): sp.t0 += k; sp.draw(dfx, t); sp.t0 -= k
    top = Image.alpha_composite(static, fig); top = Image.alpha_composite(top, fx)
    # riflesso nell'acqua
    band = np.array(top.crop((0, YW - 460, W, YW)).transpose(Image.FLIP_TOP_BOTTOM))
    band = ripple(band, t); band[..., 3] = (band[..., 3] * 0.22).astype(np.uint8)
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); refl.paste(Image.fromarray(band), (0, YW))
    bg = Image.new("RGBA", (W, H), BG + (255,))
    bd = ImageDraw.Draw(bg); bd.rectangle([0, YW, W, H], fill=(10, 10, 15, 255)); bd.line([(0, YW), (W, YW)], fill=(40, 40, 48, 255), width=2)
    out = Image.alpha_composite(bg, refl)
    glow = top.filter(ImageFilter.GaussianBlur(9)); g = np.array(glow); g[..., 3] = (g[..., 3] * 0.55).astype(np.uint8)
    out = Image.alpha_composite(out, Image.fromarray(g)); out = Image.alpha_composite(out, top)
    return out.convert("RGB")

def main():
    c = json.load(open(sys.argv[1])); out = sys.argv[2]
    static = scene_static(c.get("etichetta_sx", "CHI CI PENSA"), c.get("etichetta_dx", "CHI LO FA"))
    splashes = [Splash(530, 1.85 + 4 * i) for i in range(3)]
    if len(sys.argv) > 3:
        render(c, float(sys.argv[3]), static, splashes).save(out); return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(render(c, i / FPS, static, splashes).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
