# Avatar: the owner's cloned voice and talking face

Makes a reel spoken in the owner's own (cloned) voice, with their lip-synced face: a cut-out of them in front of the
hook photo, then a round portrait with a gold ring under the story captions.

**Privacy.** This repository is public. The voice pack (`conds.pt`, `ref.wav`, `speaker_centre.npy`) can make speech
in the owner's voice, and the face photos are personal. Keep both in `reel_kit/avatar/private/` (git-ignored) or in
the owner's private storage. Never commit them. Use them only for the owner's own page, with their consent.

## Setup (CPU only; about 15 minutes and 6 GB)
```
mkdir -p /opt/ai && cd /opt/ai
# voice: Chatterbox Multilingual (MIT licence; it adds Resemble's inaudible Perth watermark) + Whisper for checks
uv venv -p python3.11 voice && VIRTUAL_ENV=/opt/ai/voice uv pip install --index-strategy unsafe-best-match \
  --extra-index-url https://download.pytorch.org/whl/cpu "torch==2.6.0+cpu" "torchaudio==2.6.0+cpu" chatterbox-tts \
  faster-whisper noisereduce "setuptools<81"
# face: SadTalker (Apache-2.0) with GFPGAN face restoration
git clone --depth 1 https://github.com/OpenTalker/SadTalker.git && uv venv -p python3.11 talk && \
  VIRTUAL_ENV=/opt/ai/talk uv pip install --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cpu \
  "torch==2.1.2+cpu" "torchvision==0.16.2+cpu" "torchaudio==2.1.2+cpu" numpy==1.23.4 face_alignment==1.3.5 imageio==2.34.2 \
  imageio-ffmpeg==0.5.1 librosa==0.9.2 numba resampy==0.3.1 pydub==0.25.1 scipy==1.10.1 kornia==0.6.8 tqdm yacs==0.1.8 \
  pyyaml joblib==1.1.0 scikit-image==0.19.3 basicsr==1.4.2 facexlib==0.3.0 gfpgan av safetensors "setuptools<70" && \
  (cd SadTalker && bash scripts/download_models.sh)
# background removal for the hook cut-out
uv venv -p python3.11 seg && VIRTUAL_ENV=/opt/ai/seg uv pip install "rembg[cpu]" opencv-python-headless
```

## 1. Build the voice pack (once)
Give it the owner's recordings: phone videos or voice notes, ideally 1–3 minutes of them talking, with nobody else.
```
/opt/ai/voice/bin/python reel_kit/avatar/voice_profile.py reel_kit/avatar/private/voicepack rec1.wav rec2.wav
```
It finds the speech, removes the background noise, and drops anything that isn't the main speaker (announcements,
other people) by speaker-embedding similarity. It keeps the cleanest ~10 s as the cloning reference and averages the
speaker identity over all the clean speech. `profile.json` reports how similar each recording is to the main voice.
Check it: a recording well below ~0.8 is probably not the owner.

## 2. Make a reel
```
reel_kit/avatar/make_reel.sh reels/NN-slug reel_kit/avatar/private/voicepack reel_kit/avatar/private/face.jpg \
  reel_kit/avatar/private/face_matte.png   # still matte of the photo: rembg -m birefnet-portrait
```
- `clone_best.py` speaks every line 4 times (up to 8 for unclear lines) and keeps the take that Whisper transcribes
  closest to the script and that sounds closest to the owner. Scores go to `.work/avatar/voice.json`.
- `kit.py myvoice … sound build render` syncs the captions to that voice and renders the reel (`"facecam": true` moves
  the hook caption to the top and adds a dark band behind it).
- SadTalker animates the face photo to the reel's own voice track, so lips line up from t = 0. Its built-in
  enhancer is skipped (~8 s/frame on CPU); `fast_enhance.py` restores only the hook frames, the only place the face
  is shown full size.
- `facecam.py` composites it: `output/reel_face.mp4`. Set `"facecam_side": "left" | "right" | "center"` in
  reel.json to keep the hook photo's subject visible beside the owner.

Face photo: front-facing, eye level, even light, mouth closed, head and shoulders (the best of the owner's photos).
Time on this 4-core CPU: voice about 5–10 min, face about 50 min per 20 s reel (+ about 5 min to restore the hook).
Test a new setup on a 2-second clip first: SadTalker only writes its video at the very end.
