"""Put the owner's talking face on a rendered reel.

Usage (in the avatar env, see README.md):
  python facecam.py REEL_DIR FACE.mp4

FACE.mp4 is the lip-synced talking-head video (SadTalker, driven by the reel's own voice track, so it starts at 0 and
runs the whole reel). Reads REEL_DIR/timing.json and REEL_DIR/output/reel.mp4; writes REEL_DIR/output/reel_face.mp4.

Layout (1080x1920, inside Instagram's safe area):
  hook        the owner, background removed, standing in front of the hook photo (caption sits at the top)
  lines       a round portrait with a gold ring under the captions
  end card    the portrait fades out so the chant card stays clean
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

d, face = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(d, "timing.json")))
SIDE = json.load(open(os.path.join(d, "reel.json"))).get("facecam_side", "right")  # keep the hook photo's subject visible
IMG0, END, DUR = T["img0"], T["end"], T["dur"]
reel = os.path.join(d, "output", "reel.mp4")
out = os.path.join(d, "output", "reel_face.mp4")
work = tempfile.mkdtemp(prefix="facecam-")


def run(cmd):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)


# 1. background matte for the hook cut-out (only the hook frames need it)
from rembg import new_session, remove
frames = os.path.join(work, "f")
os.makedirs(frames)
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", face, "-t", f"{IMG0 + 0.1:.2f}", "-vf", "fps=30",
     os.path.join(frames, "%05d.png")])
sess = new_session("u2net_human_seg")
masks = os.path.join(work, "m")
os.makedirs(masks)
prev = None
for fn in sorted(os.listdir(frames)):
    m = np.asarray(remove(Image.open(os.path.join(frames, fn)).convert("RGB"), session=sess, only_mask=True,
                          post_process_mask=True), np.float32)
    m = m if prev is None else 0.6 * m + 0.4 * prev  # temporal smoothing: no edge flicker
    prev = m
    Image.fromarray(m.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(masks, fn))
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "30", "-i", os.path.join(masks, "%05d.png"),
     "-c:v", "ffv1", "-pix_fmt", "gray", os.path.join(work, "mask.mkv")])

# 2. portrait ring (gold, with a soft glow), drawn once
R = 240  # portrait radius
S = 2 * R + 40
ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse((12, 12, S - 12, S - 12), outline=(255, 190, 70, 170), width=14)
ring.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
ImageDraw.Draw(ring).ellipse((17, 17, S - 17, S - 17), outline=(255, 207, 77, 255), width=5)
ring.save(os.path.join(work, "ring.png"))

# face position in the source frame: centre of the matte on the first frame
m0 = np.asarray(Image.open(os.path.join(masks, sorted(os.listdir(masks))[0])), np.float32) / 255
H, W = m0.shape
ys, xs = np.nonzero(m0 > 0.5)
head_top = ys.min()
cx = int(np.median(xs[ys < head_top + 0.45 * H])) if len(xs) else W // 2
side = int(min(W, H) * 0.78)  # square crop: head and a little shoulder
cy = min(H - side // 2, head_top + int(side * 0.48))
x0, y0 = max(0, min(W - side, cx - side // 2)), max(0, cy - side // 2)

# 3. composite
BX, BY = 540 - R, 1330 - R  # portrait centre (540, 1330): under the captions, above Instagram's caption area
t_in, t_out = IMG0 - 0.35, END - 0.25
scale_h = 1300
CUT_X = {"right": "W-w+200", "left": "-200", "center": "(W-w)/2"}[SIDE]
fc = (
    f"[1:v]fps=30,split=2[fa][fb];"
    f"[2:v]format=gray[ma];"
    # hook cut-out: full figure, bottom-aligned, warm grade to sit in the photo
    f"[fa]trim=0:{IMG0 + 0.1:.2f},setpts=PTS-STARTPTS,format=rgba,eq=saturation=1.05:gamma=1.02[fa2];"
    f"[fa2][ma]alphamerge,scale=-2:{scale_h},fade=t=in:st=0:d=0.35:alpha=1,fade=t=out:st={t_in:.2f}:d=0.4:alpha=1[cut];"
    # portrait: square crop -> circle with a feathered edge
    f"[fb]crop={side}:{side}:{x0}:{y0},scale={2 * R}:{2 * R},format=rgba,"
    f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*clip(({R}-hypot(X-{R},Y-{R}))/2.5,0,1)',"
    f"fade=t=in:st={t_in:.2f}:d=0.45:alpha=1,fade=t=out:st={t_out:.2f}:d=0.45:alpha=1[bub];"
    f"[3:v]format=rgba,fade=t=in:st={t_in + 0.1:.2f}:d=0.45:alpha=1,fade=t=out:st={t_out:.2f}:d=0.45:alpha=1[ring];"
    f"[0:v][cut]overlay=x={CUT_X}:y=H-h:eof_action=pass:enable='lt(t,{IMG0 + 0.1:.2f})'[v1];"
    f"[v1][bub]overlay={BX}:{BY}:enable='between(t,{t_in:.2f},{t_out + 0.5:.2f})'[v2];"
    f"[v2][ring]overlay={BX - 20}:{BY - 20}:enable='between(t,{t_in:.2f},{t_out + 0.5:.2f})',format=yuv420p[v]"
)
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", reel, "-i", face, "-i", os.path.join(work, "mask.mkv"),
     "-loop", "1", "-t", f"{DUR}", "-i", os.path.join(work, "ring.png"),
     "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-tune", "film",
     "-profile:v", "high", "-c:a", "copy", "-movflags", "+faststart", "-t", f"{DUR}", out])
print("wrote", out)
