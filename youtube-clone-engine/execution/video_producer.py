"""
Video Producer — automated image generation, voiceover, and video assembly.
Uses DALL-E 3 for images, OpenAI TTS for voiceover, MoviePy for assembly.
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional, Callable

from openai import OpenAI

logger = logging.getLogger(__name__)

# Resolve paths relative to this file so they always work on Windows regardless
# of where Streamlit or the terminal is launched from.
_HERE = Path(__file__).resolve().parent
_DEFAULT_OUTPUT = _HERE.parent / "output" / "video"


def _ensure_dir(p: Path) -> Path:
    """Create directory p, falling back to system temp on failure."""
    try:
        os.makedirs(p, exist_ok=True)
        return p
    except OSError:
        import tempfile
        fallback = Path(tempfile.gettempdir()) / "yt-clone-engine" / "video"
        os.makedirs(fallback, exist_ok=True)
        logger.warning("Could not create %s — using temp dir %s instead", p, fallback)
        return fallback


class VideoProducer:
    def __init__(self, api_key: str = None, output_dir=None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        base = Path(output_dir) if output_dir else _DEFAULT_OUTPUT
        self.output_dir = _ensure_dir(base)

    # ── Image generation ───────────────────────────────────────────────────

    def generate_images(
        self,
        beats: List[Dict],
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        delay_sec: float = 13.0,
    ) -> List[Path]:
        """Generate a DALL-E 3 image for each beat. Returns local image paths."""
        image_paths = []
        for i, beat in enumerate(beats):
            if on_progress:
                on_progress(i, len(beats), f"Image {i + 1} / {len(beats)}")

            prompt = beat.get("image_prompt", "")[:4000]

            img_path = self._fetch_dalle_image(prompt, f"beat_{i:03d}.png")
            image_paths.append(img_path)

            if i < len(beats) - 1:
                time.sleep(delay_sec)

        return image_paths

    def _fetch_dalle_image(self, prompt: str, filename: str) -> Path:
        """Generate image with retry across available models."""
        # Try newest model first, fall back to older ones
        models = [
            ("gpt-image-1", "1536x1024", "medium"),
            ("dall-e-3",    "1792x1024", "standard"),
            ("dall-e-2",    "1024x1024", None),
        ]
        for model, size, quality in models:
            for attempt in range(2):
                try:
                    kwargs = dict(
                        model=model,
                        prompt=(prompt or "cinematic wide shot, dramatic lighting")[:4000],
                        size=size,
                        n=1,
                    )
                    if quality:
                        kwargs["quality"] = quality
                    response = self.client.images.generate(**kwargs)
                    img_data = response.data[0]
                    if getattr(img_data, "b64_json", None):
                        import base64
                        data = base64.b64decode(img_data.b64_json)
                    else:
                        data = requests.get(img_data.url, timeout=30).content
                    path = self.output_dir / filename
                    path.write_bytes(data)
                    return path
                except Exception as exc:
                    logger.warning("%s attempt %d failed: %s", model, attempt + 1, exc)
                    if attempt == 0:
                        time.sleep(2)
            # If both attempts failed for this model, try next model

        return self._placeholder(filename, prompt)

    def _placeholder(self, filename: str, prompt: str = "") -> Path:
        """Create a styled dark horror title card when image generation fails."""
        path = self.output_dir / filename
        try:
            from PIL import Image, ImageDraw, ImageFont
            import textwrap

            W, H = 1920, 1080
            img = Image.new("RGB", (W, H), color=(8, 8, 10))
            draw = ImageDraw.Draw(img)

            # Dark vignette border
            for i in range(120):
                alpha = int(180 * (1 - i / 120))
                draw.rectangle([i, i, W - i, H - i], outline=(0, 0, 0, alpha) if False else (0, 0, 0))

            # Extract a short scene description from the prompt
            scene = prompt.strip()
            if len(scene) > 200:
                # Take first meaningful sentence
                for sep in [". ", ".\n", ", "]:
                    if sep in scene[:200]:
                        scene = scene[:scene[:200].index(sep)].strip()
                        break
                else:
                    scene = scene[:150].strip()

            # Try to load a font, fall back to default
            font_large = font_small = None
            try:
                font_large = ImageFont.truetype("arial.ttf", 52)
                font_small = ImageFont.truetype("arial.ttf", 28)
            except Exception:
                try:
                    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
                    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
                except Exception:
                    font_large = ImageFont.load_default()
                    font_small = font_large

            # Thin red top accent line
            draw.rectangle([80, 80, W - 80, 83], fill=(180, 0, 0))

            # Wrap and draw scene text
            if scene:
                lines = textwrap.wrap(scene, width=55)[:5]
                y = H // 2 - (len(lines) * 65) // 2
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font_large)
                    tw = bbox[2] - bbox[0]
                    draw.text(((W - tw) // 2, y), line, font=font_large, fill=(220, 220, 220))
                    y += 65

            # Thin red bottom accent line
            draw.rectangle([80, H - 83, W - 80, H - 80], fill=(180, 0, 0))

            img.save(str(path), "PNG")
        except Exception as e:
            logger.warning("Styled placeholder failed (%s) — using solid black", e)
            try:
                from PIL import Image
                Image.new("RGB", (1920, 1080), color=(8, 8, 10)).save(str(path), "PNG")
            except Exception:
                path.write_bytes(b"")
        return path

    # ── Pillow card helpers ────────────────────────────────────────────────

    def _load_fonts(self, large: int, mid: int, small: int):
        from PIL import ImageFont
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "arial.ttf",
        ]
        def _try(size):
            for p in candidates:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
            return ImageFont.load_default()
        return _try(large), _try(mid), _try(small)

    def _render_news_overlay(self, beat: dict, filename: str) -> Path:
        """Dark news-broadcast graphic card with quote text and red accent bars."""
        path = self.output_dir / filename
        try:
            from PIL import Image, ImageDraw
            import textwrap

            W, H = 1920, 1080
            img = Image.new("RGB", (W, H), color=(6, 6, 8))
            draw = ImageDraw.Draw(img)

            font_q, font_m, font_s = self._load_fonts(50, 30, 22)

            # Red accent bars (top + bottom — like news broadcast chyron)
            draw.rectangle([0, 0, W, 8], fill=(190, 0, 0))
            draw.rectangle([0, H - 8, W, H], fill=(190, 0, 0))

            # "TRUE CRIME" label top-left
            draw.text((90, 22), "TRUE CRIME", font=font_m, fill=(255, 255, 255))

            # Dark semi-opaque quote box
            box_y1 = H // 3 - 20
            box_y2 = 2 * H // 3 + 60
            draw.rectangle([60, box_y1, W - 60, box_y2], fill=(14, 14, 18))
            draw.rectangle([60, box_y1, W - 60, box_y1 + 4], fill=(190, 0, 0))

            # Quote text
            quote = beat.get("quote_text", beat.get("segment", ""))[:280]
            lines = textwrap.wrap(f'“{quote}”', width=58)[:5]
            y = box_y1 + 28
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font_q)
                tw = bbox[2] - bbox[0]
                draw.text(((W - tw) // 2, y), line, font=font_q, fill=(228, 228, 228))
                y += 66

            # Speaker attribution
            speaker = beat.get("speaker_label", "")
            if speaker:
                bbox = draw.textbbox((0, 0), f"— {speaker}", font=font_m)
                tw = bbox[2] - bbox[0]
                draw.text(((W - tw) // 2, y + 16), f"— {speaker}", font=font_m, fill=(190, 0, 0))

            img.save(str(path), "PNG")
        except Exception as e:
            logger.warning("News overlay render failed (%s) — using placeholder", e)
            return self._placeholder(filename, beat.get("segment", ""))
        return path

    def _render_infographic(self, beat: dict, filename: str) -> Path:
        """Dark infographic slide with white text and pink accent bars."""
        path = self.output_dir / filename
        try:
            from PIL import Image, ImageDraw
            import textwrap

            W, H = 1920, 1080
            img = Image.new("RGB", (W, H), color=(6, 6, 8))
            draw = ImageDraw.Draw(img)

            font_big, font_mid, font_s = self._load_fonts(68, 36, 24)

            # Pink accent bars (infographic accent color)
            PINK = (220, 75, 135)
            draw.rectangle([80, 78, W - 80, 84], fill=PINK)
            draw.rectangle([80, H - 84, W - 80, H - 78], fill=PINK)

            display = beat.get("display_text", beat.get("segment", ""))[:400]

            # Split on " · " to detect labeled list (e.g. timeline entries)
            if " · " in display:
                header, *items = display.split(" · ")
                header = header.strip()
                bbox = draw.textbbox((0, 0), header, font=font_mid)
                tw = bbox[2] - bbox[0]
                y = H // 2 - (len(items) * 52 + 80) // 2
                draw.text(((W - tw) // 2, y), header, font=font_mid, fill=PINK)
                y += 70
                for item in items[:6]:
                    item = item.strip()
                    bbox = draw.textbbox((0, 0), item, font=font_big)
                    tw = bbox[2] - bbox[0]
                    draw.text(((W - tw) // 2, y), item, font=font_big, fill=(245, 245, 245))
                    y += 78
            else:
                lines = textwrap.wrap(display, width=40)
                y = H // 2 - (len(lines) * 78) // 2
                for i, line in enumerate(lines[:5]):
                    f = font_big if i == 0 else font_mid
                    sz = 78 if i == 0 else 54
                    fill = (255, 255, 255) if i == 0 else (200, 200, 200)
                    bbox = draw.textbbox((0, 0), line, font=f)
                    tw = bbox[2] - bbox[0]
                    draw.text(((W - tw) // 2, y), line, font=f, fill=fill)
                    y += sz

            img.save(str(path), "PNG")
        except Exception as e:
            logger.warning("Infographic render failed (%s) — using placeholder", e)
            return self._placeholder(filename, beat.get("segment", ""))
        return path

    # ── Voiceover ──────────────────────────────────────────────────────────

    def generate_voiceover(self, script: str, voice: str = "onyx") -> Path:
        """Generate TTS voiceover, splitting at sentence boundaries if needed."""
        audio_path = self.output_dir / "voiceover.mp3"
        chunks = self._split_text(script, max_chars=4000) if len(script) > 4000 else [script]

        if len(chunks) == 1:
            resp = self.client.audio.speech.create(model="tts-1-hd", voice=voice, input=chunks[0])
            resp.stream_to_file(str(audio_path))
            return audio_path

        chunk_paths = []
        for j, chunk in enumerate(chunks):
            resp = self.client.audio.speech.create(model="tts-1-hd", voice=voice, input=chunk)
            cp = self.output_dir / f"voice_chunk_{j}.mp3"
            resp.stream_to_file(str(cp))
            chunk_paths.append(cp)

        self._concat_mp3(chunk_paths, audio_path)
        return audio_path

    def _split_text(self, text: str, max_chars: int) -> List[str]:
        sentences = text.replace("\n", " ").split(". ")
        chunks, current = [], ""
        for s in sentences:
            candidate = current + s + ". "
            if len(candidate) > max_chars and current:
                chunks.append(current.strip())
                current = s + ". "
            else:
                current = candidate
        if current:
            chunks.append(current.strip())
        return chunks

    def _concat_mp3(self, parts: List[Path], out: Path):
        try:
            from pydub import AudioSegment
            combined = sum((AudioSegment.from_mp3(str(p)) for p in parts), AudioSegment.empty())
            combined.export(str(out), format="mp3")
        except Exception:
            with open(str(out), "wb") as f:
                for p in parts:
                    f.write(p.read_bytes())

    # ── Veo 3 video clip generation ────────────────────────────────────────

    def generate_video_clips_veo(
        self,
        beats: List[Dict],
        clip_duration: int = 8,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """Generate clips per beat: Veo 3 for animation, Pillow cards for overlays/infographics."""
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )
        clip_paths = []

        for i, beat in enumerate(beats):
            scene_type = beat.get("scene_type", "animation")
            label = f"Clip {i + 1}/{len(beats)} [{scene_type}]"
            if on_progress:
                on_progress(i, len(beats), label)

            base = f"clip_{i:03d}"

            if scene_type == "news_overlay":
                path = self._render_news_overlay(beat, f"{base}.png")
            elif scene_type == "infographic":
                path = self._render_infographic(beat, f"{base}.png")
            else:
                # animation — Veo 3: use the image_prompt exactly as generated
                # (it already reflects the cloned channel's visual style)
                raw_prompt = beat.get("image_prompt", "cinematic scene, dramatic lighting, moody atmosphere")
                prompt = raw_prompt[:2000]
                path = self._generate_veo_clip(client, prompt, clip_duration, f"{base}.mp4")

            clip_paths.append(path)

        return clip_paths

    def _generate_veo_clip(self, client, prompt: str, duration: int, filename: str) -> Path:
        """Generate one Veo 3 clip using correct API; fall back to styled image."""
        import time
        from google.genai import types

        path = self.output_dir / filename

        try:
            operation = client.models.generate_videos(
                model="veo-3.1-lite-generate-preview",
                source=types.VideoGenerationSource(prompt=prompt),
                config=types.GenerateVideosConfig(
                    person_generation="dont_allow",
                    aspect_ratio="16:9",
                    number_of_videos=1,
                    duration_seconds=min(max(duration, 5), 8),
                    resolution="720p",
                ),
            )

            # Poll until done (max 5 minutes)
            waited = 0
            while not operation.done and waited < 300:
                logger.info("Veo 3 generating %s — waiting...", filename)
                time.sleep(10)
                waited += 10
                operation = client.operations.get(operation)

            if operation.done:
                result = operation.result
                if result and result.generated_videos:
                    video = result.generated_videos[0].video
                    client.files.download(file=video)
                    video.save(str(path))
                    if path.exists() and path.stat().st_size > 1000:
                        return path
        except Exception as exc:
            logger.warning("Veo 3 clip failed for %s: %s", filename, exc)

        # Fallback: styled dark title card
        return self._placeholder(filename.replace(".mp4", ".png"), prompt)

    def assemble_from_clips(
        self,
        clip_paths: List[Path],
        audio_path: Path,
        output_path: Optional[Path] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> Path:
        """Assemble Veo video clips (or image fallbacks) + audio into final MP4."""
        from moviepy import VideoFileClip, ImageClip, concatenate_videoclips, AudioFileClip

        if output_path is None:
            output_path = self.output_dir / "final_video.mp4"

        if on_progress:
            on_progress("Loading audio...")
        audio = AudioFileClip(str(audio_path))
        total_dur = audio.duration
        beat_dur = total_dur / max(len(clip_paths), 1)

        TARGET_W, TARGET_H = 1920, 1080

        if on_progress:
            on_progress("Building timeline...")
        clips = []
        for cp in clip_paths:
            if cp.suffix == ".mp4" and cp.exists() and cp.stat().st_size > 1000:
                clip = VideoFileClip(str(cp))
                # Fit to 1920×1080
                scale = max(TARGET_W / clip.w, TARGET_H / clip.h)
                clip = clip.resized(scale).cropped(
                    x_center=clip.w / 2, y_center=clip.h / 2,
                    width=TARGET_W, height=TARGET_H,
                )
            else:
                # Image fallback
                img_file = cp.with_suffix(".png")
                clip = ImageClip(str(img_file)).with_duration(beat_dur)
                scale = max(TARGET_W / clip.w, TARGET_H / clip.h)
                clip = clip.resized(scale).cropped(
                    x_center=clip.w / 2, y_center=clip.h / 2,
                    width=TARGET_W, height=TARGET_H,
                )
            clips.append(clip)

        if on_progress:
            on_progress("Concatenating clips...")
        video = concatenate_videoclips(clips)

        # Trim to audio length if video is longer
        if video.duration > total_dur:
            video = video.subclipped(0, total_dur)
        video = video.with_audio(audio).with_duration(total_dur)

        if on_progress:
            on_progress("Encoding MP4 (this takes a few minutes)...")
        video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        return output_path

    # ── Thumbnail ──────────────────────────────────────────────────────────

    def generate_thumbnail_image(self, concept: Dict) -> Path:
        """Generate thumbnail using best available image model."""
        prompt = concept.get("generation_prompt", "")[:4000]
        return self._fetch_dalle_image(prompt, "thumbnail.png")

    # ── Video assembly ─────────────────────────────────────────────────────

    def assemble_video(
        self,
        image_paths: List[Path],
        audio_path: Path,
        output_path: Optional[Path] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> Path:
        """Assemble images + audio into final 1920×1080 MP4."""
        from moviepy import ImageClip, concatenate_videoclips, AudioFileClip

        if output_path is None:
            output_path = self.output_dir / "final_video.mp4"

        if on_progress:
            on_progress("Loading audio...")
        audio = AudioFileClip(str(audio_path))
        total_dur = audio.duration
        beat_dur = total_dur / max(len(image_paths), 1)

        TARGET_W, TARGET_H = 1920, 1080

        if on_progress:
            on_progress("Building video clips...")

        clips = []
        for img_path in image_paths:
            clip = ImageClip(str(img_path)).with_duration(beat_dur)
            scale = max(TARGET_W / clip.w, TARGET_H / clip.h)
            clip = clip.resized(scale)
            clip = clip.cropped(
                x_center=clip.w / 2, y_center=clip.h / 2,
                width=TARGET_W, height=TARGET_H,
            )
            clips.append(clip)

        if on_progress:
            on_progress("Concatenating clips...")
        video = concatenate_videoclips(clips)
        video = video.with_audio(audio).with_duration(total_dur)

        if on_progress:
            on_progress("Encoding MP4 (this takes a few minutes)...")
        video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        return output_path
