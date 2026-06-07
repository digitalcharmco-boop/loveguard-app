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
        """Call DALL-E 3 with retry; fall back to placeholder on failure."""
        for attempt in range(3):
            try:
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt or "cinematic wide shot, dramatic lighting",
                    size="1792x1024",
                    quality="standard",
                    n=1,
                )
                url = response.data[0].url
                data = requests.get(url, timeout=30).content
                path = self.output_dir / filename
                path.write_bytes(data)
                return path
            except Exception as exc:
                logger.warning("DALL-E attempt %d failed: %s", attempt + 1, exc)
                if attempt < 2:
                    time.sleep(2 ** attempt)

        return self._placeholder(filename)

    def _placeholder(self, filename: str) -> Path:
        """Return a solid dark-grey image when generation fails."""
        try:
            from PIL import Image
            img = Image.new("RGB", (1792, 1024), color=(30, 30, 30))
        except ImportError:
            # Write minimal 1×1 PNG bytes if Pillow unavailable
            import struct, zlib
            def _png1x1():
                sig = b"\x89PNG\r\n\x1a\n"
                ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
                ihdr_chunk = b"IHDR" + ihdr
                ihdr_crc = struct.pack(">I", zlib.crc32(ihdr_chunk) & 0xFFFFFFFF)
                idat_data = zlib.compress(b"\x00\x1e\x1e\x1e")
                idat = b"IDAT" + idat_data
                idat_crc = struct.pack(">I", zlib.crc32(idat) & 0xFFFFFFFF)
                iend = b"IEND"
                iend_crc = struct.pack(">I", zlib.crc32(iend) & 0xFFFFFFFF)
                def chunk(tag, data, crc): return struct.pack(">I", len(data)) + tag + data + crc
                return sig + chunk(b"IHDR", ihdr, ihdr_crc) + chunk(b"IDAT", idat_data, idat_crc) + chunk(b"IEND", b"", iend_crc)
            path = self.output_dir / filename
            path.write_bytes(_png1x1())
            return path

        path = self.output_dir / filename
        img.save(str(path))
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
        """Generate the selected thumbnail concept as a DALL-E 3 HD image."""
        prompt = concept.get("generation_prompt", "")[:4000]
        for attempt in range(3):
            try:
                resp = self.client.images.generate(
                    model="dall-e-3", prompt=prompt, size="1792x1024", quality="hd", n=1
                )
                data = requests.get(resp.data[0].url, timeout=30).content
                path = self.output_dir / "thumbnail.png"
                path.write_bytes(data)
                return path
            except Exception as exc:
                logger.warning("Thumbnail attempt %d failed: %s", attempt + 1, exc)
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return self._placeholder("thumbnail.png")

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
