"""Sharpen a SadTalker --still video's face with GFPGAN, fast.

Usage (SadTalker env, run from /opt/ai/SadTalker so the weights resolve):
  python fast_enhance.py IN.mp4 OUT.mp4 [UNTIL_SECONDS]

With UNTIL_SECONDS only the frames before it are restored (the facecam shows the face full size only under the
hook; the round portrait shows it at about the size SadTalker rendered it, where restoring changes nothing).

SadTalker's own --enhancer runs face detection, parsing and a 2x upscale on every full frame (~8 s/frame on CPU).
In --still mode the head barely moves, so this finds the face once (re-checked every 50 frames), restores only the
aligned 512x512 crop each frame and blends it back with a feathered mask (no 2x upscale, no per-frame detection).
"""
import subprocess, sys
import cv2, numpy as np, torch
from gfpgan import GFPGANer
from basicsr.utils import img2tensor, tensor2img
from torchvision.transforms.functional import normalize

src, dst = sys.argv[1], sys.argv[2]
UNTIL = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
torch.set_num_threads(4)
g = GFPGANer(model_path="gfpgan/weights/GFPGANv1.4.pth", upscale=1, arch="clean", channel_multiplier=2, bg_upsampler=None)
fh = g.face_helper

cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS) or 25
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
enc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                        "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "medium",
                        "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)

# feathered blend mask in crop space
m = np.zeros((512, 512), np.float32)
cv2.ellipse(m, (256, 270), (205, 240), 0, 0, 360, 1.0, -1)
m = cv2.GaussianBlur(m, (0, 0), 18)[..., None]

affine, n = None, 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if n / fps >= UNTIL:
        enc.stdin.write(frame.tobytes()); n += 1
        continue
    if affine is None or n % 50 == 0:
        fh.clean_all()
        fh.read_image(frame)
        if fh.get_face_landmarks_5(only_center_face=True, eye_dist_threshold=5) > 0:
            fh.align_warp_face()
            affine = fh.affine_matrices[0].copy()
    if affine is not None:
        crop = cv2.warpAffine(frame, affine, (512, 512), borderMode=cv2.BORDER_REFLECT)
        t = img2tensor(crop.astype(np.float32) / 255.0, bgr2rgb=True, float32=True)
        normalize(t, (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), inplace=True)
        with torch.no_grad():
            out = g.gfpgan(t.unsqueeze(0), return_rgb=False, weight=0.5)[0]
        restored = tensor2img(out.squeeze(0), rgb2bgr=True, min_max=(-1, 1)).astype(np.float32)
        inv = cv2.invertAffineTransform(affine)
        back = cv2.warpAffine(restored, inv, (W, H))
        mask = cv2.warpAffine(m, inv, (W, H))[..., None]
        frame = (back * mask + frame.astype(np.float32) * (1 - mask)).clip(0, 255).astype(np.uint8)
    enc.stdin.write(frame.tobytes())
    n += 1
    if n % 25 == 0:
        print("frames", n, flush=True)
enc.stdin.close()
enc.wait()
print("wrote", dst, n, "frames")
