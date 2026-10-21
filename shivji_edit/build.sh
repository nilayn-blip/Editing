#!/usr/bin/env bash
# Build the edited Shivji temple video.
# Usage: ./build.sh INPUT.mov FONT_DIR OUTPUT.mp4
# FONT_DIR must contain tiro.ttf (Tiro Devanagari Sanskrit) and cinzel.ttf (Cinzel), both OFL Google Fonts.
set -euo pipefail
IN="$1"; FONTS="$2"; OUT="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
DUR=12.5
TARGET_LUFS=-14

# iPhone HLG (HDR) -> Rec.709 SDR, then a gentle warm grade
TM="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=2,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
GRADE="eq=contrast=1.05:saturation=1.08:gamma=0.98,colorbalance=rs=0.02:bs=-0.03:rh=0.03:bh=-0.04,unsharp=5:5:0.6"

# 1) stabilise + grade at source timing
ffmpeg -v error -y -i "$IN" -vf "$TM,vidstabdetect=shakiness=6:accuracy=15:result=$WORK/t.trf" -f null -
ffmpeg -v error -y -i "$IN" -map 0:v:0 -map 0:a:0 \
  -vf "$TM,vidstabtransform=input=$WORK/t.trf:smoothing=20:optzoom=1:interpol=bicubic,$GRADE" \
  -c:v libx264 -crf 10 -preset fast -c:a pcm_s16le "$WORK/base.mov"

# 2) sound design
python3 "$HERE/sfx.py" "$WORK/sfx.wav" "$DUR"

# 3) re-cut (source frames @30fps):
#   hook   120-147  close-up of the shivling, digital push
#   wide     0-35   tight crop anchored high: donation box / QR out of frame
#   zoom    35-84   camera push-in, crop relaxes once the box has left frame, 0.8x (frame-blended)
#   hold    84-213  darshan, slow push-in, 0.8x (motion-interpolated), then held for the end card
#   (the 7.2s reframe and the 8.4s pull-out are dropped)
reframe() { # $1 zoom expr, $2 vertical anchor expr (0 = top, 0.5 = centre); both in terms of T (segment time, seconds)
  # zoompan on a 2x supersampled frame (avoids the integer-pixel jitter zoompan has at 1:1)
  local z="${1//T/(in/30)}" y="${2//T/(in/30)}"
  echo "scale=2160:3840:flags=lanczos,zoompan=z='$z':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*($y)':d=1:s=1080x1920:fps=30"
}
TZ="(T+35/30)"
ZOOM_Z="if(lt($TZ,1.5),1.28,if(lt($TZ,2.4),1.28-0.24*($TZ-1.5)/0.9,1.04))"
ZOOM_Y="if(lt($TZ,1.5),0,if(lt($TZ,2.4),0.5*($TZ-1.5)/0.9,0.5))"
NORM="setsar=1,fps=30,format=yuv420p"

seg() { # $1 name, $2 start frame, $3 end frame, $4 filters after the trim
  ffmpeg -v error -y -i "$WORK/base.mov" -an -filter_complex \
    "[0:v]trim=start_frame=$2:end_frame=$3,setpts=PTS-STARTPTS,$4,$NORM[v]" -map "[v]" \
    -c:v libx264 -crf 10 -preset fast "$WORK/$1.mov"
}
seg hook 120 147 "$(reframe "1.20-0.10*T/0.9" "0.4")"
seg wide   0  35 "$(reframe "1.28" "0")"
seg zoom  35  84 "$(reframe "$ZOOM_Z" "$ZOOM_Y"),setpts=1.25*PTS,minterpolate=fps=30:mi_mode=blend"
seg hold  84 213 "$(reframe "1.04+0.08*T/4.3" "0.5-0.08*T/4.3"),setpts=1.25*PTS,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,tpad=stop_mode=clone:stop_duration=3.4"

python3 "$HERE/overlays.py" "$FONTS" "$DUR" | ffmpeg -v error -y \
  -i "$WORK/hook.mov" -i "$WORK/wide.mov" -i "$WORK/zoom.mov" -i "$WORK/hold.mov" \
  -f rawvideo -pix_fmt rgba -s 1080x1920 -r 30 -i - \
  -i "$WORK/sfx.wav" -i "$WORK/base.mov" \
  -filter_complex "
    [0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0,vignette=PI/5,split[a][b];
    [b]gblur=sigma=22,eq=brightness=-0.10:saturation=0.85,format=yuva420p,fade=t=in:st=9.3:d=0.9:alpha=1[blur];
    [a][blur]overlay=format=auto[bg];
    [bg][4:v]overlay=format=auto,fade=t=in:st=0:d=0.25,fade=t=out:st=$(echo "$DUR-0.7" | bc):d=0.7,format=yuv420p[v];
    [6:a]afftdn=nr=18:nf=-30,highpass=f=90,lowpass=f=11000,volume=0.28,apad=whole_dur=$DUR,
         afade=t=in:d=0.4,afade=t=out:st=9.0:d=2.0[amb];
    [amb][5:a]amix=inputs=2:normalize=0:duration=longest,atrim=0:$DUR[a]
  " -map "[v]" -map "[a]" -t "$DUR" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a pcm_s16le "$WORK/pre.mov"

# 4) loudness: measure, then gain + true-peak limit to the target
I=$(ffmpeg -i "$WORK/pre.mov" -af ebur128 -f null - 2>&1 | awk '/Summary/{s=1} s&&/ I:/{print $2; exit}')
GAIN=$(echo "$TARGET_LUFS - ($I)" | bc -l)
ffmpeg -v error -y -i "$WORK/pre.mov" -map 0:v -map 0:a -c:v copy \
  -af "volume=${GAIN}dB,alimiter=limit=0.89:attack=2:release=60:level=disabled" \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "wrote $OUT (pre-gain ${I} LUFS, gain ${GAIN} dB)"
