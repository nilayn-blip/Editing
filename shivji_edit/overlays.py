"""Render the motion-graphics layer for the Shivji temple edit.

Writes raw RGBA frames (1080x1920 @ 30fps) to stdout; build.sh pipes them
into ffmpeg and composites them over the graded footage.

Usage: python3 overlays.py FONT_DIR DURATION_SECONDS | ffmpeg -f rawvideo ...
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
FONT_DIR = sys.argv[1]
DUR = float(sys.argv[2])

DEVA = os.path.join(FONT_DIR, "tiro.ttf")        # Tiro Devanagari Sanskrit
LATIN = os.path.join(FONT_DIR, "cinzel.ttf")     # Cinzel

GOLD_TOP, GOLD_MID, GOLD_BOT = (255, 244, 200), (247, 198, 74), (196, 128, 28)


# ---------------------------------------------------------------- helpers
def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def window(t, t_in, t_out, fade_in=0.5, fade_out=0.5):
    """0..1 opacity for an element visible between t_in and t_out."""
    if t < t_in or t > t_out:
        return 0.0
    return ease_in_out((t - t_in) / fade_in) * ease_in_out((t_out - t) / fade_out)


def gold_gradient(w, h):
    y = np.linspace(0, 1, h)[:, None]
    stops = np.array([GOLD_TOP, GOLD_MID, GOLD_BOT], float)
    top = stops[0] + (stops[1] - stops[0]) * np.clip(y / 0.55, 0, 1)
    rgb = np.where(y < 0.55, top, stops[1] + (stops[2] - stops[1]) * np.clip((y - 0.55) / 0.45, 0, 1))
    return np.ascontiguousarray(np.broadcast_to(rgb[:, None, :], (h, w, 3))).astype(np.uint8)


def text_layer(text, font_path, size, tracking=0, glow=(255, 150, 30), glow_r=18,
               shadow=True, solid=None):
    """Gold-gradient text with drop shadow and warm outer glow, on a padded RGBA canvas."""
    font = ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.RAQM)
    # measure (with manual tracking for latin caps)
    if tracking:
        widths = [font.getlength(c) for c in text]
        tw = int(sum(widths) + tracking * (len(text) - 1))
    else:
        tw = int(font.getlength(text))
    asc, desc = font.getmetrics()
    pad = glow_r * 3
    cw, ch = tw + pad * 2, asc + desc + pad * 2
    mask = Image.new("L", (cw, ch), 0)
    d = ImageDraw.Draw(mask)
    if tracking:
        x = pad
        for c, wdt in zip(text, widths):
            d.text((x, pad), c, font=font, fill=255)
            x += wdt + tracking
    else:
        d.text((pad, pad), text, font=font, fill=255)

    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    if shadow:
        sh = mask.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.75))
        sl = Image.new("RGBA", (cw, ch), (20, 6, 0, 0))
        sl.putalpha(sh)
        out = Image.alpha_composite(out, sl.transform(sl.size, Image.AFFINE, (1, 0, -3, 0, 1, -5)))
    if glow:
        gl = Image.new("RGBA", (cw, ch), glow + (0,))
        gl.putalpha(mask.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: int(min(255, v * 1.1))))
        out = Image.alpha_composite(out, gl)
    fill = Image.fromarray(gold_gradient(cw, ch)) if solid is None else Image.new("RGB", (cw, ch), solid)
    fill = fill.convert("RGBA")
    fill.putalpha(mask)
    return Image.alpha_composite(out, fill)


def ornament_line(length, color=(247, 198, 74)):
    """Thin gold rule fading at both ends with a diamond in the middle."""
    h = 40
    im = Image.new("RGBA", (length, h), (0, 0, 0, 0))
    a = np.zeros((h, length), np.uint8)
    xs = np.linspace(-1, 1, length)
    fall = (1 - np.abs(xs) ** 2.5) * 255
    a[h // 2 - 1:h // 2 + 2, :] = fall.astype(np.uint8)
    rgb = np.zeros((h, length, 3), np.uint8)
    rgb[:] = color
    im = Image.fromarray(np.dstack([rgb, a]), "RGBA")
    d = ImageDraw.Draw(im)
    c, r = length // 2, 11
    d.polygon([(c, h // 2 - r), (c + r, h // 2), (c, h // 2 + r), (c - r, h // 2)], fill=color + (255,))
    d.polygon([(c, h // 2 - 5), (c + 5, h // 2), (c, h // 2 + 5), (c - 5, h // 2)], fill=(120, 50, 0, 255))
    glow = im.filter(ImageFilter.GaussianBlur(5))
    return Image.alpha_composite(glow, im)


def with_alpha(im, a):
    if a >= 0.999:
        return im
    arr = np.array(im)
    arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def scaled(im, s):
    if abs(s - 1) < 1e-3:
        return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)


def paste_center(canvas, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.003:
        return
    im = with_alpha(scaled(im, scale), alpha)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def wipe(im, frac):
    """Left-to-right soft reveal."""
    if frac >= 1:
        return im
    arr = np.array(im)
    x = np.arange(arr.shape[1])
    edge = frac * (arr.shape[1] + 120) - 60
    m = np.clip((edge - x) / 60 + 0.5, 0, 1)
    arr[:, :, 3] = (arr[:, :, 3] * m[None, :]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ------------------------------------------------------------ static assets
title_deva = text_layer("ॐ नमः शिवाय", DEVA, 132, glow_r=22)
title_name = text_layer("श्री समर्थेश्वर महादेव", DEVA, 72, glow_r=14)
title_loc = text_layer("C.G. ROAD  ·  AHMEDABAD", LATIN, 32, tracking=10, glow_r=10, solid=(255, 236, 190))
line_short = ornament_line(560)
lower_deva = text_layer("॥ हर हर महादेव ॥", DEVA, 112, glow_r=20)
lower_latin = text_layer("HAR HAR MAHADEV", LATIN, 42, tracking=12, glow_r=12, solid=(255, 236, 190))
end_om = text_layer("ॐ", DEVA, 330, glow_r=40)
end_deva = text_layer("श्री समर्थेश्वर महादेव", DEVA, 104, glow_r=20)
end_latin = text_layer("SAMARTHESHWAR MAHADEV", LATIN, 40, tracking=10, glow_r=10)
end_sub = text_layer("C.G. ROAD  ·  AHMEDABAD", LATIN, 30, tracking=10, glow_r=8, solid=(255, 236, 190))
line_long = ornament_line(700)


def bottom_band(h_band=760, max_a=0.75):
    a = np.zeros((H, W), np.float32)
    y = np.arange(H)
    ramp = np.clip((y - (H - h_band)) / h_band, 0, 1) ** 1.4
    a[:] = ramp[:, None] * max_a
    rgb = np.zeros((H, W, 3), np.uint8)
    rgb[:] = (18, 6, 0)
    return Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), "RGBA")


def top_band(h_band=1050, max_a=0.75):
    arr = np.array(bottom_band(h_band, max_a))[::-1]
    return Image.fromarray(np.ascontiguousarray(arr), "RGBA")


BOTTOM = bottom_band()
TOP = top_band()


def make_rays():
    """Soft god-rays fanning down from above the shrine."""
    size = 2400
    im = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(im)
    c = size // 2
    rnd = np.random.default_rng(7)
    for i in range(22):
        ang = math.radians(i * (360 / 22) + rnd.uniform(-4, 4))
        width = math.radians(rnd.uniform(1.2, 3.2))
        r = size
        pts = [(c, c),
               (c + r * math.cos(ang - width), c + r * math.sin(ang - width)),
               (c + r * math.cos(ang + width), c + r * math.sin(ang + width))]
        d.polygon(pts, fill=int(rnd.uniform(90, 200)))
    im = im.filter(ImageFilter.GaussianBlur(18))
    # radial falloff
    yy, xx = np.mgrid[0:size, 0:size]
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (size / 2)
    a = np.array(im, np.float32) * np.clip(1 - rr, 0, 1) ** 1.6
    return Image.fromarray(a.astype(np.uint8))


RAYS = make_rays()


def rays_frame(t, strength):
    rot = RAYS.rotate(t * 2.2, resample=Image.BILINEAR)
    c = rot.width // 2
    crop = rot.crop((c - W // 2, c - 260, c + W // 2, c - 260 + H))  # source sits ~260px above top
    a = (np.array(crop, np.float32) * strength).astype(np.uint8)
    rgb = np.zeros((H, W, 3), np.uint8)
    rgb[:] = (255, 214, 140)
    return Image.fromarray(np.dstack([rgb, a]), "RGBA")


def flash_frame(strength):
    """Warm radial light-leak used across the punch-in zoom."""
    yy, xx = np.mgrid[0:H:4, 0:W:4]
    r = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.38) / H) ** 2)
    a = np.clip(1 - r / 0.75, 0, 1) ** 1.5 * strength
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    rgb = Image.new("RGB", (W, H), (255, 200, 110))
    rgb = rgb.convert("RGBA")
    rgb.putalpha(im)
    return rgb


# particles: golden embers drifting upward
rng = np.random.default_rng(11)
N = 70
P_X = rng.uniform(0, W, N)
P_Y0 = rng.uniform(0, H * 1.3, N)
P_SPEED = rng.uniform(40, 140, N)
P_SIZE = rng.uniform(2.0, 6.5, N)
P_SWAY = rng.uniform(10, 40, N)
P_PHASE = rng.uniform(0, 6.28, N)
P_TW = rng.uniform(1.5, 4.0, N)


def particles_frame(t, strength):
    s = 2  # draw at half-res, upscale for softness
    im = Image.new("RGBA", (W // s, H // s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(N):
        y = (P_Y0[i] - P_SPEED[i] * t) % (H * 1.3) - H * 0.15
        x = P_X[i] + P_SWAY[i] * math.sin(t * 0.9 + P_PHASE[i])
        tw = 0.55 + 0.45 * math.sin(t * P_TW[i] + P_PHASE[i])
        # fade towards the top of frame
        a = strength * tw * min(1.0, max(0.0, y / (H * 0.25)))
        if a <= 0.02:
            continue
        r = P_SIZE[i] / s
        col = (255, int(190 + 50 * tw), 90)
        d.ellipse((x / s - r * 2.2, y / s - r * 2.2, x / s + r * 2.2, y / s + r * 2.2), fill=col + (int(60 * a),))
        d.ellipse((x / s - r, y / s - r, x / s + r, y / s + r), fill=(255, 245, 210, int(255 * a)))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    return im.resize((W, H), Image.BILINEAR)


def mandala(t, radius=250):
    """Slowly rotating dotted ring behind the end-card Om."""
    size = radius * 2 + 80
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    gold = (247, 198, 74)
    for ring, (rr, n, dot, spin) in enumerate([(radius, 48, 4, 8), (radius - 30, 24, 7, -12), (radius + 22, 96, 2, 5)]):
        for k in range(n):
            ang = math.radians(k * 360 / n + t * spin)
            x, y = c + rr * math.cos(ang), c + rr * math.sin(ang)
            d.ellipse((x - dot, y - dot, x + dot, y + dot), fill=gold + (230,))
    d.ellipse((c - radius + 52, c - radius + 52, c + radius - 52, c + radius - 52), outline=gold + (170,), width=2)
    glow = im.filter(ImageFilter.GaussianBlur(6))
    return Image.alpha_composite(glow, im)


# -------------------------------------------------------------- timeline
# Output timing (see build.sh):
#   0.00 - 0.90  hook: close-up of the shivling
#   0.90 - 2.07  wide shot (reframed, title)
#   2.07 - 4.10  camera push-in, slowed 0.8x
#   4.10 - 9.50  darshan hold, slowed 0.8x with slow digital push-in
#   9.50 - end   held last frame, blurred, end card
CUT_WIDE, CUT_ZOOM, CUT_HOLD, CUT_END = 0.90, 2.07, 4.10, 9.35


def frame(t):
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 0) gold flash on the hook -> wide cut
    fl = math.exp(-((t - CUT_WIDE) / 0.12) ** 2) * 0.75
    if fl > 0.01:
        cv.alpha_composite(flash_frame(fl))

    # 1) opening title over the wide shot
    t_in, t_out = CUT_WIDE + 0.15, CUT_ZOOM + 1.6
    a = window(t, t_in, t_out, 0.6, 0.6)
    if a > 0:
        cv.alpha_composite(with_alpha(TOP, a))
        p = ease_out((t - t_in) / 1.2)
        cy = 330 - 30 * (1 - p)
        paste_center(cv, title_deva, W / 2, cy, a, 1.12 - 0.12 * p)
        paste_center(cv, wipe(line_short, ease_out((t - t_in - 0.35) / 0.9)), W / 2, cy + 105, a)
        a2 = a * ease_in_out((t - t_in - 0.45) / 0.6)
        paste_center(cv, title_name, W / 2, cy + 178 + 15 * (1 - ease_out((t - t_in - 0.45) / 0.8)), a2)
        paste_center(cv, title_loc, W / 2, cy + 252, a * ease_in_out((t - t_in - 0.75) / 0.6))

    # 2) light leak riding the camera push-in
    fl = math.sin(math.pi * min(max((t - CUT_ZOOM - 0.1) / 1.9, 0), 1)) ** 2 * 0.40
    if fl > 0.01:
        cv.alpha_composite(flash_frame(fl))

    # 3) god-rays + embers on the deity (hook and hold)
    ray_a = (window(t, 0.0, CUT_WIDE, 0.3, 0.15) + window(t, CUT_HOLD - 0.6, DUR, 1.2, 0.8)) * 0.20
    if ray_a > 0:
        cv.alpha_composite(rays_frame(t, ray_a))
    pa = max(window(t, 0.0, CUT_WIDE + 0.3, 0.3, 0.3), window(t, CUT_ZOOM + 0.8, DUR, 1.0, 0.6))
    if pa > 0:
        cv.alpha_composite(particles_frame(t, pa))

    # 4) lower third
    l_in, l_out = CUT_HOLD + 0.5, CUT_HOLD + 4.5
    a = window(t, l_in, l_out, 0.45, 0.5)
    if a > 0:
        cv.alpha_composite(with_alpha(BOTTOM, a))
        rev = ease_out((t - l_in) / 0.9)
        cy = 1565 + 40 * (1 - ease_out((t - l_in) / 0.7))
        paste_center(cv, wipe(lower_deva, rev), W / 2, cy, a)
        paste_center(cv, wipe(line_short, ease_out((t - l_in - 0.3) / 0.8)), W / 2, cy + 92, a)
        paste_center(cv, lower_latin, W / 2, cy + 148, a * ease_in_out((t - l_in - 0.6) / 0.6))

    # 5) end card; footage is blurred/darkened in ffmpeg
    e = CUT_END
    a = window(t, e, DUR + 1, 0.8, 0.1)
    if a > 0:
        p = ease_out((t - e) / 1.4)
        cy = 760
        paste_center(cv, mandala(t), W / 2, cy, a * 0.85, 0.85 + 0.15 * p)
        pulse = 1 + 0.02 * math.sin(t * 3)
        paste_center(cv, end_om, W / 2, cy - 10, a, (0.9 + 0.1 * p) * pulse)
        a2 = a * ease_in_out((t - e - 0.55) / 0.6)
        paste_center(cv, end_deva, W / 2, 1170 + 25 * (1 - ease_out((t - e - 0.55) / 0.8)), a2)
        paste_center(cv, wipe(line_long, ease_out((t - e - 0.85) / 0.9)), W / 2, 1268, a2)
        a3 = a * ease_in_out((t - e - 1.15) / 0.6)
        paste_center(cv, end_latin, W / 2, 1330, a3)
        paste_center(cv, end_sub, W / 2, 1392, a3 * 0.9)

    return cv


def main():
    out = sys.stdout.buffer
    for i in range(int(round(DUR * FPS))):
        out.write(frame(i / FPS).tobytes())


if __name__ == "__main__":
    main()
