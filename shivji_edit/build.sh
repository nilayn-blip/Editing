#!/usr/bin/env bash
# Build the edited Shivji temple video.
# Usage: ./build.sh INPUT.mov FONT_DIR OUTPUT.mp4
# FONT_DIR must contain tiro.ttf (Tiro Devanagari Sanskrit) and cinzel.ttf (Cinzel), both OFL Google Fonts.
set -euo pipefail
IN="$1"; FONTS="$2"; OUT="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
SRC_DUR=10.6; TAIL=2.4; DUR=13.0

# iPhone HLG (HDR) -> Rec.709 SDR
TM="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=2,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"

# 1) stabilisation analysis
ffmpeg -v error -y -i "$IN" -vf "$TM,vidstabdetect=shakiness=5:accuracy=15:result=$WORK/t.trf" -f null -

# 2) sound design
python3 "$HERE/sfx.py" "$WORK/sfx.wav" "$DUR"

# 3) reframe: start tighter + anchored high (keeps donation box/QR out of the opening),
#    relax to a light 1.04 crop once the camera has pushed in on the shivling.
Z="if(lt(t,1.1),1.10,if(lt(t,2.8),1.10-0.06*(t-1.1)/1.7,1.04))"
YF="if(lt(t,1.1),0.22,if(lt(t,2.8),0.22+0.28*(t-1.1)/1.7,0.5))"

GRADE="eq=contrast=1.05:saturation=1.08:gamma=0.98,colorbalance=rs=0.02:bs=-0.03:rh=0.03:bh=-0.04,unsharp=5:5:0.6,vignette=PI/5"

python3 "$HERE/overlays.py" "$FONTS" "$DUR" | ffmpeg -v error -y \
  -i "$IN" \
  -f rawvideo -pix_fmt rgba -s 1080x1920 -r 30 -i - \
  -i "$WORK/sfx.wav" \
  -filter_complex "
    [0:v]$TM,vidstabtransform=input=$WORK/t.trf:smoothing=12:optzoom=1,
         scale=w='trunc(1080*($Z)/2)*2':h='trunc(1920*($Z)/2)*2':eval=frame,
         crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*($YF)',
         $GRADE,fps=30,tpad=stop_mode=clone:stop_duration=$TAIL,split[a][b];
    [b]gblur=sigma=22,eq=brightness=-0.10:saturation=0.85,format=yuva420p,fade=t=in:st=9.35:d=0.9:alpha=1[blur];
    [a][blur]overlay=format=auto[bg];
    [bg][1:v]overlay=format=auto,fade=t=in:st=0:d=0.5,fade=t=out:st=$(echo "$DUR-0.7" | bc):d=0.7,format=yuv420p[v];
    [0:a:0]highpass=f=90,lowpass=f=12000,volume=0.40,apad=whole_dur=$DUR,afade=t=in:d=0.4,afade=t=out:st=$(echo "$SRC_DUR-1.4" | bc):d=1.6[amb];
    [amb][2:a]amix=inputs=2:normalize=0:duration=longest,atrim=0:$DUR,loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000[a]
  " -map "[v]" -map "[a]" -t "$DUR" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "wrote $OUT"
