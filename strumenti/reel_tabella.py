#!/usr/bin/env python3
"""Reel tipo A "tabella a due colonne" (es. Abitudine | Costo all'anno) - Mentalità Capitale.

Stessa resa di reel_testo.py (testo fermo dal primo fotogramma su video in movimento), ma con il corpo
in due colonne: riquadri bianchi a sinistra (voce) e a destra (cifra), più due intestazioni.
Uso: python3 reel_tabella.py contenuto.json uscita.mp4 [secondo]

contenuto.json: sfondo, inizio_video, durata, y_inizio, titolo[], intestazioni[2], righe[[voce, cifra]],
invito[], nota
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel_testo import font, emoji_img, split_emoji, box, W, H, FPS, YELLOW, BLUE, WHITE, BLACK

XL, XR0, XR1 = 60, 720, 940     # colonna sinistra da XL; colonna destra tra XR0 e XR1 (le icone coprono x > 940)

def cell(layer, x, y, text, f, align="left", width=None, pad=(18, 10)):
    d = ImageDraw.Draw(layer)
    e, t = split_emoji(text)
    tw = d.textlength(t, font=f)
    ei = emoji_img(e, f.size) if e else None
    cw = tw + (ei.width + 10 if ei else 0)
    bw = width or cw + pad[0] * 2
    bh = f.size + pad[1] * 2 + 6
    x0 = x if align == "left" else x - bw / 2
    d.rounded_rectangle([x0, y, x0 + bw, y + bh], radius=14, fill=WHITE)
    tx = x0 + (bw - cw) / 2 if align == "center" else x0 + pad[0]
    if ei:
        layer.paste(ei, (int(tx), int(y + pad[1] + 4)), ei); tx += ei.width + 10
    d.text((tx, y + pad[1]), t, font=f, fill=BLACK)
    return x0 + bw, y + bh

def build_overlay(c):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = c.get("y_inizio", 300)
    y = box(ov, y, c["titolo"], font("Inter-Black.otf", c.get("f_titolo", 62)), YELLOW, BLACK, pad=(30, 18), gap=4) + 24
    fh, fr = font("Inter-ExtraBold.otf", c.get("f_intestazioni", 38)), font("Inter-Bold.otf", c.get("f_righe", 34))
    gap = c.get("spazio_righe", 10)
    cr = (XR0 + XR1) / 2
    _, yb = cell(ov, XL, y, c["intestazioni"][0], fh)
    cell(ov, cr, y, c["intestazioni"][1], fh, align="center")
    y = yb + 16
    for voce, cifra in c["righe"]:
        xe, yb = cell(ov, XL, y, voce, fr)
        assert xe < XR0 - 10, f"voce troppo lunga: {voce} ({xe:.0f} px)"
        cell(ov, cr, y, cifra, fr, align="center", width=XR1 - XR0 - 10)
        y = yb + gap
    if c.get("invito"):
        y = box(ov, y + 18, c["invito"], font("Inter-Black.otf", c.get("f_invito", 40)), BLUE, WHITE, pad=(26, 14)) + 10
    if c.get("nota"):
        fn = font("Inter-SemiBold.otf", 24); d = ImageDraw.Draw(ov)
        tw = d.textlength(c["nota"], font=fn)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((W / 2 - tw / 2, y + 12), c["nota"], font=fn, fill=(0, 0, 0, 220))
        ov = Image.alpha_composite(ov, sh.filter(ImageFilter.GaussianBlur(3)))
        ImageDraw.Draw(ov).text((W / 2 - tw / 2, y + 12), c["nota"], font=fn, fill=WHITE)
        y += 46
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(ov.split()[3].point(lambda a: int(a * 0.35)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(shadow, (0, 6)); out.alpha_composite(ov)
    return out, y

if __name__ == "__main__":
    c = json.load(open(sys.argv[1])); out = sys.argv[2]
    dur = c.get("durata", 7); ss = str(c.get("inizio_video", 0))
    ov, yb = build_overlay(c)
    print("fine del blocco di testo a y =", yb, "(deve restare sotto 1590)")
    ovp = "/tmp/_overlay_tabella.png"; ov.save(ovp)
    filt = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}[b];[b][1:v]overlay=0:0[v]"
    if len(sys.argv) > 3:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(float(ss) + float(sys.argv[3])), "-i", c["sfondo"], "-i", ovp,
                        "-filter_complex", filt, "-map", "[v]", "-frames:v", "1", out], check=True)
        sys.exit()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", ss, "-t", str(dur), "-i", c["sfondo"], "-i", ovp,
                    "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", filt, "-map", "[v]", "-map", "2:a", "-t", str(dur), "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], check=True)
