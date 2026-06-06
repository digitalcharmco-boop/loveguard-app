#!/usr/bin/env python3
"""
YouTube Channel Clone Engine — Auto Mode
Enter a channel or video URL → auto-fetch transcripts, frames, thumbnails
→ enter topic → click Start → get a finished MP4 + thumbnail + docx.
"""

import base64
import mimetypes
import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(__file__))

try:
    for _k in ["OPENAI_API_KEY"]:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="YouTube Clone Engine — Auto",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
body { background-color: #0f0f0f; }
.yt-header { text-align:center; color:#FF0000; font-size:2rem; font-weight:900; }
.yt-sub { text-align:center; color:#888; font-size:0.85rem; margin-top:0.1rem; }
.fetch-box { background:#111; border:1px solid #2a2a2a; border-radius:8px; padding:1rem; margin:0.5rem 0; }
.cost-note { color:#888; font-size:0.8rem; }
.fetched-badge { color:#00cc66; font-weight:700; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _b64(data: bytes, mime: str = "image/jpeg") -> str:
    return base64.b64encode(data).decode()

def _bytes_to_b64_mime(data_list: list, mime: str = "image/jpeg"):
    return [_b64(d) for d in data_list], [mime] * len(data_list)

def _files_to_b64(files):
    b64s, mimes = [], []
    for f in files:
        b64s.append(base64.b64encode(f.read()).decode())
        mime, _ = mimetypes.guess_type(f.name)
        mimes.append(mime or "image/jpeg")
    return b64s, mimes

def _get_engine():
    from execution.youtube_clone_engine import YouTubeCloneEngine
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not set.")
        st.stop()
    if "auto_engine" not in st.session_state:
        st.session_state.auto_engine = YouTubeCloneEngine(api_key=api_key)
    return st.session_state.auto_engine

def _get_producer():
    from execution.video_producer import VideoProducer
    api_key = os.getenv("OPENAI_API_KEY")
    if "auto_producer" not in st.session_state:
        st.session_state.auto_producer = VideoProducer(api_key=api_key)
    return st.session_state.auto_producer

def _get_fetcher():
    from execution.youtube_fetcher import YouTubeFetcher
    if "auto_fetcher" not in st.session_state:
        st.session_state.auto_fetcher = YouTubeFetcher()
    return st.session_state.auto_fetcher


# ── Pipeline ──────────────────────────────────────────────────────────────────

def _run_pipeline(
    engine, producer,
    channel_url, transcripts, topic,
    visual_b64s, visual_mimes,
    thumb_b64s, thumb_mimes,
    voice, max_beats,
    status_widget,
):
    result = {}

    with status_widget:
        st.write("**[1/9]** Extracting Style DNA from transcripts...")
        dna = engine.extract_style_dna(transcripts, channel_url)
        result["style_dna"] = dna
        st.write(f"✅ Style DNA — niche: {dna.get('niche', '—')}")

        st.write("**[2/9]** Generating script...")
        script_result = engine.generate_script(dna, topic)
        script = script_result["script"]
        wc = script_result["word_count"]
        result.update(script=script, word_count=wc,
                      target_word_count=script_result["target_word_count"])
        st.write(f"✅ Script — {wc} words")

        visual_profile = None
        if visual_b64s:
            st.write("**[3/9]** Analyzing visual style samples...")
            visual_profile = engine.analyze_visual_samples(
                visual_b64s[:5], visual_mimes[:5]
            )
            result["visual_profile"] = visual_profile
            st.write("✅ Visual style profile extracted")
        else:
            result["visual_profile"] = None
            st.write("**[3/9]** No visual samples — skipping")

        st.write("**[4/9]** Generating image prompts...")
        all_prompts = engine.generate_image_prompts(script, visual_profile or {})
        beats = all_prompts[:max_beats]
        result["image_prompts"] = all_prompts
        st.write(f"✅ {len(beats)} beats selected (of {len(all_prompts)} generated)")

        thumbnail_dna = None
        if thumb_b64s:
            st.write("**[5/9]** Analyzing thumbnail design language...")
            thumbnail_dna = engine.analyze_thumbnails(thumb_b64s[:3], thumb_mimes[:3])
            result["thumbnail_dna"] = thumbnail_dna
            st.write("✅ Thumbnail DNA extracted")
        else:
            result["thumbnail_dna"] = None
            st.write("**[5/9]** No thumbnails — skipping")

        concepts = engine.generate_thumbnail_concepts(thumbnail_dna or {}, topic, script)
        result["thumbnail_concepts"] = concepts
        st.write("✅ 5 thumbnail concepts generated")

        img_ph = st.empty()
        img_ph.write(f"**[6/9]** Generating {len(beats)} images via DALL-E 3...")

        def on_img(i, total, msg):
            remaining_min = (total - i) * 13 // 60
            img_ph.write(f"**[6/9]** {msg} (~{remaining_min} min left)")

        image_paths = producer.generate_images(beats, on_progress=on_img)
        result["image_paths"] = [str(p) for p in image_paths]
        img_ph.write(f"✅ {len(image_paths)} images generated")

        st.write("**[7/9]** Generating thumbnail (HD)...")
        thumb_path = producer.generate_thumbnail_image(concepts[0])
        result["thumbnail_path"] = str(thumb_path)
        st.write("✅ Thumbnail generated")

        st.write("**[8/9]** Generating voiceover...")
        audio_path = producer.generate_voiceover(script, voice=voice)
        result["audio_path"] = str(audio_path)
        st.write("✅ Voiceover generated")

        asm_ph = st.empty()
        asm_ph.write("**[9/9]** Assembling final video...")

        from pathlib import Path

        def on_asm(msg):
            asm_ph.write(f"**[9/9]** {msg}")

        video_path = producer.assemble_video(
            image_paths=[Path(p) for p in result["image_paths"]],
            audio_path=Path(result["audio_path"]),
            on_progress=on_asm,
        )
        result["video_path"] = str(video_path)
        asm_ph.write("✅ Video assembled")

        session_data = {
            "channel_url": channel_url,
            "topic": topic,
            "style_dna": result["style_dna"],
            "script": result["script"],
            "word_count": result["word_count"],
            "target_word_count": result["target_word_count"],
            "visual_profile": result.get("visual_profile"),
            "image_prompts": result["image_prompts"],
            "thumbnail_dna": result.get("thumbnail_dna"),
            "thumbnail_concepts": result["thumbnail_concepts"],
        }
        result["docx_bytes"] = engine.export_to_docx(session_data)

    return result


# ── Results page ──────────────────────────────────────────────────────────────

def _render_results():
    r = st.session_state.auto_result
    st.success("Production complete!")

    st.markdown("### Final Video")
    vp = r.get("video_path")
    if vp and os.path.exists(vp):
        st.video(vp)
        with open(vp, "rb") as f:
            st.download_button("Download MP4", f.read(),
                               file_name="youtube_video.mp4", mime="video/mp4")

    st.markdown("### Thumbnail")
    tp = r.get("thumbnail_path")
    if tp and os.path.exists(tp):
        st.image(tp, use_column_width=True)
        with open(tp, "rb") as f:
            st.download_button("Download Thumbnail PNG", f.read(),
                               file_name="thumbnail.png", mime="image/png")

    st.markdown("### Script")
    st.text_area("", value=r.get("script", ""), height=300, label_visibility="collapsed")

    if r.get("docx_bytes"):
        st.download_button(
            "Download Full Package (.docx)",
            data=r["docx_bytes"],
            file_name="youtube_clone_package.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.markdown("---")
    if st.button("Start New Session"):
        for k in ["auto_result", "auto_engine", "auto_producer",
                  "auto_fetcher", "fetched"]:
            st.session_state.pop(k, None)
        st.rerun()


# ── Fetch section (outside form so it can rerun) ──────────────────────────────

def _render_fetch_section():
    st.markdown("### 1. Source Videos")
    st.caption("Enter a channel URL to auto-fetch the 3 most recent videos, or paste specific video URLs.")

    src_type = st.radio(
        "",
        ["Channel URL — auto-fetch recent videos", "Specific video URLs"],
        key="src_type",
        label_visibility="collapsed",
        horizontal=True,
    )

    fetcher = _get_fetcher()
    fetch_clicked = False
    video_urls_to_fetch = []
    channel_url_out = ""

    if src_type.startswith("Channel"):
        col1, col2 = st.columns([4, 1])
        with col1:
            ch_url = st.text_input(
                "Channel URL",
                placeholder="https://www.youtube.com/@channelname",
                key="fetch_channel_url",
                label_visibility="collapsed",
            )
        with col2:
            n_vids = st.selectbox("Videos", [2, 3], index=1, key="fetch_n_vids")
        fetch_clicked = st.button("Fetch from YouTube", key="fetch_ch_btn", type="primary")
        channel_url_out = ch_url.strip()
        if fetch_clicked and ch_url.strip():
            with st.spinner("Listing channel videos..."):
                try:
                    video_urls_to_fetch = fetcher.get_channel_video_urls(ch_url.strip(), n_vids)
                except Exception as e:
                    st.error(f"Could not list channel videos: {e}")
                    fetch_clicked = False
    else:
        v1 = st.text_input("Video URL 1 *", placeholder="https://www.youtube.com/watch?v=...", key="fv1")
        v2 = st.text_input("Video URL 2 *", placeholder="https://www.youtube.com/watch?v=...", key="fv2")
        v3 = st.text_input("Video URL 3 (optional)", placeholder="https://www.youtube.com/watch?v=...", key="fv3")
        fetch_clicked = st.button("Fetch from YouTube", key="fetch_url_btn", type="primary")
        video_urls_to_fetch = [u.strip() for u in [v1, v2, v3] if u.strip()]
        channel_url_out = video_urls_to_fetch[0] if video_urls_to_fetch else ""

    if fetch_clicked and video_urls_to_fetch:
        prog = st.empty()
        def on_prog(msg):
            prog.caption(f"⏳ {msg}")

        with st.spinner("Fetching transcripts, thumbnails, and frames..."):
            try:
                fetched = fetcher.fetch_from_urls(
                    video_urls_to_fetch,
                    n_frames=5,
                    on_progress=on_prog,
                )
                fetched["channel_url"] = channel_url_out
                fetched["video_urls"] = video_urls_to_fetch
                st.session_state.fetched = fetched
                prog.empty()
                st.rerun()
            except Exception as e:
                st.error(f"Fetch failed: {e}")

    # Show fetched data preview
    if "fetched" in st.session_state:
        f = st.session_state.fetched
        n_t = len(f.get("transcripts", []))
        n_th = len(f.get("thumbnail_bytes", []))
        n_fr = len(f.get("frame_bytes", []))

        st.markdown(
            f'<div class="fetched-badge">✅ {n_t} transcripts · {n_fr} frames · {n_th} thumbnails fetched</div>',
            unsafe_allow_html=True,
        )

        if f.get("frame_bytes"):
            st.caption("Extracted frames:")
            cols = st.columns(min(5, len(f["frame_bytes"])))
            for i, frame in enumerate(f["frame_bytes"][:5]):
                cols[i].image(frame, use_column_width=True)

        if f.get("thumbnail_bytes"):
            st.caption("Channel thumbnails:")
            cols = st.columns(min(3, len(f["thumbnail_bytes"])))
            for i, thumb in enumerate(f["thumbnail_bytes"][:3]):
                cols[i].image(thumb, use_column_width=True)

        for i, t in enumerate(f.get("transcripts", [])):
            with st.expander(f"Transcript {i+1} — {len(t.split())} words"):
                st.text(t[:600] + ("…" if len(t) > 600 else ""))

        if st.button("Clear & re-fetch", key="clear_fetch"):
            st.session_state.pop("fetched", None)
            st.rerun()

        st.markdown("---")
        return True  # fetched data is ready

    return False  # no fetched data yet


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.markdown('<div class="yt-header">▶ YouTube Clone Engine — Auto</div>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sub">Enter a URL → auto-fetch everything → click Start → get a finished video</div>', unsafe_allow_html=True)
    st.markdown("---")

    if "auto_result" in st.session_state:
        _render_results()
        return

    has_fetched = _render_fetch_section()

    # ── Production form ───────────────────────────────────────────────────
    st.markdown("### 2. Topic")
    topic = st.text_input(
        "Topic for the new video",
        placeholder="e.g. Why most people never reach their goals",
        key="auto_topic",
        label_visibility="collapsed",
    )

    # Manual fallback uploads (shown when fetch hasn't been done)
    visual_files, thumbnail_files = [], []
    if not has_fetched:
        st.markdown("### 3. Visual Samples *(optional — or use URL fetch above)*")
        visual_files = st.file_uploader(
            "Upload 3–5 video frame screenshots",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="auto_visuals",
        )
        st.markdown("### 4. Thumbnail Samples *(optional)*")
        thumbnail_files = st.file_uploader(
            "Upload 2–3 channel thumbnail images",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="auto_thumbs",
        )
        st.markdown("### 5. Settings")
    else:
        st.markdown("### 3. Settings")

    col1, col2 = st.columns(2)
    with col1:
        voice = st.selectbox(
            "Voiceover voice",
            ["onyx", "echo", "alloy", "fable", "nova", "shimmer"],
            help="onyx=deep male · echo=male · alloy=neutral · fable=british · nova=female · shimmer=soft female",
        )
    with col2:
        max_beats = st.slider("Max image beats", min_value=10, max_value=30, value=20)

    img_cost = max_beats * 0.04 + 0.08
    st.markdown(
        f'<div class="cost-note">Estimated cost: ~${img_cost:.2f} DALL-E + ~$0.03 TTS</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")
    start = st.button("▶ Start Full Production", type="primary", use_container_width=True)

    if start:
        # Resolve inputs from fetched data OR manual uploads
        if has_fetched:
            f = st.session_state.fetched
            transcripts = f.get("transcripts", [])
            channel_url = f.get("channel_url", "")
            visual_b64s, visual_mimes = _bytes_to_b64_mime(f.get("frame_bytes", []), "image/jpeg")
            thumb_b64s, thumb_mimes = _bytes_to_b64_mime(f.get("thumbnail_bytes", []), "image/jpeg")
        else:
            transcripts = []  # no manual transcript inputs in this flow
            channel_url = ""
            visual_b64s, visual_mimes = _files_to_b64(list(visual_files)) if visual_files else ([], [])
            thumb_b64s, thumb_mimes = _files_to_b64(list(thumbnail_files)) if thumbnail_files else ([], [])

        errors = []
        if len(transcripts) < 2:
            errors.append("Need at least 2 transcripts — use the URL fetch above.")
        if not topic.strip():
            errors.append("Topic is required.")
        for e in errors:
            st.error(e)
        if errors:
            st.stop()

        engine = _get_engine()
        producer = _get_producer()

        status = st.status("Running full production pipeline...", expanded=True)
        try:
            result = _run_pipeline(
                engine=engine,
                producer=producer,
                channel_url=channel_url,
                transcripts=transcripts,
                topic=topic.strip(),
                visual_b64s=visual_b64s,
                visual_mimes=visual_mimes,
                thumb_b64s=thumb_b64s,
                thumb_mimes=thumb_mimes,
                voice=voice,
                max_beats=max_beats,
                status_widget=status,
            )
            status.update(label="Production complete!", state="complete")
            st.session_state.auto_result = result
            st.rerun()
        except Exception as exc:
            status.update(label=f"Error: {exc}", state="error")
            st.exception(exc)


if __name__ == "__main__":
    main()
