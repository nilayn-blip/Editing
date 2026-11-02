"""Put the owner's talking face on a rendered reel.

Usage (in the avatar env, see README.md):
  python facecam.py REEL_DIR FACE.mp4 [MATTE.png]

FACE.mp4 is the lip-synced talking-head video (SadTalker, driven by the reel's own voice track, so it starts at 0 and
runs the whole reel). MATTE.png is a still alpha matte of the face photo (rembg "birefnet-portrait"); SadTalker
--still keeps the head in place, so one clean matte serves every frame with no edge flicker. Without it, each hook
frame is matted with u2net_human_seg (rougher). Reads REEL_DIR/timing.json and REEL_DIR/output/reel.mp4; writes
REEL_DIR/output/reel_face.mp4.

Layout (1080x1920, inside Instagram's safe area):
  hook        the owner as a head-and-shoulders bust beside the hook photo's subject; the photo behind softens
              (portrait-mode depth) while they speak
  lines       a round portrait with a gold ring under the captions
  end card    the portrait fades out so the chant card stays clean
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

d, face = sys.argv[1], sys.argv[2]
matte = sys.argv[3] if len(sys.argv) > 3 else None
T = json.load(open(os.path.join(d, "timing.json")))
R_ = json.load(open(os.path.join(d, "reel.json")))
SIDE = R_.get("facecam_side", "right")  # keep the hook photo's subject visible
IMG0, END, DUR = T["img0"], T["end"], T["dur"]
reel = os.path.join(d, "output", "reel.mp4")
out = os.path.join(d, "output", "reel_face.mp4")
work = tempfile.mkdtemp(prefix="facecam-")


def run(cmd):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)


probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", face], capture_output=True, text=True, check=True).stdout.strip().split(",")
W, H = int(probe[0]), int(probe[1])

# 1. matte for the hook bust: still (preferred) or per frame
if matte:
    m = np.asarray(Image.open(matte).convert("L").resize((W, H), Image.LANCZOS), np.float32)
else:
    from rembg import new_session, remove
    fr = os.path.join(work, "f0.png")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", face, "-frames:v", "1", fr])
    m = np.asarray(remove(Image.open(fr).convert("RGB"), session=new_session("u2net_human_seg"), only_mask=True,
                          post_process_mask=True), np.float32)
ys, xs = np.nonzero(m > 128)
head_top, head_l, head_r = ys.min(), np.percentile(xs[ys < ys.min() + 0.3 * H], 2), np.percentile(xs[ys < ys.min() + 0.3 * H], 98)
fade = np.clip((H - 1 - np.arange(H)) / (H * 0.04), 0, 1)[:, None]  # soften only the very bottom edge
Image.fromarray((m * fade).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)).save(os.path.join(work, "matte.png"))
# depth-of-field layer mask: none behind the hook caption, ramping in over 260 px (no visible seam)
ramp = np.clip((np.arange(1920) - 380) / 260, 0, 1)[:, None] * np.ones((1, 1080))
Image.fromarray((ramp * 255).astype(np.uint8)).save(os.path.join(work, "dof.png"))

# bust size: head about 340 px wide, standing on the bottom edge (face around y = 1250)
k = 340 / max(1.0, head_r - head_l)
bw, bh = int(W * k) // 2 * 2, int(H * k) // 2 * 2
head_cx = (head_l + head_r) / 2 * k
by = 1920 - bh
bx = {"right": 1080 - bw + 60, "left": -60, "center": (1080 - bw) // 2}[SIDE]
bx = int(min(max(bx, 240 - head_cx), 840 - head_cx))  # keep the face centre between x = 240 and 840

# 2. portrait ring (gold, with a soft glow), drawn once
R = 240  # portrait radius
S = 2 * R + 40
ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse((12, 12, S - 12, S - 12), outline=(255, 190, 70, 170), width=14)
ring.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
ImageDraw.Draw(ring).ellipse((17, 17, S - 17, S - 17), outline=(255, 207, 77, 255), width=5)
ring.save(os.path.join(work, "ring.png"))

# portrait crop: square around the head and a little shoulder
side = int(min(W, H, (head_r - head_l) * 1.75)) // 2 * 2
cx = int((head_l + head_r) / 2)
x0 = max(0, min(W - side, cx - side // 2))
y0 = max(0, min(H - side, int(head_top - 0.12 * side)))

# 3. composite
BX, BY = 540 - R, 1330 - R  # portrait centre (540, 1330): under the captions, above Instagram's caption area
t_in, t_out = IMG0 - 0.35, END - 0.25
fc = (
    f"[0:v]split=2[base][bg];"
    # portrait-mode depth: the hook photo softens and dims a little behind the speaker
    f"[bg]trim=0:{IMG0 + 0.1:.2f},setpts=PTS-STARTPTS,gblur=sigma=4,eq=brightness=-0.05,format=rgba[bgb];"
    f"[4:v]format=gray[dm];[bgb][dm]alphamerge,"
    f"fade=t=in:st=0:d=0.35:alpha=1,fade=t=out:st={t_in:.2f}:d=0.4:alpha=1[soft];"
    f"[base][soft]overlay=0:0:eof_action=pass[v0];"
    f"[1:v]fps=30,split=2[fa][fb];"
    # hook bust: matte, gentle grade toward the photo's light, fade in/out
    f"[fa]trim=0:{IMG0 + 0.1:.2f},setpts=PTS-STARTPTS,eq=saturation=0.85:brightness=-0.05:gamma=0.95,colorbalance=rs=-0.04:bs=0.04:rm=-0.03:bm=0.03,format=rgba[fa2];"
    f"[2:v]format=gray,scale={W}:{H}[ma];"
    f"[fa2][ma]alphamerge,scale={bw}:{bh},fade=t=in:st=0:d=0.35:alpha=1,fade=t=out:st={t_in:.2f}:d=0.4:alpha=1[cut];"
    # portrait: square crop -> circle with a feathered edge
    f"[fb]crop={side}:{side}:{x0}:{y0},scale={2 * R}:{2 * R},format=rgba,"
    f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*clip(({R}-hypot(X-{R},Y-{R}))/2.5,0,1)',"
    f"fade=t=in:st={t_in:.2f}:d=0.45:alpha=1,fade=t=out:st={t_out:.2f}:d=0.45:alpha=1[bub];"
    f"[3:v]format=rgba,fade=t=in:st={t_in + 0.1:.2f}:d=0.45:alpha=1,fade=t=out:st={t_out:.2f}:d=0.45:alpha=1[ring];"
    f"[v0][cut]overlay=x={bx}:y={by}:eof_action=pass:enable='lt(t,{IMG0 + 0.1:.2f})'[v1];"
    f"[v1][bub]overlay={BX}:{BY}:enable='between(t,{t_in:.2f},{t_out + 0.5:.2f})'[v2];"
    f"[v2][ring]overlay={BX - 20}:{BY - 20}:enable='between(t,{t_in:.2f},{t_out + 0.5:.2f})',format=yuv420p[v]"
)
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", reel, "-i", face,
     "-loop", "1", "-t", f"{IMG0 + 0.2:.2f}", "-i", os.path.join(work, "matte.png"),
     "-loop", "1", "-t", f"{DUR}", "-i", os.path.join(work, "ring.png"),
     "-loop", "1", "-t", f"{IMG0 + 0.2:.2f}", "-i", os.path.join(work, "dof.png"),
     "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-tune", "film",
     "-profile:v", "high", "-c:a", "copy", "-movflags", "+faststart", "-t", f"{DUR}", out])
print("wrote", out, f"(bust {bw}x{bh} at {bx},{by}; portrait crop {side} at {x0},{y0})")
