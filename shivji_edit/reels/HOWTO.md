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
Copy `reels/01-neelkanth/reel.json` and edit it. The format is **short and punchy, 15–20 s**
(`"pace": "short"`, `"hook_style": "bold"`).
- `intro`: the hook, a scroll-stopping question or statement in max about 7 words. It is shown big and bold
  over the first image. Mark the key word with `*…*` to make it gold, e.g. `Shiva का *गला* नीला क्यों है?`
- `lines`: exactly **3** lines, one beat each, max about 12 words. Even a story is told in 3 beats: problem,
  turn, meaning. Use natural spoken Hindi with a few common English words. In `caption`, write English
  words in Latin script and optionally mark one key word with `*…*`. In `spoken`, spell the same words in
  Devanagari so the voice says them naturally. Never show the same line twice in two scripts.
- `end`: the closing chant, e.g. `॥ हर हर महादेव ॥` (spoken without the ॥ marks).
- Keep it devotional and accurate to the scriptures. No claims about miracle cures, no politics, nothing
  against any community.
- `caption_post`: the Instagram caption: the hook line, 1–2 sentences telling the tale, a comment prompt
  ("कमेंट में लिखिए: हर हर महादेव"), and about 10 hashtags.

## 4. Find images (Wikimedia Commons only)
Use only CC0, public domain, CC BY or CC BY-SA files. Use **5 images, one per beat**: hook, line 1, line 2,
line 3, end. The kit then changes images exactly on the line changes.
- **Hook and end: real photos.** Temple, idol, shrine, aarti, Kailash, Ganga or Kashi ghats: striking,
  high-resolution photos (for example the big Murudeshwar Shiva, Adiyogi, Kedarnath, Mahakal and other
  temples).
- **Lines: classic paintings** that show the story moment (Raja Ravi Varma, Pahari/Kangra, Rajput,
  Kalighat, Bengal school, museum collections).
Portrait or near-square images crop best to 9:16.
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

## 6. Deliver: draft first, then the owner's own voice
The owner narrates the reels in their own voice. So:
1. Build and render the **draft** with the computer voice (`narrate`), as above. Commit and push it.
2. Send the draft `output/reel.mp4` to the user with SendUserFile (status `proactive`), together with the
   **recording script**: the hook, the 3 lines and the end chant, numbered, in Devanagari as they should be
   spoken. Add these recording tips: "record in one take on your phone, in a quiet room, phone about 15–20 cm
   from your mouth, calm and slow, with about a 1-second pause between lines; send the voice note or audio
   file here". Include the `caption_post` text so it's ready for Instagram.
3. When the recording arrives in the session, run:
   ```
   python3 reel_kit/kit.py reels/NN-slug myvoice /path/to/recording.m4a sound build render
   ```
   This cleans the audio, splits it at the pauses, syncs captions to the real voice and renders the final reel.
   If it reports the wrong number of lines, ask the user to re-record with clearer pauses. Check the
   snapshots again, then commit and push and send the final `reel.mp4` and `reel_voice_only.mp4`.
4. Tick the row in `CONTENT_PLAN.md` and add it to the **Made** table (mark it `draft` until the owner's voice
   is in).
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
