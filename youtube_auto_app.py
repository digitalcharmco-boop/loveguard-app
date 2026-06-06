#!/usr/bin/env python3
"""
YouTube Channel Clone Engine — Auto Mode
One-click: enter inputs → click Start → get finished MP4 + thumbnail + docx.
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
.step-row { background:#1a1a1a; border-left:3px solid #FF0000;
            padding:0.5rem 1rem; border-radius:0 6px 6px 0; margin:0.3rem 0; }
.cost-note { color:#888; font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)


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


def _run_pipeline(
    engine, producer,
    channel_url, transcripts, topic,
    visual_files, thumbnail_files,
    voice, max_beats,
    status_widget,
):
    """Run all 11 states + video production. Returns result dict."""
    result = {}

    with status_widget:
        # ── State 4: Style DNA ──────────────────────────────────────────
        st.write("**[1/9]** Extracting Style DNA from transcripts...")
        dna = engine.extract_style_dna(transcripts, channel_url)
        result["style_dna"] = dna
        st.write(f"✅ Style DNA extracted — niche: {dna.get('niche', '—')}")

        # ── State 5: Script ─────────────────────────────────────────────
        st.write("**[2/9]** Generating script...")
        script_result = engine.generate_script(dna, topic)
        script = script_result["script"]
        wc = script_result["word_count"]
        result["script"] = script
        result["word_count"] = wc
        result["target_word_count"] = script_result["target_word_count"]
        st.write(f"✅ Script generated — {wc} words")

        # ── State 6: Visual analysis ────────────────────────────────────
        visual_profile = None
        if visual_files:
            st.write("**[3/9]** Analyzing visual style samples...")
            b64s, mimes = _files_to_b64(visual_files)
            visual_profile = engine.analyze_visual_samples(b64s[:5], mimes[:5])
            result["visual_profile"] = visual_profile
            st.write("✅ Visual style profile extracted")
        else:
            result["visual_profile"] = None
            st.write("**[3/9]** No visual samples — skipping visual analysis")

        # ── State 7: Image prompts ──────────────────────────────────────
        st.write("**[4/9]** Generating image prompts for every beat...")
        all_prompts = engine.generate_image_prompts(script, visual_profile or {})
        # Cap at max_beats
        beats = all_prompts[:max_beats]
        result["image_prompts"] = all_prompts
        st.write(f"✅ {len(beats)} beats selected (of {len(all_prompts)} generated)")

        # ── State 9: Thumbnail analysis ─────────────────────────────────
        thumbnail_dna = None
        if thumbnail_files:
            st.write("**[5/9]** Analyzing thumbnail design language...")
            b64s, mimes = _files_to_b64(thumbnail_files)
            thumbnail_dna = engine.analyze_thumbnails(b64s[:3], mimes[:3])
            result["thumbnail_dna"] = thumbnail_dna
            st.write("✅ Thumbnail DNA extracted")
        else:
            result["thumbnail_dna"] = None
            st.write("**[5/9]** No thumbnails — skipping thumbnail analysis")

        # ── State 10: Thumbnail concepts ────────────────────────────────
        concepts = engine.generate_thumbnail_concepts(
            thumbnail_dna or {}, topic, script
        )
        result["thumbnail_concepts"] = concepts
        st.write("✅ 5 thumbnail concepts generated")

        # ── Image generation (DALL-E 3) ─────────────────────────────────
        img_status = st.empty()
        img_status.write(f"**[6/9]** Generating {len(beats)} images via DALL-E 3...")

        def on_img_progress(i, total, msg):
            img_status.write(f"**[6/9]** {msg} (allow ~{(total - i) * 13 // 60} min remaining)")

        image_paths = producer.generate_images(beats, on_progress=on_img_progress)
        result["image_paths"] = [str(p) for p in image_paths]
        img_status.write(f"✅ {len(image_paths)} images generated")

        # ── Thumbnail image (DALL-E 3 HD) ───────────────────────────────
        st.write("**[7/9]** Generating thumbnail image (HD)...")
        thumb_path = producer.generate_thumbnail_image(concepts[0])
        result["thumbnail_path"] = str(thumb_path)
        st.write("✅ Thumbnail image generated")

        # ── Voiceover (OpenAI TTS) ──────────────────────────────────────
        st.write("**[8/9]** Generating voiceover...")
        audio_path = producer.generate_voiceover(script, voice=voice)
        result["audio_path"] = str(audio_path)
        st.write("✅ Voiceover generated")

        # ── Video assembly (MoviePy) ─────────────────────────────────────
        asm_status = st.empty()
        asm_status.write("**[9/9]** Assembling final video...")

        from pathlib import Path

        def on_asm(msg):
            asm_status.write(f"**[9/9]** {msg}")

        video_path = producer.assemble_video(
            image_paths=[Path(p) for p in result["image_paths"]],
            audio_path=Path(result["audio_path"]),
            on_progress=on_asm,
        )
        result["video_path"] = str(video_path)
        asm_status.write("✅ Video assembled")

        # ── Export docx ─────────────────────────────────────────────────
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


def main():
    st.markdown('<div class="yt-header">▶ YouTube Clone Engine — Auto</div>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sub">Fill in the form below and click Start — get a finished video</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── Results page ────────────────────────────────────────────────────────
    if "auto_result" in st.session_state:
        r = st.session_state.auto_result
        st.success("Production complete!")

        # Video
        st.markdown("### Final Video")
        video_path = r.get("video_path")
        if video_path and os.path.exists(video_path):
            st.video(video_path)
            with open(video_path, "rb") as vf:
                st.download_button(
                    "Download MP4",
                    data=vf.read(),
                    file_name="youtube_video.mp4",
                    mime="video/mp4",
                )

        # Thumbnail
        st.markdown("### Thumbnail")
        thumb_path = r.get("thumbnail_path")
        if thumb_path and os.path.exists(thumb_path):
            st.image(thumb_path, use_column_width=True)
            with open(thumb_path, "rb") as tf:
                st.download_button(
                    "Download Thumbnail PNG",
                    data=tf.read(),
                    file_name="thumbnail.png",
                    mime="image/png",
                )

        # Script + docx
        st.markdown("### Script")
        st.text_area("Generated Script", value=r.get("script", ""), height=300)

        if r.get("docx_bytes"):
            st.download_button(
                "Download Full Package (.docx)",
                data=r["docx_bytes"],
                file_name="youtube_clone_package.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        st.markdown("---")
        if st.button("Start New Session"):
            del st.session_state["auto_result"]
            if "auto_engine" in st.session_state:
                del st.session_state["auto_engine"]
            if "auto_producer" in st.session_state:
                del st.session_state["auto_producer"]
            st.rerun()
        return

    # ── Input form ───────────────────────────────────────────────────────────
    with st.form("auto_form"):
        st.markdown("### 1. Channel")
        channel_url = st.text_input(
            "Channel URL",
            placeholder="https://www.youtube.com/@channelname",
        )

        st.markdown("### 2. Transcripts")
        t1 = st.text_area("Transcript 1 *", height=150, placeholder="Paste full video transcript...")
        t2 = st.text_area("Transcript 2 *", height=150, placeholder="Paste full video transcript...")
        t3 = st.text_area("Transcript 3 (optional)", height=100)

        st.markdown("### 3. Topic")
        topic = st.text_input(
            "Topic for the new video *",
            placeholder="e.g. Why most people never reach their goals",
        )

        st.markdown("### 4. Visual Samples *(optional but recommended)*")
        visual_files = st.file_uploader(
            "Upload 3–5 video frame screenshots",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="auto_visuals",
        )

        st.markdown("### 5. Thumbnail Samples *(optional)*")
        thumbnail_files = st.file_uploader(
            "Upload 2–3 channel thumbnail images",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="auto_thumbs",
        )

        st.markdown("### 6. Settings")
        col1, col2 = st.columns(2)
        with col1:
            voice = st.selectbox(
                "Voiceover voice",
                ["onyx", "echo", "alloy", "fable", "nova", "shimmer"],
                index=0,
                help="onyx=deep male · echo=male · alloy=neutral · fable=british · nova=female · shimmer=soft female",
            )
        with col2:
            max_beats = st.slider(
                "Max image beats",
                min_value=10,
                max_value=30,
                value=20,
                help="More beats = more variety but longer generation time and higher cost",
            )

        img_cost = max_beats * 0.04 + 0.08  # standard + 1 HD thumbnail
        st.markdown(
            f'<div class="cost-note">Estimated DALL-E cost: ~${img_cost:.2f} '
            f'({max_beats} standard images + 1 HD thumbnail) + TTS ~$0.03</div>',
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("▶ Start Full Production", type="primary", use_container_width=True)

    if submitted:
        transcripts = [t.strip() for t in [t1, t2, t3] if t.strip()]
        errors = []
        if not channel_url.strip():
            errors.append("Channel URL is required.")
        if len(transcripts) < 2:
            errors.append("At least 2 transcripts are required.")
        if not topic.strip():
            errors.append("Topic is required.")
        if errors:
            for e in errors:
                st.error(e)
            st.stop()

        engine = _get_engine()
        producer = _get_producer()

        status = st.status("Running full production pipeline...", expanded=True)
        try:
            result = _run_pipeline(
                engine=engine,
                producer=producer,
                channel_url=channel_url.strip(),
                transcripts=transcripts,
                topic=topic.strip(),
                visual_files=list(visual_files) if visual_files else [],
                thumbnail_files=list(thumbnail_files) if thumbnail_files else [],
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
