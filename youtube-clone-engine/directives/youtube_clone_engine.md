# YouTube Channel Clone Engine

## Goal
Reverse-engineer a YouTube channel's content DNA and produce fully original scripts, image prompts, video prompts, and thumbnail concepts that replicate the channel's style — never its wording.

## Inputs
| Input | Description |
|-------|-------------|
| `channel_url` | YouTube channel link (for reference/labeling) |
| `transcripts` | 2–3 complete video transcripts from the channel |
| `topic` | User-provided topic OR AI-generated idea selected by user |
| `visual_samples` | 3–5 video frame screenshots (not thumbnails) — bytes |
| `thumbnail_samples` | 2–3 thumbnail images — bytes |

## Tools / Scripts
- `execution/youtube_clone_engine.py` — `YouTubeCloneEngine` class

## 11-State Pipeline

| State | Name | Action |
|-------|------|--------|
| 1 | Channel Link | Collect channel URL |
| 2 | Video Transcripts | Collect 2–3 full transcripts |
| 3 | Topic Selection | User provides topic OR generate ideas via `generate_topic_ideas()` |
| 4 | Style DNA Analysis | Run `extract_style_dna()` → display 14-dimension profile |
| 5 | Script Generation | Run `generate_script()` → display with word count, await confirmation |
| 6 | Visual Sample Input | Collect 3–5 screenshots → run `analyze_visual_samples()` → display profile |
| 7 | Image Prompts | Run `generate_image_prompts()` → one standalone prompt per 3–5 second beat |
| 8 | Video Prompts (optional) | If yes → run `generate_video_prompts()` → append to beats |
| 9 | Thumbnail Analysis | Collect 2–3 thumbnails → run `analyze_thumbnails()` → display DNA |
| 10 | Thumbnail Generation | Run `generate_thumbnail_concepts()` → 5 distinct concepts |
| 11 | Export (optional) | If yes → run `export_to_docx()` → provide download |

## Outputs
- **Style DNA**: 14-dimension JSON dict (niche, hook_architecture, tone_profile, etc.)
- **Script**: Publish-ready spoken script, ±5% of target word count
- **Visual Profile**: 8-dimension visual style JSON
- **Image Prompts**: Array of beat dicts with image_prompt, camera_angle, lighting, mood, action, visual_style
- **Video Prompts**: Same array with added `video_prompt` field
- **Thumbnail Concepts**: 5 dicts with visual_concept, text_overlay, emotion_trigger, generation_prompt
- **Word Document**: `.docx` export of all session data

## Visual Firewall
Visual sample input (State 6) and image/video prompt generation (States 7–8) are strictly off-limits until the script is confirmed in State 5.

## Absolute Rules
1. Never reproduce source content — style cloning only
2. Scripts contain zero visual direction or stage directions
3. Every image prompt is fully standalone (subject, environment, lighting, mood, camera, visual style)
4. State sequence is non-negotiable — no skipping, no merging

## Error Handling
- **API timeout**: Retry up to 3 times with exponential backoff (1s, 2s, 4s)
- **JSON parse failure**: Log raw response and raise ValueError with context
- **Image decode error**: Validate base64 before sending to API; skip corrupt images with warning
- **Word count mismatch >5%**: Log warning but return script as-is; UI flags deviation to user

## Edge Cases
- Transcripts under 200 words each: warn user that DNA accuracy may be limited
- More than 5 visual samples uploaded: process first 5 only (vision API context limits)
- Script > 2,000 words: image prompt generation may approach token limits; set max_tokens=16000
- Video prompts for scripts > 150 beats: generate in two batches of 75 if API errors occur

## Environment Variables
- `OPENAI_API_KEY` — Required. Use gpt-4o for all calls (supports vision).

## Model
All calls use `gpt-4o`. This handles both text and vision tasks in a single model.
