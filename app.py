"""
NastaliqScan — AI Dyslexia Screener for Urdu & English
Premium UI integration (backend logic unchanged)
"""

import json
import os
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

load_dotenv()

st.set_page_config(
    page_title="NastaliqScan — AI Dyslexia Screener",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;600;700&family=Manrope:wght@400;500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,500;8..60,700&display=swap');

:root{
  --bg:#FAF8F3;
  --surface:#FFFFFF;
  --surface-soft:#F7F5F0;
  --border:#E8E4DC;
  --border-strong:#C9C4BB;

  --navy-900:#0B1220;
  --navy-800:#0F172A;
  --navy-700:#1E2A3B;

  --green-600:#059669;
  --green-100:#ECFDF5;
  --yellow-600:#D97706;
  --yellow-100:#FFFBEB;
  --red-600:#DC2626;
  --red-100:#FEF2F2;

  --amber-500:#D97706;
  --amber-400:#F59E0B;
  --amber-100:#FEF3C7;
  --amber-200:#FDE68A;
  --blue-100:#DBEAFE;
  --blue-700:#1D4ED8;
  --gold-600:#B45309;

  --text-primary:#1E1B16;
  --text-secondary:#6B6560;
  --text-muted:#B8B3AC;
  --text-inverse:#FFFFFF;

  --radius-sm:10px;
  --radius-md:14px;
  --radius-lg:22px;

  --shadow-sm:0 1px 4px rgba(0,0,0,0.06);
  --shadow-md:0 6px 18px rgba(0,0,0,0.08);
  --shadow-lg:0 18px 50px rgba(0,0,0,0.12);

  --font-ui:'Manrope',system-ui,sans-serif;
  --font-display:'Source Serif 4',Georgia,serif;
  --font-urdu:'Noto Nastaliq Urdu',serif;
  --ok:#059669;
  --bad:#dc2626;
  --text-soft:#475569;
}

*{box-sizing:border-box;}
html,body{
  font-family:var(--font-ui);
  background:var(--bg);
  color:var(--text-primary);
}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0 !important; max-width:100% !important;}

.ns-shell{max-width:760px;margin:0 auto;padding:2.5rem 1.1rem 4rem;}
.ns-hero{
  background:var(--navy-900);
  border-radius:22px;
  border:1px solid rgba(255,255,255,.08);
  padding:2rem 1.3rem 1.6rem;
  box-shadow:var(--shadow-md);
}
.ns-eyebrow{
  display:inline-flex;align-items:center;gap:6px;
  font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:#c7d2fe;background:rgba(199,210,254,.08);border:1px solid rgba(199,210,254,.33);
  border-radius:999px;padding:4px 10px;margin-bottom:.9rem;
}
.ns-title{
  font-family:var(--font-display);font-size:clamp(2rem,4.6vw,3rem);line-height:1.04;
  color:var(--text-inverse);letter-spacing:-.02em;
}
.ns-title em{color:var(--amber-400);font-style:italic;}
.ns-urdu{
  font-family:var(--font-urdu);direction:rtl;text-align:center;
  color:rgba(255,255,255,.75);margin-top:.45rem;font-size:1.02rem;
}
.ns-sub{
  margin-top:.85rem;color:rgba(255,255,255,.83);line-height:1.62;font-size:.93rem;
}
.ns-pills{margin-top:.9rem;display:flex;flex-wrap:wrap;gap:7px;}
.ns-pill{
  font-size:.72rem;
  color:#E2E8F0;
  border:1px solid rgba(148,163,184,.45);
  background:rgba(15,23,42,.35);
  border-radius:999px;
  padding:4px 10px;
  font-weight:600;
}
.ns-disclaimer{
  margin-top:.9rem;border:1px solid var(--amber-400);background:var(--amber-100);
  color:var(--gold-600);border-radius:var(--radius-sm);padding:.68rem .9rem;
  font-size:.8rem;line-height:1.5;
}

.ns-label{
  margin-top:1.35rem;margin-bottom:.55rem;
  font-size:.7rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--text-muted);
}
.ns-mode-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:.9rem;}
.ns-mode-card{
  border:1px solid var(--border);background:var(--surface);border-radius:var(--radius-md);
  padding:.9rem .95rem;box-shadow:var(--shadow-sm);
  color: var(--text-primary) !important;
}
.ns-mode-card.active{
  border-color: var(--amber-500);
  background: #fffdf7;
  box-shadow: var(--shadow-md);
}
.ns-mode-card:hover {
  transform: translateY(-2px);
  border-color: #93c5fd;
  transition: all .2s ease;
}
.ns-mode-card .t {
  font-weight: 800;
  font-size: .92rem;
  color: var(--navy-900) !important;
}
.ns-mode-card .d {
  margin-top: .25rem;
  font-size: .8rem;
  color: var(--text-secondary) !important;
  line-height: 1.45;
}
.ns-mode-title{font-size:.89rem;font-weight:700;color:var(--text-primary);}
.ns-mode-desc{margin-top:.2rem;font-size:.77rem;color:var(--text-secondary);line-height:1.45;}

div[data-testid="stRadio"] > label{display:none !important;}
div[data-testid="stRadio"] > div{
  display:flex !important; gap:8px !important; margin-bottom:10px !important;
}
div[data-testid="stRadio"] > div > label{
  background:var(--surface) !important;border:1px solid var(--border) !important;border-radius:10px !important;
  padding:8px 10px !important; flex:1 !important; text-align:center !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked){
  border-color:var(--amber-500) !important; background:#fff8ef !important;
}
div[data-testid="stRadio"] > div > label p{font-size:.8rem !important; font-weight:600 !important; color:var(--navy-900) !important;}

.ns-panel{
  border:1px solid var(--border);border-radius:var(--radius-lg);
  background:var(--surface);box-shadow:var(--shadow-sm);overflow:hidden;
}
.ns-panel-head{
  padding:.85rem 1rem;border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;gap:8px;align-items:center;
}
.ns-panel-title{font-size:.9rem;font-weight:700;color:var(--text-primary);display:inline-flex;align-items:center;gap:7px;}
.ns-dot{width:8px;height:8px;border-radius:999px;background:var(--amber-500);}
.ns-panel-meta{font-size:.73rem;color:var(--text-muted);}
.ns-panel-body{padding:.95rem 1rem;}
.ns-panel-foot{
  padding:.65rem 1rem .95rem;display:flex;justify-content:space-between;align-items:center;gap:8px;
}
.ns-count{font-size:.74rem;color:var(--text-muted);}
.ns-count.active{color:var(--amber-500);font-weight:700;}
.ns-urdu-badge{
  font-size:.7rem;
  font-weight:700;
  color:var(--blue-700);
  background:var(--blue-100);
  border:1px solid #BFDBFE;
  border-radius:999px;
  padding:3px 8px;
}

.stTextArea textarea{
  font-family:var(--font-ui) !important;background:var(--surface) !important;color:var(--text-primary) !important;
  border:1px solid var(--border) !important;border-radius:10px !important;padding:14px !important;line-height:1.65 !important;
}
.stTextArea textarea:focus{
  border-color:var(--amber-500) !important;box-shadow:0 0 0 3px rgba(217,119,6,.14) !important;
}
.stTextArea textarea::placeholder{color:var(--text-muted) !important;}

[data-testid="stSelectbox"] > div > div{
  border:1px solid var(--border) !important;border-radius:10px !important;background:var(--surface) !important;
}
[data-testid="stFileUploader"]{
  border:1px dashed var(--border-strong) !important;border-radius:12px !important;background:var(--surface-soft) !important;
}
[data-testid="stImage"] img{border-radius:12px !important;border:1px solid var(--border) !important;}

.ns-ghost .stButton > button{
  background:#fff !important;border:1px solid var(--border) !important;color:var(--text-secondary) !important;
  width:auto !important;padding:6px 12px !important;font-size:.76rem !important;font-weight:600 !important;
}
.ns-ghost .stButton > button:hover{
  border-color:var(--amber-500) !important;color:var(--amber-500) !important;
}

.ns-cta{margin-top:1rem;}
.ns-cta .stButton > button{
  width:100% !important;background:var(--amber-500) !important;color:#fff !important;border:none !important;
  border-radius:12px !important;padding:13px 16px !important;font-size:.93rem !important;font-weight:700 !important;
  box-shadow:var(--shadow-md) !important;
}
.ns-cta .stButton > button:hover{
  background:var(--amber-400) !important; transform:translateY(-1px) !important; box-shadow:var(--shadow-lg) !important;
}

.ns-report-label{
  margin-top:2.1rem;margin-bottom:.8rem;font-size:.7rem;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;color:var(--text-muted);
}
.ns-step{margin-bottom:1rem;}
.ns-risk{
  border-radius:16px;padding:1.2rem 1.2rem;border:1px solid;
  display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;
}
.ns-risk.LOW{background:var(--green-100);border-color:#86efac;}
.ns-risk.MODERATE{background:var(--yellow-100);border-color:#fde68a;}
.ns-risk.HIGH{background:var(--red-100);border-color:#fca5a5;}
.ns-risk-kicker{font-size:.67rem;font-weight:800;letter-spacing:.11em;text-transform:uppercase;}
.ns-risk-kicker.LOW{color:var(--green-600);}
.ns-risk-kicker.MODERATE{color:var(--yellow-600);}
.ns-risk-kicker.HIGH{color:var(--red-600);}
.ns-risk-title{
  font-family:var(--font-display);font-size:clamp(1.65rem,3.6vw,2.3rem);
  line-height:1.1;margin-top:.18rem;
}
.ns-risk-title.LOW { color: #059669; }
.ns-risk-title.MODERATE { color: #D97706; }
.ns-risk-title.HIGH { color: #DC2626; }
.ns-risk-sub{font-size:.82rem;color:var(--text-secondary);margin-top:.35rem;line-height:1.45;}

.ns-metric{min-width:125px;display:flex;flex-direction:column;align-items:flex-end;gap:6px;}
.ns-meter{width:125px;height:10px;border-radius:999px;background:rgba(15,23,42,.12);overflow:hidden;}
.ns-fill{height:100%;border-radius:999px;}
.ns-fill.LOW{width:24%;background:linear-gradient(90deg,#10b981,#059669);}
.ns-fill.MODERATE{width:58%;background:linear-gradient(90deg,#f59e0b,#d97706);}
.ns-fill.HIGH{width:92%;background:linear-gradient(90deg,#ef4444,#dc2626);}
.ns-conf{
  font-size:.66rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;
  padding:3px 9px;border-radius:999px;border:1px solid;
}
.ns-conf.LOW{background:#FEE2E2;border-color:#FCA5A5;color:#B91C1C;}
.ns-conf.MEDIUM{background:#FFFBEB;border-color:var(--amber-200);color:#92400E;}
.ns-conf.HIGH{background:#DCFCE7;border-color:#86EFAC;color:#166534;}

.ns-card{border:1px solid var(--border);border-radius:14px;background:var(--surface);box-shadow:var(--shadow-sm);}
.ns-card-head{
  padding:.78rem .95rem;border-bottom:1px solid var(--border);
  font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--text-muted);
}
.ns-card-body{padding:.95rem;}

.ns-insight {
  font-size: .96rem;
  color: #1f2937 !important;
  line-height: 1.75;
  font-weight: 450;
}
.ns-insight.urdu{
  font-family:var(--font-urdu);direction:rtl;text-align:right;line-height:2.1;color:var(--text-primary);font-size:1.05rem;
}

.ns-highlight{
  border:1px solid var(--border);border-radius:10px;background:var(--surface-soft);
  padding:.8rem .88rem;margin-bottom:.65rem;
}
.ns-highlight-lbl{
  font-size:.66rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--text-muted);margin-bottom:.5rem;
}
.ns-text-display{
  font-family:var(--font-urdu);direction:rtl;text-align:right;line-height:2.2;font-size:1.04rem;color:var(--text-primary);
}
.ns-hl{
  background:var(--amber-100);border-bottom:2px solid var(--amber-500);border-radius:3px;padding:0 3px;position:relative;
}
.ns-hl .ns-tt{
  display:none;position:absolute;left:50%;transform:translateX(-50%);bottom:calc(100% + 7px);
  background:var(--navy-800);color:#fff;font-size:.71rem;white-space:nowrap;border-radius:6px;padding:5px 9px;z-index:10;
  font-family:var(--font-ui);direction:ltr;
}
.ns-hl:hover .ns-tt{display:block;}

.ns-corr-list{margin-top:.58rem;display:flex;flex-direction:column;gap:4px;direction:rtl;}
.ns-corr-pair{display:flex;align-items:center;gap:8px;font-size:.82rem;}
.ns-corr-wrong {
  color: var(--bad);
  text-decoration: line-through;
  font-family: var(--font-urdu);
}
.ns-corr-arrow{color:var(--text-muted);font-size:.74rem;}
.ns-corr-right {
  color: var(--ok);
  font-weight: 800;
  font-family: var(--font-urdu);
}

.ns-row{
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: .9rem;
  color: var(--text-primary) !important;
  line-height: 1.6;
  padding: .68rem 0;
  border-bottom: 1px solid #f1f5f9;
}
.ns-row:last-child{border-bottom:none;}
.ns-row div:last-child {
  color: #ffffff !important;
}
.ns-idx{
  width:20px;
  height:20px;
  border-radius:6px;
  background:#0f172a;
  color:#ffffff;
  font-size:.68rem;
  font-weight:800;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  flex-shrink:0;
  margin-top:1px;
}
.urdu-block{font-family:var(--font-urdu);direction:rtl;text-align:right;line-height:2;font-size:.96rem;color:var(--text-primary);}

.ns-suggest{
  border:1px solid #edd8b8;background:#fff9ef;border-radius:14px;
}
.ns-sug-row{
  display:flex;align-items:flex-start;gap:10px;padding:.8rem .95rem;border-bottom:1px solid #f4e7d3;
}
.ns-sug-row:last-child{border-bottom:none;}
.ns-sug-num{
  width:20px;height:20px;border-radius:6px;background:#f9ddb2;color:#9a5809;font-size:.72rem;font-weight:800;
  display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;
}
.ns-sug-text{font-size:.88rem;line-height:1.58;color:#7a4b16;}
.ns-sug-text.urdu{font-family:var(--font-urdu);direction:rtl;text-align:right;line-height:2;font-size:.95rem;}

.ns-footer{
  margin-top:1.4rem;border-top:1px solid var(--border);padding-top:1rem;
  font-size:.74rem;color:var(--text-muted);line-height:1.7;text-align:center;
}

.ns-why {
  margin-top: 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .9rem 1rem;
}
.ns-why-title {
  font-size: .78rem;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: .45rem;
}
.ns-why ul { margin: 0; padding-left: 1rem; }
.ns-why li {
  color: var(--text-secondary);
  font-size: .86rem;
  line-height: 1.55;
  margin: .2rem 0;
}

.ns-quick-export {
  margin-top: .9rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .8rem .9rem;
}
.ns-quick-export-title {
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: .55rem;
}
.ns-results-divider {
  height: 1px;
  background: var(--border);
  margin: 1.1rem 0 .7rem 0;
}

@media (max-width:560px){
  .ns-shell{padding:1.8rem .8rem 3.2rem;}
  .ns-hero{padding:1.5rem 1rem 1.3rem;}
  .ns-mode-grid{grid-template-columns:1fr;}
  .ns-risk{flex-direction:column;}
  .ns-metric{align-items:flex-start;}
  .ns-quick-export { padding: .75rem .75rem; }
  .ns-why { padding: .8rem .8rem; }
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

Analyse the writing sample below and respond with STRICT JSON ONLY — no preamble, no markdown fences.

Writing sample:
\"\"\"{user_input}\"\"\"

Rules:
1. Identify up to 3 patterns MAXIMUM, ranked by severity (most impactful first).
2. Write ONE main diagnostic insight (2 sentences max) that a teacher can act on immediately. Be decisive.
3. Give exactly 3 concrete, numbered recommendations.
4. For Urdu text: list up to 3 specific error words with their corrections.
   For English text: same approach, or return an empty corrections list.
5. Pick a clear risk level — do not hedge.

Return exactly this JSON shape and nothing else:
{{
  "risk_level": "LOW | MODERATE | HIGH",
  "confidence": "LOW | MEDIUM | HIGH",
  "main_insight": "One decisive 2-sentence diagnostic finding a teacher can act on.",
  "detected_patterns": ["most severe pattern", "second pattern", "third pattern"],
  "corrections": [
    {{"error": "پسن", "correct": "پسند", "note": "missing د"}},
    {{"error": "سات", "correct": "ساتھ", "note": "missing ھ"}}
  ],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}
"""

VISION_PROMPT_TEMPLATE = """You are an expert in Urdu handwriting analysis and dyslexia screening.

Analyse the uploaded handwriting image and respond with STRICT JSON ONLY — no preamble, no markdown fences.

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
        {"error": "پسن", "correct": "پسند", "note": "missing د"},
        {"error": "سات", "correct": "ساتھ", "note": "missing ھ"},
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
        tip = f"✓ {c['correct']}" + (f" — {c['note']}" if c.get("note") else "")
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
            f"<span class='ns-corr-arrow'>→</span>"
            f"<span class='ns-corr-right'>{c['correct']}</span>"
            f"</div>"
        )
    rows += "</div>"
    return rows


def build_report_payload(result: Dict[str, Any], mode: str, original_text: str) -> Dict[str, Any]:
    return {
        "app": "NastaliqScan",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "risk_level": result.get("risk_level", "MODERATE"),
        "confidence": result.get("confidence", "MEDIUM"),
        "main_insight": result.get("main_insight", ""),
        "detected_patterns": result.get("detected_patterns", []),
        "corrections": result.get("corrections", []),
        "suggestions": result.get("suggestions", []),
        "input_excerpt": (original_text or "")[:300],
        "disclaimer": "Screening support only. Not a clinical diagnosis.",
    }


def build_shareable_summary(result: Dict[str, Any], mode: str) -> str:
    risk = result.get("risk_level", "MODERATE").title()
    confidence = result.get("confidence", "MEDIUM").title()
    insight = result.get("main_insight", "No insight available.")
    patterns = result.get("detected_patterns", [])
    top_patterns = ", ".join(patterns[:3]) if patterns else "No strong repetitive patterns detected"
    return (
        f"NastaliqScan Result ({mode})\n"
        f"Risk: {risk}\n"
        f"Confidence: {confidence}\n"
        f"Insight: {insight}\n"
        f"Patterns: {top_patterns}\n"
        f"Disclaimer: Screening support only, not a clinical diagnosis."
    )


def build_linkedin_summary(result: Dict[str, Any]) -> str:
    risk = result.get("risk_level", "MODERATE").title()
    confidence = result.get("confidence", "MEDIUM").title()
    insight = (result.get("main_insight") or "No insight available.").strip()
    patterns = result.get("detected_patterns", [])[:2]
    pattern_lines = "\n".join([f"- {p}" for p in patterns]) if patterns else "- No strong repetitive patterns detected"
    return (
        "NastaliqScan AI Screening Result\n"
        f"Risk Level: {risk}\n"
        f"Confidence: {confidence}\n\n"
        "Key Insight:\n"
        f"{insight}\n\n"
        "Detected Patterns:\n"
        f"{pattern_lines}\n\n"
        "Why this matters: Early detection of dyslexia in Urdu is almost non-existent.\n\n"
        "#AISeekho #BuildWithAI #EdTech #Pakistan"
    )


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_simple_pdf(report_lines: List[str]) -> bytes:
    import arabic_reshaper
    from bidi.algorithm import get_display

    buffer = BytesIO()
    # Register fonts
    pdfmetrics.registerFont(TTFont('Urdu', 'fonts/NotoNastaliqUrdu-Regular.ttf'))
    pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))  # fallback
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []
    
    # Configure reshaper for Urdu
    configuration = {
        'language': 'Urdu'
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)

    for line in report_lines:
        # Detect Urdu
        if any('\u0600' <= ch <= '\u06FF' for ch in line):
            reshaped_text = reshaper.reshape(line)
            bidi_text = get_display(reshaped_text)
            
            style = styles["Normal"].clone('urdu_style')
            style.fontName = 'Urdu'
            style.fontSize = 12
            style.leading = 16
            story.append(Paragraph(bidi_text, style))
        else:
            style = styles["Normal"]
            story.append(Paragraph(line, style))
        story.append(Spacer(1, 8))
    doc.build(story)
    return buffer.getvalue()


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
      <div class='ns-risk-title {risk}'>{headline}</div>
      <div class='ns-risk-sub'>{sublabel}</div>
    </div>
    <div class='ns-metric'>
      <div class='ns-meter'><div class='ns-fill {risk}'></div></div>
      <div class='ns-conf {confidence}' title='Confidence reflects pattern consistency, not diagnosis certainty'>{confidence.title()} Confidence</div>
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
    <div class='ns-card-head'>Step 2 · AI Insight</div>
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
    <div class='ns-card-head'>Step 3 · Patterns ({len(patterns)}/3)</div>
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
            "<div class='ns-row'><div class='ns-idx'>—</div><div>No strong repetitive patterns detected.</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div></div></div>", unsafe_allow_html=True)

    st.markdown(
        """
<div class='ns-step'>
  <div class='ns-suggest'>
    <div class='ns-card-head' style='border-bottom:1px solid #f4e7d3;'>Step 4 · Suggestions</div>
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
        "Screening support only · Not a clinical diagnosis · Consult a qualified educational psychologist for formal evaluation<br>"
        "<strong>NastaliqScan</strong> · AI Seekho Project"
        "</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.markdown("<div class='ns-shell'>", unsafe_allow_html=True)

    st.markdown(
        """
<div class='ns-hero'>
  <div class='ns-eyebrow'>🔬 AI Seekho · Early Screening</div>
  <div class='ns-title'>Nastaliq<em>Scan</em></div>
  <div class='ns-urdu'>اردو اور انگلش تحریر کا ذہین تجزیہ</div>
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
  ⚠ <strong>Not a medical diagnosis tool.</strong> Results are for early screening support only.
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
        "session_id": hashlib.sha256(str(time.time()).encode()).hexdigest()[:8],
        "analysis_generated_at": "",
        "linkedin_summary_text": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown(
        """
<div class='ns-why'>
  <div class='ns-why-title'>Why this matters</div>
  <ul>
    <li>Urdu dyslexia tools are almost non-existent</li>
    <li>Early detection changes learning outcomes</li>
    <li>Teachers lack fast screening tools</li>
    <li>This tool gives instant structured feedback</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='ns-quick-export'><div class='ns-quick-export-title'>Quick Export</div>", unsafe_allow_html=True)
    top_c1, top_c2 = st.columns(2)
    has_result = bool(st.session_state.get("analysis_result"))
    if has_result:
        top_mode = "Text" if st.session_state.get("analysis_urdu") else "Handwriting"
        top_payload = build_report_payload(
            st.session_state.analysis_result,
            mode=top_mode,
            original_text=st.session_state.get("analysis_original", ""),
        )
        top_payload_json = json.dumps(top_payload, ensure_ascii=False, indent=2)
        top_pdf_lines = [
            "NastaliqScan Report",
            f"Generated: {top_payload['generated_at']}",
            f"Mode: {top_payload['mode']}",
            f"Risk: {top_payload['risk_level']}",
            f"Confidence: {top_payload['confidence']}",
            "",
            "Insight:",
            top_payload.get("main_insight", ""),
            "",
            "Patterns:",
        ] + [f"- {p}" for p in top_payload.get("detected_patterns", [])] + [
            "",
            "Suggestions:",
        ] + [f"- {s}" for s in top_payload.get("suggestions", [])] + [
            "",
            "Disclaimer: Screening support only. Not a clinical diagnosis.",
        ]
        top_pdf_bytes = generate_simple_pdf(top_pdf_lines)
    else:
        top_payload_json = "{}"
        top_pdf_bytes = b"%PDF-1.4\n%%EOF"

    with top_c1:
        st.download_button(
            "Download JSON",
            data=top_payload_json.encode("utf-8"),
            file_name=f"nastaliqscan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            disabled=not has_result,
        )
    with top_c2:
        st.download_button(
            "Download PDF",
            data=top_pdf_bytes,
            file_name=f"nastaliqscan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=not has_result,
        )
    st.markdown("</div>", unsafe_allow_html=True)
    if not has_result:
        st.caption("Run analysis to enable download")
    elif st.session_state.get("linkedin_summary_text"):
        st.code(st.session_state["linkedin_summary_text"])

    st.markdown("<div class='ns-label'>Choose Analysis Mode</div>", unsafe_allow_html=True)

    mode = st.radio(
        "Mode",
        ["✍️ Text Analysis", "📷 Handwriting Scan"],
        horizontal=True,
        label_visibility="collapsed",
        key="mode_radio",
    )
    is_text = mode.startswith("✍️")

    text_active = "active" if is_text else ""
    image_active = "active" if not is_text else ""
    st.markdown(
        f"""
<div class='ns-mode-grid'>
  <div class='ns-mode-card {text_active}'>
    <div class='ns-mode-title'>✍️ Text Analysis</div>
    <div class='ns-mode-desc'>Paste Urdu/English writing for language-level pattern analysis.</div>
  </div>
  <div class='ns-mode-card {image_active}'>
    <div class='ns-mode-title'>📷 Handwriting Scan</div>
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
                st.session_state.user_input = "مج اسکول جانا پسن ہے۔ میں روز دوستوں کے سات کلتا ہوں"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        user_input = st.text_area(
            "Writing sample input",
            height=160,
            placeholder="Urdu: مجھے اسکول جانا پسند ہے...\n\nEnglish: I like to go to school every day...",
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
    <div class='ns-panel-meta'>JPG · JPEG · JFIF · PNG</div>
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
                st.image(str(sp), caption=sp.name, use_container_width=True)
            else:
                st.info("Sample unavailable — upload an image below.")

        uploaded_file = st.file_uploader(
            "Upload handwriting",
            type=["jpg", "jpeg", "png", "jfif"],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded sample", use_container_width=True)

        st.markdown("</div></div>", unsafe_allow_html=True)
        user_input = ""

    st.markdown("<div class='ns-cta'>", unsafe_allow_html=True)
    run = st.button("Run AI Screening", key="analyze_btn")
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
            status_slot = st.empty()
            status_slot.info("Analyzing writing patterns...")
            time.sleep(0.35)
            status_slot.info("Detecting dyslexia signals...")
            time.sleep(0.35)
            status_slot.info("Generating structured report...")
            try:
                result = run_analysis_with_safety(mode="text", text_input=cleaned)
                st.session_state.analysis_result = result
                st.session_state.analysis_original = cleaned
                st.session_state.analysis_urdu = contains_urdu(cleaned)
                st.session_state.analysis_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except RuntimeError as e:
                st.error(str(e))
                st.markdown("</div>", unsafe_allow_html=True)
                return
            except (json.JSONDecodeError, ValueError):
                st.error("Could not parse a result ? try a longer or clearer sample.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            except Exception as e:
                st.error(f"Analysis temporarily unavailable. Please try again. ({e})")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            finally:
                status_slot.empty()
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

            status_slot = st.empty()
            status_slot.info("Analyzing writing patterns...")
            time.sleep(0.35)
            status_slot.info("Detecting dyslexia signals...")
            time.sleep(0.35)
            status_slot.info("Generating structured report...")
            try:
                result = run_analysis_with_safety(
                    mode="image",
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )
                st.session_state.analysis_result = result
                st.session_state.analysis_original = ""
                st.session_state.analysis_urdu = False
                st.session_state.analysis_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except RuntimeError as e:
                st.error(str(e))
                st.markdown("</div>", unsafe_allow_html=True)
                return
            except (json.JSONDecodeError, ValueError):
                st.error("Could not parse a result ? try a clearer image.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            except Exception as e:
                st.error(f"Analysis temporarily unavailable. Please try again. ({e})")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            finally:
                status_slot.empty()

    if st.session_state.analysis_result:
        st.markdown("<div class='ns-results-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='ns-report-label'>Analysis Report</div>", unsafe_allow_html=True)
        st.caption(
            f"Timestamp: {st.session_state.get('analysis_generated_at', 'N/A')}  |  "
            f"Session ID: {st.session_state.get('session_id', 'unknown')}"
        )
        render_results(
            st.session_state.analysis_result,
            original_text=st.session_state.analysis_original,
            urdu_mode=st.session_state.analysis_urdu,
        )

        # Export / Share block (bottom duplicate)
        current_mode = "Text" if st.session_state.analysis_original else "Handwriting"
        payload = build_report_payload(
            st.session_state.analysis_result,
            mode=current_mode,
            original_text=st.session_state.analysis_original,
        )
        payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
        share_text = build_shareable_summary(st.session_state.analysis_result, current_mode)
        pdf_lines = [
            "NastaliqScan Report",
            f"Generated: {payload['generated_at']}",
            f"Mode: {payload['mode']}",
            f"Risk: {payload['risk_level']}",
            f"Confidence: {payload['confidence']}",
            "",
            "Insight:",
            payload.get("main_insight", ""),
            "",
            "Patterns:",
        ] + [f"- {p}" for p in payload.get("detected_patterns", [])] + [
            "",
            "Suggestions:",
        ] + [f"- {s}" for s in payload.get("suggestions", [])] + [
            "",
            "Disclaimer: Screening support only. Not a clinical diagnosis.",
        ]
        pdf_bytes = generate_simple_pdf(pdf_lines)

        st.markdown("<div class='ns-label'>Export & Share</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "Download JSON Report",
                data=payload_json.encode("utf-8"),
                file_name=f"nastaliqscan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "Download PDF Report",
                data=pdf_bytes,
                file_name=f"nastaliqscan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with c3:
            if st.button("Copy LinkedIn Summary", key="linkedin_copy_bottom", use_container_width=True):
                st.session_state["linkedin_summary_text"] = build_linkedin_summary(st.session_state.analysis_result)

        st.caption("Shareable Result")
        st.code(st.session_state.get("linkedin_summary_text") or share_text)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main() 