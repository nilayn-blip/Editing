# Making the daily reel for @nirva_nataless

Work on branch `claude/shivji-temple-video-edit-0efgap`. All paths below are relative to `shivji_edit/`.

## 1. Setup (about 1 minute)
```
pip install -q numpy scipy pillow piper-tts
ls /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell   # kit.py finds it itself
```
The Hindi voice (`hi_IN-pratham-medium`, about 60 MB) downloads from huggingface.co on first use into
`~/.cache/piper-voices/`.

## 2. Pick the topic
Take the first unticked row in `CONTENT_PLAN.md` and use the next free number: `reels/NN-slug/`.

## 3. Write the script (reel.json)
Copy `reels/_example/reel.json` and edit it.
- `intro`: a scroll-stopping hook, max about 10 words, shown on a black card.
- `lines`: 3 for a quote reel; 5–7 for a story reel. One idea per line, max about 12 words, in natural spoken
  Hindi with a few common English words (Life, trust, easy, heavy, result…). In `caption`, write English
  words in Latin script. In `spoken`, spell the same words in Devanagari (लाइफ़, ट्रस्ट…) so the voice says them
  naturally. Never show the same line twice in two scripts.
- `end`: the closing chant, e.g. `॥ हर हर महादेव ॥` (spoken without the ॥ marks).
- Keep it devotional and accurate to the scriptures. No claims about miracles cures, no politics, nothing
  against any community.
- `caption_post`: the Instagram caption: one line from the reel, a short sentence of context, a question to
  invite comments, and about 10 hashtags (#mahadev #harharmahadev #shiva #bholenath #sanatandharma, plus
  topic-specific ones).

## 4. Find paintings (Wikimedia Commons only)
Use only CC0, public domain, CC BY or CC BY-SA files. Prefer classic Indian paintings (Raja Ravi Varma,
Pahari/Kangra, Rajput, Mughal-era, Kalighat, Bengal school, museum collections) for a consistent, beautiful
look. Portrait or near-square works crop best to 9:16.
```
python3 -I reel_kit/tools/wm.py "query one" "query two"     # lists title, size, licence, author
```
Searches are rate-limited. Use 3–6 focused queries, and look at what has already been fetched in other
`reels/*/.dl` folders first. Do not reuse a painting that was used in the last 10 reels. Pick 6–8
paintings that match the lines in order, and list them in `paintings` (key p1, p2…, `file` = "File:…" title).

## 5. Build
```
python3 reel_kit/kit.py reels/NN-slug fetch      # slow: Wikimedia throttles; it resumes if re-run
```
Run `fetch` in the background and watch its log. A background job is stopped after 2 hours; if that happens,
re-run it (it skips files it already has). If one painting stays blocked for more than about 45 minutes, drop
it from `paintings` and carry on (5 paintings is the minimum).
Never `pkill -f` a pattern that also appears in your own command line.

Then look at every downloaded painting (`reels/NN-slug/.dl/a/*.jpg`; make a contact sheet with Pillow and
view it). Drop any that are off-topic or poor. Set `inset` [l, t, r, b] to crop away paper borders or oval
frames, and `focus` ("x% y%") on the faces. Then run:
```
python3 reel_kit/kit.py reels/NN-slug assemble narrate sound build
cd reels/NN-slug/project && HYPERFRAMES_BROWSER_PATH=$(ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell) \
  npx -y hyperframes@0.8.184 snapshot --at <one time per segment + end card> --no-end -o /tmp/snap
```
Look at the snapshots. Check that faces aren't cut off, captions are readable and the right painting sits
under each line. Fix `inset`/`focus` and repeat `assemble build` if needed. Then render:
```
python3 reel_kit/kit.py reels/NN-slug render     # check + render + encode + voice-only version + loudness report
```
Both videos must be 1080x1920 at 30 fps, and `reel.mp4` must measure about -14 LUFS.

## 6. Deliver
- `git add` the reel folder (the `.dl` and `.work` folders are ignored), tick the row in `CONTENT_PLAN.md`,
  add it to the **Made** table, commit and push to the branch.
- Send both `output/reel.mp4` and `output/reel_voice_only.mp4` to the user with the SendUserFile tool
  (status `proactive`). Put the `caption_post` text in the caption so they can copy it straight into
  Instagram.
- If something blocks the reel (for example Wikimedia blocks downloads for hours), say so plainly in the
  final message. Don't send a half-made reel.

## Rules
- Nothing from YouTube or any other copyrighted source. Only Commons images with the licences above.
- Music is the kit's original synthesised score. To use a famous bhajan, the user adds it in Instagram from
  the `reel_voice_only.mp4` version.
- The watermark "Nirvana ✦ Nilay" and the end card "@nirva_nataless / FOLLOW FOR MORE" come from the kit;
  don't remove them.
- The narration voice is CC BY-NC-SA (non-commercial). This is fine for the personal page; warn the user if
  they ever say a reel is a paid promotion.
