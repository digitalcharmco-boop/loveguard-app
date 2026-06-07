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


class VideoProducer:
    def __init__(self, api_key: str = None, output_dir: str = ".tmp/video"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
