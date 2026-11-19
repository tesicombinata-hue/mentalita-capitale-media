#!/usr/bin/env python3
"""Reel "testo su video" (scheda A di claude/GUIDA-REEL.md) - Mentalità Capitale.

Tutto il testo fermo dal primo fotogramma, riquadri ad alto contrasto, sfondo chiaro con zoom lento.
Uso: python3 reel_testo.py contenuto.json uscita.mp4 [secondo]   (con il secondo salva solo un fotogramma .png)

contenuto.json:
{
  "sfondo": "bg.mp4",                # VIDEO di giorno con movimento vero (consigliato) oppure immagine .jpg
  "inizio_video": 0,                 # secondo da cui parte il video di sfondo
  "durata": 6.5,
  "titolo": ["RIGA 1", "RIGA 2"],    # riquadro giallo, testo nero
  "righe": ["💶 testo", "..."],       # riquadri bianchi, testo nero grassetto; l'emoji iniziale è facoltativa
  "chiusura": ["riga", "riga"],       # riquadro bianco, testo nero (facoltativo)
  "invito": ["Commenta PAROLA", "..."],  # riquadro blu #4DA3FF, testo bianco
  "nota": "Fonte: ..."               # testo piccolo bianco con ombra (facoltativo)
}
"""
import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/opentype/inter/"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YELLOW, BLUE, WHITE, BLACK = (255, 214, 10), (77, 163, 255), (255, 255, 255), (12, 12, 12)
MAXW = 860          # larghezza massima dei riquadri
CX = W // 2         # centro orizzontale

def font(name, size): return ImageFont.truetype(FD + name, size)

_ef = ImageFont.truetype(EMOJI, 109)
def emoji_img(ch, size):
    im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=_ef, embedded_color=True)
    im = im.crop(im.getbbox() or (0, 0, 1, 1))
    r = size / im.height
    return im.resize((max(1, int(im.width * r)), size), Image.LANCZOS)

def split_emoji(s):
    """separa un'eventuale emoji iniziale dal testo"""
    if s and ord(s[0]) > 0x2000 and s[0] not in "→€–":
        i = 1
        while i < len(s) and (ord(s[i]) in (0xFE0F, 0x200D) or ord(s[i]) > 0x1F000):
            i += 1
        return s[:i], s[i:].lstrip()
    return None, s

def box(layer, y, lines, f, fill, color, pad=(26, 14), radius=18, gap=6, emoji_size=None):
    d = ImageDraw.Draw(layer)
    parts = [split_emoji(l) for l in lines]
    lh = f.size + gap
    widths = []
    for e, t in parts:
        w = d.textlength(t, font=f)
        if e: w += emoji_img(e, emoji_size or f.size).width + 12
        widths.append(w)
    bw = min(MAXW, max(widths) + pad[0] * 2)
    bh = lh * len(lines) - gap + pad[1] * 2 + 6
    x0 = CX - bw / 2
    d.rounded_rectangle([x0, y, x0 + bw, y + bh], radius=radius, fill=fill)
    for i, ((e, t), w) in enumerate(zip(parts, widths)):
        tx = CX - w / 2; ty = y + pad[1] + i * lh
        if e:
            ei = emoji_img(e, emoji_size or f.size)
            layer.paste(ei, (int(tx), int(ty + 4)), ei)
            tx += ei.width + 12
        d.text((tx, ty), t, font=f, fill=color)
    return y + bh

def build_overlay(c):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = c.get("y_inizio", 300)
    y = box(ov, y, c["titolo"], font("Inter-Black.otf", 60), YELLOW, BLACK, pad=(30, 18), gap=4) + 26
    fr = font("Inter-Bold.otf", 40)
    for r in c["righe"]:
        y = box(ov, y, [r], fr, WHITE, BLACK, pad=(22, 10), radius=14, emoji_size=40) + 12
    if c.get("chiusura"):
        y = box(ov, y + 14, c["chiusura"], font("Inter-ExtraBold.otf", 40), WHITE, BLACK, pad=(24, 12)) + 12
    if c.get("invito"):
        y = box(ov, y + 14, c["invito"], font("Inter-Black.otf", 38), BLUE, WHITE, pad=(24, 12)) + 12
    if c.get("nota"):
        d = ImageDraw.Draw(ov); fn = font("Inter-SemiBold.otf", 24)
        tw = d.textlength(c["nota"], font=fn)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((CX - tw / 2, y + 16), c["nota"], font=fn, fill=(0, 0, 0, 200))
        ov = Image.alpha_composite(ov, sh.filter(ImageFilter.GaussianBlur(3)))
        ImageDraw.Draw(ov).text((CX - tw / 2, y + 16), c["nota"], font=fn, fill=WHITE)
        y += 50
    # ombra morbida sotto i riquadri, per staccarli dallo sfondo
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(ov.split()[3].point(lambda a: int(a * 0.35)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(shadow, (0, 6)); out.alpha_composite(ov)
    return out, y

def frame(bg, ov, t, dur):
    z = 1.0 + 0.06 * (t / dur)                 # zoom lento
    w, h = int(W * z), int(H * z)
    im = bg.resize((w, h), Image.BILINEAR).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))
    im = im.convert("RGBA"); im.alpha_composite(ov)
    return im.convert("RGB")

if __name__ == "__main__":
    c = json.load(open(sys.argv[1])); out = sys.argv[2]
    dur = c.get("durata", 6.5)
    if c["sfondo"].lower().endswith((".mp4", ".mov")):
        # sfondo VIDEO (consigliato: movimento vero). Il testo è un livello fisso sopra il video.
        ov, ybottom = build_overlay(c)
        print("fine del blocco di testo a y =", ybottom, "(sotto 1590 resta libero)")
        ov.save("_overlay.png")
        ss = str(c.get("inizio_video", 0))
        if len(sys.argv) > 3:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(float(ss) + float(sys.argv[3])), "-i", c["sfondo"], "-i", "_overlay.png",
                            "-filter_complex", f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[b];[b][1:v]overlay=0:0",
                            "-frames:v", "1", out], check=True)
            sys.exit()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", ss, "-t", str(dur), "-i", c["sfondo"], "-i", "_overlay.png",
                        "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=44100:cl=stereo",
                        "-filter_complex", f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}[b];[b][1:v]overlay=0:0[v]",
                        "-map", "[v]", "-map", "2:a", "-t", str(dur), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", out], check=True)
        sys.exit()
    bg = Image.open(c["sfondo"]).convert("RGB")
    if bg.size != (W, H):
        r = max(W / bg.width, H / bg.height); bg = bg.resize((int(bg.width * r) + 1, int(bg.height * r) + 1))
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.resize((int(W * 1.08), int(H * 1.08)), Image.LANCZOS).crop((int(W * 0.04), int(H * 0.04), int(W * 0.04) + W, int(H * 0.04) + H))
    ov, ybottom = build_overlay(c)
    print("fine del blocco di testo a y =", ybottom, "(sotto 1590 resta libero)")
    if len(sys.argv) > 3:
        frame(bg, ov, float(sys.argv[3]), dur).save(out); sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out],
                         stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame(bg, ov, i / FPS, dur).tobytes())
    p.stdin.close(); p.wait()
