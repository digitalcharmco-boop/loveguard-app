#!/usr/bin/env python3
"""
YouTube Content Calendar — Auto Mode
Clones a channel's style DNA → generates 5–10 original video concepts
→ select which to produce → batch produces MP4 + thumbnail for each.
"""

import base64
import io
import mimetypes
import os
import sys
import zipfile

import streamlit as st

sys.path.append(os.path.dirname(__file__))

st.set_page_config(
    page_title="YouTube Content Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    for _k in ["OPENAI_API_KEY"]:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

st.markdown("""
<style>
body { background-color: #0f0f0f; }
.yt-header { text-align:center; color:#FF0000; font-size:2rem; font-weight:900; }
.yt-sub { text-align:center; color:#888; font-size:0.85rem; margin-top:0.1rem; }
.concept-card {
    background:#1a1a1a; border:1px solid #2a2a2a; border-radius:8px;
    padding:1rem; margin:0.5rem 0;
}
.concept-num { color:#FF0000; font-weight:800; font-size:1.1rem; }
.concept-title { font-size:1.1rem; font-weight:700; margin:0.3rem 0; }
.concept-label { color:#FF0000; font-size:0.7rem; font-weight:700;
                 text-transform:uppercase; letter-spacing:0.8px; }
.done-badge { color:#00cc66; font-weight:700; }
.cost-note { color:#888; font-size:0.8rem; }
.fetched-badge { color:#00cc66; font-weight:700; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()

def _bytes_to_b64_mime(data_list, mime="image/jpeg"):
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
    if "cal_engine" not in st.session_state:
        st.session_state.cal_engine = YouTubeCloneEngine(api_key=api_key)
    return st.session_state.cal_engine

def _get_producer():
    from execution.video_producer import VideoProducer
    api_key = os.getenv("OPENAI_API_KEY")
    if "cal_producer" not in st.session_state:
        st.session_state.cal_producer = VideoProducer(api_key=api_key)
    return st.session_state.cal_producer

def _get_fetcher():
    from execution.youtube_fetcher import YouTubeFetcher
    if "cal_fetcher" not in st.session_state:
        st.session_state.cal_fetcher = YouTubeFetcher()
    return st.session_state.cal_fetcher


# ── Single video production ────────────────────────────────────────────────────

def _produce_video(engine, producer, concept, style_dna, channel_url,
                   visual_b64s, visual_mimes, thumb_b64s, thumb_mimes,
                   voice, max_beats, status_widget, video_index):
    """Produce one video from a calendar concept. Returns result dict."""
    from pathlib import Path

    topic = concept["topic"]
    result = {"concept": concept}

    with status_widget:
        st.write(f"**Script** — generating for: *{concept['title']}*")
        script_result = engine.generate_script(style_dna, topic)
        script = script_result["script"]
        result.update(script=script, word_count=script_result["word_count"])
        st.write(f"✅ Script — {script_result['word_count']} words")

        visual_profile = None
        if visual_b64s:
            st.write("**Visual analysis...**")
            visual_profile = engine.analyze_visual_samples(visual_b64s[:5], visual_mimes[:5])
            result["visual_profile"] = visual_profile
            st.write("✅ Visual profile extracted")

        st.write("**Image prompts...**")
        all_prompts = engine.generate_image_prompts(script, visual_profile or {})
        beats = all_prompts[:max_beats]
        result["image_prompts"] = all_prompts
        st.write(f"✅ {len(beats)} beats")

        thumbnail_dna = None
        if thumb_b64s:
            st.write("**Thumbnail analysis...**")
            thumbnail_dna = engine.analyze_thumbnails(thumb_b64s[:3], thumb_mimes[:3])
        thumb_concepts = engine.generate_thumbnail_concepts(
            thumbnail_dna or {}, topic, script
        )
        result["thumbnail_concepts"] = thumb_concepts
        st.write("✅ Thumbnail concepts ready")

        img_ph = st.empty()
        img_ph.write(f"**DALL-E 3** — generating {len(beats)} images...")

        def on_img(i, total, msg):
            img_ph.write(f"**DALL-E 3** — {msg} (~{(total - i) * 13 // 60} min left)")

        output_dir = f".tmp/video/video_{video_index:02d}"
        producer.output_dir = __import__("pathlib").Path(output_dir)
        producer.output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = producer.generate_images(beats, on_progress=on_img)
        result["image_paths"] = [str(p) for p in image_paths]
        img_ph.write(f"✅ {len(image_paths)} images generated")

        st.write("**Thumbnail (HD)...**")
        thumb_path = producer.generate_thumbnail_image(thumb_concepts[0])
        result["thumbnail_path"] = str(thumb_path)
        st.write("✅ Thumbnail generated")

        st.write("**Voiceover...**")
        audio_path = producer.generate_voiceover(script, voice=voice)
        result["audio_path"] = str(audio_path)
        st.write("✅ Voiceover ready")

        asm_ph = st.empty()
        asm_ph.write("**Assembling MP4...**")

        def on_asm(msg):
            asm_ph.write(f"**Assembling** — {msg}")

        video_path = producer.assemble_video(
            image_paths=[Path(p) for p in result["image_paths"]],
            audio_path=Path(result["audio_path"]),
            on_progress=on_asm,
        )
        result["video_path"] = str(video_path)
        asm_ph.write("✅ MP4 assembled")

    return result


# ── Fetch section ──────────────────────────────────────────────────────────────

def _render_fetch_section():
    st.markdown("### 1. Source Channel")
    st.caption("Fetch transcripts, frames, and thumbnails automatically — no manual uploads needed.")

    src_type = st.radio(
        "",
        ["Channel URL — auto-fetch recent videos", "Specific video URLs"],
        key="cal_src_type",
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
                key="cal_channel_url",
                label_visibility="collapsed",
            )
        with col2:
            n_vids = st.selectbox("Videos", [2, 3], index=1, key="cal_n_vids")
        fetch_clicked = st.button("Fetch from YouTube", key="cal_fetch_ch", type="primary")
        channel_url_out = ch_url.strip()
        if fetch_clicked and ch_url.strip():
            with st.spinner("Listing channel videos..."):
                try:
                    video_urls_to_fetch = fetcher.get_channel_video_urls(ch_url.strip(), n_vids)
                except Exception as e:
                    st.error(f"Could not list channel videos: {e}")
                    fetch_clicked = False
    else:
        v1 = st.text_input("Video URL 1 *", key="cal_v1")
        v2 = st.text_input("Video URL 2 *", key="cal_v2")
        v3 = st.text_input("Video URL 3 (optional)", key="cal_v3")
        fetch_clicked = st.button("Fetch from YouTube", key="cal_fetch_urls", type="primary")
        video_urls_to_fetch = [u.strip() for u in [v1, v2, v3] if u.strip()]
        channel_url_out = video_urls_to_fetch[0] if video_urls_to_fetch else ""

    if fetch_clicked and video_urls_to_fetch:
        prog = st.empty()
        def on_prog(msg):
            prog.caption(f"⏳ {msg}")
        with st.spinner("Fetching..."):
            try:
                fetched = fetcher.fetch_from_urls(video_urls_to_fetch, n_frames=5, on_progress=on_prog)
                fetched["channel_url"] = channel_url_out
                fetched["video_urls"] = video_urls_to_fetch
                st.session_state.cal_fetched = fetched
                prog.empty()
                st.rerun()
            except Exception as e:
                st.error(f"Fetch failed: {e}")

    if "cal_fetched" in st.session_state:
        f = st.session_state.cal_fetched
        n_t = len(f.get("transcripts", []))
        n_fr = len(f.get("frame_bytes", []))
        n_th = len(f.get("thumbnail_bytes", []))
        st.markdown(
            f'<div class="fetched-badge">✅ {n_t} transcripts · {n_fr} frames · {n_th} thumbnails</div>',
            unsafe_allow_html=True,
        )
        if f.get("frame_bytes"):
            cols = st.columns(min(5, len(f["frame_bytes"])))
            for i, fr in enumerate(f["frame_bytes"][:5]):
                cols[i].image(fr, use_column_width=True)
        if st.button("Clear & re-fetch", key="cal_clear"):
            for k in ["cal_fetched", "cal_dna", "cal_calendar"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown("---")
        return True

    return False


# ── Calendar generation ────────────────────────────────────────────────────────

def _render_calendar_section(engine):
    f = st.session_state.cal_fetched
    transcripts = f.get("transcripts", [])
    channel_url = f.get("channel_url", "")

    st.markdown("### 2. Generate Content Calendar")

    col1, col2 = st.columns([3, 1])
    with col2:
        n_concepts = st.selectbox("How many video ideas?", [5, 7, 10], index=0, key="cal_n_concepts")

    # Extract DNA if not done
    if "cal_dna" not in st.session_state:
        with col1:
            if st.button("Generate Calendar →", key="cal_gen_btn", type="primary"):
                with st.spinner("Extracting style DNA and generating content ideas..."):
                    dna = engine.extract_style_dna(transcripts, channel_url)
                    st.session_state.cal_dna = dna
                    concepts = engine.generate_content_calendar(dna, n_videos=n_concepts)
                    st.session_state.cal_calendar = concepts
                st.rerun()
        return False
    else:
        with col1:
            if st.button("Regenerate Calendar", key="cal_regen_btn"):
                with st.spinner("Generating fresh content ideas..."):
                    concepts = engine.generate_content_calendar(
                        st.session_state.cal_dna, n_videos=n_concepts
                    )
                    st.session_state.cal_calendar = concepts
                st.rerun()

    return True


# ── Concept selection ──────────────────────────────────────────────────────────

def _render_concept_picker():
    concepts = st.session_state.cal_calendar
    produced = st.session_state.get("cal_produced", {})

    st.markdown("### 3. Your Content Calendar")
    st.caption("Select the videos you want to produce, then click **Produce Selected**.")

    selected_indices = []
    for i, c in enumerate(concepts):
        is_done = i in produced
        col_check, col_content = st.columns([0.05, 0.95])
        with col_check:
            checked = st.checkbox("", key=f"cal_sel_{i}", value=is_done, disabled=is_done)
        with col_content:
            with st.container():
                done_label = ' <span class="done-badge">✅ Produced</span>' if is_done else ""
                st.markdown(
                    f'<div class="concept-card">'
                    f'<span class="concept-num">#{i + 1}</span>{done_label}'
                    f'<div class="concept-title">{c.get("title", "")}</div>'
                    f'<div class="concept-label">Topic</div>{c.get("topic", "")}<br><br>'
                    f'<div class="concept-label">Hook</div>{c.get("hook", "")}<br><br>'
                    f'<div class="concept-label">Angle</div>{c.get("angle", "")}<br><br>'
                    f'<div class="concept-label">Thumbnail Idea</div>{c.get("thumbnail_concept", "")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        if checked and not is_done:
            selected_indices.append(i)

    return selected_indices


# ── Production settings + trigger ─────────────────────────────────────────────

def _render_production_controls(selected_indices):
    if not selected_indices:
        return

    st.markdown("### 4. Production Settings")
    col1, col2 = st.columns(2)
    with col1:
        voice = st.selectbox(
            "Voiceover voice",
            ["onyx", "echo", "alloy", "fable", "nova", "shimmer"],
            help="onyx=deep male · echo=male · alloy=neutral · fable=british · nova=female · shimmer=soft female",
        )
    with col2:
        max_beats = st.slider("Max image beats per video", 10, 25, 15)

    n_sel = len(selected_indices)
    cost_per = max_beats * 0.04 + 0.08
    total_cost = cost_per * n_sel
    time_est = n_sel * (max_beats * 13 + 300) // 60
    st.markdown(
        f'<div class="cost-note">'
        f'{n_sel} video(s) selected · ~${total_cost:.2f} DALL-E + TTS · '
        f'~{time_est} min estimated</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")
    produce = st.button(
        f"▶ Produce {n_sel} Video{'s' if n_sel > 1 else ''}",
        type="primary",
        use_container_width=True,
    )

    return produce, voice, max_beats


# ── Download section ───────────────────────────────────────────────────────────

def _render_downloads():
    produced = st.session_state.get("cal_produced", {})
    if not produced:
        return

    st.markdown("### Downloads")
    for idx, result in produced.items():
        concept = result.get("concept", {})
        title = concept.get("title", f"Video {idx + 1}")
        slug = title[:30].replace(" ", "_").replace("/", "-")

        with st.expander(f"#{idx + 1} — {title}", expanded=True):
            vp = result.get("video_path")
            if vp and os.path.exists(vp):
                st.video(vp)
                col1, col2 = st.columns(2)
                with open(vp, "rb") as f:
                    col1.download_button(
                        "Download MP4",
                        f.read(),
                        file_name=f"{slug}.mp4",
                        mime="video/mp4",
                        key=f"dl_mp4_{idx}",
                    )
            tp = result.get("thumbnail_path")
            if tp and os.path.exists(tp):
                st.image(tp, use_column_width=True)
                with open(tp, "rb") as f:
                    col2.download_button(
                        "Download Thumbnail",
                        f.read(),
                        file_name=f"{slug}_thumbnail.png",
                        mime="image/png",
                        key=f"dl_thumb_{idx}",
                    )

    # Zip all
    if len(produced) > 1:
        st.markdown("---")
        if st.button("Download All as ZIP", use_container_width=True):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for idx, result in produced.items():
                    slug = result.get("concept", {}).get("title", f"video_{idx}")[:30]
                    slug = slug.replace(" ", "_").replace("/", "-")
                    vp = result.get("video_path")
                    if vp and os.path.exists(vp):
                        zf.write(vp, f"{idx+1:02d}_{slug}.mp4")
                    tp = result.get("thumbnail_path")
                    if tp and os.path.exists(tp):
                        zf.write(tp, f"{idx+1:02d}_{slug}_thumbnail.png")
            buf.seek(0)
            st.download_button(
                "Download ZIP",
                buf.read(),
                file_name="content_calendar_videos.zip",
                mime="application/zip",
            )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.markdown('<div class="yt-header">📅 YouTube Content Calendar</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="yt-sub">Clone any channel\'s style → generate 5–10 original video ideas '
        '→ produce each as a finished MP4 + thumbnail ready to post</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    engine = _get_engine()
    producer = _get_producer()

    # Step 1: Fetch
    has_fetched = _render_fetch_section()
    if not has_fetched:
        return

    # Step 2: Generate calendar
    has_calendar = _render_calendar_section(engine)
    if not has_calendar:
        return

    # Show any completed downloads first
    _render_downloads()

    # Step 3: Concept picker
    selected_indices = _render_concept_picker()

    # Step 4: Production settings + trigger
    if not selected_indices:
        st.markdown("")
        st.caption("Select at least one concept above to enable production.")
        if st.button("Start New Session", key="cal_restart"):
            for k in list(st.session_state.keys()):
                if k.startswith("cal_"):
                    del st.session_state[k]
            st.rerun()
        return

    controls = _render_production_controls(selected_indices)
    if not controls:
        return
    produce, voice, max_beats = controls

    if not produce:
        return

    # Resolve visual/thumbnail data from fetched cache
    f = st.session_state.cal_fetched
    visual_b64s, visual_mimes = _bytes_to_b64_mime(f.get("frame_bytes", []), "image/jpeg")
    thumb_b64s, thumb_mimes = _bytes_to_b64_mime(f.get("thumbnail_bytes", []), "image/jpeg")
    style_dna = st.session_state.cal_dna
    channel_url = f.get("channel_url", "")

    if "cal_produced" not in st.session_state:
        st.session_state.cal_produced = {}

    concepts = st.session_state.cal_calendar

    for i, idx in enumerate(selected_indices):
        concept = concepts[idx]
        st.markdown(f"#### Producing Video {i + 1}/{len(selected_indices)}: *{concept['title']}*")
        status = st.status(f"Video #{idx + 1} — {concept['title']}", expanded=True)
        try:
            result = _produce_video(
                engine=engine,
                producer=producer,
                concept=concept,
                style_dna=style_dna,
                channel_url=channel_url,
                visual_b64s=visual_b64s,
                visual_mimes=visual_mimes,
                thumb_b64s=thumb_b64s,
                thumb_mimes=thumb_mimes,
                voice=voice,
                max_beats=max_beats,
                status_widget=status,
                video_index=idx,
            )
            status.update(label=f"✅ {concept['title']} — complete", state="complete")
            st.session_state.cal_produced[idx] = result
        except Exception as exc:
            status.update(label=f"❌ {concept['title']} — failed: {exc}", state="error")
            st.exception(exc)

    st.rerun()


if __name__ == "__main__":
    main()
