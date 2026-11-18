#!/usr/bin/env python3
"""Reel "4 pillole di mentalità" - Mentalità Capitale.
Quattro scene visive, nessun dato reale: è una metafora.
1) Una brutta giornata non è una brutta vita  2) Prima non succede niente, poi tutto insieme
3) Meno apparire, più avere (cursori)  4) CAPITALE acrostico.
Uso: python3 reel_mentalita.py out.mp4 [secondo]  (con il secondo salva un fotogramma png)"""
import math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/inter/InterDisplay-"
F = lambda n, s: ImageFont.truetype(FD + n + ".otf", s)
BLUE = (77, 163, 255); RED = (255, 70, 70); WHITE = (255, 255, 255); GREY = (110, 110, 110)
DIM = (45, 45, 45)

def ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def mix(c, a): return tuple(int(v * a) for v in c)
def lerp(a, b, p): return a + (b - a) * p
def centered(d, y, text, f, col):
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=col)

def glowed(draw_fn, radius=14, boost=1.6):
    """disegna due volte: alone sfocato + tratto nitido"""
    base = Image.new("RGB", (W, H)); draw_fn(ImageDraw.Draw(base), 1.0)
    g = base.filter(ImageFilter.GaussianBlur(radius))
    im = Image.eval(Image.blend(g, base, 0.5), lambda v: min(255, int(v * boost)))
    draw_fn(ImageDraw.Draw(im), 0.7)
    return im

def stickman(d, x, y, h, phase, col=WHITE):
    w = max(3, int(h * 0.075)); head = h * 0.13
    hip = (x, y - h * 0.45); neck = (x, y - h * 0.78)
    sw = math.sin(phase) * h * 0.16
    d.line([hip, (x + sw, y)], fill=col, width=w); d.line([hip, (x - sw, y)], fill=col, width=w)
    d.line([hip, neck], fill=col, width=w)
    d.line([(x, y - h * 0.72), (x - sw * 0.8, y - h * 0.48)], fill=col, width=w)
    d.line([(x, y - h * 0.72), (x + sw * 0.8, y - h * 0.48)], fill=col, width=w)
    cy = y - h * 0.78 - head
    d.ellipse([x - head, cy - head, x + head, cy + head], fill=col)

# ---------------- SCENA 1: una brutta giornata ----------------
random.seed(7)
N = 320
S = [0.0]
for i in range(1, N):
    step = 1.6 + random.uniform(-3.2, 3.2)
    if 120 <= i < 134: step = -4.5 + random.uniform(-1.2, 1.2)   # la brutta giornata
    S.append(S[-1] + step)
DIP_A, DIP_B = 120, 134
def s_at(x):
    i = int(max(0, min(N - 2, x))); f = x - i
    return S[i] + (S[i + 1] - S[i]) * f

def scene1(t, T=9.0):
    p = ease((t - 4.3) / 2.6)
    L = lerp(DIP_A - 6, 0, p); R = lerp(DIP_B + 6, N - 1, p)
    vs = [s_at(L)] + S[int(L) + 1:int(R) + 1] + [s_at(R)]
    lo, hi = min(vs), max(vs); pad = (hi - lo) * 0.15
    X0, X1, Y0, Y1 = 60, 1020, 700, 1380
    sx = lambda x: X0 + (X1 - X0) * (x - L) / (R - L)
    sy = lambda v: Y1 - (Y1 - Y0) * (v - lo + pad) / (hi - lo + 2 * pad)
    xs = [L] + list(range(int(L) + 1, int(R) + 1)) + [R]
    def draw(d, k):
        for a, b in zip(xs, xs[1:]):
            red = DIP_A <= a and b <= DIP_B + 0.01
            d.line([(sx(a), sy(s_at(a))), (sx(b), sy(s_at(b)))], fill=RED if red else BLUE, width=int(9 * k))
    im = glowed(draw); d = ImageDraw.Draw(im)
    q = ease((t - 0.4) / 3.2); xm = lerp(DIP_A + 0.5, DIP_B - 0.5, q)
    walking = 0.4 < t < 3.6
    zoom = 28 / (R - L)
    hgt = 150 * max(0.5, zoom ** 0.3)
    stickman(d, sx(xm), sy(s_at(xm)) - 5, hgt, t * 8 if walking else 0.55)
    fb = F("Bold", 78)
    centered(d, 420, "Una brutta giornata", fb, mix(WHITE, ease(t / 0.5)))
    a = ease((t - 6.0) / 0.7)
    if a > 0: centered(d, 515, "non è una brutta vita", fb, mix(BLUE, a))
    return im

# ---------------- SCENA 2: semaforo, sii paziente ----------------
CAR = [(0,72),(4,52),(40,44),(112,20),(190,10),(252,20),(322,44),(356,54),(362,72),(352,82),(0,82)]
WIN = [(124,26),(190,17),(238,26),(224,42),(132,42)]
def car_img(col, scale=1.0, dark=False):
    w, h = 380, 120
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(x + 8, y + 6) for x, y in CAR], fill=col + (255,))
    d.polygon([(x + 8, y + 6) for x, y in WIN], fill=(20, 24, 40, 255))
    hl = tuple(min(255, int(c * 1.35)) for c in col)
    d.line([(60, 56), (150, 34), (320, 52)], fill=hl + (255,), width=3)
    for cx in (84, 292):
        d.ellipse([cx - 28, 66, cx + 28, 122 - 6], fill=(15, 15, 15, 255))
        d.ellipse([cx - 15, 79, cx + 15, 103], fill=(150, 150, 150, 255) if not dark else (90, 90, 90, 255))
    if scale != 1.0: im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return im

CAR_BLUE = car_img((70, 120, 235))
WRECKS = [(1500, 18, 0), (1880, -150, 1), (2150, 35, 0)]   # (x nel mondo, rotazione, 0/1 = ammaccata/ribaltata)
WRECK_IMGS = [car_img((105, 105, 110), scale=0.82, dark=True).rotate(r, expand=True, resample=Image.BICUBIC) for _, r, _ in WRECKS]

def scene2(t, T=10.0):
    im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    GY = 1130  # linea della strada (sotto le ruote)
    # avanzamento della macchina: ferma fino a 4,0 s, poi accelera
    u = max(0.0, t - 4.0)
    off = 260 * u * u if u < 1.2 else 260 * 1.44 + 624 * (u - 1.2)
    # strada: trattini che scorrono
    for k in range(-2, 14):
        x = k * 160 - (off % 160)
        d.line([(x, GY + 40), (x + 70, GY + 40)], fill=(40, 40, 40), width=6)
    # semaforo nel mondo a x=900
    lx = 900 - off
    if lx > -80:
        d.rectangle([lx - 4, GY - 300, lx + 4, GY + 30], fill=(70, 70, 70))
        d.rounded_rectangle([lx - 34, GY - 420, lx + 34, GY - 290], radius=14, fill=(25, 25, 25))
        state = 0 if t < 3.0 else (1 if t < 3.6 else 2)
        cols = [(255, 50, 50), (255, 190, 40), (60, 220, 110)]
        for i, yy in enumerate([GY - 395, GY - 355, GY - 315]):
            on = (i == 0 and state == 0) or (i == 1 and state == 1) or (i == 2 and state == 2)
            c = cols[i] if on else (55, 55, 55)
            if on:
                gl = Image.new("RGB", (W, H)); ImageDraw.Draw(gl).ellipse([lx - 40, yy - 40, lx + 40, yy + 40], fill=c)
                im = ImageChops_add(im, gl.filter(ImageFilter.GaussianBlur(22))); d = ImageDraw.Draw(im)
            d.ellipse([lx - 15, yy - 15, lx + 15, yy + 15], fill=c)
    # macchine distrutte (chi non ha aspettato), con fumo
    for (wx, rot, kind), wim in zip(WRECKS, WRECK_IMGS):
        x = wx - off
        if -500 < x < W + 100:
            bb = wim.getbbox(); im.paste(wim, (int(x), int(GY - 30 - bb[3])), wim)
            sm = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sm)
            for j in range(5):
                ph = (t * 0.8 + j * 0.2) % 1.0
                r = 18 + 40 * ph; sx_, sy_ = x + wim.size[0] * 0.6 + 20 * j, GY - wim.size[1] - 120 * ph
                ds.ellipse([sx_ - r, sy_ - r, sx_ + r, sy_ + r], fill=(160, 160, 160, int(90 * (1 - ph))))
            im.paste(sm.filter(ImageFilter.GaussianBlur(8)), (0, 0), sm.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
    # riflesso e macchina blu (ferma a x=330 dello schermo)
    cx = 330
    refl = CAR_BLUE.transpose(Image.FLIP_TOP_BOTTOM)
    ra = refl.split()[3].point(lambda v: int(v * 0.18)); refl.putalpha(ra)
    im.paste(refl, (cx, GY + 2), refl)
    im.paste(CAR_BLUE, (cx, GY - CAR_BLUE.size[1] + 8), CAR_BLUE)
    d = ImageDraw.Draw(im)
    fb = F("Bold", 70)
    a1 = ease(t / 0.5) * (1 - ease((t - 2.8) / 0.3))
    if a1 > 0: centered(d, 520, "Sii paziente.", fb, mix(WHITE, a1))
    a2 = ease((t - 3.2) / 0.5)
    if a2 > 0:
        centered(d, 480, "Tutto arriva", fb, mix(WHITE, a2))
        centered(d, 570, "al momento giusto.", fb, mix(BLUE, a2))
    return im

def ImageChops_add(a, b):
    from PIL import ImageChops
    return ImageChops.add(a, b)

# ---------------- SCENA 3: i cursori e l'ego ----------------
SL = ["Felicità", "Gentilezza", "Ottimismo", "Fiducia", "Rispetto", "Ego"]
def scene3(t, T=9.5):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    SW = 250; cxs = [210, 540, 870]; rows = [830, 1010]
    pos = []
    for i in range(6):
        x0 = cxs[i % 3] - SW / 2; y = rows[i // 3]; pos.append((x0, y))
    # l'ego scende tra 6,4 e 7,2 s; gli altri salgono tra 6,8 e 7,8 s
    ego = 1 - ease((t - 6.4) / 0.8)
    up = ease((t - 6.8) / 1.0)
    # tentativi a vuoto: il cursore prova a tirare su i primi 5 cursori (resistenza)
    tries = [(0.9, 0), (1.9, 1), (2.9, 2), (3.9, 3), (4.9, 4)]
    wiggle = [0.0] * 6
    for st, i in tries:
        p = (t - st) / 0.7
        if 0 < p < 1: wiggle[i] = 30 * math.sin(math.pi * p)
    fl = F("Medium", 36)
    knobs = []
    for i, name in enumerate(SL):
        x0, y = pos[i]
        v = ego if i == 5 else up
        col = RED if i == 5 else BLUE
        tw = d.textlength(name, font=fl)
        d.text((x0 + (SW - tw) / 2, y - 64), name, font=fl, fill=(190, 190, 190))
        d.line([(x0, y), (x0 + SW, y)], fill=DIM, width=10)
        kx = x0 + SW * v + (wiggle[i] if i < 5 else 0)
        if kx > x0 + 2: d.line([(x0, y), (kx, y)], fill=col, width=10)
        d.rounded_rectangle([kx - 7, y - 24, kx + 7, y + 24], radius=5, fill=WHITE)
        knobs.append((kx, y))
    # percorso del cursore
    path = [(0.0, (620, 1500))]
    for st, i in tries:
        k = knobs[i]
        path += [(st - 0.25, (pos[i][0], k[1])), (st, (pos[i][0], k[1])), (st + 0.35, (pos[i][0] + 30, k[1])), (st + 0.7, (pos[i][0], k[1]))]
    ex, ey = pos[5][0] + SW, rows[1]
    path += [(5.9, (ex, ey)), (6.4, (ex, ey)), (7.2, (pos[5][0], ey)), (7.8, (pos[5][0] + 40, ey + 120)), (9.5, (pos[5][0] + 60, ey + 200))]
    for (ta, pa), (tb, pb) in zip(path, path[1:]):
        if ta <= t <= tb:
            q = ease((t - ta) / max(0.01, tb - ta)); cx, cy = lerp(pa[0], pb[0], q), lerp(pa[1], pb[1], q); break
    else: cx, cy = path[-1][1]
    pts = [(0, 0), (0, 52), (13, 40), (24, 64), (34, 59), (23, 36), (40, 36)]
    d.polygon([(cx + x + 4, cy + y + 4) for x, y in pts], fill=(255, 255, 255), outline=(0, 0, 0))
    centered(d, 1420, "@mentalita.capitale", F("Regular", 30), (80, 80, 80))
    im2 = im.filter(ImageFilter.GaussianBlur(10))
    return Image.eval(Image.blend(im2, im, 0.65), lambda v: min(255, int(v * 1.35)))

# ---------------- SCENA 4: CAPITALE ----------------
WORDS = ["ostanza", "bitudini", "azienza", "struzione", "empo", "utocontrollo", "ungo periodo", "quilibrio"]
def scene4(t, T=10.0):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    letters = "CAPITALE"
    fbig = F("Bold", 120); fl = F("Bold", 66); fw = F("Regular", 66)
    # fase 1: parola grande al centro (0-2,2 s), fase 2: le lettere scendono in colonna (2,2-3,4 s)
    p = ease((t - 2.2) / 1.2)
    a0 = ease(t / 0.6)
    spacing = 118
    x_start = (W - spacing * (len(letters) - 1)) / 2
    col_x, col_y0, row = 300, 600, 92
    for i, ch in enumerate(letters):
        f = fbig if p < 0.5 else fl
        tw = d.textlength(ch, font=f); twl = d.textlength(ch, font=fl)
        x = lerp(x_start + i * spacing - tw / 2, col_x - 30, p); y = lerp(860, col_y0 + i * row, p)
        d.text((x, y - (60 if p < 0.5 else 33)), ch, font=f, fill=mix(BLUE, a0))
        # fase 3: ogni lettera diventa parola (3,6 s in poi, una ogni 0,45 s)
        a = ease((t - 3.6 - i * 0.45) / 0.4)
        if a > 0:
            d.text((col_x - 30 + twl + 1, y - 33), WORDS[i], font=fw, fill=mix(WHITE, a))
    a5 = ease((t - 7.6) / 0.6)
    if a5 > 0:
        centered(d, 1420, "Mentalità Capitale", F("Bold", 48), mix(WHITE, a5))
        centered(d, 1484, "@mentalita.capitale", F("Regular", 34), mix(GREY, a5))
    im2 = im.filter(ImageFilter.GaussianBlur(10))
    return Image.eval(Image.blend(im2, im, 0.7), lambda v: min(255, int(v * 1.3)))

SCENES = [(scene1, 9.0), (scene2, 10.0), (scene3, 9.5), (scene4, 10.0)]
XF = 0.4  # dissolvenza tra le scene
DUR = sum(T for _, T in SCENES)

def frame(t):
    acc = 0.0
    for k, (fn, T) in enumerate(SCENES):
        if t < acc + T or k == len(SCENES) - 1:
            lt = t - acc; im = fn(lt)
            if lt > T - XF and k < len(SCENES) - 1:   # dissolvenza al nero
                im = Image.eval(im, lambda v, a=(T - lt) / XF: int(v * a))
            if lt < XF and k > 0:
                im = Image.eval(im, lambda v, a=lt / XF: int(v * a))
            return im
        acc += T

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "reel_mentalita.mp4"
    if len(sys.argv) > 2: frame(float(sys.argv[2])).save(out); sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i",
                          "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
