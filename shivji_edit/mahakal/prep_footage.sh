#!/usr/bin/env bash
# Prepare clean (text-free) SDR footage for the HyperFrames Mahakal composition.
# Usage: ./prep_footage.sh INPUT.mov OUT.mp4
#
# Output timeline (30 fps):
#   0.00 - 0.90   hook: close-up of the shivling (source frames 120-147), digital push
#   0.90 - 2.07   wide shot, cropped high so the donation box / QR is out of frame (0-35)
#   2.07 - ~4.07  camera push-in, crop relaxes, slowed 0.8x with frame blending (35-84)
#   ~4.07 - ~11.2 darshan hold, slowed 0.6x (motion-interpolated) with a slow push (84-213)
#   then the last frame is held until DUR for the end card
set -euo pipefail
IN="$1"; OUT="$2"
DUR=15.5
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

TM="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=2,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
GRADE="eq=contrast=1.05:saturation=1.08:gamma=0.98,colorbalance=rs=0.02:bs=-0.03:rh=0.03:bh=-0.04,unsharp=5:5:0.6"
NORM="setsar=1,fps=30,format=yuv420p"

ffmpeg -v error -y -i "$IN" -vf "$TM,vidstabdetect=shakiness=6:accuracy=15:result=$WORK/t.trf" -f null -
ffmpeg -v error -y -i "$IN" -map 0:v:0 \
  -vf "$TM,vidstabtransform=input=$WORK/t.trf:smoothing=20:optzoom=1:interpol=bicubic,$GRADE" \
  -c:v libx264 -crf 10 -preset fast "$WORK/base.mov"

reframe() { # $1 zoom expr, $2 vertical anchor expr (0 = top, 0.5 = centre); both in terms of T (segment time, s)
  local z="${1//T/(in/30)}" y="${2//T/(in/30)}"
  echo "scale=2160:3840:flags=lanczos,zoompan=z='$z':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*($y)':d=1:s=1080x1920:fps=30,setpts=N/30/TB"
}
TZ="(T+35/30)"
ZOOM_Z="if(lt($TZ,1.5),1.28,if(lt($TZ,2.4),1.28-0.24*($TZ-1.5)/0.9,1.04))"
ZOOM_Y="if(lt($TZ,1.5),0,if(lt($TZ,2.4),0.5*($TZ-1.5)/0.9,0.5))"

seg() { # $1 name, $2 start frame, $3 end frame, $4 filters after the trim
  ffmpeg -v error -y -i "$WORK/base.mov" -an -filter_complex \
    "[0:v]trim=start_frame=$2:end_frame=$3,setpts=PTS-STARTPTS,$4,$NORM[v]" -map "[v]" \
    -c:v libx264 -crf 10 -preset fast "$WORK/$1.mov"
}
seg hook 120 147 "$(reframe "1.20-0.10*T/0.9" "0.4")"
seg wide   0  35 "$(reframe "1.28" "0")"
seg zoom  35  84 "$(reframe "$ZOOM_Z" "$ZOOM_Y"),setpts=1.25*PTS,minterpolate=fps=30:mi_mode=blend"
seg hold  84 213 "$(reframe "1.04+0.10*T/4.3" "0.5-0.08*T/4.3"),setpts=PTS/0.6,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,tpad=stop_mode=clone:stop_duration=6"

for s in hook wide zoom hold; do
  printf '%s %s\n' "$s" "$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$WORK/$s.mov")"
done

ffmpeg -v error -y -i "$WORK/hook.mov" -i "$WORK/wide.mov" -i "$WORK/zoom.mov" -i "$WORK/hold.mov" \
  -filter_complex "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0,vignette=PI/5,format=yuv420p[v]" \
  -map "[v]" -t "$DUR" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -movflags +faststart "$OUT"
echo "wrote $OUT"
