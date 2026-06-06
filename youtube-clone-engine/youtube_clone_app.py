#!/usr/bin/env python3
"""
YouTube Channel Clone Engine — Streamlit UI
11-state interactive pipeline for channel analysis and content generation.
"""

import base64
import mimetypes
import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(__file__))

# Load Streamlit Cloud secrets into env vars
try:
    for _key in ["OPENAI_API_KEY"]:
        if _key in st.secrets and not os.environ.get(_key):
            os.environ[_key] = str(st.secrets[_key])
except Exception:
    pass

from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="YouTube Channel Clone Engine",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    body { background-color: #0f0f0f; }
    .yt-header {
        text-align: center;
        color: #FF0000;
        font-size: 1.9rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin-bottom: 0;
    }
    .yt-sub {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin-top: 0.1rem;
    }
    .state-label {
        color: #FF0000;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    .state-title {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .dna-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin: 0.4rem 0;
    }
    .dna-label {
        color: #FF0000;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 0.2rem;
    }
    .beat-card {
        background: #111;
        border-left: 3px solid #FF0000;
        padding: 0.6rem 1rem;
        margin: 0.4rem 0;
        border-radius: 0 6px 6px 0;
    }
    .beat-number {
        color: #FF0000;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .thumb-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 1.1rem;
        margin: 0.6rem 0;
    }
    .thumb-number {
        color: #FF0000;
        font-weight: 800;
        font-size: 1.1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

STATE_NAMES = {
    1: "Channel Link",
    2: "Video Transcripts",
    3: "Topic Selection",
    4: "Style DNA Analysis",
    5: "Script Generation",
    6: "Visual Sample Analysis",
    7: "Image Prompts",
    8: "Video Prompts",
    9: "Thumbnail Analysis",
    10: "Thumbnail Generation",
    11: "Export",
}

# ── Session state initialisation ────────────────────────────────────────────


def _init():
    defaults = {
        "yt_state": 1,
        "channel_url": "",
        "transcripts": [],
        "topic": "",
        "topic_ideas": [],
        "style_dna": None,
        "script": "",
        "word_count": 0,
        "target_word_count": 0,
        "visual_profile": None,
        "image_prompts": [],
        "thumbnail_dna": None,
        "thumbnail_concepts": [],
        "include_video_prompts": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _get_engine():
    from execution.youtube_clone_engine import YouTubeCloneEngine

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error(
            "**OPENAI_API_KEY not found.** Add it to your `.env` file or Streamlit secrets."
        )
        st.stop()
    if "yt_engine" not in st.session_state:
        st.session_state.yt_engine = YouTubeCloneEngine(api_key=api_key)
    return st.session_state.yt_engine


def _files_to_b64(uploaded_files):
    """Convert Streamlit uploaded files to (b64_strings, mime_types) lists."""
    b64_list, mime_list = [], []
    for f in uploaded_files:
        raw = f.read()
        b64_list.append(base64.b64encode(raw).decode("utf-8"))
        mime, _ = mimetypes.guess_type(f.name)
        mime_list.append(mime or "image/jpeg")
    return b64_list, mime_list


# ── Header ───────────────────────────────────────────────────────────────────


def _render_header():
    st.markdown('<div class="yt-header">▶ YouTube Channel Clone Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sub">Reverse-engineer any channel\'s content DNA</div>', unsafe_allow_html=True)
    st.markdown("---")
    current = st.session_state.yt_state
    c1, c2 = st.columns([5, 1])
    with c1:
        st.progress(current / 11)
    with c2:
        st.caption(f"{current} / 11")
    st.markdown(
        f'<div class="state-label">State {current} — {STATE_NAMES.get(current, "")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")


# ── State renderers ──────────────────────────────────────────────────────────


def _state_1():
    st.markdown("**Please provide the YouTube channel link.**")
    url = st.text_input(
        "Channel URL",
        value=st.session_state.channel_url,
        placeholder="https://www.youtube.com/@channelname",
        label_visibility="collapsed",
    )
    if st.button("Continue →", key="s1_next"):
        if not url.strip():
            st.warning("Please enter a channel URL.")
        else:
            st.session_state.channel_url = url.strip()
            st.session_state.yt_state = 2
            st.rerun()


def _state_2():
    st.markdown("**Provide 2–3 complete video transcripts from this channel.**")
    st.caption("Paste the full spoken content of each video.")
    t1 = st.text_area("Transcript 1 *", height=180, key="t1")
    t2 = st.text_area("Transcript 2 *", height=180, key="t2")
    t3 = st.text_area("Transcript 3 (optional)", height=120, key="t3")

    if st.button("Submit Transcripts →", key="s2_next"):
        transcripts = [t.strip() for t in [t1, t2, t3] if t.strip()]
        if len(transcripts) < 2:
            st.warning("Please provide at least 2 transcripts.")
        else:
            st.session_state.transcripts = transcripts
            st.session_state.yt_state = 3
            st.rerun()


def _state_3(engine):
    st.markdown("**Do you have a topic in mind, or should I generate video ideas?**")
    choice = st.radio(
        "",
        ["I have a topic in mind", "Generate ideas based on the channel"],
        key="s3_choice",
        label_visibility="collapsed",
    )

    if choice == "I have a topic in mind":
        topic = st.text_input(
            "Your topic",
            placeholder="e.g. 'Why most people never reach their goals'",
            key="s3_topic_input",
        )
        if st.button("Continue →", key="s3_own_next"):
            if not topic.strip():
                st.warning("Please enter a topic.")
                return
            st.session_state.topic = topic.strip()
            st.session_state.yt_state = 4
            st.rerun()
    else:
        if not st.session_state.topic_ideas:
            if st.button("Generate Video Ideas →", key="s3_gen"):
                with st.spinner("Analyzing channel DNA and generating ideas..."):
                    dna = engine.extract_style_dna(
                        st.session_state.transcripts, st.session_state.channel_url
                    )
                    st.session_state.style_dna = dna
                    st.session_state.target_word_count = int(dna.get("target_word_count", 1200))
                    st.session_state.topic_ideas = engine.generate_topic_ideas(dna)
                st.rerun()
        else:
            st.markdown("**Select a topic:**")
            selected = st.radio("", st.session_state.topic_ideas, key="s3_idea_select", label_visibility="collapsed")
            custom = st.text_input("Or enter a custom topic:", key="s3_custom")
            if st.button("Use This Topic →", key="s3_idea_next"):
                final = custom.strip() if custom.strip() else selected
                st.session_state.topic = final
                st.session_state.yt_state = 4
                st.rerun()


def _state_4(engine):
    # Compute style DNA if not already done (happens when user provided own topic)
    if not st.session_state.style_dna:
        with st.spinner("Extracting Style DNA from transcripts..."):
            dna = engine.extract_style_dna(
                st.session_state.transcripts, st.session_state.channel_url
            )
            st.session_state.style_dna = dna
            st.session_state.target_word_count = int(dna.get("target_word_count", 1200))
        st.rerun()

    dna = st.session_state.style_dna
    twc = dna.get("target_word_count", 1200)

    st.markdown(f"**Topic:** `{st.session_state.topic}`")
    st.markdown(f"**Target Word Count:** `{twc} words`")
    st.markdown("---")

    dimension_labels = [
        ("niche", "Niche"),
        ("target_audience", "Target Audience"),
        ("hook_architecture", "Hook Architecture"),
        ("script_flow", "Script Flow"),
        ("sentence_rhythm", "Sentence Rhythm"),
        ("tone_profile", "Tone Profile"),
        ("transition_techniques", "Transition Techniques"),
        ("curiosity_gaps", "Curiosity Gaps"),
        ("emotional_triggers", "Emotional Triggers"),
        ("retention_devices", "Retention Devices"),
        ("direct_address_style", "Direct Address Style"),
        ("words_per_second", "Words Per Second"),
    ]

    col1, col2 = st.columns(2)
    for i, (key, label) in enumerate(dimension_labels):
        val = dna.get(key, "—")
        card = f'<div class="dna-card"><div class="dna-label">{label}</div>{val}</div>'
        (col1 if i % 2 == 0 else col2).markdown(card, unsafe_allow_html=True)

    if dna.get("overall_voice"):
        st.markdown(
            f'<div class="dna-card"><div class="dna-label">Overall Voice</div>{dna["overall_voice"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    if st.button(f"Generate Script (~{twc} words) →", key="s4_next"):
        with st.spinner("Writing script..."):
            result = engine.generate_script(dna, st.session_state.topic)
            st.session_state.script = result["script"]
            st.session_state.word_count = result["word_count"]
            st.session_state.target_word_count = result["target_word_count"]
        st.session_state.yt_state = 5
        st.rerun()


def _state_5():
    wc = st.session_state.word_count
    twc = st.session_state.target_word_count
    pct = abs(wc - twc) / twc * 100 if twc else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Word Count", wc)
    col2.metric("Target", twc)
    col3.metric("Deviation", f"{pct:.1f}%", delta_color="inverse" if pct > 5 else "normal")

    if pct > 5:
        st.warning(f"Word count is {pct:.1f}% off target (acceptable: ≤5%).")

    st.markdown("---")
    st.text_area("Script", value=st.session_state.script, height=500, key="s5_script_view")

    if st.button("Confirm Script & Continue →", key="s5_next"):
        # Capture any manual edits
        st.session_state.script = st.session_state.s5_script_view
        st.session_state.word_count = len(st.session_state.script.split())
        st.session_state.yt_state = 6
        st.rerun()


def _state_6(engine):
    if st.session_state.visual_profile:
        # Already analyzed — show profile and let user continue
        vp = st.session_state.visual_profile
        st.markdown("**Visual Style Profile**")
        st.markdown("---")
        col1, col2 = st.columns(2)
        items = list(vp.items())
        for i, (key, val) in enumerate(items):
            card = f'<div class="dna-card"><div class="dna-label">{key.replace("_", " ").title()}</div>{val}</div>'
            (col1 if i % 2 == 0 else col2).markdown(card, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Generate Image Prompts →", key="s6_next"):
            st.session_state.yt_state = 7
            st.rerun()
        return

    st.markdown("**Upload 3–5 screenshots or frame samples from the channel's videos — not thumbnails.**")
    st.caption("These drive the visual style for all image and video prompts.")
    files = st.file_uploader(
        "Upload screenshots",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="s6_uploads",
        label_visibility="collapsed",
    )

    if files:
        st.caption(f"{len(files)} file(s) selected.")
        if len(files) > 5:
            st.warning("Only the first 5 images will be used.")
            files = files[:5]

    if st.button("Analyze Visuals →", key="s6_analyze"):
        if not files:
            st.warning("Please upload at least one screenshot.")
            return
        with st.spinner("Analyzing visual style..."):
            b64s, mimes = _files_to_b64(files)
            vp = engine.analyze_visual_samples(b64s, mimes)
            st.session_state.visual_profile = vp
        st.rerun()


def _state_7(engine):
    # Generate prompts on first entry
    if not st.session_state.image_prompts:
        with st.spinner("Generating image prompts for every beat (this may take a moment)..."):
            prompts = engine.generate_image_prompts(
                st.session_state.script, st.session_state.visual_profile
            )
            st.session_state.image_prompts = prompts
        st.rerun()

    prompts = st.session_state.image_prompts
    st.markdown(f"**{len(prompts)} beats generated.**")
    st.markdown("---")

    for beat in prompts:
        bn = beat.get("beat_number", "?")
        seg = beat.get("segment", "")
        with st.expander(f"Beat {bn} — {seg[:60]}{'…' if len(seg) > 60 else ''}", expanded=False):
            st.markdown(
                f'<div class="beat-card">'
                f'<div class="beat-number">Script Segment</div>{seg}</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="beat-number" style="color:#FF0000;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin:0.6rem 0 0.2rem;">Image Prompt — copy ↓</div>', unsafe_allow_html=True)
            st.code(beat.get("image_prompt", ""), language=None)
            cols = st.columns(2)
            for i, (field, label) in enumerate([
                ("camera_angle", "Camera Angle"),
                ("lighting", "Lighting"),
                ("mood", "Mood"),
                ("action", "Action"),
                ("visual_style", "Visual Style"),
            ]):
                if beat.get(field):
                    cols[i % 2].markdown(
                        f'<div class="beat-card"><div class="beat-number">{label}</div>{beat[field]}</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("")
    if st.button("Continue →", key="s7_next"):
        st.session_state.yt_state = 8
        st.rerun()


def _state_8(engine):
    # If video prompts already generated, show review + continue
    if st.session_state.include_video_prompts:
        prompts = st.session_state.image_prompts
        st.markdown(f"**{len(prompts)} video prompts generated.** Copy any prompt below.")
        st.markdown("---")
        for beat in prompts:
            bn = beat.get("beat_number", "?")
            seg = beat.get("segment", "")
            with st.expander(f"Beat {bn} — {seg[:60]}{'…' if len(seg) > 60 else ''}", expanded=False):
                st.markdown(
                    f'<div class="beat-card"><div class="beat-number">Script Segment</div>{seg}</div>',
                    unsafe_allow_html=True,
                )
                if beat.get("image_prompt"):
                    st.markdown('<div class="beat-number" style="color:#FF0000;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin:0.6rem 0 0.2rem;">Image Prompt — copy ↓</div>', unsafe_allow_html=True)
                    st.code(beat["image_prompt"], language=None)
                if beat.get("video_prompt"):
                    st.markdown('<div class="beat-number" style="color:#FF0000;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin:0.6rem 0 0.2rem;">Video Prompt — copy ↓</div>', unsafe_allow_html=True)
                    st.code(beat["video_prompt"], language=None)
        st.markdown("")
        if st.button("Continue to Thumbnail Analysis →", key="s8_continue"):
            st.session_state.yt_state = 9
            st.rerun()
        return

    st.markdown("**Would you like video motion prompts generated for each image prompt?**")
    col1, col2 = st.columns(2)

    if col1.button("Yes — Generate Video Prompts", key="s8_yes"):
        with st.spinner("Generating video motion prompts..."):
            enhanced = engine.generate_video_prompts(st.session_state.image_prompts)
            st.session_state.image_prompts = enhanced
            st.session_state.include_video_prompts = True
        st.rerun()

    if col2.button("No — Skip to Thumbnails", key="s8_no"):
        st.session_state.yt_state = 9
        st.rerun()


def _state_9(engine):
    if st.session_state.thumbnail_dna:
        td = st.session_state.thumbnail_dna
        st.markdown("**Thumbnail DNA**")
        st.markdown("---")
        col1, col2 = st.columns(2)
        items = list(td.items())
        for i, (key, val) in enumerate(items):
            display = ", ".join(val) if isinstance(val, list) else str(val)
            card = f'<div class="dna-card"><div class="dna-label">{key.replace("_", " ").title()}</div>{display}</div>'
            (col1 if i % 2 == 0 else col2).markdown(card, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Generate Thumbnail Concepts →", key="s9_next"):
            st.session_state.yt_state = 10
            st.rerun()
        return

    st.markdown("**Upload 2–3 thumbnail images from this channel.**")
    files = st.file_uploader(
        "Upload thumbnails",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="s9_uploads",
        label_visibility="collapsed",
    )
    if files:
        st.caption(f"{len(files)} file(s) selected.")

    if st.button("Analyze Thumbnails →", key="s9_analyze"):
        if not files:
            st.warning("Please upload at least one thumbnail.")
            return
        with st.spinner("Analyzing thumbnail design language..."):
            b64s, mimes = _files_to_b64(files[:3])
            td = engine.analyze_thumbnails(b64s, mimes)
            st.session_state.thumbnail_dna = td
        st.rerun()


def _state_10(engine):
    if not st.session_state.thumbnail_concepts:
        with st.spinner("Generating 5 thumbnail concepts..."):
            concepts = engine.generate_thumbnail_concepts(
                st.session_state.thumbnail_dna,
                st.session_state.topic,
                st.session_state.script,
            )
            st.session_state.thumbnail_concepts = concepts
        st.rerun()

    st.markdown("**5 Thumbnail Concepts**")
    st.markdown("---")
    for concept in st.session_state.thumbnail_concepts:
        cn = concept.get("concept_number", "?")
        with st.expander(f"Concept {cn} — {concept.get('text_overlay', '')[:60]}", expanded=cn == 1):
            st.markdown(
                f'<div class="thumb-card">'
                f'<span class="thumb-number">Concept {cn}</span><br><br>'
                f'<b>Visual Concept:</b> {concept.get("visual_concept", "")}<br><br>'
                f'<b>Text Overlay:</b> {concept.get("text_overlay", "")}<br><br>'
                f'<b>Emotion Trigger:</b> {concept.get("emotion_trigger", "")}'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="beat-number" style="color:#FF0000;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin:0.4rem 0 0.2rem;">Generation Prompt — copy ↓</div>', unsafe_allow_html=True)
            st.code(concept.get("generation_prompt", ""), language=None)

    st.markdown("")
    if st.button("Continue to Export →", key="s10_next"):
        st.session_state.yt_state = 11
        st.rerun()


def _state_11(engine):
    st.markdown("**Would you like everything exported as a structured Word document?**")
    col1, col2 = st.columns(2)

    if col1.button("Yes — Generate .docx", key="s11_yes"):
        session_data = {
            "channel_url": st.session_state.channel_url,
            "topic": st.session_state.topic,
            "style_dna": st.session_state.style_dna,
            "script": st.session_state.script,
            "word_count": st.session_state.word_count,
            "target_word_count": st.session_state.target_word_count,
            "visual_profile": st.session_state.visual_profile,
            "image_prompts": st.session_state.image_prompts,
            "thumbnail_dna": st.session_state.thumbnail_dna,
            "thumbnail_concepts": st.session_state.thumbnail_concepts,
        }
        with st.spinner("Compiling Word document..."):
            docx_bytes = engine.export_to_docx(session_data)

        topic_slug = st.session_state.topic[:40].replace(" ", "_").replace("/", "-")
        filename = f"youtube_clone_{topic_slug}.docx"
        st.download_button(
            "Download Word Document",
            data=docx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="s11_download",
        )

    if col2.button("No — Session Complete", key="s11_no"):
        st.success("Session complete. All content has been generated.")

    st.markdown("---")
    if st.button("Start New Session", key="s11_restart"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    _init()
    engine = _get_engine()
    _render_header()

    state = st.session_state.yt_state
    dispatch = {
        1: lambda: _state_1(),
        2: lambda: _state_2(),
        3: lambda: _state_3(engine),
        4: lambda: _state_4(engine),
        5: lambda: _state_5(),
        6: lambda: _state_6(engine),
        7: lambda: _state_7(engine),
        8: lambda: _state_8(engine),
        9: lambda: _state_9(engine),
        10: lambda: _state_10(engine),
        11: lambda: _state_11(engine),
    }
    dispatch.get(state, lambda: st.error(f"Unknown state: {state}"))()


if __name__ == "__main__":
    main()
