#!/usr/bin/env python3
"""Motore comune dei Reel animati di Mentalità Capitale (omini su fondo nero).

Fornisce: omini con scheletro e pose, testi (frase fissa in alto, fumetti, etichette, contatori),
bagliore, scrittura del video con ffmpeg, effetti sonori sintetizzati e unione audio/video.
Usato da reel_ponte.py, reel_acceso.py, reel_fondamenta.py (24/11).
"""
import math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (6, 6, 9)
WHITE = (240, 240, 240)
BLUE = (77, 163, 255)
GREY = (120, 120, 132)
DARK = (28, 28, 34)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
INTER = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
_fonts = {}

def font(size, path=MONO):
    k = (path, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]

def ease(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

def seg(t, a, b):
    """0 prima di a, 1 dopo b, lineare in mezzo."""
    if b <= a: return 1.0 if t >= b else 0.0
    return max(0.0, min(1.0, (t - a) / (b - a)))

# ---------------- omini ----------------
BASE = dict(torso=62, neck=8, head=17, ua=34, fa=32, th=44, sh=44)

def P(**k):
    b = dict(torso=180, head=180, ua_l=8, fa_l=8, ua_r=-8, fa_r=-8, th_l=3, sh_l=3, th_r=-3, sh_r=-3)
    b.update(k); return b

STAND = P()
CARRY = P(ua_l=80, fa_l=95, ua_r=70, fa_r=90)                       # braccia avanti, porta qualcosa
PLACE = P(torso=140, head=135, ua_l=40, fa_l=30, ua_r=30, fa_r=20, th_l=40, sh_l=-30, th_r=30, sh_r=-35)
POINT = P(ua_r=100, fa_r=100, ua_l=10, fa_l=10)
CHEER = P(ua_l=150, fa_l=160, ua_r=-150, fa_r=-160)
REACH = P(torso=120, head=115, ua_r=20, fa_r=10, ua_l=40, fa_l=30, th_l=60, sh_l=-40, th_r=50, sh_r=-60)
HANG = P(ua_l=175, fa_l=178, ua_r=165, fa_r=170, th_l=10, sh_l=0, th_r=-12, sh_r=-5)
SIT_TYPE = P(torso=172, head=165, ua_l=60, fa_l=95, ua_r=55, fa_r=92, th_l=90, sh_l=0, th_r=88, sh_r=-2)
SIT_SLEEP = P(torso=120, head=95, ua_l=70, fa_l=100, ua_r=65, fa_r=105, th_l=90, sh_l=0, th_r=88, sh_r=-2)
SAD = P(torso=172, head=150, ua_l=5, fa_l=5, ua_r=-5, fa_r=-5)

def walk(p, amp=25):
    s = math.sin(p)
    return P(th_l=amp * s, sh_l=amp * s - 18 * max(0, -s), th_r=-amp * s, sh_r=-amp * s - 18 * max(0, s),
             ua_l=-18 * s, fa_l=-18 * s + 12, ua_r=18 * s, fa_r=18 * s + 12)

def walk_carry(p):
    w = walk(p); w.update(ua_l=80, fa_l=95, ua_r=70, fa_r=90); return w

def clap(p):
    s = (math.sin(p) + 1) / 2
    return P(ua_l=60, fa_l=95 + 35 * s, ua_r=55, fa_r=60 - 35 * s, head=175)

def laugh(p):
    s = math.sin(p)
    return P(torso=190 + 6 * s, head=200 + 8 * s, ua_l=40, fa_l=-60, ua_r=30, fa_r=-70)

def dig(p):
    s = math.sin(p)
    return P(torso=150 + 10 * s, head=140, ua_l=50 + 40 * s, fa_l=30 + 50 * s, ua_r=40 + 40 * s, fa_r=25 + 50 * s,
             th_l=30, sh_l=-20, th_r=-10, sh_r=-10)

def type_(p):
    s = math.sin(p)
    q = dict(SIT_TYPE); q["fa_l"] += 6 * s; q["fa_r"] -= 6 * s; return q

def mix(a, b, k):
    k = ease(k); return {n: a[n] + (b[n] - a[n]) * k for n in a}

def skeleton(hip, pose, f=1, rot=0, k=1.0):
    S_ = {n: v * k for n, v in BASE.items()}
    def dv(a): r = math.radians(a); return (math.sin(r) * f, math.cos(r))
    def add(p, a, L): v = dv(a); return (p[0] + v[0] * L, p[1] + v[1] * L)
    pts = {"H": (0, 0)}
    S = add((0, 0), pose["torso"], S_["torso"]); N = add(S, pose["head"], S_["neck"] + S_["head"])
    pts["S"], pts["N"] = S, N
    for s in "lr":
        e = add(S, pose["ua_" + s], S_["ua"]); h = add(e, pose["fa_" + s], S_["fa"])
        kn = add((0, 0), pose["th_" + s], S_["th"]); fo = add(kn, pose["sh_" + s], S_["sh"])
        pts["e" + s], pts["h" + s], pts["k" + s], pts["f" + s] = e, h, kn, fo
    t = math.radians(rot) * f; c, sn = math.cos(t), math.sin(t)
    return {n: (hip[0] + x * c - y * sn, hip[1] + x * sn + y * c) for n, (x, y) in pts.items()}, S_["head"]

def feet_offset(pose, k=1.0):
    sk, _ = skeleton((0, 0), pose, 1, 0, k)
    return max(sk["fl"][1], sk["fr"][1])

def on_ground(x, gy, pose, k=1.0):
    return (x, gy - feet_offset(pose, k))

def draw_fig(dr, hip, pose, col, f=1, rot=0, k=1.0):
    sk, r = skeleton(hip, pose, f, rot, k)
    lw = max(3, int(9 * k))
    for a, b in [("H", "S"), ("S", "el"), ("el", "hl"), ("S", "er"), ("er", "hr"), ("H", "kl"), ("kl", "fl"), ("H", "kr"), ("kr", "fr")]:
        dr.line([sk[a], sk[b]], fill=col, width=lw)
    for p in sk.values():
        dr.ellipse([p[0] - lw / 2, p[1] - lw / 2, p[0] + lw / 2, p[1] + lw / 2], fill=col)
    n = sk["N"]; dr.ellipse([n[0] - r, n[1] - r, n[0] + r, n[1] + r], fill=col)
    return sk

# ---------------- testi ----------------
def text_w(s, fnt):
    b = fnt.getbbox(s); return b[2] - b[0]

def centered(dr, y, s, fnt, col):
    dr.text(((W - text_w(s, fnt)) / 2, y), s, font=fnt, fill=col)

def phrase(dr, lines, t0=None, t=None, y=270, size=68, cps=40):
    """Frase fissa in alto. lines = [(testo, colore)]. Se t0 è dato, si scrive lettera per lettera da t0."""
    fnt = font(size); yy = y
    total = None if t0 is None else int(max(0, (t - t0)) * cps)
    for s, col in lines:
        shown = s if total is None else s[:max(0, total)]
        if total is not None: total -= len(s)
        dr.text(((W - text_w(s, fnt)) / 2, yy), shown, font=fnt, fill=col)
        yy += int(size * 1.3)
    return yy

def bubble(dr, x, y, s, size=34, alpha=1.0, tail=(0, 40)):
    """Fumetto bianco con testo nero centrato in (x, y)."""
    if alpha <= 0: return
    fnt = font(size); tw = text_w(s, fnt); pad = 18
    x0, y0, x1, y1 = x - tw / 2 - pad, y - size / 2 - pad + 4, x + tw / 2 + pad, y + size / 2 + pad + 4
    c = tuple(int(BG[i] + (255 - BG[i]) * alpha) for i in range(3))
    tc = tuple(int(255 + (10 - 255) * alpha) for _ in range(3))
    dr.polygon([(x - 14, y1 - 2), (x + 14, y1 - 2), (x + tail[0], y1 + tail[1])], fill=c)
    dr.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=c)
    dr.text((x - tw / 2, y - size / 2 + 2), s, font=fnt, fill=tc)

def label(dr, x, y, s, col=WHITE, size=30):
    fnt = font(size); dr.text((x - text_w(s, fnt) / 2, y), s, font=fnt, fill=col)

def watermark(dr):
    fnt = font(26, INTER); s = "@mentalita.capitale"
    dr.text(((W - text_w(s, fnt)) / 2, 1515), s, font=fnt, fill=(90, 90, 100))

def glow(img, layer, radius=18, strength=1.0):
    """Aggiunge il bagliore del livello luminoso all'immagine."""
    small = layer.resize((W // 3, H // 3))
    g = small.filter(ImageFilter.GaussianBlur(radius / 3)).resize((W, H))
    a = np.asarray(img, dtype=np.int16) + (np.asarray(g, dtype=np.int16) * strength).astype(np.int16)
    a = np.clip(a + np.asarray(layer, dtype=np.int16), 0, 255).astype(np.uint8)
    return Image.fromarray(a)

# ---------------- video ----------------
class Writer:
    def __init__(self, path):
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                                   "-crf", "18", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    def add(self, img):
        self.p.stdin.write(img.convert("RGB").tobytes())
    def close(self):
        self.p.stdin.close(); self.p.wait()

def render(path, dur, frame_fn):
    w = Writer(path)
    for i in range(int(round(dur * FPS))):
        w.add(frame_fn(i / FPS))
    w.close()

# ---------------- suoni ----------------
SR = 44100
_rng = np.random.default_rng(7)

def _env(n, a=0.002, d=0.15):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d); return e

def s_tok(f=180, d=0.09, v=0.6):             # legno, passo, asse posata
    n = int(SR * 0.35); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * 0.7 + np.sin(2 * np.pi * f * 2.7 * t) * 0.3 + _rng.normal(0, 0.15, n)
    return x * _env(n, 0.001, d) * v

def s_crack(v=0.8):
    n = int(SR * 0.5); x = _rng.normal(0, 1, n)
    x = x * (_rng.random(n) < 0.25) * _env(n, 0.001, 0.12); return x * v

def s_whoosh(d=0.6, v=0.4, up=True):
    n = int(SR * d); x = _rng.normal(0, 1, n); t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 2; k = np.exp(-((t - (0.6 if up else 0.4)) ** 2) / 0.05)
    y = np.convolve(x, np.ones(25) / 25, mode="same")
    return (y * env * (0.5 + k)) * v

def s_click(v=0.5):
    n = int(SR * 0.08); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * t) * _env(n, 0.0005, 0.008) + _rng.normal(0, 0.3, n) * _env(n, 0.0005, 0.004)) * v

def s_pop(v=0.4, f=700):
    n = int(SR * 0.15); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (f + 600 * np.exp(-t * 40)) * t) * _env(n, 0.001, 0.04) * v

def s_type(v=0.2):
    return s_click(v) * 0.8

def s_clap(v=0.25):
    n = int(SR * 0.12); return _rng.normal(0, 1, n) * _env(n, 0.001, 0.025) * v

def s_thud(v=0.8, f=70):
    n = int(SR * 0.6); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t * (1 + 0.5 * np.exp(-t * 20))) * _env(n, 0.002, 0.18) + _rng.normal(0, 0.2, n) * _env(n, 0.001, 0.05)) * v

def s_rise(d=1.6, v=0.35, f0=220, f1=440):    # accordo che sale sulla risposta
    n = int(SR * d); t = np.arange(n) / SR; f = f0 + (f1 - f0) * (t / d) ** 2
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.5 * np.sin(ph * 1.5) + 0.35 * np.sin(ph * 2)
    env = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.5); return x * env * v / 1.8

def s_chime(v=0.35, f=880):
    n = int(SR * 1.4); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * m * t) / m for m in (1, 2, 3.01))
    return x * _env(n, 0.002, 0.45) * v / 1.8

def s_hum(d, v=0.05, f=55):
    n = int(SR * d); t = np.arange(n) / SR; return np.sin(2 * np.pi * f * t) * v

def mixdown(dur, events, path):
    out = np.zeros(int(SR * (dur + 0.5)))
    for t0, x in events:
        i = int(t0 * SR); j = min(len(out), i + len(x)); out[i:j] += x[: j - i]
    out = out[: int(SR * dur)]
    peak = np.max(np.abs(out)) or 1; out = out / peak * 0.85
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())

def mux(video, audio, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", out], check=True)
