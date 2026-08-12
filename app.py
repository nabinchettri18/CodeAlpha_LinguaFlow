import html
import json
import os
import subprocess
import time

import requests

import streamlit as st
import streamlit.components.v1 as components

from src.translator import Translator, TranslationError
from src.languages import LANGUAGES
from src.language_detector import (
    LanguageDetector,
    LanguageDetectionError,
)


GEMINI_HEALTH_URL = "http://127.0.0.1:8765/health"


@st.cache_resource
def start_gemini_service():
    """
    Ensure the local Gemini Node service is running.

    If another Gemini service is already running, reuse it.
    Otherwise start gemini_server.mjs automatically.
    """

    # First check whether the service is already running.
    try:
        response = requests.get(
            GEMINI_HEALTH_URL,
            timeout=1,
        )

        if response.ok:
            return {
                "running": True,
                "process": None,
            }

    except requests.RequestException:
        pass

    server_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "gemini_server.mjs",
    )

    if not os.path.exists(server_file):
        return {
            "running": False,
            "process": None,
            "error": "gemini_server.mjs was not found.",
        }

    try:
        creation_flags = 0

        if os.name == "nt":
            creation_flags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            ["node", server_file],
            cwd=os.path.dirname(server_file),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )

    except Exception as exc:
        return {
            "running": False,
            "process": None,
            "error": f"Could not start Gemini service: {exc}",
        }

    # Give Node a short moment to start, then verify it.
    for _ in range(20):
        try:
            response = requests.get(
                GEMINI_HEALTH_URL,
                timeout=1,
            )

            if response.ok:
                return {
                    "running": True,
                    "process": process,
                }

        except requests.RequestException:
            time.sleep(0.25)

    return {
        "running": False,
        "process": process,
        "error": (
            "Gemini service started but did not become "
            "ready on port 8765."
        ),
    }


gemini_service = start_gemini_service()

if not gemini_service.get("running"):
    st.warning(
        gemini_service.get(
            "error",
            "Gemini service is unavailable.",
        )
    )


st.set_page_config(
    page_title="LinguaFlow",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="collapsed",
)


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ur": "Urdu",
    "ar": "Arabic",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pt-BR": "Portuguese (Brazil)",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-Hans": "Chinese (Simplified)",
    "zh-Hant": "Chinese (Traditional)",
    "tr": "Turkish",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "nb": "Norwegian",
    "pl": "Polish",
    "cs": "Czech",
    "ro": "Romanian",
    "el": "Greek",
    "he": "Hebrew",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "tl": "Tagalog",
    "sw": "Swahili",
    "ga": "Irish",
    "hu": "Hungarian",
    "uk": "Ukrainian",
    "fa": "Persian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "eu": "Basque",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sq": "Albanian",
    "az": "Azerbaijani",
    "ky": "Kyrgyz",
}


def language_code_from_name(name):
    """Return language code from display name."""
    for code, display_name in LANGUAGE_NAMES.items():
        if display_name == name:
            return code

    return LANGUAGES.get(name)


def language_name_from_code(code):
    """Return display name from language code."""
    return LANGUAGE_NAMES.get(code, code)


def count_words(text):
    """Simple Unicode-friendly word count."""
    if not text or not text.strip():
        return 0

    return len(text.strip().split())


def add_history(
    source_text,
    translated_text,
    source_code,
    target_code,
):
    """Add a translation to session history."""

    if not source_text.strip() or not translated_text.strip():
        return

    item = {
        "source_text": source_text.strip(),
        "translated_text": translated_text.strip(),
        "source_code": source_code,
        "target_code": target_code,
        "source_language": language_name_from_code(
            source_code
        ),
        "target_language": language_name_from_code(
            target_code
        ),
        "favorite": False,
    }

    history = st.session_state.translation_history

    # Avoid adding the exact same translation repeatedly.
    if history:

        latest = history[0]

        if (
            latest["source_text"] == item["source_text"]
            and latest["translated_text"]
            == item["translated_text"]
            and latest["source_code"]
            == item["source_code"]
            and latest["target_code"]
            == item["target_code"]
        ):
            return

    history.insert(0, item)

    # Keep the session history reasonably small.
    if len(history) > 50:
        del history[50:]


def swap_callback():
    """Safely swap the translation direction."""

    detected_code = st.session_state.detected_code
    detected_name = st.session_state.detected_language

    # Nothing to swap if language detection hasn't happened.
    if not detected_code or not detected_name:
        return

    translated = st.session_state.translated_text

    if translated:
        st.session_state.translation_input = translated
        st.session_state.translated_text = ""

    st.session_state.target_language = detected_name

    st.session_state.detected_code = None
    st.session_state.detected_language = None

    st.session_state.last_source_code = None
    st.session_state.last_target_code = None


def clear_workspace_callback():
    """
    Safely clear the Streamlit text-area widget state.

    This callback runs before the next script execution,
    so Streamlit allows us to modify the widget state.
    """

    st.session_state.translation_input = ""
    st.session_state.translated_text = ""

    st.session_state.detected_code = None
    st.session_state.detected_language = None

    st.session_state.last_source_code = None
    st.session_state.last_target_code = None


def clear_result_callback():
    """Clear only the translated result."""

    st.session_state.translated_text = ""


def reuse_history_callback(index):
    """
    Safely load a history item back into the input box.
    """

    item = st.session_state.translation_history[index]

    st.session_state.translation_input = (
        item["source_text"]
    )

    st.session_state.target_language = (
        item["target_language"]
    )

    st.session_state.translated_text = ""

    st.session_state.detected_code = None
    st.session_state.detected_language = None


def set_target_language(language):
    """Set target language from the popular-language buttons."""

    st.session_state.target_language = language


if "translation_input" not in st.session_state:
    st.session_state.translation_input = ""

if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""

if "detected_code" not in st.session_state:
    st.session_state.detected_code = None

if "detected_language" not in st.session_state:
    st.session_state.detected_language = None

if "last_source_code" not in st.session_state:
    st.session_state.last_source_code = None

if "last_target_code" not in st.session_state:
    st.session_state.last_target_code = None

if "translation_history" not in st.session_state:
    st.session_state.translation_history = []

if "favorites" not in st.session_state:
    st.session_state.favorites = []

if "history_open" not in st.session_state:
    st.session_state.history_open = False

if "target_language" not in st.session_state:

    if "English" in LANGUAGES:
        st.session_state.target_language = "English"

    else:
        st.session_state.target_language = list(
            LANGUAGES.keys()
        )[0]


@st.cache_resource
def load_translator():
    return Translator()


@st.cache_resource
def load_language_detector():
    return LanguageDetector()


translator = load_translator()
language_detector = load_language_detector()


st.markdown(
    """
<style>

/* ==========================================================
   GLOBAL
   ========================================================== */

html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section.main {
    background: #f7f8fa !important;
}

header[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    display: none !important;
}

[data-testid="stDecoration"] {
    display: none !important;
}

#MainMenu {
    display: none !important;
}

footer {
    display: none !important;
}

div[data-testid="stAlert"] {
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 10px !important;
    color: #1e40af !important;
}

div[data-testid="stAlert"] p {
    color: #1e40af !important;
    font-weight: 600 !important;
}

div[data-testid="stAlert"] svg {
    color: #2563eb !important;
}

.block-container {
    max-width: 1200px !important;
    padding-top: 28px !important;
    padding-bottom: 60px !important;
}


/* ==========================================================
   HEADER
   ========================================================== */

.lingua-header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;

    padding-bottom: 20px;
    margin-bottom: 60px;

    border-bottom: 1px solid #e5e7eb;
}

.lingua-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.lingua-logo {
    width: 42px;
    height: 42px;

    display: flex;
    align-items: center;
    justify-content: center;

    background: #111827;
    color: #ffffff;

    border-radius: 11px;

    font-size: 20px;
    font-weight: 800;

    box-shadow:
        0 4px 12px rgba(17, 24, 39, 0.12);
}

.lingua-name {
    color: #111827;

    font-size: 22px;
    font-weight: 800;

    letter-spacing: -0.7px;
}

.lingua-subtitle {
    margin-top: 2px;

    color: #9ca3af;

    font-size: 12px;
}

.lingua-status {
    display: flex;
    align-items: center;
    gap: 8px;

    padding: 8px 13px;

    background: #ffffff;

    border: 1px solid #e5e7eb;

    border-radius: 999px;

    color: #4b5563;

    font-size: 12px;
    font-weight: 650;
}

.lingua-status-dot {
    width: 7px;
    height: 7px;

    background: #22c55e;

    border-radius: 50%;
}


/* ==========================================================
   HERO
   ========================================================== */

.lingua-hero {
    max-width: 850px;

    margin: 0 auto 45px auto;

    text-align: center;
}

.lingua-hero-label {
    display: inline-block;

    padding: 7px 13px;

    margin-bottom: 18px;

    background: #eff6ff;

    border: 1px solid #dbeafe;

    border-radius: 999px;

    color: #2563eb;

    font-size: 11px;
    font-weight: 800;

    letter-spacing: 1px;
}

.lingua-hero-title {
    margin: 0;

    color: #111827;

    font-size: 56px;

    line-height: 1.05;

    font-weight: 850;

    letter-spacing: -3px;
}

.lingua-hero-title span {
    color: #2563eb;
}

.lingua-hero-description {
    max-width: 700px;

    margin: 18px auto 0 auto;

    color: #6b7280;

    font-size: 16px;

    line-height: 1.7;
}


/* ==========================================================
   LANGUAGE AREA
   ========================================================== */

.language-label {
    margin-bottom: 7px;

    color: #6b7280;

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 1px;

    text-transform: uppercase;
}


/* ==========================================================
   SELECTBOX
   ========================================================== */

div[data-testid="stSelectbox"]
div[data-baseweb="select"] > div {

    min-height: 46px !important;

    background: #ffffff !important;

    border: 1px solid #d1d5db !important;

    border-radius: 10px !important;
}


/* ==========================================================
   DETECTED LANGUAGE
   ========================================================== */

.detected-language {

    display: inline-flex;

    align-items: center;

    gap: 7px;

    margin-top: 9px;

    padding: 6px 10px;

    background: #f0fdf4;

    border: 1px solid #dcfce7;

    border-radius: 999px;

    color: #15803d;

    font-size: 12px;

    font-weight: 700;
}

.detected-language-dot {

    width: 6px;
    height: 6px;

    background: #22c55e;

    border-radius: 50%;
}


/* ==========================================================
   TEXT AREA
   ========================================================== */

div[data-testid="stTextArea"] textarea {

    min-height: 260px !important;

    background: #ffffff !important;

    border: 1px solid #e5e7eb !important;

    border-radius: 12px !important;

    color: #111827 !important;

    font-size: 16px !important;

    line-height: 1.7 !important;

    padding: 16px !important;
}

div[data-testid="stTextArea"] textarea:focus {

    border-color: #2563eb !important;

    box-shadow:
        0 0 0 2px rgba(37, 99, 235, 0.10) !important;
}


/* ==========================================================
   OUTPUT
   ========================================================== */

.translation-output {

    min-height: 260px;

    padding: 17px;

    background: #ffffff;

    border: 1px solid #e5e7eb;

    border-radius: 12px;

    color: #111827;

    font-size: 16px;

    line-height: 1.7;

    white-space: pre-wrap;

    overflow-wrap: break-word;
}

.translation-placeholder {

    color: #9ca3af;
}


/* ==========================================================
   CHARACTER COUNT
   ========================================================== */

.character-count {

    margin-top: 8px;

    color: #9ca3af;

    font-size: 12px;
}

.stats-line {

    margin-top: 8px;

    color: #9ca3af;

    font-size: 12px;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

div[data-testid="stButton"] > button {

    min-height: 46px !important;

    background: #ffffff !important;

    border: 1px solid #d1d5db !important;

    border-radius: 10px !important;

    color: #374151 !important;

    font-size: 13px !important;

    font-weight: 700 !important;

    box-shadow: none !important;
}

div[data-testid="stButton"] > button:hover {

    background: #f8fbff !important;

    border-color: #93c5fd !important;

    color: #2563eb !important;
}


/* ==========================================================
   PRIMARY BUTTON
   ========================================================== */

div[data-testid="stFormSubmitButton"] > button {

    min-height: 50px !important;

    background: #2563eb !important;

    border: 1px solid #2563eb !important;

    border-radius: 10px !important;

    color: #ffffff !important;

    font-size: 14px !important;

    font-weight: 750 !important;
}

div[data-testid="stFormSubmitButton"] > button:hover {

    background: #1d4ed8 !important;
}


/* ==========================================================
   FEATURE BUTTONS
   ========================================================== */

.feature-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 10px;
}

.feature-caption {
    color: #9ca3af;
    font-size: 11px;
    margin-top: 6px;
}


/* ==========================================================
   INFO
   ========================================================== */

.info-section {

    max-width: 1080px;

    margin: 55px auto 0 auto;

    padding-top: 25px;

    border-top: 1px solid #e5e7eb;
}

.info-title {

    color: #111827;

    font-size: 18px;

    font-weight: 750;
}

.info-text {

    max-width: 800px;

    margin-top: 7px;

    color: #6b7280;

    font-size: 14px;

    line-height: 1.7;
}


/* ==========================================================
   HISTORY
   ========================================================== */

.history-card {

    padding: 16px;

    margin-bottom: 10px;

    background: #ffffff;

    border: 1px solid #e5e7eb;

    border-radius: 12px;
}

.history-meta {

    color: #9ca3af;

    font-size: 11px;

    font-weight: 700;

    margin-bottom: 8px;
}

.history-source {

    color: #374151;

    font-size: 13px;

    line-height: 1.5;

    margin-bottom: 7px;
}

.history-translation {

    color: #111827;

    font-size: 14px;

    line-height: 1.6;

    font-weight: 600;
}


/* ==========================================================
   FOOTER
   ========================================================== */

.lingua-footer {

    max-width: 1080px;

    margin: 55px auto 0 auto;

    padding-top: 20px;

    border-top: 1px solid #e5e7eb;

    text-align: center;

    color: #9ca3af;

    font-size: 12px;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 800px) {

    .lingua-header {
        margin-bottom: 40px;
    }

    .lingua-status {
        display: none;
    }

    .lingua-hero-title {
        font-size: 40px;
        letter-spacing: -2px;
    }

    .lingua-hero-description {
        font-size: 14px;
    }

    .translation-output {
        min-height: 210px;
    }

    div[data-testid="stTextArea"] textarea {
        min-height: 210px !important;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


st.html(
    """
    <div class="lingua-header">

        <div class="lingua-brand">

            <div class="lingua-logo">
                L
            </div>

            <div>

                <div class="lingua-name">
                    LinguaFlow
                </div>

                <div class="lingua-subtitle">
                    Language Translation Tool
                </div>

            </div>

        </div>

        <div class="lingua-status">

            <span class="lingua-status-dot"></span>

            <span>
                Translation ready
            </span>

        </div>

    </div>
    """
)


st.html(
    """
    <div class="lingua-hero">

        <div class="lingua-hero-label">
            LANGUAGE TRANSLATION
        </div>

        <h1 class="lingua-hero-title">
            Translate without
            <span>boundaries.</span>
        </h1>

        <div class="lingua-hero-description">
            Translate text between supported languages quickly
            and clearly, with automatic language detection
            and a simple workspace designed for everyday use.
        </div>

    </div>
    """
)


source_col, swap_col, target_col = st.columns(
    [5, 1, 5],
    vertical_alignment="bottom",
)


with source_col:

    st.html(
        """
        <div class="language-label">
            FROM
        </div>
        """
    )

    st.selectbox(
        "Source language",
        ["✨ Auto-detect"],
        disabled=True,
        label_visibility="collapsed",
    )

    if st.session_state.detected_language:

        detected_name = html.escape(
            st.session_state.detected_language
        )

        st.html(
            f"""
            <div class="detected-language">

                <span class="detected-language-dot"></span>

                <span>
                    Detected: {detected_name}
                </span>

            </div>
            """
        )


with swap_col:

    st.html("<div style='height:24px'></div>")

    st.button (
        "⇄",
        use_container_width=True,
        help="Swap translation direction",
        on_click=swap_callback,
    )


with target_col:

    st.html(
        """
        <div class="language-label">
            TO
        </div>
        """
    )

    language_list = list(LANGUAGES.keys())

    current_target = st.session_state.target_language

    if current_target not in language_list:

        current_target = language_list[0]

        st.session_state.target_language = (
            current_target
        )

    target_language = st.selectbox(
        "Target language",
        language_list,
        index=language_list.index(
            current_target
        ),
        key="target_language",
        label_visibility="collapsed",
    )


input_col, output_col = st.columns(
    2,
    gap="large",
)


with input_col:

    st.html(
        """
        <div class="language-label">
            ORIGINAL TEXT
        </div>
        """
    )

    source_text = st.text_area(
        "Original text",
        placeholder=(
            "Type or paste the text you want to translate..."
        ),
        height=260,
        key="translation_input",
        label_visibility="collapsed",
    )

    st.html(
        f"""
        <div class="stats-line">
            {len(source_text):,} characters ·
            {count_words(source_text):,} words
        </div>
        """
    )


if source_text.strip():

    try:

        detected_code = language_detector.detect(
            source_text
        )

        detected_name = LANGUAGE_NAMES.get(
            detected_code
        )

        supported_codes = set(
            LANGUAGES.values()
        )

        if (
            detected_name
            and detected_code in supported_codes
        ):

            st.session_state.detected_code = (
                detected_code
            )

            st.session_state.detected_language = (
                detected_name
            )

        else:

            st.session_state.detected_code = None
            st.session_state.detected_language = None

    except (
        LanguageDetectionError,
        ValueError,
    ):

        st.session_state.detected_code = None
        st.session_state.detected_language = None

else:

    st.session_state.detected_code = None
    st.session_state.detected_language = None


with output_col:

    st.html(
        """
        <div class="language-label">
            TRANSLATION
        </div>
        """
    )

    if st.session_state.translated_text:

        safe_translation = html.escape(
            st.session_state.translated_text
        )

        st.html(
            f"""
            <div class="translation-output">
                {safe_translation}
            </div>
            """
        )

        st.html(
            f"""
            <div class="stats-line">
                {len(st.session_state.translated_text):,}
                characters ·
                {count_words(st.session_state.translated_text):,}
                words
            </div>
            """
        )

    else:

        st.html(
            """
            <div class="translation-output">

                <span class="translation-placeholder">
                    Your translation will appear here...
                </span>

            </div>
            """
        )


st.html(
    """
    <div
        style="
            max-width:1080px;
            margin:10px auto 0 auto;
        "
    >
        <div class="feature-caption">
            🎤 Voice input uses your browser's speech
            recognition. After speaking, copy the recognized
            text into the original text box.
        </div>
    </div>
    """
)

components.html(
    """
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            background: transparent;
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        .voice-button {
            width: 100%;
            min-height: 42px;

            border: 1px solid #d1d5db;
            border-radius: 9px;

            background: #ffffff;
            color: #374151;

            font-size: 13px;
            font-weight: 700;

            cursor: pointer;
        }

        .voice-button:hover {
            background: #f8fbff;
            border-color: #93c5fd;
            color: #2563eb;
        }

        .voice-button.active {
            background: #fef2f2;
            border-color: #fecaca;
            color: #dc2626;
        }

        .voice-status {
            margin-top: 5px;
            color: #9ca3af;
            font-size: 11px;
            text-align: center;
        }
    </style>

    <button
        id="voiceButton"
        class="voice-button"
        type="button"
    >
        🎤 Voice input
    </button>

    <div
        id="voiceStatus"
        class="voice-status"
    >
        Click to speak
    </div>

    <script>
        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        const button =
            document.getElementById("voiceButton");

        const status =
            document.getElementById("voiceStatus");

        if (!SpeechRecognition) {

            button.disabled = true;
            button.textContent =
                "🎤 Voice input unavailable";

            status.textContent =
                "Use Chrome or Edge for voice input.";

        } else {

            const recognition =
                new SpeechRecognition();

            recognition.continuous = false;
            recognition.interimResults = false;

            button.onclick = function () {

                try {

                    recognition.start();

                    button.classList.add("active");

                    button.textContent =
                        "⏹ Listening...";

                    status.textContent =
                        "Speak now";

                } catch (error) {

                    status.textContent =
                        "Microphone is already active.";

                }

            };

            recognition.onresult = function (event) {

                const transcript =
                    event.results[0][0].transcript;

                navigator.clipboard.writeText(
                    transcript
                ).then(
                    function () {

                        status.textContent =
                            "Recognized text copied. "
                            + "Paste it into Original Text.";

                    }
                ).catch(
                    function () {

                        status.textContent =
                            transcript;

                    }
                );
            };

            recognition.onerror = function () {

                status.textContent =
                    "Voice recognition failed.";

            };

            recognition.onend = function () {

                button.classList.remove("active");

                button.textContent =
                    "🎤 Voice input";

            };
        }
    </script>
    """,
    height=72,
    scrolling=False,
)


translate_col, clear_col = st.columns(
    [5, 1]
)


with translate_col:

    with st.form(
        "translation_form",
        clear_on_submit=False,
    ):

        submitted = st.form_submit_button(
            "Translate",
            use_container_width=True,
        )


with clear_col:

    clear_clicked = st.button(
        "Clear",
        use_container_width=True,
        on_click=clear_workspace_callback,
        key="clear_workspace",
    )


if submitted:

    if not source_text.strip():

        st.warning(
            "Please enter some text to translate."
        )

    elif not st.session_state.detected_code:

        st.warning(
            "Unable to detect the language. "
            "Try entering a longer sentence."
        )

    else:

        source_code = (
            st.session_state.detected_code
        )

        target_code = LANGUAGES.get(
            target_language
        )

        if not target_code:

            st.error(
                "The selected target language "
                "is not available."
            )

        elif source_code == target_code:

            translated = source_text.strip()

            st.session_state.translated_text = (
                translated
            )

            st.session_state.last_source_code = (
                source_code
            )

            st.session_state.last_target_code = (
                target_code
            )

            add_history(
                source_text,
                translated,
                source_code,
                target_code,
            )

            st.rerun()

        else:

            with st.spinner(
                "Translating..."
            ):

                try:

                    translated = translator.translate(
                        text=source_text,
                        source_language=source_code,
                        target_language=target_code,
                    )

                    st.session_state.translated_text = (
                        translated
                    )

                    st.session_state.last_source_code = (
                        source_code
                    )

                    st.session_state.last_target_code = (
                        target_code
                    )

                    add_history(
                        source_text,
                        translated,
                        source_code,
                        target_code,
                    )

                    st.rerun()

                except TranslationError as exc:

                    print(f"[LinguaFlow] Translation error: {exc}")

                    st.error(
                        "Translation unavailable. "
                        "Please try again or choose another language."
                    )

                except Exception as exc:

                    st.error(
                        f"Translation failed: {exc}"
                    )


if st.session_state.translated_text:

    st.html(
        """
        <div
            style="
                max-width:1080px;
                margin:12px auto 0 auto;
            "
        >
            <span class="character-count">
                Translation complete
            </span>
        </div>
        """
    )

    translation_to_copy = str(
        st.session_state.translated_text
    )

    source_to_copy = str(
        st.session_state.translation_input
    )

    target_code_for_speech = (
        st.session_state.last_target_code
        or language_code_from_name(target_language)
        or "en"
    )

    # --------------------------------------------------------
    # ACTION ROW 1
    # --------------------------------------------------------

    action_col1, action_col2, action_col3 = st.columns(
        3
    )


    # --------------------------------------------------------
    # --------------------------------------------------------

    with action_col1:

        js_text = json.dumps(
            translation_to_copy,
            ensure_ascii=False,
        )

        components.html(
            f"""
            <style>

                * {{
                    box-sizing: border-box;
                }}

                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}

                .action-button {{
                    width: 100%;
                    min-height: 42px;

                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 7px;

                    background: #ffffff;

                    border: 1px solid #d1d5db;

                    border-radius: 9px;

                    color: #374151;

                    font-size: 13px;
                    font-weight: 700;

                    cursor: pointer;
                }}

                .action-button:hover {{
                    background: #f8fbff;
                    border-color: #93c5fd;
                    color: #2563eb;
                }}

            </style>

            <button
                id="copyTranslation"
                class="action-button"
                type="button"
            >
                📋 Copy translation
            </button>

            <script>

                const text =
                    {js_text};

                const button =
                    document.getElementById(
                        "copyTranslation"
                    );

                button.onclick =
                    async function () {{

                    try {{

                        await navigator.clipboard.writeText(
                            text
                        );

                        button.textContent =
                            "✓ Copied!";

                        setTimeout(
                            function () {{
                                button.textContent =
                                    "📋 Copy translation";
                            }},
                            1600
                        );

                    }} catch (error) {{

                        button.textContent =
                            "Copy failed";

                    }}

                }};

            </script>
            """,
            height=48,
            scrolling=False,
        )


    # --------------------------------------------------------
    # --------------------------------------------------------

    with action_col2:

        speech_text = json.dumps(
            translation_to_copy,
            ensure_ascii=False,
        )

        speech_lang = json.dumps(
            target_code_for_speech,
        )

        components.html(
            f"""
            <style>
                * {{ box-sizing: border-box; }}
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}
                .listen-wrap {{
                    display: flex;
                    gap: 6px;
                }}
                #listen {{
                    flex: 1;
                    min-height: 42px;
                }}
                #speed {{
                    width: 95px;
                    min-height: 42px;
                    padding: 0 8px;
                    border: 1px solid #d1d5db;
                    border-radius: 9px;
                    background: #ffffff;
                    color: #374151;
                    font-size: 13px;
                    font-weight: 700;
                }}
                button {{
                    min-height: 42px;
                    border: 1px solid #d1d5db;
                    border-radius: 9px;
                    background: #ffffff;
                    color: #374151;
                    font-size: 13px;
                    font-weight: 700;
                    cursor: pointer;
                }}
                button:hover,
                #speed:hover {{
                    background: #f8fbff;
                    border-color: #93c5fd;
                    color: #2563eb;
                }}
            </style>

            <div class="listen-wrap">
                <button id="listen" type="button">🔊 Listen</button>

                <select id="speed">
                    <option value="0.75">0.75x</option>
                    <option value="1" selected>1x</option>
                    <option value="1.25">1.25x</option>
                    <option value="1.5">1.5x</option>
                </select>
            </div>

            <script>
                const speechText = {speech_text};
                const requestedLanguage = {speech_lang};

                const listenButton = document.getElementById("listen");
                const speedSelect = document.getElementById("speed");

                const languageMap = {{
                    "en": "en-US",
                    "hi": "hi-IN", "bn": "bn-IN", "mr": "mr-IN",
                    "gu": "gu-IN", "ur": "ur-IN", "pa": "pa-IN",
                    "as": "as-IN", "or": "or-IN", "ne": "ne-NP",
                    "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
                    "ml": "ml-IN",
                    "ar": "ar-SA", "es": "es-ES", "fr": "fr-FR",
                    "de": "de-DE", "it": "it-IT", "pt": "pt-PT",
                    "pt-br": "pt-BR", "ru": "ru-RU", "ja": "ja-JP",
                    "ko": "ko-KR", "zh-hans": "zh-CN", "zh-hant": "zh-TW",
                    "tr": "tr-TR", "nl": "nl-NL", "sv": "sv-SE",
                    "da": "da-DK", "fi": "fi-FI", "nb": "nb-NO",
                    "pl": "pl-PL", "cs": "cs-CZ", "ro": "ro-RO",
                    "el": "el-GR", "he": "he-IL", "th": "th-TH",
                    "vi": "vi-VN", "id": "id-ID", "ms": "ms-MY",
                    "tl": "fil-PH", "sw": "sw-KE", "ga": "ga-IE",
                    "hu": "hu-HU", "uk": "uk-UA", "fa": "fa-IR",
                    "bg": "bg-BG", "ca": "ca-ES", "eu": "eu-ES",
                    "et": "et-EE", "lv": "lv-LV", "lt": "lt-LT",
                    "sk": "sk-SK", "sl": "sl-SI", "sq": "sq-AL",
                    "az": "az-AZ", "ky": "ky-KG"
                }};

                function getSpeechLocale(code) {{
                    const normalized = String(code || "en").toLowerCase();
                    return languageMap[normalized] || normalized;
                }}

                function findVoice(locale) {{
                    const voices = window.speechSynthesis.getVoices();
                    if (!voices.length) return null;

                    const wanted = locale.toLowerCase();
                    const family = wanted.split("-")[0];

                    return (
                        voices.find(v =>
                            v.lang &&
                            v.lang.toLowerCase() === wanted
                        ) ||
                        voices.find(v =>
                            v.lang &&
                            v.lang.toLowerCase().split("-")[0] === family
                        ) ||
                        null
                    );
                }}

                function stopSpeech() {{
                    window.speechSynthesis.cancel();
                    listenButton.textContent = "🔊 Listen";
                }}

                listenButton.onclick = function () {{
                    if (!("speechSynthesis" in window)) {{
                        listenButton.textContent = "Not supported";
                        return;
                    }}

                    if (!speechText.trim()) return;

                    if (window.speechSynthesis.speaking) {{
                        stopSpeech();
                        return;
                    }}

                    window.speechSynthesis.cancel();

                    const locale = getSpeechLocale(requestedLanguage);
                    const utterance = new SpeechSynthesisUtterance(speechText);
                    const voice = findVoice(locale);

                    utterance.lang = locale;
                    utterance.rate = Number(speedSelect.value);
                    utterance.pitch = 1;

                    if (voice) {{
                        utterance.voice = voice;
                        utterance.lang = voice.lang;
                    }}

                    utterance.onstart = function () {{
                        listenButton.textContent = "⏹ Stop";
                    }};

                    utterance.onend = function () {{
                        listenButton.textContent = "🔊 Listen";
                    }};

                    utterance.onerror = function () {{
                        listenButton.textContent = "🔊 Listen";
                    }};

                    window.speechSynthesis.speak(utterance);
                }};

                window.speechSynthesis.onvoiceschanged = function () {{
                    window.speechSynthesis.getVoices();
                }};
            </script>
            """,
            height=48,
            scrolling=False,
        )


    # --------------------------------------------------------
    # --------------------------------------------------------

    with action_col3:

        st.download_button(
            "⬇ Download",
            data=translation_to_copy,
            file_name="linguaflow_translation.txt",
            mime="text/plain",
            use_container_width=True,
        )


    # --------------------------------------------------------
    # ACTION ROW 2
    # --------------------------------------------------------

    action_col4, action_col5, action_col6 = st.columns(
        3
    )


    # --------------------------------------------------------
    # --------------------------------------------------------

    with action_col4:

        original_js = json.dumps(
            source_to_copy,
            ensure_ascii=False,
        )

        components.html(
            f"""
            <style>

                * {{
                    box-sizing: border-box;
                }}

                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}

                button {{
                    width: 100%;
                    min-height: 42px;

                    border: 1px solid #d1d5db;
                    border-radius: 9px;

                    background: #ffffff;
                    color: #374151;

                    font-size: 13px;
                    font-weight: 700;

                    cursor: pointer;
                }}

                button:hover {{
                    background: #f8fbff;
                    border-color: #93c5fd;
                    color: #2563eb;
                }}

            </style>

            <button id="copyOriginal">
                📋 Copy original
            </button>

            <script>

                const original =
                    {original_js};

                const button =
                    document.getElementById(
                        "copyOriginal"
                    );

                button.onclick =
                    async function () {{

                    try {{

                        await navigator.clipboard.writeText(
                            original
                        );

                        button.textContent =
                            "✓ Copied!";

                        setTimeout(
                            function () {{
                                button.textContent =
                                    "📋 Copy original";
                            }},
                            1600
                        );

                    }} catch (error) {{

                        button.textContent =
                            "Copy failed";

                    }}

                }};

            </script>
            """,
            height=48,
            scrolling=False,
        )


    # --------------------------------------------------------
    # --------------------------------------------------------

    with action_col5:

        current_source = (
            st.session_state.translation_input
        )

        current_translation = (
            st.session_state.translated_text
        )

        already_favorite = any(
            item["source_text"] == current_source
            and item["translated_text"]
            == current_translation
            for item in st.session_state.favorites
        )

        if st.button(
            "★ Favorited"
            if already_favorite
            else "☆ Favorite",
            use_container_width=True,
            key="favorite_current",
        ):

            favorite_item = {
                "source_text": current_source,
                "translated_text": current_translation,
                "source_code": (
                    st.session_state.last_source_code
                ),
                "target_code": (
                    st.session_state.last_target_code
                ),
                "source_language": language_name_from_code(
                    st.session_state.last_source_code
                    or ""
                ),
                "target_language": language_name_from_code(
                    st.session_state.last_target_code
                    or ""
                ),
            }

            if already_favorite:

                st.session_state.favorites = [
                    item
                    for item
                    in st.session_state.favorites
                    if not (
                        item["source_text"]
                        == current_source
                        and item["translated_text"]
                        == current_translation
                    )
                ]

            else:

                st.session_state.favorites.insert(
                    0,
                    favorite_item,
                )

            st.rerun()


    # --------------------------------------------------------
    # --------------------------------------------------------

    with action_col6:

        st.button(
            "Clear translation",
            use_container_width=True,
            key="clear_result",
            on_click=clear_result_callback,
        )


st.html(
    """
    <div
        style="
            max-width:1080px;
            margin:35px auto 0 auto;
        "
    >

        <div class="language-label">
            POPULAR LANGUAGES
        </div>

    </div>
    """
)


popular_languages = [
    "English",
    "Hindi",
    "Bengali",
    "Urdu",
    "Spanish",
    "French",
]


popular_columns = st.columns(
    len(popular_languages)
)


for column, language in zip(
    popular_columns,
    popular_languages,
):

    with column:

        if language in language_list:

            st.button(
                language,
                use_container_width=True,
                key=f"popular_{language}",
                on_click=set_target_language,
                args=(language,),
            )


st.html(
    """
    <div
        style="
            max-width:1080px;
            margin:45px auto 0 auto;
        "
    >

        <div class="language-label">
            TRANSLATION HISTORY
        </div>

    </div>
    """
)


history_count = len(
    st.session_state.translation_history
)

favorite_count = len(
    st.session_state.favorites
)


history_top1, history_top2, history_top3 = st.columns(
    [4, 2, 2]
)


with history_top1:

    st.caption(
        f"{history_count} translation"
        + ("s" if history_count != 1 else "")
        + f" · {favorite_count} favorite"
        + ("s" if favorite_count != 1 else "")
    )


with history_top2:

    if history_count:

        if st.button(
            "Show / Hide",
            use_container_width=True,
            key="toggle_history",
        ):

            st.session_state.history_open = (
                not st.session_state.history_open
            )

            st.rerun()


with history_top3:

    if history_count:

        if st.button(
            "Clear history",
            use_container_width=True,
            key="clear_history",
        ):

            st.session_state.translation_history = []

            st.rerun()


if st.session_state.history_open:

    if not st.session_state.translation_history:

        st.info(
            "No translation history yet."
        )

    else:

        for index, item in enumerate(
            st.session_state.translation_history
        ):

            source_name = html.escape(
                item["source_language"]
            )

            target_name = html.escape(
                item["target_language"]
            )

            safe_source = html.escape(
                item["source_text"]
            )

            safe_translation = html.escape(
                item["translated_text"]
            )

            st.html(
                f"""
                <div class="history-card">

                    <div class="history-meta">
                        {source_name}
                        →
                        {target_name}
                    </div>

                    <div class="history-source">
                        {safe_source}
                    </div>

                    <div class="history-translation">
                        {safe_translation}
                    </div>

                </div>
                """
            )

            h1, h2, h3, h4 = st.columns(
                [2, 2, 2, 2]
            )


            # ------------------------------------------------
            # ------------------------------------------------

            with h1:

                st.button(
                   "↩ Reuse",
                   key=f"reuse_{index}",
                   use_container_width=True,
                   on_click=reuse_history_callback,
                   args=(index,),
                )
            # ------------------------------------------------
            # ------------------------------------------------

            with h2:

                history_copy = json.dumps(
                    item["translated_text"],
                    ensure_ascii=False,
                )

                components.html(
                    f"""
                    <button
                        id="historyCopy{index}"
                        style="
                            width:100%;
                            min-height:42px;
                            border:1px solid #d1d5db;
                            border-radius:9px;
                            background:#ffffff;
                            color:#374151;
                            font-size:13px;
                            font-weight:700;
                            cursor:pointer;
                        "
                    >
                        📋 Copy
                    </button>

                    <script>

                    const historyText =
                        {history_copy};

                    const historyButton =
                        document.getElementById(
                            "historyCopy{index}"
                        );

                    historyButton.onclick =
                        async function () {{

                        try {{

                            await navigator.clipboard.writeText(
                                historyText
                            );

                            historyButton.textContent =
                                "✓ Copied!";

                            setTimeout(
                                function () {{
                                    historyButton.textContent =
                                        "📋 Copy";
                                }},
                                1200
                            );

                        }} catch (error) {{

                            historyButton.textContent =
                                "Copy failed";

                        }}

                    }};

                    </script>
                    """,
                    height=48,
                    scrolling=False,
                )


            # ------------------------------------------------
            # ------------------------------------------------

            with h3:

                history_text = json.dumps(
                    item["translated_text"],
                    ensure_ascii=False,
                )

                history_lang = json.dumps(
                    item["target_code"] or "en"
                )

                components.html(
                    f"""
                    <button
                        id="historyListen{index}"
                        style="
                            width:100%;
                            min-height:42px;
                            border:1px solid #d1d5db;
                            border-radius:9px;
                            background:#ffffff;
                            color:#374151;
                            font-size:13px;
                            font-weight:700;
                            cursor:pointer;
                        "
                    >🔊 Listen</button>

                    <script>
                        const historySpeech{index} = {history_text};
                        const historyLang{index} = {history_lang};
                        const historyButton{index} =
                            document.getElementById("historyListen{index}");

                        const historyLanguageMap{index} = {{
                            "en":"en-US","hi":"hi-IN","bn":"bn-IN","mr":"mr-IN",
                            "gu":"gu-IN","ur":"ur-IN","pa":"pa-IN","as":"as-IN",
                            "or":"or-IN","ne":"ne-NP","ta":"ta-IN","te":"te-IN",
                            "kn":"kn-IN","ml":"ml-IN","ar":"ar-SA","es":"es-ES",
                            "fr":"fr-FR","de":"de-DE","it":"it-IT","pt":"pt-PT",
                            "pt-br":"pt-BR","ru":"ru-RU","ja":"ja-JP","ko":"ko-KR",
                            "zh-hans":"zh-CN","zh-hant":"zh-TW","tr":"tr-TR",
                            "nl":"nl-NL","sv":"sv-SE","da":"da-DK","fi":"fi-FI",
                            "nb":"nb-NO","pl":"pl-PL","cs":"cs-CZ","ro":"ro-RO",
                            "el":"el-GR","he":"he-IL","th":"th-TH","vi":"vi-VN",
                            "id":"id-ID","ms":"ms-MY","tl":"fil-PH","sw":"sw-KE",
                            "ga":"ga-IE","hu":"hu-HU","uk":"uk-UA","fa":"fa-IR",
                            "bg":"bg-BG","ca":"ca-ES","eu":"eu-ES","et":"et-EE",
                            "lv":"lv-LV","lt":"lt-LT","sk":"sk-SK","sl":"sl-SI",
                            "sq":"sq-AL","az":"az-AZ","ky":"ky-KG"
                        }};

                        historyButton{index}.onclick = function () {{
                            window.speechSynthesis.cancel();

                            const code = String(historyLang{index} || "en").toLowerCase();
                            const locale =
                                historyLanguageMap{index}[code] || code;

                            const utterance =
                                new SpeechSynthesisUtterance(historySpeech{index});

                            utterance.lang = locale;
                            utterance.rate = 1;

                            const voices =
                                window.speechSynthesis.getVoices();

                            const family = locale.split("-")[0];

                            const voice =
                                voices.find(v =>
                                    v.lang &&
                                    v.lang.toLowerCase() === locale.toLowerCase()
                                ) ||
                                voices.find(v =>
                                    v.lang &&
                                    v.lang.toLowerCase().split("-")[0] === family
                                );

                            if (voice) {{
                                utterance.voice = voice;
                                utterance.lang = voice.lang;
                            }}

                            window.speechSynthesis.speak(utterance);
                        }};
                    </script>
                    """,
                    height=48,
                    scrolling=False,
                )


            # ------------------------------------------------
            # ------------------------------------------------

            with h4:

                is_favorite = any(
                    fav["source_text"]
                    == item["source_text"]
                    and fav["translated_text"]
                    == item["translated_text"]
                    for fav
                    in st.session_state.favorites
                )

                if st.button(
                    "★ Saved"
                    if is_favorite
                    else "☆ Save",
                    key=f"save_history_{index}",
                    use_container_width=True,
                ):

                    if is_favorite:

                        st.session_state.favorites = [
                            fav
                            for fav
                            in st.session_state.favorites
                            if not (
                                fav["source_text"]
                                == item["source_text"]
                                and fav["translated_text"]
                                == item[
                                    "translated_text"
                                ]
                            )
                        ]

                    else:

                        st.session_state.favorites.append(
                            item.copy()
                        )

                    st.rerun()


if st.session_state.favorites:

    st.html(
        """
        <div
            style="
                max-width:1080px;
                margin:30px auto 0 auto;
            "
        >

            <div class="language-label">
                FAVORITES
            </div>

        </div>
        """
    )

    for index, item in enumerate(
        st.session_state.favorites
    ):

        st.html(
            f"""
            <div class="history-card">

                <div class="history-meta">
                    {html.escape(item["source_language"])}
                    →
                    {html.escape(item["target_language"])}
                </div>

                <div class="history-source">
                    {html.escape(item["source_text"])}
                </div>

                <div class="history-translation">
                    {html.escape(item["translated_text"])}
                </div>

            </div>
            """
        )


st.html(
    """
    <div class="info-section">

        <div class="info-title">
            Simple translation, focused on the text.
        </div>

        <div class="info-text">
          Created by Nabin chettri.
          Do follow me on LINKEDIN.
        </div>

    </div>
    """
)


st.html(
    """
    <div class="lingua-footer">
        LinguaFlow · Language made simple
    </div>
    """
)