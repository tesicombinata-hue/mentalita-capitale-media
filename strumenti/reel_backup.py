#!/usr/bin/env python3
"""Reel B in inglese "Life hits everyone. Who gets back up?" – 28/11.

Un pugno gigante con scritto LIFE colpisce quattro archetipi in tre round.
MOTIVATION resta a terra al primo; EGO si rialza e prova a colpire il pugno: KO; OBSESSION si rialza finché il corpo
non cede; DISCIPLINE si rialza ogni volta. Finale: dopo il momento serio, Discipline si fa un selfie con l'Ego KO
("FOR THE GRAM"): elemento fuori tono che fa commentare ("was that necessary?" / "that's not discipline").
Uso: python3 reel_backup.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc
import motore_arch as A
from motore_arch import W, H, WHITE, BLUE, RED, ease, lin, keys

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C["durata"]
GY = 1330
XS = [160, 400, 640, 880]                  # MOTIVATION, EGO, OBSESSION, DISCIPLINE
NAMES = C["nomi"]
R1, R2, R3 = C["round"]                    # inizio delle tre spazzate
SW = 0.8                                   # durata della spazzata
JAB = R2 + 1.75                            # il pugno che risponde all'Ego
SELFIE = C["selfie"]
K = 0.62

def fist_x(t):
    for r in (R1, R2, R3):
        if r - 0.1 <= t < r + SW: return lin(t, r, r + SW, 1350, -350)
    if JAB - 0.15 <= t < JAB + 0.5:                                     # jab sull'Ego
        return keys(t, [(JAB - 0.15, 1350), (JAB, XS[1] + 150), (JAB + 0.12, XS[1] + 175), (JAB + 0.5, 1350)])
    return None

def hit(i, r): return r + SW * (1350 - (XS[i] + 130)) / 1700

# stato di ogni archetipo: lista di (t, rotazione) ; facce per intervallo
def rot_kf(i):
    kf = [(0, 0)]
    def down(t0): kf.extend([(t0, kf[-1][1]), (t0 + 0.3, -88)])
    def up(t0, d=0.6, to=0): kf.extend([(t0, -88), (t0 + d, to)])
    down(hit(i, R1))
    if i == 0: return kf
    if i == 1: up(R1 + 1.6, 0.35); down(hit(i, R2)); up(R2 + 1.1, 0.35); down(JAB + 0.05); return kf
    if i == 2: up(R1 + 2.0, 0.5); down(hit(i, R2)); up(R2 + 2.0, 0.6); down(hit(i, R3)); up(R3 + 1.6, 0.6, -40); kf.extend([(R3 + 2.6, -40), (R3 + 3.0, -88)]); return kf
    up(R1 + 2.5, 0.9); down(hit(i, R2)); up(R2 + 2.6, 0.9); down(hit(i, R3)); up(R3 + 2.4, 1.1); return kf

ROT = [rot_kf(i) for i in range(4)]

def face_of(i, t, rot):
    if i == 0: return "smile" if t < R1 else ("tired" if t > R1 + 0.8 else "scared")
    if i == 1:
        if t >= JAB: return "ko"
        return "smug" if t < R1 else "angry"
    if i == 2:
        if t >= R3 + 2.9: return "ko"
        return "neutral" if t < R1 else "strain"
    if t >= SELFIE: return "smug"
    return "focus" if rot > -60 else "tired"

def fist(d, v, x, y, red=False):
    col = (232, 232, 236); edge = RED if red else (90, 90, 100)
    d.polygon([v.p(x + 90, y - 50), v.p(1500, y - 70), v.p(1500, y + 70), v.p(x + 90, y + 50)], fill=(190, 190, 196), outline=edge)
    A0 = v.p(x - 120, y - 90); B0 = v.p(x + 110, y + 90)
    d.rounded_rectangle([A0[0], A0[1], B0[0], B0[1]], radius=int(v.s(46)), fill=col, outline=edge, width=int(v.s(6)))
    for k in range(1, 4):
        X = v.p(x - 120 + k * 57, y - 90); Y = v.p(x - 120 + k * 57, y - 20)
        d.line([X, Y], fill=(150, 150, 158), width=int(v.s(5)))
    fnt = mc.font(int(v.s(58)), mc.INTER); s = "LIFE"; P = v.p(x - 5, y + 10)
    d.text((P[0] - mc.text_w(s, fnt) / 2, P[1] - v.s(30)), s, font=fnt, fill=(RED if red else (20, 20, 24)))

def frame(t):
    img = Image.new("RGB", (W, H), A.BG); d = ImageDraw.Draw(img)
    shake = 8 * math.sin(t * 70) * max(0, 1 - min(abs(t - hit(3, r)) for r in (R1, R2, R3)) / 0.25)
    v = A.V(1.14 + 0.03 * ease(t / 2), 520 + shake, 960)
    G = v.p(0, GY); d.rectangle([0, G[1], W, H], fill=(14, 14, 18)); d.line([(0, G[1]), (W, G[1])], fill=(70, 70, 80), width=3)
    rnd = 1 if t < R2 - 0.3 else (2 if t < R3 - 0.3 else 3)
    for i in range(4):
        rot = keys(t, ROT[i])
        kind = face_of(i, t, rot)
        col = BLUE if i == 3 else WHITE
        arms = (0.1, 0.1)
        if i == 1 and R2 + 1.5 <= t < JAB + 0.05: arms = (0.2, 0.95)                    # l'Ego carica il pugno
        if i == 3 and t >= C["fine0"] and t < SELFIE: arms = (0.6, 0.6)
        if i == 3 and t >= SELFIE: arms = (0.78, 0.1)                                    # telefono alzato
        sit = 0.0
        if i == 0 and t > R1 + 1.0:                                                      # Motivation resta seduto a terra
            rot = keys(t, [(R1 + 1.0, -88), (R1 + 1.6, 0)]); sit = ease((t - R1 - 1.0) / 0.6)
        x = XS[i] + (60 * ease((t - R2 - 1.5) / 0.25) if (i == 1 and t < JAB + 0.05) else 0)
        if i == 1 and t >= JAB + 0.05: x = XS[1] + 60 - 90 * ease((t - JAB) / 0.3)
        x += 185 * K * math.sin(math.radians(-rot)) * (0 if sit > 0 else 1)          # steso: centrato sul suo posto
        head = A.figure(d, v, x, GY, kind, col, rot=rot, arms=arms, sit=sit, k=K)
        if i == 3 and t >= SELFIE:                                                       # il telefono e il flash
            ph = v.p(XS[3] - 122 * K, GY - 358 * K)
            d.rounded_rectangle([ph[0] - 18, ph[1] - 30, ph[0] + 18, ph[1] + 30], radius=6, fill=(30, 30, 36), outline=WHITE, width=3)
            fl = C["flash"]
            if 0 <= t - fl < 0.25:
                a = 1 - (t - fl) / 0.25; r = 60 + 300 * (t - fl)
                d.ellipse([ph[0] - r, ph[1] - r, ph[0] + r, ph[1] + r], fill=tuple(int(255 * a) for _ in range(3)))
    fx = fist_x(t)
    if fx is not None: fist(d, v, fx, GY - 160, red=(rnd >= 2))
    for i, s, a0, b0 in C["fumetti"]:
        if a0 <= t < b0:
            al = ease((t - a0) / 0.08) * (1 - ease((t - b0 + 0.08) / 0.08))
            A.bubble(d, v, (XS[i] + (-60 if i == 3 else 0), GY - 330), s, al)
    for i, nm in enumerate(NAMES):
        out = (i == 0 and t > R1 + 1) or (i == 1 and t > JAB + 0.3) or (i == 2 and t > R3 + 3.0)
        A.label(d, v, XS[i], GY + 40, nm, (85, 85, 92) if out else (BLUE if i == 3 else (215, 215, 220)))
    A.counter(d, f"ROUND {rnd}/3", 1 - 0.6 * ease((t - C['fine0']) / 0.4))
    A.caption(d, C["testi"], t, DUR)
    A.question(d, C["domanda"], t, C["domanda_t"], 410, 48)
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    ev = [(0.0, mc.s_hum(DUR, 0.03))]
    for s, a, b in C["testi"]: ev.append((a, mc.s_pop(0.25, 800)))
    for r in (R1, R2, R3):
        ev.append((r, mc.s_whoosh(0.8, 0.5)))
        for i in range(4): ev.append((hit(i, r), mc.s_thud(0.7, 65)))
    ev += [(JAB, mc.s_thud(1.0, 55)), (JAB + 0.02, mc.s_crack(0.8))]
    for i in range(1, 4):
        for (a, ra), (b, rb) in zip(ROT[i], ROT[i][1:]):
            if rb > ra + 30: ev.append((a, mc.s_whoosh(0.35, 0.15)))
    ev += [(C["fine0"], mc.s_rise(2.4, 0.4)), (C["domanda_t"], mc.s_chime(0.35, 660)), (C["flash"], mc.s_click(0.6))]
    for i, s, a, b in C["fumetti"]: ev.append((a, mc.s_pop(0.2, 650)))
    A.finish(OUT, DUR, frame, ev)
