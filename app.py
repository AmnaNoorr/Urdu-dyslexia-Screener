"""
NastaliqScan â€” AI Dyslexia Screener for Urdu & English
Premium UI integration (backend logic unchanged)
"""

import json
import os
import re
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(
    page_title="NastaliqScan â€” AI Dyslexia Screener",
    page_icon="ðŸ”¬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url(''https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;600;700&family=Manrope:wght@400;500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,500;8..60,700&display=swap'');

:root{
  --bg:#FAF8F3;
  --surface:#FFFFFF;
  --surface-soft:#F7F5F0;
  --border:#E8E4DC;

  --navy-900:#0B1220;

  --amber-500:#D97706;
  --amber-400:#F59E0B;
  --amber-100:#FEF3C7;

  --text-primary:#1E1B16;
  --text-secondary:#5f5a55;
  --text-muted:#9a948d;

  --ok:#059669;
  --bad:#dc2626;

  --font-ui:''Manrope'',system-ui,sans-serif;
  --font-display:''Source Serif 4'',Georgia,serif;
  --font-urdu:''Noto Nastaliq Urdu'',serif;
}

/* ===================== GLOBAL FIX (IMPORTANT) ===================== */
html, body, .stApp {
  background: var(--bg) !important;
  color: var(--text-primary) !important;
}

* { box-sizing: border-box; }

#MainMenu, footer, header { visibility: hidden; }

/* FORCE STREAMLIT TEXT VISIBILITY */
.stMarkdown, .stText, p, span, div {
  color: var(--text-primary);
}

/* ===================== HERO ===================== */
.ns-hero{
  background:var(--navy-900);
  border-radius:22px;
  padding:2rem 1.3rem;
  box-shadow:0 6px 18px rgba(0,0,0,.2);
}

.ns-title{
  font-family:var(--font-display);
  font-size:2.4rem;
  color:#fff;
}

.ns-title em{ color:var(--amber-400); }

.ns-urdu{
  font-family:var(--font-urdu);
  direction:rtl;
  text-align:center;
  color:rgba(255,255,255,.8);
}

/* ===================== MODE CARDS (FIXED) ===================== */
.ns-mode-card{
  border:1px solid var(--border);
  background:var(--surface);
  border-radius:14px;
  padding:1rem;
  color:var(--text-primary) !important;
}

.ns-mode-card *{
  color:var(--text-primary) !important;
}

.ns-mode-card.active{
  border-color:var(--amber-500);
  background:#fffaf0;
}

.ns-mode-title{
  font-weight:800;
  font-size:.95rem;
  color:var(--text-primary) !important;
}

.ns-mode-desc{
  font-size:.82rem;
  color:var(--text-secondary) !important;
}

/* ===================== PANELS ===================== */
.ns-panel{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:16px;
}

.ns-panel-body, .ns-panel-head, .ns-panel-foot {
  color: var(--text-primary);
}

/* ===================== TEXT AREA ===================== */
.stTextArea textarea{
  background:white !important;
  color:var(--text-primary) !important;
  border:1px solid var(--border) !important;
}

/* ===================== FIX PATTERNS VISIBILITY ===================== */
.ns-row{
  display:flex;
  gap:10px;
  padding:.7rem 0;
  border-bottom:1px solid #eee;
  color:var(--text-primary) !important;
}

.ns-row div{
  color:var(--text-primary) !important;
}

.ns-idx{
  width:22px;
  height:22px;
  border-radius:6px;
  background:#eee;
  font-weight:700;
}

/* ===================== INSIGHT FIX ===================== */
.ns-insight{
  font-size:1rem;
  line-height:1.7;
  color:var(--text-primary) !important;
}

/* ===================== URDU ===================== */
.urdu-block{
  font-family:var(--font-urdu);
  direction:rtl;
  text-align:right;
  color:var(--text-primary) !important;
  line-height:2;
}

/* ===================== CTA ===================== */
.ns-cta .stButton > button{
  width:100%;
  background:var(--amber-500) !important;
  color:white !important;
  border-radius:12px;
  font-weight:700;
}

/* ===================== SMALL FIXES ===================== */
.ns-count{
  color:var(--text-muted);
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

SAMPLE_IMAGE_FILES = {
    "Urdu Sample 1 (urdu1.jfif)": Path("samples/urdu1.jfif"),
    "Urdu Sample 2 (urdu2.jpg)": Path("samples/urdu2.jpg"),
    "English Sample (english1.jfif)": Path("samples/english1.jfif"),
}

SYSTEM_PROMPT_TEMPLATE = """You are an expert linguist specialising in Urdu dyslexia screening.

Analyse the writing sample below and respond with STRICT JSON ONLY â€” no preamble, no markdown fences.

Writing sample:
\"\"\"{user_input}\"\"\"

Rules:
1. Identify up to 3 patterns MAXIMUM, ranked by severity (most impactful first).
2. Write ONE main diagnostic insight (2 sentences max) that a teacher can act on immediately. Be decisive.
3. Give exactly 3 concrete, numbered recommendations.
4. For Urdu text: list up to 3 specific error words with their corrections.
   For English text: same approach, or return an empty corrections list.
5. Pick a clear risk level â€” do not hedge.

Return exactly this JSON shape and nothing else:
{{
  "risk_level": "LOW | MODERATE | HIGH",
  "confidence": "LOW | MEDIUM | HIGH",
  "main_insight": "One decisive 2-sentence diagnostic finding a teacher can act on.",
  "detected_patterns": ["most severe pattern", "second pattern", "third pattern"],
  "corrections": [
    {{"error": "Ù¾Ø³Ù†", "correct": "Ù¾Ø³Ù†Ø¯", "note": "missing â€ŒØ¯"}},
    {{"error": "Ø³Ø§Øª", "correct": "Ø³Ø§ØªÚ¾", "note": "missing Ú¾"}}
  ],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}
"""

VISION_PROMPT_TEMPLATE = """You are an expert in Urdu handwriting analysis and dyslexia screening.

Analyse the uploaded handwriting image and respond with STRICT JSON ONLY â€” no preamble, no markdown fences.

Rules:
1. Identify up to 3 handwriting patterns MAXIMUM, ranked by severity.
2. Write ONE main diagnostic insight (2 sentences max) a teacher can act on immediately. Be decisive.
3. Give exactly 3 concrete recommendations.
4. Set corrections to an empty list (image mode).
5. Pick a clear risk level.

Return exactly this JSON shape and nothing else:
{{
  "risk_level": "LOW | MODERATE | HIGH",
  "confidence": "LOW | MEDIUM | HIGH",
  "main_insight": "One decisive 2-sentence diagnostic finding.",
  "detected_patterns": ["most severe", "second", "third"],
  "corrections": [],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}
"""

FALLBACK_RESULT = {
    "risk_level": "MODERATE",
    "confidence": "LOW",
    "main_insight": "Analysis temporarily unavailable due to API limits. Showing fallback screening result.",
    "detected_patterns": [],
    "corrections": [],
    "suggestions": [
        "Try again after a few minutes",
        "Reduce number of repeated submissions",
        "Upgrade API plan for continuous usage",
    ],
}

SESSION_CALL_COOLDOWN_SECONDS = 8
SESSION_DAILY_SOFT_LIMIT = 20
DEV_MODE = False

MOCK_RESULT = {
    "risk_level": "MODERATE",
    "confidence": "MEDIUM",
    "main_insight": "Mock mode is enabled. This is a simulated screening result for development/testing.",
    "detected_patterns": [
        "Inconsistent spelling patterns",
        "Letter formation variability",
        "Word spacing irregularity",
    ],
    "corrections": [
        {"error": "Ù¾Ø³Ù†", "correct": "Ù¾Ø³Ù†Ø¯", "note": "missing Ø¯"},
        {"error": "Ø³Ø§Øª", "correct": "Ø³Ø§ØªÚ¾", "note": "missing Ú¾"},
    ],
    "suggestions": [
        "Use guided reading practice daily",
        "Practice structured handwriting drills",
        "Consult a specialist for formal assessment",
    ],
}


def extract_json_safely(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty response from model")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e > s:
            return json.loads(text[s:e + 1])
        raise


def normalize_result(data: Dict[str, Any]) -> Dict[str, Any]:
    risk = str(data.get("risk_level", "")).upper().strip()
    if risk not in {"LOW", "MODERATE", "HIGH"}:
        risk = "MODERATE"
    confidence = str(data.get("confidence", "")).upper().strip()
    if confidence not in {"LOW", "MEDIUM", "HIGH"}:
        confidence = "MEDIUM"
    patterns = data.get("detected_patterns", [])
    if not isinstance(patterns, list):
        patterns = []
    patterns = [str(p).strip() for p in patterns if str(p).strip()][:3]
    main_insight = str(data.get("main_insight", data.get("explanation", ""))).strip()
    suggestions = data.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()][:3]
    raw_corr = data.get("corrections", [])
    corrections: List[Dict[str, str]] = []
    if isinstance(raw_corr, list):
        for c in raw_corr:
            if isinstance(c, dict) and c.get("error") and c.get("correct"):
                corrections.append({
                    "error": str(c["error"]).strip(),
                    "correct": str(c["correct"]).strip(),
                    "note": str(c.get("note", "")).strip(),
                })
    return {
        "risk_level": risk,
        "confidence": confidence,
        "main_insight": main_insight,
        "detected_patterns": patterns,
        "corrections": corrections,
        "suggestions": suggestions,
    }


def call_gemini(user_input: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")
    client = genai.Client(api_key=api_key)
    prompt = SYSTEM_PROMPT_TEMPLATE.replace("{user_input}", user_input)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.25, response_mime_type="application/json"),
    )
    return normalize_result(extract_json_safely(response.text))


def call_gemini_vision(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_text(text=VISION_PROMPT_TEMPLATE),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(temperature=0.25, response_mime_type="application/json"),
    )
    return normalize_result(extract_json_safely(response.text))


@st.cache_data(show_spinner=False)
def _cached_text_analysis(text_input: str) -> Dict[str, Any]:
    return call_gemini(text_input)


@st.cache_data(show_spinner=False)
def _cached_image_analysis(image_hash: str, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    # image_hash keeps cache key stable/explicit; bytes are used for actual call.
    _ = image_hash
    return call_gemini_vision(image_bytes, mime_type)


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).upper()
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "QUOTA" in msg


def _can_call_api(now_ts: float) -> bool:
    last_ts = float(st.session_state.get("last_api_call_ts", 0.0))
    count = int(st.session_state.get("api_call_count", 0))
    if now_ts - last_ts < SESSION_CALL_COOLDOWN_SECONDS:
        return False
    if count >= SESSION_DAILY_SOFT_LIMIT:
        return False
    return True


def _mark_api_call(now_ts: float) -> None:
    st.session_state["last_api_call_ts"] = now_ts
    st.session_state["api_call_count"] = int(st.session_state.get("api_call_count", 0)) + 1


def run_analysis_with_safety(
    *,
    mode: str,
    text_input: str = "",
    image_bytes: bytes = b"",
    mime_type: str = "",
) -> Dict[str, Any]:
    if DEV_MODE:
        return MOCK_RESULT.copy()

    now_ts = time.time()

    if mode == "text":
        input_hash = hashlib.sha256(text_input.encode("utf-8")).hexdigest()
    else:
        input_hash = hashlib.sha256(image_bytes).hexdigest()

    if st.session_state.get("last_input_hash") == input_hash and st.session_state.get("analysis_result"):
        return st.session_state["analysis_result"]

    if not _can_call_api(now_ts):
        return FALLBACK_RESULT.copy()

    try:
        if mode == "text":
            result = _cached_text_analysis(text_input)
        else:
            result = _cached_image_analysis(input_hash, image_bytes, mime_type)
        _mark_api_call(now_ts)
        st.session_state["last_input_hash"] = input_hash
        return result
    except Exception as exc:
        if _is_quota_error(exc):
            return FALLBACK_RESULT.copy()
        raise


def contains_urdu(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def detect_image_mime(uploaded_file) -> str:
    detected = (getattr(uploaded_file, "type", "") or "").lower().strip()
    if detected in {"image/jpeg", "image/png"}:
        return detected
    name = (getattr(uploaded_file, "name", "") or "").lower()
    if name.endswith((".jpg", ".jpeg", ".jfif")):
        return "image/jpeg"
    if name.endswith(".png"):
        return "image/png"
    return ""


def hl_text(original: str, corrections: List[Dict[str, str]]) -> str:
    highlighted = original
    for c in corrections:
        err = re.escape(c["error"])
        tip = f"âœ“ {c['correct']}" + (f" â€” {c['note']}" if c.get("note") else "")
        span = (
            f"<span class='ns-hl'>{c['error']}"
            f"<span class='ns-tt'>{tip}</span></span>"
        )
        highlighted = re.sub(err, span, highlighted, count=1)
    return highlighted


def corr_rows(corrections: List[Dict[str, str]]) -> str:
    if not corrections:
        return ""
    rows = "<div class='ns-corr-list'>"
    for c in corrections:
        rows += (
            f"<div class='ns-corr-pair'>"
            f"<span class='ns-corr-wrong'>{c['error']}</span>"
            f"<span class='ns-corr-arrow'>â†’</span>"
            f"<span class='ns-corr-right'>{c['correct']}</span>"
            f"</div>"
        )
    rows += "</div>"
    return rows


def render_results(result: Dict[str, Any], original_text: str, urdu_mode: bool) -> None:
    risk = result["risk_level"]
    confidence = result.get("confidence", "MEDIUM")
    insight = result.get("main_insight") or "No diagnostic insight returned."
    patterns = result.get("detected_patterns", [])
    corrections = result.get("corrections", [])
    suggestions = result.get("suggestions", [])

    risk_labels = {
        "LOW": ("Screening Summary", "Low Risk", "No major dyslexia indicators detected."),
        "MODERATE": ("Screening Summary", "Moderate Risk", "Some repeated patterns need closer support."),
        "HIGH": ("Screening Summary", "High Risk", "Multiple strong indicators were observed."),
    }
    eyebrow, headline, sublabel = risk_labels.get(risk, risk_labels["MODERATE"])

    st.markdown(
        f"""
<div class='ns-step'>
  <div class='ns-risk {risk}'>
    <div>
      <div class='ns-risk-kicker {risk}'>{eyebrow}</div>
      <div class='ns-risk-title'>{headline}</div>
      <div class='ns-risk-sub'>{sublabel}</div>
    </div>
    <div class='ns-metric'>
      <div class='ns-meter'><div class='ns-fill {risk}'></div></div>
      <div class='ns-conf {confidence}'>{confidence.title()} Confidence</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    insight_cls = "ns-insight urdu" if urdu_mode else "ns-insight"
    st.markdown(
        f"""
<div class='ns-step'>
  <div class='ns-card'>
    <div class='ns-card-head'>Step 2 Â· AI Insight</div>
    <div class='ns-card-body'>
      <div class='{insight_cls}'>{insight}</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class='ns-step'>
  <div class='ns-card'>
    <div class='ns-card-head'>Step 3 Â· Patterns ({len(patterns)}/3)</div>
    <div class='ns-card-body'>
""",
        unsafe_allow_html=True,
    )

    if urdu_mode and original_text and corrections:
        st.markdown(
            f"""
<div class='ns-highlight'>
  <div class='ns-highlight-lbl'>Inline Error Highlights</div>
  <div class='ns-text-display'>{hl_text(original_text, corrections)}</div>
  {corr_rows(corrections)}
</div>
""",
            unsafe_allow_html=True,
        )

    if patterns:
        for i, p in enumerate(patterns, 1):
            pcls = "urdu-block" if urdu_mode else ""
            st.markdown(
                f"<div class='ns-row'><div class='ns-idx'>{i}</div><div class='{pcls}'>{p}</div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div class='ns-row'><div class='ns-idx'>â€”</div><div>No strong repetitive patterns detected.</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div></div></div>", unsafe_allow_html=True)

    st.markdown(
        """
<div class='ns-step'>
  <div class='ns-suggest'>
    <div class='ns-card-head' style='border-bottom:1px solid #f4e7d3;'>Step 4 Â· Suggestions</div>
""",
        unsafe_allow_html=True,
    )

    if suggestions:
        for i, s in enumerate(suggestions, 1):
            tcls = "ns-sug-text urdu" if urdu_mode else "ns-sug-text"
            st.markdown(
                f"<div class='ns-sug-row'><div class='ns-sug-num'>{i}</div><div class='{tcls}'>{s}</div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div class='ns-sug-row'><div class='ns-sug-num'>1</div><div class='ns-sug-text'>Schedule guided reading practice with a specialist.</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='ns-footer'>"
        "Screening support only Â· Not a clinical diagnosis Â· Consult a qualified educational psychologist for formal evaluation<br>"
        "<strong>NastaliqScan</strong> Â· AI Seekho Project"
        "</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.markdown("<div class='ns-shell'>", unsafe_allow_html=True)

    st.markdown(
        """
<div class='ns-hero'>
  <div class='ns-eyebrow'>ðŸ”¬ AI Seekho Â· Early Screening</div>
  <div class='ns-title'>Nastaliq<em>Scan</em></div>
  <div class='ns-urdu'>Ø§Ø±Ø¯Ùˆ Ø§ÙˆØ± Ø§Ù†Ú¯Ù„Ø´ ØªØ­Ø±ÛŒØ± Ú©Ø§ Ø°ÛÛŒÙ† ØªØ¬Ø²ÛŒÛ</div>
  <p class='ns-sub'>
    A focused AI screener for early dyslexia indicators in Urdu and English writing,
    designed for fast classroom and parent support workflows.
  </p>
  <div class='ns-pills'>
    <span class='ns-pill'>Text + Handwriting</span>
    <span class='ns-pill'>Gemini Powered</span>
    <span class='ns-pill'>RTL Optimized</span>
    <span class='ns-pill'>Structured AI Report</span>
  </div>
</div>
<div class='ns-disclaimer'>
  âš  <strong>Not a medical diagnosis tool.</strong> Results are for early screening support only.
</div>
""",
        unsafe_allow_html=True,
    )

    defaults = {
        "user_input": "",
        "show_image_sample_hint": False,
        "selected_sample_label": list(SAMPLE_IMAGE_FILES.keys())[0],
        "analysis_result": None,
        "analysis_original": "",
        "analysis_urdu": False,
        "active_mode": "text",
        "last_input_hash": "",
        "last_api_call_ts": 0.0,
        "api_call_count": 0,
        "last_run": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown("<div class='ns-label'>Choose Analysis Mode</div>", unsafe_allow_html=True)

    mode = st.radio(
        "Mode",
        ["âœï¸ Text Analysis", "ðŸ“· Handwriting Scan"],
        horizontal=True,
        label_visibility="collapsed",
        key="mode_radio",
    )
    is_text = mode.startswith("âœï¸")

    text_active = "active" if is_text else ""
    image_active = "active" if not is_text else ""
    st.markdown(
        f"""
<div class='ns-mode-grid'>
  <div class='ns-mode-card {text_active}'>
    <div class='ns-mode-title'>âœï¸ Text Analysis</div>
    <div class='ns-mode-desc'>Paste Urdu/English writing for language-level pattern analysis.</div>
  </div>
  <div class='ns-mode-card {image_active}'>
    <div class='ns-mode-title'>ðŸ“· Handwriting Scan</div>
    <div class='ns-mode-desc'>Upload handwriting to evaluate visual consistency signals.</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    uploaded_file = None
    image_bytes = b""
    mime_type = ""

    if is_text:
        current_text = st.session_state.get("user_input", "")
        char_count = len(current_text)
        wc_active = "active" if char_count >= 25 else ""
        is_urdu = contains_urdu(current_text)
        urdu_badge = "<span class='ns-urdu-badge'>Urdu detected</span>" if is_urdu else ""

        st.markdown(
            """
<div class='ns-panel'>
  <div class='ns-panel-head'>
    <div class='ns-panel-title'><span class='ns-dot'></span>Writing Sample</div>
    <div class='ns-panel-meta'>Minimum 25 characters</div>
  </div>
  <div class='ns-panel-body'>
""",
            unsafe_allow_html=True,
        )

        col_s, _ = st.columns([1, 5])
        with col_s:
            st.markdown("<div class='ns-ghost'>", unsafe_allow_html=True)
            if st.button("Try sample", key="sample_btn"):
                st.session_state.user_input = "Ù…Ø¬ Ø§Ø³Ú©ÙˆÙ„ Ø¬Ø§Ù†Ø§ Ù¾Ø³Ù† ÛÛ’Û” Ù…ÛŒÚº Ø±ÙˆØ² Ø¯ÙˆØ³ØªÙˆÚº Ú©Û’ Ø³Ø§Øª Ú©Ù„ØªØ§ ÛÙˆÚº"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        user_input = st.text_area(
            "Writing sample input",
            height=160,
            placeholder="Urdu: Ù…Ø¬Ú¾Û’ Ø§Ø³Ú©ÙˆÙ„ Ø¬Ø§Ù†Ø§ Ù¾Ø³Ù†Ø¯ ÛÛ’...\n\nEnglish: I like to go to school every day...",
            key="user_input",
            label_visibility="collapsed",
        )

        st.markdown(
            f"""
  </div>
  <div class='ns-panel-foot'>
    <div class='ns-count {wc_active}'>{char_count} chars</div>
    {urdu_badge}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            """
<div class='ns-panel'>
  <div class='ns-panel-head'>
    <div class='ns-panel-title'><span class='ns-dot'></span>Handwriting Image</div>
    <div class='ns-panel-meta'>JPG Â· JPEG Â· JFIF Â· PNG</div>
  </div>
  <div class='ns-panel-body'>
""",
            unsafe_allow_html=True,
        )

        st.session_state.selected_sample_label = st.selectbox(
            "Built-in sample:",
            list(SAMPLE_IMAGE_FILES.keys()),
            index=list(SAMPLE_IMAGE_FILES.keys()).index(st.session_state.selected_sample_label),
        )

        col_t, _ = st.columns([1, 5])
        with col_t:
            st.markdown("<div class='ns-ghost'>", unsafe_allow_html=True)
            if st.button("Load sample", key="load_sample_btn"):
                st.session_state.show_image_sample_hint = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.show_image_sample_hint:
            sp = SAMPLE_IMAGE_FILES.get(st.session_state.selected_sample_label)
            if sp and sp.exists():
                st.image(str(sp), caption=sp.name, width="stretch")
            else:
                st.info("Sample unavailable â€” upload an image below.")

        uploaded_file = st.file_uploader(
            "Upload handwriting",
            type=["jpg", "jpeg", "png", "jfif"],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded sample", width="stretch")

        st.markdown("</div></div>", unsafe_allow_html=True)
        user_input = ""

    st.markdown("<div class='ns-cta'>", unsafe_allow_html=True)
    run = st.button("Analyze Writing Sample", key="analyze_btn")
    st.markdown("</div>", unsafe_allow_html=True)

    if run:
        st.session_state.analysis_result = None

        if is_text:
            cleaned = (st.session_state.get("user_input") or "").strip()
            if st.session_state.last_run == cleaned:
                st.stop()
            st.session_state.last_run = cleaned
            if not cleaned:
                st.warning("Please enter some text before running the analysis.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            if len(cleaned) < 25:
                st.warning("Please enter at least 25 characters for a reliable result.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            with st.spinner("Analysing writing patternsâ€¦"):
                try:
                    result = run_analysis_with_safety(mode="text", text_input=cleaned)
                    st.session_state.analysis_result = result
                    st.session_state.analysis_original = cleaned
                    st.session_state.analysis_urdu = contains_urdu(cleaned)
                except RuntimeError as e:
                    st.error(str(e))
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                except (json.JSONDecodeError, ValueError):
                    st.error("Could not parse a result â€” try a longer or clearer sample.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                except Exception as e:
                    st.error(f"Analysis temporarily unavailable. Please try again. ({e})")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
        else:
            if uploaded_file is not None:
                mime_type = detect_image_mime(uploaded_file)
                if mime_type not in {"image/jpeg", "image/png"}:
                    st.warning("Unsupported format. Upload a JPG, JPEG, JFIF, or PNG.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                image_bytes = uploaded_file.read()
            elif st.session_state.show_image_sample_hint:
                sp = SAMPLE_IMAGE_FILES.get(st.session_state.selected_sample_label)
                if sp and sp.exists():
                    image_bytes = sp.read_bytes()
                    mime_type = "image/png" if sp.suffix.lower() == ".png" else "image/jpeg"
                else:
                    st.warning("Sample could not be loaded. Please upload an image.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
            else:
                st.warning("Please upload an image or load a sample first.")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            if not image_bytes:
                st.warning("The image appears empty. Try another file.")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            image_run_key = hashlib.sha256(image_bytes).hexdigest()
            if st.session_state.last_run == image_run_key:
                st.stop()
            st.session_state.last_run = image_run_key

            with st.spinner("Analysing handwritingâ€¦"):
                try:
                    result = run_analysis_with_safety(
                        mode="image",
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                    )
                    st.session_state.analysis_result = result
                    st.session_state.analysis_original = ""
                    st.session_state.analysis_urdu = False
                except RuntimeError as e:
                    st.error(str(e))
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                except (json.JSONDecodeError, ValueError):
                    st.error("Could not parse a result â€” try a clearer image.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                except Exception as e:
                    st.error(f"Analysis temporarily unavailable. Please try again. ({e})")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

    if st.session_state.analysis_result:
        st.markdown("<div class='ns-report-label'>Analysis Report</div>", unsafe_allow_html=True)
        render_results(
            st.session_state.analysis_result,
            original_text=st.session_state.analysis_original,
            urdu_mode=st.session_state.analysis_urdu,
        )

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
