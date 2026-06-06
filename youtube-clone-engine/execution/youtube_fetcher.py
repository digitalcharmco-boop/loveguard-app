"""
YouTube Fetcher — auto-fetch transcripts, thumbnails, and video frames
from a channel URL or individual video URLs. No YouTube API key required.

Requires: youtube-transcript-api, yt-dlp (imageio-ffmpeg used for frames)
"""

import json
import logging
import re
import subprocess
from typing import Callable, Dict, List, Optional
from urllib.request import urlopen

logger = logging.getLogger(__name__)

VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
)


class YouTubeFetcher:
    def __init__(self):
        try:
            import imageio_ffmpeg
            self._ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            self._ffmpeg = "ffmpeg"  # fall back to system ffmpeg

    # ── URL / ID helpers ───────────────────────────────────────────────────

    def extract_video_id(self, url: str) -> Optional[str]:
        m = VIDEO_ID_RE.search(url)
        return m.group(1) if m else None

    def is_channel_url(self, url: str) -> bool:
        return self.extract_video_id(url) is None

    def get_channel_video_urls(self, channel_url: str, max_videos: int = 3) -> List[str]:
        """Use yt-dlp to list most recent video URLs from a channel (no download)."""
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                f"--playlist-end={max_videos}",
                "--print", "url",
                "--no-warnings",
                "--quiet",
                channel_url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        urls = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not urls:
            raise RuntimeError(
                "Could not list channel videos. Check the URL and try again."
            )
        return urls[:max_videos]

    # ── Transcript ─────────────────────────────────────────────────────────

    def fetch_transcript(self, video_id: str) -> str:
        """Fetch auto-generated or manual captions via youtube-transcript-api."""
        from youtube_transcript_api import YouTubeTranscriptApi
        entries = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(e["text"] for e in entries)

    # ── Thumbnail ──────────────────────────────────────────────────────────

    def fetch_thumbnail(self, video_id: str) -> bytes:
        """Download the highest-res thumbnail for a video ID."""
        for quality in ("maxresdefault", "hqdefault", "mqdefault"):
            url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
            try:
                with urlopen(url, timeout=10) as resp:
                    data = resp.read()
                if len(data) > 5_000:  # reject YouTube's placeholder image (~1 KB)
                    return data
            except Exception:
                continue
        raise RuntimeError(f"Could not fetch thumbnail for video {video_id}")

    # ── Video frames ───────────────────────────────────────────────────────

    def extract_frames(self, video_url: str, n_frames: int = 5) -> List[bytes]:
        """
        Extract n evenly-spaced frames from a video using yt-dlp + ffmpeg.
        Streams directly — no full video download.
        """
        duration = self._get_duration(video_url)
        stream_url = self._get_stream_url(video_url)

        frames = []
        for i in range(n_frames):
            t = duration * (i + 1) / (n_frames + 1)
            frame = self._grab_frame(stream_url, t)
            if frame:
                frames.append(frame)

        return frames

    def _get_duration(self, video_url: str) -> float:
        result = subprocess.run(
            ["yt-dlp", "--no-warnings", "--quiet", "--print", "%(duration)s", video_url],
            capture_output=True, text=True, timeout=30,
        )
        raw = result.stdout.strip()
        if not raw:
            raise RuntimeError("Could not determine video duration.")
        return float(raw)

    def _get_stream_url(self, video_url: str) -> str:
        result = subprocess.run(
            [
                "yt-dlp",
                "--no-warnings", "--quiet",
                "-f", "worst[ext=mp4][height<=480]/worst[ext=mp4]/worst",
                "--get-url",
                video_url,
            ],
            capture_output=True, text=True, timeout=30,
        )
        url = result.stdout.strip().split("\n")[0]
        if not url:
            raise RuntimeError("Could not get video stream URL.")
        return url

    def _grab_frame(self, stream_url: str, timestamp: float) -> Optional[bytes]:
        try:
            proc = subprocess.run(
                [
                    self._ffmpeg,
                    "-ss", f"{timestamp:.2f}",
                    "-i", stream_url,
                    "-vframes", "1",
                    "-f", "image2",
                    "-vcodec", "mjpeg",
                    "-q:v", "4",
                    "pipe:1",
                ],
                capture_output=True,
                timeout=30,
            )
            return proc.stdout if len(proc.stdout) > 1000 else None
        except Exception as e:
            logger.warning("Frame grab at %.1fs failed: %s", timestamp, e)
            return None

    # ── High-level fetch ───────────────────────────────────────────────────

    def fetch_from_urls(
        self,
        video_urls: List[str],
        n_frames: int = 5,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> Dict:
        """
        Given a list of video URLs, fetch transcripts, thumbnails, and frames.

        Returns:
            {
                "transcripts": List[str],
                "thumbnail_bytes": List[bytes],   # one per video
                "frame_bytes": List[bytes],        # n_frames from first video
                "video_ids": List[str],
            }
        """
        transcripts, thumbnails, frames, video_ids = [], [], [], []

        for i, url in enumerate(video_urls):
            vid_id = self.extract_video_id(url)
            if not vid_id:
                logger.warning("Skipping — no video ID in: %s", url)
                continue
            video_ids.append(vid_id)

            label = f"[{i + 1}/{len(video_urls)}]"

            if on_progress:
                on_progress(f"{label} Fetching transcript...")
            try:
                transcripts.append(self.fetch_transcript(vid_id))
            except Exception as e:
                logger.warning("Transcript failed for %s: %s", vid_id, e)

            if on_progress:
                on_progress(f"{label} Fetching thumbnail...")
            try:
                thumbnails.append(self.fetch_thumbnail(vid_id))
            except Exception as e:
                logger.warning("Thumbnail failed for %s: %s", vid_id, e)

            # Extract frames from the first video only
            if i == 0:
                if on_progress:
                    on_progress(f"{label} Extracting {n_frames} video frames...")
                try:
                    frames = self.extract_frames(url, n_frames=n_frames)
                except Exception as e:
                    logger.warning("Frame extraction failed: %s", e)

        return {
            "transcripts": transcripts,
            "thumbnail_bytes": thumbnails,
            "frame_bytes": frames,
            "video_ids": video_ids,
        }
