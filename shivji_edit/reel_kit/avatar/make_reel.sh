#!/bin/bash
# Make a reel spoken by the owner's cloned voice, with their lip-synced face.
# Usage: reel_kit/avatar/make_reel.sh reels/NN-slug VOICEPACK_DIR FACE_PHOTO.jpg
# Needs the three envs from README.md (/opt/ai/voice, /opt/ai/talk + /opt/ai/SadTalker, /opt/ai/seg).
set -euo pipefail
cd "$(dirname "$0")/../.."  # shivji_edit/
D=$1; PACK=$(realpath "$2"); PHOTO=$(realpath "$3")
AV=reel_kit/avatar
W=$D/.work/avatar; mkdir -p "$W"

# 1. narration in the cloned voice: best of 4 takes per line (more for unclear lines), one take with 1 s pauses
/opt/ai/voice/bin/python $AV/clone_best.py "$D" "$PACK" "$W/voice.wav" 4

# 2. captions synced to that voice, score, page and the plain render (the facecam layout moves the hook caption up)
python3 - "$D" <<'EOF'
import json, sys
p = sys.argv[1] + "/reel.json"; r = json.load(open(p)); r["facecam"] = True
json.dump(r, open(p, "w"), ensure_ascii=False, indent=1)
EOF
python3 reel_kit/kit.py "$D" myvoice "$W/voice.wav" sound build render

# 3. lip-synced talking head, driven by the reel's own placed voice track so it lines up from t=0
( cd /opt/ai/SadTalker && /opt/ai/talk/bin/python inference.py --driven_audio "$OLDPWD/$D/.work/voice_only.wav" \
    --source_image "$PHOTO" --result_dir "$OLDPWD/$W/talk" --preprocess full --still --size 256 --cpu )
RAW=$(ls -t "$W"/talk/*.mp4 | head -1)
# restore the face only where it is shown full size (the hook)
IMG0=$(python3 -c "import json;print(json.load(open('$D/timing.json'))['img0'] + 0.3)")
( cd /opt/ai/SadTalker && /opt/ai/talk/bin/python "$OLDPWD/$AV/fast_enhance.py" "$OLDPWD/$RAW" "$OLDPWD/$W/face.mp4" "$IMG0" )
FACE=$W/face.mp4

# 4. composite: cut-out under the hook, round portrait under the lines
/opt/ai/seg/bin/python $AV/facecam.py "$D" "$FACE"
echo "done: $D/output/reel_face.mp4"
