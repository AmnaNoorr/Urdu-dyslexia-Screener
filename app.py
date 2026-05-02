import json
import os
from typing import Any, Dict, List

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
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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

4. Return STRICT JSON ONLY in this format:

{
  "risk_level": "LOW | MODERATE | HIGH",
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

5. Keep explanations simple and non-technical.

6. Do NOT include any text outside JSON.
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


def main() -> None:
    st.title("🧠 Urdu Dyslexia Screener (AI Seekho Project)")
    st.markdown(
        """
This AI tool screens Urdu/English writing for possible dyslexia-related patterns.
It is designed for **early screening support** only, not diagnosis.
        """
    )

    st.info("⚠️ This is NOT a medical diagnosis tool. Please consult a qualified professional.")

    user_input = st.text_area(
        "✍️ Enter Urdu or English writing sample",
        height=200,
        placeholder="Urdu: مجھے اسکول جانا پسند ہے...\n\nEnglish: I like to go to school...",
    )

    if st.button("Analyze Writing"):
        if not user_input.strip():
            st.warning("Please enter some text before analysis.")
            return

        with st.spinner("Analyzing writing patterns with Gemini..."):
            try:
                result = call_gemini(user_input)
            except json.JSONDecodeError:
                st.error("Model response format was invalid. Please try again.")
                return
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        render_risk_level(result["risk_level"])

        st.subheader("Detected Patterns")
        if result["detected_patterns"]:
            for pattern in result["detected_patterns"]:
                st.markdown(f"- {pattern}")
        else:
            st.write("No strong repetitive patterns detected in the provided sample.")

        st.subheader("Explanation")
        st.write(result["explanation"] or "No explanation returned.")

        st.subheader("Suggestions")
        if result["suggestions"]:
            for suggestion in result["suggestions"]:
                st.markdown(f"- {suggestion}")
        else:
            st.write("Consider regular reading and guided writing practice with teacher support.")

        st.caption("This is not a medical diagnosis. Please consult a professional.")


if __name__ == "__main__":
    main()
