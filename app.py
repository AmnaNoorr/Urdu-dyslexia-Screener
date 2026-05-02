import json
import os
import re  # ADDED: Urdu detection helper
from pathlib import Path  # ADDED: local sample image paths
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

st.set_page_config(
    page_title="Urdu Dyslexia Screener (AI Seekho Project)",
    page_icon="🧠",
    layout="centered",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;600&family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

.urdu-text {
    font-family: 'Noto Nastaliq Urdu', serif;
    direction: rtl;
    text-align: right;
}

.risk-box {
    border-radius: 12px;
    padding: 14px 16px;
    color: #111827;
    font-weight: 700;
    margin-bottom: 12px;
}

.risk-low {
    background: #dcfce7;
    border: 1px solid #86efac;
}

.risk-moderate {
    background: #fef9c3;
    border: 1px solid #fde047;
}

.risk-high {
    background: #fee2e2;
    border: 1px solid #fca5a5;
}

/* ADDED: confidence badge styles */
.confidence-box {
    border-radius: 12px;
    padding: 10px 14px;
    color: #111827;
    font-weight: 600;
    margin-bottom: 12px;
    display: inline-block;
}

.confidence-low {
    background: #fee2e2;
    border: 1px solid #fca5a5;
}

.confidence-medium {
    background: #fef9c3;
    border: 1px solid #fde047;
}

.confidence-high {
    background: #dcfce7;
    border: 1px solid #86efac;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ADDED: bundled sample handwriting images for demo mode.
SAMPLE_IMAGE_FILES = {
    "Urdu Sample 1 (urdu1.jfif)": Path("samples/urdu1.jfif"),
    "Urdu Sample 2 (urdu2.jpg)": Path("samples/urdu2.jpg"),
    "English Sample (english1.jfif)": Path("samples/english1.jfif"),
}

SYSTEM_PROMPT_TEMPLATE = """SYSTEM ROLE:
You are an expert in linguistics, Urdu language processing, and learning disorders, specifically dyslexia detection.

TASK:
Analyze the user's writing and detect possible indicators of dyslexia.

INPUT TEXT:
"{user_input}"

INSTRUCTIONS:
1. Analyze for the following patterns:
   - Letter confusion (especially similar Urdu letters like ب ت ث)
   - Phonetic spelling errors
   - Missing letters or words
   - Repeated inconsistencies in spelling
   - Word order or sentence structure issues
   - Simplified vocabulary usage
   - Mixing Urdu and English incorrectly

2. Be careful:
   - Do NOT assume dyslexia from a single minor mistake
   - Look for consistent patterns

3. Classify risk into:
   - LOW
   - MODERATE
   - HIGH

4. Add confidence based on strength and consistency of detected patterns:
   - LOW
   - MEDIUM
   - HIGH

5. Return STRICT JSON ONLY in this format:

{
  "risk_level": "LOW | MODERATE | HIGH",
  "confidence": "LOW | MEDIUM | HIGH",
  "detected_patterns": [
    "pattern 1",
    "pattern 2"
  ],
  "explanation": "Simple explanation in 2-3 sentences",
  "suggestions": [
    "suggestion 1",
    "suggestion 2"
  ]
}

6. Keep explanations simple and non-technical.

7. Do NOT include any text outside JSON.
"""

# IMPROVED: Vision prompt quality + confidence output.
VISION_PROMPT_TEMPLATE = """SYSTEM ROLE:
You are an expert in Urdu handwriting analysis and learning disorders such as dyslexia.

TASK:
Analyze the uploaded handwriting image and identify possible indicators of dyslexia.

INSTRUCTIONS:
1. Carefully examine the handwriting for:
   - Reversed or incorrectly formed Urdu letters (e.g., ب ت ث)
   - Inconsistent letter shapes
   - Irregular spacing between letters and words
   - Misalignment (text not following a straight baseline)
   - Inconsistent letter sizes
   - Unusual or broken stroke formation

2. Do NOT assume dyslexia from a single issue.
   Only flag patterns if they appear repeatedly.

3. Mention specific Urdu letters if possible (e.g., reversed ب or incorrectly formed ت).

4. Avoid generic statements like "some inconsistencies detected".

5. Be specific and evidence-based in observations.

6. Classify risk into:
   - LOW
   - MODERATE
   - HIGH

7. Add confidence based on strength and consistency of detected patterns:
   - LOW
   - MEDIUM
   - HIGH

8. Return STRICT JSON ONLY:

{
  "risk_level": "LOW | MODERATE | HIGH",
  "confidence": "LOW | MEDIUM | HIGH",
  "detected_patterns": [
    "pattern 1",
    "pattern 2"
  ],
  "explanation": "Simple explanation",
  "suggestions": [
    "suggestion 1"
  ]
}

9. Keep explanation simple and non-medical.

10. Do NOT include any text outside JSON.
"""


def extract_json_safely(text: str) -> Dict[str, Any]:
    """Extract and parse JSON safely, even if the model wraps it accidentally."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty response from model")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)
        raise


def normalize_result(data: Dict[str, Any]) -> Dict[str, Any]:
    risk = str(data.get("risk_level", "")).upper().strip()
    if risk not in {"LOW", "MODERATE", "HIGH"}:
        risk = "MODERATE"

    # ADDED: confidence normalization.
    confidence = str(data.get("confidence", "")).upper().strip()
    if confidence not in {"LOW", "MEDIUM", "HIGH"}:
        confidence = "MEDIUM"

    patterns = data.get("detected_patterns", [])
    if not isinstance(patterns, list):
        patterns = []
    patterns = [str(p).strip() for p in patterns if str(p).strip()]

    explanation = str(data.get("explanation", "")).strip()

    suggestions = data.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()]

    return {
        "risk_level": risk,
        "confidence": confidence,
        "detected_patterns": patterns,
        "explanation": explanation,
        "suggestions": suggestions,
    }


def call_gemini(user_input: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your environment or .env file.")

    client = genai.Client(api_key=api_key)

    prompt = SYSTEM_PROMPT_TEMPLATE.replace("{user_input}", user_input)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    parsed = extract_json_safely(response.text)
    return normalize_result(parsed)


# IMPROVED: Vision call now accepts real detected mime type.
def call_gemini_vision(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your environment or .env file.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_text(text=VISION_PROMPT_TEMPLATE),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    parsed = extract_json_safely(response.text)
    return normalize_result(parsed)


def render_risk_level(risk_level: str) -> None:
    css_class = {
        "LOW": "risk-low",
        "MODERATE": "risk-moderate",
        "HIGH": "risk-high",
    }.get(risk_level, "risk-moderate")

    st.markdown(
        f"<div class='risk-box {css_class}'>📊 Risk Level: {risk_level.title()}</div>",
        unsafe_allow_html=True,
    )


# ADDED: confidence display.
def render_confidence(confidence: str) -> None:
    # IMPROVED: styled confidence badge with subtle explanatory help text.
    css_class = {
        "LOW": "confidence-low",
        "MEDIUM": "confidence-medium",
        "HIGH": "confidence-high",
    }.get(confidence, "confidence-medium")
    st.markdown(
        f"<div class='confidence-box {css_class}'>Confidence: {confidence.title()}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Confidence indicates how strong and consistent the detected patterns are.")


# ADDED: Urdu detection for RTL output styling.
def contains_urdu(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


# ADDED: shared renderer for Urdu/English blocks.
def render_text_block(text: str, urdu_mode: bool) -> None:
    if urdu_mode and text:
        st.markdown(f"<div class='urdu-text'>{text}</div>", unsafe_allow_html=True)
    else:
        st.write(text)


# ADDED: why-this-matters text with fallback.
def build_why_this_matters(result: Dict[str, Any]) -> str:
    explanation = (result.get("explanation") or "").strip()
    if explanation:
        return (
            f"{explanation} These patterns may affect reading fluency, spelling accuracy, "
            "and writing consistency."
        )
    return "These patterns may affect reading fluency, spelling accuracy, and writing consistency."


# IMPROVED: robust upload mime detection.
def detect_image_mime(uploaded_file) -> str:
    detected = (getattr(uploaded_file, "type", "") or "").lower().strip()
    if detected in {"image/jpeg", "image/png"}:
        return detected

    name = (getattr(uploaded_file, "name", "") or "").lower()
    if name.endswith(".jpg") or name.endswith(".jpeg") or name.endswith(".jfif"):
        return "image/jpeg"
    if name.endswith(".png"):
        return "image/png"
    return ""


def main() -> None:
    st.title("🧠 Urdu Dyslexia Screener (AI Seekho Project)")
    st.markdown(
        """
This AI tool screens Urdu/English writing for possible dyslexia-related patterns.
It is designed for **early screening support** only, not diagnosis.
        """
    )

    st.info("⚠️ This is NOT a medical diagnosis tool. Please consult a qualified professional.")

    # ADDED: state for sample input UX.
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    if "show_image_sample_hint" not in st.session_state:
        st.session_state.show_image_sample_hint = False
    if "selected_sample_label" not in st.session_state:
        st.session_state.selected_sample_label = list(SAMPLE_IMAGE_FILES.keys())[0]

    mode = st.radio(
        "Choose analysis mode",
        ["Text Analysis", "Handwriting Image Analysis"],
        horizontal=True,
    )

    user_input = st.session_state.user_input
    uploaded_file = None

    if mode == "Text Analysis":
        if st.button("Try Sample Input"):
            # ADDED: demo-friendly sample with likely errors.
            st.session_state.user_input = "مج اسکول جانا پسن ہے۔ میں روز دوستوں کے سات کلتا ہوں"

        user_input = st.text_area(
            "✍️ Enter Urdu or English writing sample",
            height=200,
            placeholder="Urdu: مجھے اسکول جانا پسند ہے...\n\nEnglish: I like to go to school...",
            key="user_input",
        )
    else:
        # ADDED: real sample image selector.
        st.markdown("**Sample Handwriting Images**")
        st.session_state.selected_sample_label = st.selectbox(
            "Choose sample",
            list(SAMPLE_IMAGE_FILES.keys()),
            index=list(SAMPLE_IMAGE_FILES.keys()).index(st.session_state.selected_sample_label),
        )

        if st.button("Try Sample Input"):
            st.session_state.show_image_sample_hint = True

        if st.session_state.show_image_sample_hint:
            sample_path = SAMPLE_IMAGE_FILES.get(st.session_state.selected_sample_label)
            if sample_path and sample_path.exists():
                st.image(str(sample_path), caption=f"Sample: {sample_path.name}", use_container_width=True)
            else:
                st.info("Sample image mode ready: upload a demo handwritten Urdu JPG/PNG/JFIF to continue.")

        uploaded_file = st.file_uploader(
            "📸 Upload handwritten Urdu sample image",
            type=["jpg", "jpeg", "png", "jfif"],
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded handwriting sample", use_container_width=True)

    if st.button("Analyze Writing"):
        if mode == "Text Analysis":
            cleaned = user_input.strip()
            if not cleaned:
                st.warning("Please enter some text before analysis.")
                return
            # IMPROVED: minimum length guard for reliability.
            if len(cleaned) < 25:
                st.warning("Please enter a longer writing sample for accurate analysis.")
                return
        else:
            image_bytes = b""
            mime_type = ""

            if uploaded_file is not None:
                mime_type = detect_image_mime(uploaded_file)
                if mime_type not in {"image/jpeg", "image/png"}:
                    st.warning("Unsupported image type. Please upload a JPG, JPEG, JFIF, or PNG image.")
                    return
                image_bytes = uploaded_file.read()
            elif st.session_state.show_image_sample_hint:
                sample_path = SAMPLE_IMAGE_FILES.get(st.session_state.selected_sample_label)
                if sample_path and sample_path.exists():
                    image_bytes = sample_path.read_bytes()
                    mime_type = "image/png" if sample_path.suffix.lower() == ".png" else "image/jpeg"
                else:
                    st.warning("Sample image could not be loaded. Please upload an image.")
                    return
            else:
                st.warning("Please upload an image before analysis.")
                return

        # IMPROVED: mode-specific loading message.
        spinner_text = "Analyzing text patterns..." if mode == "Text Analysis" else "Analyzing handwriting patterns..."

        with st.spinner(spinner_text):
            try:
                if mode == "Text Analysis":
                    result = call_gemini(user_input)
                else:
                    if not image_bytes:
                        st.warning("Uploaded image appears empty. Please try another file.")
                        return
                    result = call_gemini_vision(image_bytes, mime_type)
            except json.JSONDecodeError:
                # IMPROVED: user-friendly empty/invalid response messaging.
                st.error("No analysis could be generated. Try a clearer sample.")
                return
            except ValueError:
                # IMPROVED: explicit handling for empty model responses.
                st.error("No analysis could be generated. Try a clearer sample.")
                return
            except Exception as exc:
                # IMPROVED: user-friendly API failure message.
                st.error("Analysis temporarily unavailable. Please try again.")
                return

        # ADDED: compact summary block for demo impact.
        st.subheader("📌 Summary")
        st.write(f"{result['risk_level'].title()} risk detected with {result.get('confidence', 'MEDIUM').lower()} confidence.")

        render_risk_level(result["risk_level"])
        # ADDED: confidence under risk level.
        render_confidence(result.get("confidence", "MEDIUM"))

        urdu_mode = mode == "Text Analysis" and contains_urdu(user_input)

        # IMPROVED: emoji headings.
        st.subheader("🔍 Detected Patterns")
        if result["detected_patterns"]:
            for pattern in result["detected_patterns"]:
                if urdu_mode:
                    # IMPROVED: consistent Urdu RTL rendering for patterns.
                    st.markdown(f"<div class='urdu-text'>• {pattern}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"- {pattern}")
        else:
            st.write("No strong repetitive patterns detected in the provided sample.")

        st.subheader("🧠 Explanation")
        render_text_block(result["explanation"] or "No explanation returned.", urdu_mode)

        # ADDED: why this matters section.
        st.subheader("👉 Why this matters")
        render_text_block(build_why_this_matters(result), urdu_mode)

        st.subheader("💡 Suggestions")
        if result["suggestions"]:
            for suggestion in result["suggestions"]:
                if urdu_mode:
                    # IMPROVED: consistent Urdu RTL rendering for suggestions.
                    st.markdown(f"<div class='urdu-text'>• {suggestion}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"- {suggestion}")
        else:
            st.write("Consider regular reading and guided writing practice with teacher support.")

        st.caption("This is not a medical diagnosis. Please consult a professional.")


if __name__ == "__main__":
    main()
