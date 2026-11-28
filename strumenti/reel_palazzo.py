#!/usr/bin/env python3
"""Reel B in inglese "3 builders. Same land." – 28/11 (idea del titolare).

EGO tira su in fretta un palazzo bellissimo (colonne, timpano, cupola) ma senza fondamenta: crolla presto.
Arrabbiato, distrugge con un pugno la casetta di ACTION TAKER. ACTION TAKER raccoglie i pezzi del palazzo
dell'Ego e ricostruisce la sua casa, più grande e più bella (luci accese, bandiera blu).
L'Ego prova a colpire ancora: il palazzo non si muove, lui rimbalza e finisce KO sulle sue macerie.
PERFECTIONIST misura ogni mattone e lo mette in una griglia perfetta, lentissimo: a fine video ha fatto 3 file su un progetto
molto più grande (sagoma tratteggiata); alza fiero il mattone successivo: "ALMOST READY".
Uso: python3 reel_palazzo.py contenuto.json uscita.mp4 [secondo -> png]
"""
import json, math, sys, os, random
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motore_mc as mc
import motore_arch as A
from motore_arch import W, H, WHITE, BLUE, RED, ease, lin, keys

C = json.load(open(sys.argv[1])); OUT = sys.argv[2]
DUR = C["durata"]; T = C["tempi"]
GY = 1300
EX, PX, AX = 195, 480, 872
SX = 608                # muretto del Perfectionist
PB = [0.8 + 1.38 * k for k in range(12)]   # quando posa ogni mattone (12 = 3 file da 4)
EGO0 = 342            # dove sta l'Ego
ATP = AX + 82         # Action Taker davanti alla sua casa              # EGO, PERFECTIONIST, ACTION TAKER
MARBLE, MARBLE_E = (232, 232, 238), (120, 120, 132)
BRICK, BRICK_E = (205, 200, 196), (80, 76, 74)
LIGHT = (255, 214, 120)

# ---------------- pezzi ----------------
def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def tri(w, h): return [(-w / 2, h / 2), (w / 2, h / 2), (0, -h / 2)]
def dome(r):
    return [(r * math.cos(a), -r * math.sin(a) + r / 2) for a in [math.pi * k / 16 for k in range(17)]]

COL_H, COL_W = 230, 30
PIECES = [  # nome, forma, (dx, dy) rispetto al centro e al suolo del palazzo dell'Ego
    ("base", rect(290, 26), (0, -13)),
    ("c1", rect(COL_W, COL_H), (-105, -26 - COL_H / 2)), ("c2", rect(COL_W, COL_H), (-35, -26 - COL_H / 2)),
    ("c3", rect(COL_W, COL_H), (35, -26 - COL_H / 2)), ("c4", rect(COL_W, COL_H), (105, -26 - COL_H / 2)),
    ("arch", rect(300, 24), (0, -26 - COL_H - 12)),
    ("ped", tri(310, 78), (0, -26 - COL_H - 24 - 39)),
    ("dome", dome(58), (0, -26 - COL_H - 24 - 78 - 29)),
]
NAMES_P = [p[0] for p in PIECES]

def draw_piece(d, v, shape, cx, cy, rot, fill=MARBLE, edge=MARBLE_E, name=""):
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    P = [v.p(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in shape]
    d.polygon(P, fill=fill, outline=edge)
    if name.startswith("c"):                                   # scanalature delle colonne
        for k in (-7, 0, 7):
            q = [v.p(cx + k * ca - y * sa, cy + k * sa + y * ca) for y in (-COL_H / 2 + 10, COL_H / 2 - 10)]
            d.line(q, fill=(195, 195, 205), width=max(1, int(v.s(2))))

rng0 = random.Random(3)
RUBBLE = {n: (EX + rng0.uniform(-150, 150), GY - (8 if n in ("base", "arch") else 14), rng0.choice([88, -92, 85, -87]) if n.startswith("c") else rng0.uniform(-30, 30))
          for n in NAMES_P}
RUBBLE["c1"] = (EX - 150, GY - 15, 90); RUBBLE["c2"] = (EX - 60, GY - 15, -88); RUBBLE["c3"] = (EX + 70, GY - 15, 92); RUBBLE["c4"] = (EX + 160, GY - 15, 86)
RUBBLE["dome"] = (EX + 20, GY - 30, 12); RUBBLE["ped"] = (EX - 20, GY - 36, -18)

# nuovo palazzo di Action Taker: base di mattoni + pezzi dell'Ego sopra
NEW_BASE_H = 4 * 21
def new_pos(n):
    dx, dy = dict((p[0], p[2]) for p in PIECES)[n]
    return (AX + dx, GY - NEW_BASE_H + dy)

def ego_palace_state(n, t):
    """Posizione (x, y, rot, visibile) di un pezzo del palazzo dell'Ego nel tempo."""
    i = NAMES_P.index(n); dx, dy = PIECES[i][2]
    t_in = T["ego0"] + i * 0.42
    if t < t_in: return None
    home = (EX + dx, GY + dy)
    if t < T["crollo"]:
        k = ease((t - t_in) / 0.35)
        wob = 0.0 if t < T["crollo"] - 1.0 else 3 * math.sin(t * 22) * (t - T["crollo"] + 1.0)
        return (home[0], home[1] - 260 * (1 - k), wob, MARBLE)
    rub = RUBBLE[n]
    k = min(1, (t - T["crollo"] - 0.04 * i) / 0.55); k = max(0, k); e = k * k
    pos = (home[0] + (rub[0] - home[0]) * e, home[1] + (rub[1] - home[1]) * e, rub[2] * e)
    # pezzi portati via da Action Taker
    if n in CARRY:
        a, b = CARRY[n]
        if t >= a:
            q = ease((t - a) / (b - a)); tgt = new_pos(n)
            if t < b:
                x = rub[0] + (tgt[0] - rub[0]) * q; y = rub[1] + (tgt[1] - rub[1]) * q - 230 * math.sin(q * math.pi)
                return (x, y, rub[2] * (1 - q), MARBLE)
            return (tgt[0], tgt[1], 0, MARBLE)
    return (pos[0], pos[1], pos[2], MARBLE)

# chi viene portato e quando (dal JSON: [nome, inizio, fine])
CARRY = {n: (a, b) for n, a, b in C["trasporti"]}

def at_bricks(t):
    """Mattoni di Action Taker: prima casetta, pugno, poi base del palazzo nuovo."""
    out = []
    rng = random.Random(5)
    if t < T["pugno"]:
        rows = int(lin(t, 0.5, T["pugno"] - 0.3, 0, 9))
        for r in range(rows):
            w = 3 if r < 7 else (2 if r < 8 else 1)
            for c in range(w):
                out.append((AX + (c - (w - 1) / 2) * 44 + rng.uniform(-6, 6) + (11 if r % 2 else 0), GY - 11 - r * 21, rng.uniform(-5, 5)))
        return out, None
    return None, None

def brick(d, v, x, y, r, fill=BRICK, edge=BRICK_E):
    draw_piece(d, v, rect(42, 20), x, y, r, fill, edge)

def frame(t):
    img = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
    # camera: un po' più vicina sui momenti chiave
    z = keys(t, [(0, 1.08), (T["pugno"] - 1.2, 1.08), (T["pugno"] - 0.3, 1.22), (T["pugno"] + 0.8, 1.22), (T["pugno"] + 1.6, 1.08),
                 (T["karma"] - 0.3, 1.08), (T["karma"], 1.2), (T["karma"] + 1.0, 1.2), (T["karma"] + 1.6, 1.05)])
    cx = keys(t, [(0, 540), (T["pugno"] - 1.2, 540), (T["pugno"] - 0.3, 700), (T["pugno"] + 0.8, 700), (T["pugno"] + 1.6, 540),
                  (T["karma"] - 0.3, 540), (T["karma"], 620), (T["karma"] + 1.0, 620), (T["karma"] + 1.6, 540)])
    shake = 0.0
    for st in (T["crollo"] + 0.5, T["pugno"], T["karma"]):
        if 0 <= t - st < 0.35: shake = 10 * math.sin(t * 80) * (1 - (t - st) / 0.35)
    v = A.V(z, cx + shake, 935)
    # cielo e terreno
    for k in range(16):
        y0 = 120 * k; c = int(6 + min(k, 11) * 1.4); d.rectangle([0, y0, W, y0 + 120], fill=(c, c, c + 6))
    G = v.p(0, GY); d.rectangle([0, G[1], W, H], fill=(18, 18, 22)); d.line([(0, G[1]), (W, G[1])], fill=(85, 85, 95), width=3)
    for k in range(-2, 14):
        P = v.p(k * 90 + 20, GY + 26); d.line([P, (P[0] + v.s(40), P[1])], fill=(40, 40, 48), width=3)
    # palazzo nuovo di Action Taker: base di mattoni
    if t >= T["rifa0"]:
        rows = int(lin(t, T["rifa0"], T["rifa0"] + 0.9, 0, 4))
        rng = random.Random(8)
        for r in range(rows):
            for c in range(7):
                brick(d, v, AX - 135 + c * 45 + (10 if r % 2 else 0) + rng.uniform(-3, 3), GY - 11 - r * 21, rng.uniform(-3, 3))
    # finestre accese dietro le colonne (palazzo nuovo)
    if t >= T["luci"]:
        a = ease((t - T["luci"]) / 0.5)
        for dx in (-70, 0, 70):
            P0 = v.p(AX + dx - 22, GY - NEW_BASE_H - 26 - COL_H + 40); P1 = v.p(AX + dx + 22, GY - NEW_BASE_H - 26 - 30)
            d.rectangle([P0, P1], fill=tuple(int(c * a) for c in LIGHT))
    # pezzi del palazzo dell'Ego (anche quelli portati da Action Taker)
    for n, shape, _ in PIECES:
        s = ego_palace_state(n, t)
        if s: draw_piece(d, v, shape, s[0], s[1], s[2], s[3], MARBLE_E, n)
    # bandiera blu sul palazzo nuovo
    if t >= T["luci"]:
        top = new_pos("dome"); x0, y0 = top[0], top[1] - 29
        d.line([v.p(x0, y0), v.p(x0, y0 - 90)], fill=WHITE, width=int(v.s(5)))
        wv = math.sin(t * 6) * 6
        d.polygon([v.p(x0, y0 - 90), v.p(x0 + 60, y0 - 78 + wv), v.p(x0, y0 - 62)], fill=BLUE)
    # polvere dei crolli
    for st, x0 in ((T["crollo"] + 0.45, EX), (T["pugno"] + 0.1, AX)):
        k = t - st
        if 0 <= k < 1.2:
            rng = random.Random(int(x0))
            for i in range(26):
                ang = rng.uniform(math.pi, 2 * math.pi); sp = rng.uniform(80, 260)
                px_ = x0 + math.cos(ang) * sp * k * 1.6; py_ = GY - 10 + math.sin(ang) * sp * k * 0.6
                r = v.s(rng.uniform(10, 26) * (0.5 + k)); c = int(110 * (1 - k / 1.2)); Q = v.p(px_, py_)
                d.ellipse([Q[0] - r, Q[1] - r, Q[0] + r, Q[1] + r], fill=(c, c, c))
    # casetta di Action Taker e i mattoni che volano col pugno
    br, _ = at_bricks(t)
    if br:
        for x, y, r in br: brick(d, v, x, y, r)
    else:
        rng = random.Random(9); k = min(1, (t - T["pugno"]) / 0.7)
        if t < T["rifa0"] + 0.2:
            rows_prev = 9; rng2 = random.Random(5)
            for r in range(rows_prev):
                w = 3 if r < 7 else (2 if r < 8 else 1)
                for c in range(w):
                    x = AX + (c - (w - 1) / 2) * 44 + rng2.uniform(-6, 6) + (11 if r % 2 else 0); y = GY - 11 - r * 21; rr = rng2.uniform(-5, 5)
                    fx = x + rng.uniform(40, 260); fy = GY - 11 - rng.choice([0, 0, 21]); fr = rng.uniform(-90, 90)
                    e = k * k; brick(d, v, x + (fx - x) * e, y + (fy - y) * e - 160 * math.sin(k * math.pi) * rng.uniform(0.3, 1), rr + (fr - rr) * e)
    # PERFECTIONIST: progetto tratteggiato, mattoni in griglia perfetta, lentissimo
    bp = [(SX - 88, GY), (SX - 88, GY - 300), (SX, GY - 390), (SX + 88, GY - 300), (SX + 88, GY)]
    for (x0, y0), (x1, y1) in zip(bp, bp[1:]):
        L = math.hypot(x1 - x0, y1 - y0); nseg = int(L // 18)
        for k in range(0, nseg, 2):
            a0, a1 = k / nseg, min(1, (k + 1) / nseg)
            d.line([v.p(x0 + (x1 - x0) * a0, y0 + (y1 - y0) * a0), v.p(x0 + (x1 - x0) * a1, y0 + (y1 - y0) * a1)], fill=(70, 110, 160), width=int(v.s(3)))
    slot = lambda k: (SX - 63 + (k % 4) * 42, GY - 11 - (k // 4) * 21)
    placed = sum(1 for tb in PB if t >= tb)
    for k in range(placed): brick(d, v, *slot(k), 0, (238, 234, 228), BRICK_E)
    fin = t >= T["fine0"] + 0.4
    if not fin and placed < len(PB):
        tb = PB[placed]; ph = 1 - (tb - t) / 1.38                                     # 0..1 del ciclo
        hold = (PX + 70, GY - 190)                                                    # davanti al petto
        if ph < 0.65:                                                                 # lo guarda e lo misura
            hb = (hold[0], hold[1] - 6 * math.sin(t * 6)); arms = (0.3, 0.42)
            brick(d, v, hb[0], hb[1], 4 * math.sin(t * 5), (238, 234, 228), BRICK_E)
            if int(t * 4) % 2 == 0:
                d.line([v.p(hb[0] - 34, hb[1] - 20), v.p(hb[0] + 34, hb[1] - 20)], fill=(150, 200, 255), width=int(v.s(3)))
        else:                                                                         # lo posa con calma
            q = ease((ph - 0.65) / 0.35); sx_, sy_ = slot(placed)
            brick(d, v, hold[0] + (sx_ - hold[0]) * q, hold[1] + (sy_ - hold[1]) * q, 0, (238, 234, 228), BRICK_E); arms = (0.3, 0.3)
        A.figure(d, v, PX, GY, "focus", WHITE, k=0.86, arms=arms)
    else:
        A.figure(d, v, PX, GY, "big" if fin else "focus", WHITE, k=0.86, arms=(0.95, 0.95) if fin else (0.2, 0.2))
        if fin: brick(d, v, PX, GY - 405, 6 * math.sin(t * 2), (238, 234, 228), BRICK_E)
    # EGO
    ex = keys(t, [(0, EGO0), (T["pugno"] - 1.4, EGO0), (T["pugno"] - 0.35, AX - 150), (T["pugno"] + 0.6, AX - 150),
                  (T["pugno"] + 1.4, EGO0), (T["karma"] - 0.8, EGO0), (T["karma"] - 0.1, AX - 255), (T["karma"] + 0.05, AX - 255),
                  (T["karma"] + 0.6, PX - 40)])
    erot, ekind, earms = 0.0, "smug", (0.85, 0.85)
    if T["crollo"] <= t < T["pugno"] - 1.4: ekind, earms = "scared", (0.6, 0.6)
    if T["pugno"] - 1.4 <= t < T["pugno"] + 0.6: ekind, earms = "angry", ((0.1, 0.55) if t < T["pugno"] - 0.12 else (0.1, 0.62))
    if T["pugno"] + 0.6 <= t < T["karma"] - 0.8: ekind, earms = ("smug" if t < T["rifa0"] + 1.5 else "worried"), (0.1, 0.1)
    if T["karma"] - 0.8 <= t < T["karma"] + 0.05: ekind, earms = "angry", (0.1, 0.6)
    if t >= T["karma"] + 0.05:
        erot = keys(t, [(T["karma"] + 0.05, 0), (T["karma"] + 0.55, -88)]); ekind = "ko"; earms = (0.3, 0.3)
    ecol = WHITE
    head = A.figure(d, v, ex + (130 * math.sin(math.radians(-erot)) if erot else 0), GY, ekind, ecol, rot=erot, arms=earms, k=0.86)
    # ACTION TAKER
    ax_, akind, aarms, alegs = ATP, "focus", (0.2, 0.6 + 0.25 * math.sin(t * 9)), 0.0
    if T["pugno"] <= t < T["rifa0"]: akind, aarms = ("scared" if t < T["pugno"] + 0.8 else "worried"), (0.2, 0.2)
    for n, a, b in C["trasporti"]:                                                   # va a prendere i pezzi
        if a - 0.45 <= t < b:
            rub = RUBBLE[n]; tgt = new_pos(n)
            if t < a: ax_ = keys(t, [(a - 0.45, ATP if a == C['trasporti'][0][1] else new_pos(n)[0] - 150), (a, rub[0] + 40)]); aarms = (0.1, 0.1)
            else: ax_ = rub[0] + 40 + (tgt[0] - 150 - rub[0] - 40) * ease((t - a) / (b - a)); aarms = (0.95, 0.95)
            alegs = 0.6 * math.sin(t * 16); akind = "strain"
    if t >= T["luci"]: akind, aarms, ax_ = "big", (0.9, 0.9), keys(t, [(T['luci'], new_pos('dome')[0] - 150), (T['luci'] + 0.5, AX - 120)])
    A.figure(d, v, ax_, GY, akind, BLUE, arms=aarms, legs=alegs, k=0.86)
    # scoppio dei pugni
    for st, px_, py_ in ((T["pugno"], AX - 60, GY - 175), (T["karma"], AX - 160, GY - 175)):
        k = t - st
        if 0 <= k < 0.3:
            C0 = v.p(px_, py_); rr = v.s(40 + 160 * k); a_ = 1 - k / 0.3
            pts = [(C0[0] + (rr if j % 2 == 0 else rr * 0.45) * math.cos(j * math.pi / 8), C0[1] + (rr if j % 2 == 0 else rr * 0.45) * math.sin(j * math.pi / 8)) for j in range(16)]
            d.polygon(pts, fill=tuple(int(255 * a_) for _ in range(3)))
    # fumetti
    pos = {0: (EGO0, GY - 420), 1: (PX, GY - 420), 2: (ATP, GY - 420)}
    for i, s, a0, b0 in C["fumetti"]:
        if a0 <= t < b0:
            al = ease((t - a0) / 0.06) * (1 - ease((t - b0 + 0.06) / 0.06))
            p_ = (ex, GY - 420) if i == 0 else (pos[i] if i != 2 else (ax_, GY - 420))
            A.bubble(d, v, p_, s, al, size=28)
    # etichette
    if abs(ex - EGO0) < 5 or t >= T["karma"] + 0.6: A.label(d, v, ex if t < T["karma"] else PX - 110, GY + 40, "EGO", (215, 215, 220) if t < T["karma"] + 0.5 else (85, 85, 92))
    A.label(d, v, PX, GY + 72, "PERFECTIONIST", (215, 215, 220))
    if not (C["trasporti"][0][1] - 0.45 <= t < T["luci"]): A.label(d, v, min(ax_, 905), GY + 40, "ACTION TAKER", BLUE)
    A.caption(d, C["testi"], t, DUR)
    A.question(d, C["domanda"], t, C["domanda_t"], 420, 50)
    return img

if __name__ == "__main__":
    if len(sys.argv) > 3:
        frame(float(sys.argv[3])).save(OUT); sys.exit()
    ev = [(0.0, mc.s_hum(DUR, 0.03))]
    for s, a, b in C["testi"]: ev.append((a, mc.s_pop(0.25, 800)))
    for i in range(len(PIECES)): ev.append((T["ego0"] + i * 0.42 + 0.3, mc.s_tok(300, 0.06, 0.3)))
    for k in range(int((T["pugno"] - 0.8) / 0.4)): ev.append((0.5 + k * 0.4, mc.s_tok(220, 0.04, 0.15)))
    ev += [(T["crollo"] - 1.0, mc.s_crack(0.4)), (T["crollo"] - 0.4, mc.s_crack(0.6)), (T["crollo"] + 0.3, mc.s_thud(1.0, 50)), (T["crollo"] + 0.45, mc.s_crack(0.9)),
           (T["pugno"], mc.s_thud(1.0, 60)), (T["pugno"] + 0.05, mc.s_crack(0.9)), (T["pugno"] + 0.5, mc.s_tok(200, 0.06, 0.4)),
           (T["karma"], mc.s_thud(1.0, 90)), (T["karma"] + 0.02, mc.s_chime(0.3, 1500)), (T["karma"] + 0.55, mc.s_thud(0.7, 55)),
           (T["luci"], mc.s_rise(2.4, 0.45)), (C["domanda_t"], mc.s_chime(0.35, 660))]
    for n, a, b in C["trasporti"]: ev += [(a, mc.s_whoosh(0.4, 0.2)), (b, mc.s_tok(300, 0.06, 0.35))]
    for i, s, a, b in C["fumetti"]: ev.append((a, mc.s_pop(0.2, 650)))
    A.finish(OUT, DUR, frame, ev)
