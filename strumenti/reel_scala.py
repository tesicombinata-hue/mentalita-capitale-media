#!/usr/bin/env python3
"""Reel tipo B "Chi teneva la scala" - Mentalità Capitale.

Un figlio sale una scala (PRIMO LAVORO, PRIMA AZIENDA, PRIMO MILIONE) mentre la madre la tiene ferma da sotto,
sotto la pioggia, la neve e la notte, e invecchia. In cima le telecamere: "Mi sono fatto da solo."
La scala trema, lui guarda giù, scende, la porta su e le dà il trofeo: "Lei teneva la scala."
Uso: python3 reel_scala.py contenuto.json uscita.mp4 [secondo]
"""
import json, math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 16.3
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

# ---------- mondo ----------
GROUND, TOPY = 3000, 1200          # terreno e cima del muro
WALL_X = 560                        # faccia sinistra del muro
LAD = (462, 548)                    # montanti della scala
LAD_TOP = 1120
SIGNS = [(2560, "PRIMO LAVORO"), (2050, "PRIMA AZIENDA"), (1520, "PRIMO MILIONE")]
PED = (800, TOPY)                   # piedistallo del trofeo
CAMX = 965                          # operatore

def ease(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)
def lerp(a, b, k): return a + (b - a) * k
def keyed(t, keys):                 # keys: [(t, value_tuple)], interpolazione con easing
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
            return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
    return keys[-1][1]

CAM = [(0, (430, 2760, 2.0)), (1.2, (430, 2760, 2.0)), (2.3, (600, 2060, 0.93)), (6.3, (600, 2060, 0.93)),
       (7.0, (770, 1130, 1.65)), (9.7, (770, 1130, 1.65)), (10.3, (450, 2740, 1.5)), (11.6, (450, 2740, 1.5)),
       (11.9, (680, 1180, 1.65)), (12.3, (680, 1180, 1.65)), (12.6, (600, 2060, 0.93)), (13.25, (600, 2060, 0.93)),
       (13.6, (740, 1130, 1.65)), (DUR, (740, 1130, 1.65))]

class Cam:
    def __init__(s, t):
        s.cx, s.cy, s.s = keyed(t, CAM)
    def p(s, x, y): return ((x - s.cx) * s.s + W / 2, (y - s.cy) * s.s + H / 2)
    def w(s, v): return max(1, int(round(v * s.s)))

# ---------- omini ----------
KF = 1.25
SEG = {k: v * KF for k, v in dict(torso=62, neck=8, head=18, ua=34, fa=32, th=44, sh=44).items()}
def P(**k):
    b = dict(torso=180, head=180, ua_l=8, fa_l=8, ua_r=-8, fa_r=-8, th_l=3, sh_l=3, th_r=-3, sh_r=-3); b.update(k); return b
STAND = P()
HOLD = P(ua_l=95, fa_l=100, ua_r=80, fa_r=95)
TIRED = P(torso=165, head=150, ua_l=80, fa_l=85, ua_r=70, fa_r=80, th_l=8, sh_l=-5, th_r=-2, sh_r=-8)
RAISE = P(ua_l=170, fa_l=178, ua_r=-10, fa_r=-5)
LOOKD = P(torso=170, head=140, ua_l=20, fa_l=30, ua_r=-5, fa_r=0)
GIVE = P(ua_l=80, fa_l=85, ua_r=70, fa_r=80)
FILM = P(ua_l=60, fa_l=150, ua_r=70, fa_r=150)
def climb(p):
    s = math.sin(p)
    return P(torso=180, head=185, ua_l=150 + 20 * s, fa_l=175, ua_r=150 - 20 * s, fa_r=175,
             th_l=50 + 35 * s, sh_l=-20, th_r=50 - 35 * s, sh_r=-20)
def walk(p):
    s = math.sin(p)
    return P(th_l=25 * s, sh_l=25 * s - 18 * max(0, -s), th_r=-25 * s, sh_r=-25 * s - 18 * max(0, s),
             ua_l=-18 * s, fa_l=-18 * s + 12, ua_r=18 * s, fa_r=18 * s + 12)
def mix(a, b, k):
    k = ease(k); return {n: a[n] + (b[n] - a[n]) * k for n in a}

def skel(hip, pose, f):
    hx, hy = hip; pts = {}
    def add(p, a, L):
        r = math.radians(a); return (p[0] + math.sin(r) * f * L, p[1] + math.cos(r) * L)
    S = add((0, 0), pose["torso"], SEG["torso"]); N = add(S, pose["head"], SEG["neck"] + SEG["head"])
    pts.update(H=(0, 0), S=S, N=N)
    for s in "lr":
        e = add(S, pose["ua_" + s], SEG["ua"]); h = add(e, pose["fa_" + s], SEG["fa"])
        k = add((0, 0), pose["th_" + s], SEG["th"]); fo = add(k, pose["sh_" + s], SEG["sh"])
        pts.update({"e" + s: e, "h" + s: h, "k" + s: k, "f" + s: fo})
    return {n: (hx + x, hy + y) for n, (x, y) in pts.items()}

def hip_on(xfeet, yfeet, pose, f):
    sk = skel((0, 0), pose, f); return (xfeet, yfeet - max(sk["fl"][1], sk["fr"][1]))

def draw_person(dr, cam, sk, body=(242, 242, 245), lw=12, skirt=None, hair=None, tie=False):
    L = lambda a, b, c=body, w=lw: dr.line([cam.p(*sk[a]), cam.p(*sk[b])], fill=c, width=cam.w(w))
    if skirt:
        hx, hy = sk["H"]; sx, sy = sk["S"]
        top = (hx + (sx - hx) * 0.45, hy + (sy - hy) * 0.45)
        poly = [(top[0] - 20, top[1]), (top[0] + 20, top[1]), (hx + 46, hy + 70), (hx - 46, hy + 70)]
        dr.polygon([cam.p(*q) for q in poly], fill=skirt)
    for a, b in [("H", "S"), ("H", "kl"), ("kl", "fl"), ("H", "kr"), ("kr", "fr"), ("S", "el"), ("el", "hl"), ("S", "er"), ("er", "hr")]:
        L(a, b)
    for p in sk.values():
        x, y = cam.p(*p); r = cam.w(lw) / 2; dr.ellipse([x - r, y - r, x + r, y + r], fill=body)
    if tie:
        hx, hy = sk["H"]; sx, sy = sk["S"]
        dr.line([cam.p(sx, sy + 6), cam.p(sx + (hx - sx) * 0.55, sy + (hy - sy) * 0.55)], fill=(200, 40, 40), width=cam.w(7))
    nx, ny = sk["N"]; r = SEG["head"]
    if hair:
        bx, by = nx - 24, ny - 14; x, y = cam.p(bx, by); rr = 14 * cam.s
        dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=hair)
    x, y = cam.p(nx, ny); rr = r * cam.s; dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=body)

# ---------- scena ----------
def sky(t):
    y = np.linspace(0, 1, H)[:, None]
    def grad(a, b): a, b = np.array(a), np.array(b); return a + (b - a) * y[..., None]
    rain = grad((14, 20, 34), (30, 38, 54)); snow = grad((6, 8, 16), (20, 26, 42)); sun = grad((70, 38, 14), (246, 170, 70))
    wr = 1 - ease((t - 3.4) / 0.6); ws = ease((t - 3.4) / 0.6) * (1 - ease((t - 6.4) / 0.6)); wsun = ease((t - 6.4) / 0.6)
    img = rain * wr + snow * ws + sun * wsun
    return np.repeat(img, W, axis=1).astype(np.uint8), wr, ws, wsun

def rays(dr, cam, t, k):
    if k <= 0: return
    cx, cy = cam.p(780, TOPY + 10)
    for i in range(18):
        a0 = math.radians(i * 20 + t * 4); a1 = a0 + math.radians(9)
        R = 3000
        dr.polygon([(cx, cy), (cx + R * math.cos(a0), cy - R * abs(math.sin(a0))), (cx + R * math.cos(a1), cy - R * abs(math.sin(a1)))],
                   fill=(255, 230, 160, int(55 * k)))
    r = 120 * cam.s; dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 220, 140, int(200 * k)))

def world(dr, cam, t, shake):
    # terreno e muro
    dr.rectangle([*cam.p(-500, GROUND), *cam.p(1600, GROUND + 800)], fill=(20, 21, 26))
    dr.rectangle([*cam.p(WALL_X, TOPY), *cam.p(1600, GROUND)], fill=(40, 43, 50))
    for yy in range(TOPY + 60, GROUND, 120):
        dr.line([cam.p(WALL_X, yy), cam.p(1600, yy)], fill=(52, 56, 64), width=cam.w(3))
        off = 0 if (yy // 120) % 2 else 110
        for xx in range(WALL_X + off, 1600, 220):
            dr.line([cam.p(xx, yy - 60), cam.p(xx, yy)], fill=(52, 56, 64), width=cam.w(3))
    dr.rectangle([*cam.p(WALL_X, TOPY - 10), *cam.p(1600, TOPY + 8)], fill=(70, 74, 82))
    # cartelli
    fs = ImageFont.truetype(FX, max(8, int(26 * cam.s)))
    for y, txt in SIGNS:
        x0, y0 = cam.p(WALL_X + 30, y - 32); x1, y1 = cam.p(WALL_X + 330, y + 32)
        dr.rounded_rectangle([x0, y0, x1, y1], radius=cam.w(8), fill=(40, 30, 14), outline=(232, 170, 60), width=cam.w(4))
        tw = dr.textlength(txt, font=fs); dr.text(((x0 + x1) / 2 - tw / 2, (y0 + y1) / 2 - fs.size * 0.6), txt, font=fs, fill=(245, 190, 80))
    # scala (trema quando la madre non ce la fa più)
    wood = (176, 104, 46)
    for x in LAD:
        dr.line([cam.p(x + shake, LAD_TOP), cam.p(x, GROUND)], fill=wood, width=cam.w(12))
    for y in range(LAD_TOP + 50, GROUND, 70):
        k = (y - LAD_TOP) / (GROUND - LAD_TOP); sx = shake * (1 - k)
        dr.line([cam.p(LAD[0] + sx, y), cam.p(LAD[1] + sx, y)], fill=wood, width=cam.w(8))
    # rampicanti: il tempo che passa
    g = ease((t - 4.0) / 7.0)
    if g > 0:
        hmax = (GROUND - LAD_TOP) * 0.45 * g
        for x, ph in ((LAD[0], 0), (LAD[1], 1.7)):
            pts = [cam.p(x + 10 * math.sin(y * 0.02 + ph), GROUND - y) for y in range(0, int(hmax), 20)]
            if len(pts) > 1: dr.line(pts, fill=(60, 140, 70), width=cam.w(5))
            for y in range(30, int(hmax), 60):
                lx, ly = cam.p(x + 10 * math.sin(y * 0.02 + ph) + (12 if (y // 60) % 2 else -12), GROUND - y); r = 7 * cam.s
                dr.ellipse([lx - r, ly - r, lx + r, ly + r], fill=(80, 170, 90))
    # piedistallo
    x0, y0 = cam.p(PED[0] - 34, PED[1] - 70); x1, y1 = cam.p(PED[0] + 34, PED[1])
    dr.rectangle([x0, y0, x1, y1], fill=(28, 28, 32), outline=(90, 90, 96), width=cam.w(3))

def trophy(dr, cam, x, y):
    gold = (240, 190, 60)
    pts = [(x - 26, y - 70), (x + 26, y - 70), (x + 14, y - 30), (x - 14, y - 30)]
    dr.polygon([cam.p(*q) for q in pts], fill=gold)
    dr.line([cam.p(x, y - 30), cam.p(x, y - 12)], fill=gold, width=cam.w(8))
    dr.rectangle([*cam.p(x - 18, y - 12), *cam.p(x + 18, y)], fill=gold)
    for sgn in (-1, 1):
        dr.arc([*cam.p(x + sgn * 26 - 12, y - 66), *cam.p(x + sgn * 26 + 12, y - 44)], 0, 360, fill=gold, width=cam.w(5))

def camera_rig(dr, cam, x, y):
    c = (150, 150, 158)
    for dx in (-30, 0, 30): dr.line([cam.p(x, y - 110), cam.p(x + dx, y)], fill=c, width=cam.w(5))
    dr.rectangle([*cam.p(x - 40, y - 150), *cam.p(x + 30, y - 105)], fill=(60, 60, 66), outline=c, width=cam.w(3))
    dr.rectangle([*cam.p(x - 62, y - 140), *cam.p(x - 40, y - 115)], fill=(90, 90, 98))

def bubble(dr, cam, x, y, txt, fnt):
    sx, sy = cam.p(x, y)
    tw = dr.textlength(txt, font=fnt); pw, ph = tw + 44, fnt.size + 28
    sx = max(pw / 2 + 20, min(W - 150 - pw / 2, sx)); sy = max(ph + 40, sy)
    dr.rounded_rectangle([sx - pw / 2, sy - ph, sx + pw / 2, sy], radius=ph / 2, fill=(14, 14, 18), outline=(240, 240, 240), width=3)
    dr.text((sx - tw / 2, sy - ph + 12), txt, font=fnt, fill=(245, 245, 245))

BUB = [(0.2, 1.4, "mom", "Ti tengo io."), (1.5, 2.6, "son", "Grazie, mà!"), (2.7, 3.8, "son", "Tienila ferma!"),
       (4.0, 5.2, "mom", "Ho le mani gelate..."), (5.3, 6.4, "son", "Ce l'ho fatta!"), (7.1, 8.3, "cam", "Come ci sei riuscito?"),
       (8.4, 9.8, "son", "Mi sono fatto da solo."), (10.2, 11.6, "mom", "...tutto bene lassù?"), (14.2, DUR, "son", "Lei teneva la scala.")]

# ---------- personaggi nel tempo ----------
def son_state(t):
    f = 1
    if t < 5.0:
        k = t / 5.0; yf = lerp(2650, TOPY + 30, k)
        return hip_on(505 - 30, yf, climb(t * 7), f), climb(t * 7), f, None
    if t < 5.6:
        k = (t - 5.0) / 0.6; return hip_on(lerp(505, 650, k), TOPY, walk(k * 6), f), walk(k * 6), f, None
    if t < 7.3: return hip_on(650, TOPY, STAND, f), STAND, f, None
    if t < 7.6:
        k = (t - 7.3) / 0.3; return hip_on(lerp(650, 730, k), TOPY, walk(k * 4), f), walk(k * 4), f, None
    if t < 11.5:
        pose = mix(STAND, RAISE, (t - 7.8) / 0.4) if t < 11.1 else mix(RAISE, STAND, (t - 11.1) / 0.3)
        return hip_on(730, TOPY, pose, f), pose, f, "hand"
    if t < 11.75:                                   # la scala trema: si gira verso il bordo
        k = (t - 11.5) / 0.25; return hip_on(lerp(730, 620, ease(k)), TOPY, walk(k * 4), -1), walk(k * 4), -1, None
    if t < 12.15:                                   # guarda giù
        return hip_on(620, TOPY, mix(STAND, LOOKD, (t - 11.75) / 0.2), -1), mix(STAND, LOOKD, (t - 11.75) / 0.2), -1, None
    if t < 12.3:
        k = (t - 12.15) / 0.15; return hip_on(lerp(620, 520, k), TOPY, walk(k * 3), -1), walk(k * 3), -1, None
    if t < 12.65:                                   # scende di corsa
        k = (t - 12.3) / 0.35; return hip_on(505 - 30, lerp(TOPY + 30, 2950, ease(k)), climb(0.5), f), climb(0.5), f, None
    if t < 13.3:                                    # la porta su
        k = (t - 12.65) / 0.65; return hip_on(505 - 30, lerp(2750, TOPY + 30, ease(k)), climb(t * 18), f), climb(t * 18), f, None
    if t < 13.8: return hip_on(620, TOPY, STAND, f), STAND, f, None
    if t < 14.3:
        k = (t - 13.8) / 0.5; return hip_on(620, TOPY, mix(STAND, GIVE, k), f), mix(STAND, GIVE, k), f, None
    return hip_on(620, TOPY, mix(GIVE, STAND, (t - 14.6) / 0.4), f), mix(GIVE, STAND, (t - 14.6) / 0.4), f, None

def mom_state(t):
    f = 1; age = ease((t - 3.0) / 8.0)
    if t < 12.65:
        pose = mix(HOLD, TIRED, age)
        return hip_on(392, GROUND, pose, f), pose, f, age, None
    if t < 13.3:
        k = (t - 12.65) / 0.65; return hip_on(505 - 30, lerp(2950, TOPY + 30, ease(k)), climb(t * 18), f), climb(t * 18), f, 1, None
    pose = mix(STAND, RAISE, (t - 14.5) / 0.5) if t > 14.5 else STAND
    return hip_on(720, TOPY, pose, f), pose, f, 1, ("hand" if t > 14.3 else None)

def trophy_pos(t, son_sk, mom_sk):
    if t < 7.6 or 11.5 <= t < 14.0: return PED[0], PED[1] - 70
    if t < 11.5: return son_sk["hl"][0], son_sk["hl"][1] + 30
    if t < 14.3:
        k = (t - 14.0) / 0.3; return lerp(PED[0], mom_sk["hl"][0], k), lerp(PED[1] - 70, mom_sk["hl"][1] + 30, k)
    return mom_sk["hl"][0], mom_sk["hl"][1] + 30

def render(t, rnd_rain, rnd_snow, fnt):
    cam = Cam(t)
    arr, wr, ws, wsun = sky(t)
    img = Image.fromarray(arr).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dro = ImageDraw.Draw(ov)
    rays(dro, cam, t, wsun)
    if ws > 0:
        for x, y, r in rnd_snow[:60]:
            dro.ellipse([x - 1.5, y * 0.6 - 1.5, x + 1.5, y * 0.6 + 1.5], fill=(255, 255, 255, int(160 * ws)))
    img = Image.alpha_composite(img, ov)
    dr = ImageDraw.Draw(img)
    shake = 9 * math.sin(t * 55) if 10.9 < t < 11.6 else 0
    world(dr, cam, t, shake)
    camera_rig(dr, cam, CAMX, TOPY)
    s_hip, s_pose, s_f, _ = son_state(t); s_sk = skel(s_hip, s_pose, s_f)
    m_hip, m_pose, m_f, age, _ = mom_state(t); m_sk = skel(m_hip, m_pose, m_f)
    c_pose = FILM; c_sk = skel(hip_on(CAMX + 70, TOPY, c_pose, -1), c_pose, -1)
    draw_person(dr, cam, c_sk, body=(200, 200, 206))
    hair = tuple(int(lerp(a, b, age)) for a, b in zip((70, 45, 30), (150, 150, 158)))
    draw_person(dr, cam, m_sk, skirt=(196, 84, 128), hair=hair)
    draw_person(dr, cam, s_sk, tie=True)
    trophy(dr, cam, *trophy_pos(t, s_sk, m_sk))
    # pioggia e neve davanti
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0)); df = ImageDraw.Draw(fx)
    if wr > 0:
        for x0, y0, sp in rnd_rain:
            x = (x0 + 260 * t * sp) % W; y = (y0 + 1700 * t * sp) % H
            df.line([(x, y), (x - 9, y - 38)], fill=(190, 205, 230, int(110 * wr)), width=2)
    if ws > 0:
        for x0, y0, sp in rnd_snow:
            x = (x0 + 40 * math.sin(t * 2 + y0)) % W; y = (y0 + 160 * t * sp) % H; r = 3 + 2 * sp
            df.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, int(200 * ws)))
    img = Image.alpha_composite(img, fx); dr = ImageDraw.Draw(img)
    heads = {"son": s_sk["N"], "mom": m_sk["N"], "cam": c_sk["N"]}
    for t0, t1, who, txt in BUB:
        if t0 <= t < t1:
            x, y = heads[who]; bubble(dr, cam, x, y - (110 if t > 7 else 46), txt, fnt)
    wm = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 40)
    tw = dr.textlength("@mentalita.capitale", font=wm)
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(over).text((W / 2 - tw / 2, 1500), "@mentalita.capitale", font=wm, fill=(255, 255, 255, 70))
    img = Image.alpha_composite(img, over)
    return img.convert("RGB")

def main():
    out = sys.argv[2]
    rnd = random.Random(7)
    rain = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.8, 1.2)) for _ in range(140)]
    snow = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.6, 1.4)) for _ in range(150)]
    fnt = ImageFont.truetype(FB, 36)
    if len(sys.argv) > 3:
        render(float(sys.argv[3]), rain, snow, fnt).save(out); return
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(render(i / FPS, rain, snow, fnt).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
