# Editing toolkit: what each GitHub repo does in this pipeline

The series workflow: phone recording → one finished vertical reel (1080x1920). Repos are listed by the job they do.
"Used" means it runs in the pipeline; "Reference" means its rules or ideas shaped the edit; "Not used" says why.

## Used

| Repo | Job in the pipeline |
|---|---|
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Renders the edit (HTML → MP4), cuts the person out of the frame (`remove-background`), lint and snapshot checks |
| [kurbaitaev/ghost-editor](https://github.com/kurbaitaev/ghost-editor) | The editor: cuts on word times, captions that avoid the face, cards, push-ins, SFX levels against the voice, music ducking, render QA report |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Transcription with word timestamps (captions, cut points) |
| [Rikorose/DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) | Removes fan hum and room noise; capped at 30 dB so the voice stays natural |
| [advimman/lama](https://github.com/advimman/lama) (ONNX build) | Fills in the fan hub and downrod when the ceiling fan is removed |
| [opencv/opencv_zoo](https://github.com/opencv/opencv_zoo) | YuNet face detection (face track, so captions never land on the mouth) |
| [1adrianb/face-alignment](https://github.com/1adrianb/face-alignment) | Face landmarks (earlier framing work) |

## Reference (rules and quality gates)

| Repo | What it contributed |
|---|---|
| [ArtCog/chatmonteur](https://github.com/ArtCog/chatmonteur) | Editorial rulebook and two quality gates for talking-head edits |
| [browser-use/video-use](https://github.com/browser-use/video-use) | Agent-driven editing method (already folded into ChatMonteur); its voice features need an ElevenLabs key |
| [RafaelGodoyEbert/JSON-SubLayer](https://github.com/RafaelGodoyEbert/JSON-SubLayer) | Word-level caption timing checks; we do the same by re-listening to every uncertain word with spelling hints |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | Alternative code-to-video renderer (Hyperframes is used instead) |

## Not used (and why)

| Repo / topic | Why not |
|---|---|
| [0xsline/OpenChatCut](https://github.com/0xsline/OpenChatCut) | Desktop timeline app; can't run headless in the cloud pipeline |
| [topics/talking-head](https://github.com/topics/talking-head), MuseTalk, PersonaLive | AI-generated or lip-synced faces; ruled out: real footage only |
| [topics/viral-videos](https://github.com/topics/viral-videos) (awesome-*-videos lists) | Prompt collections for fully AI-generated videos; not applicable to real talking-head footage |
| [Virlo-AI/Virlo-Agent-Plugin](https://github.com/Virlo-AI/Virlo-Agent-Plugin) | Trend data for agents; needs a paid API key |
| [EloyGMDev/vomcat](https://github.com/EloyGMDev/vomcat) | Cuts Shorts out of long YouTube videos; our recordings are already short |
| ruflo | Agent orchestration harness, not a video editor |

## House rules for the series (from feedback)

- Real footage only: no AI or lip-synced faces. Remove only the ceiling fan; keep the real room.
- Captions are exactly the spoken words (spelling corrected), never over the mouth.
- On-screen text matches what is said; useful context labels are allowed (e.g. "rule of 72", "Sushruta Samhita").
- Clean voice at -16 LUFS, music ducked well below it, restrained SFX.
- End on "Jai Hind" with a comment call-to-action.
