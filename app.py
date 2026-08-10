import html
import json

import streamlit as st
import streamlit.components.v1 as components

from src.translator import Translator, TranslationError
from src.languages import LANGUAGES
from src.language_detector import (
    LanguageDetector,
    LanguageDetectionError,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LinguaFlow",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# LANGUAGE NAMES
# ============================================================

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


# ============================================================
# SESSION STATE
# ============================================================

if "translation_input" not in st.session_state:
    st.session_state.translation_input = ""

if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""

if "detected_code" not in st.session_state:
    st.session_state.detected_code = None

if "detected_language" not in st.session_state:
    st.session_state.detected_language = None

if "target_language" not in st.session_state:

    if "English" in LANGUAGES:
        st.session_state.target_language = "English"
    else:
        st.session_state.target_language = list(
            LANGUAGES.keys()
        )[0]

if "translation_history" not in st.session_state:
    st.session_state.translation_history = []


# ============================================================
# SERVICES
# ============================================================

@st.cache_resource
def load_translator():
    return Translator()


@st.cache_resource
def load_language_detector():
    return LanguageDetector()


translator = load_translator()
language_detector = load_language_detector()


# ============================================================
# INPUT VALIDATION
# ============================================================

def is_meaningful_text(text):
    """
    Reject obvious gibberish while allowing short
    valid words such as "Hi", "Hello", "Yes", etc.
    """

    text = text.strip()

    if not text:
        return False

    # Remove whitespace for analysis
    compact_text = "".join(
        char
        for char in text
        if not char.isspace()
    )

    # Count alphabetic/unicode letters
    letters = sum(
        1
        for char in compact_text
        if char.isalpha()
    )

    # A short word can still be valid.
    # Examples: Hi, Yes, No, OK
    if len(compact_text) <= 5:

        return letters >= 2

    # Longer text needs a reasonable amount
    # of actual alphabetic content.
    if letters < 3:
        return False

    # Reject symbol/number-heavy input.
    if letters / len(compact_text) < 0.30:
        return False

    return True

# ============================================================
# CSS
# ============================================================

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
   WARNING / ERROR
   ========================================================== */

div[data-testid="stAlert"] {

    background: #eff6ff !important;

    border: 1px solid #bfdbfe !important;

    border-radius: 10px !important;
}

div[data-testid="stAlert"] p {

    color: #1d4ed8 !important;

    font-size: 13px !important;

    font-weight: 600 !important;
}


/* ==========================================================
   TRANSLATION HISTORY
   ========================================================== */

.history-section {

    max-width: 1080px;

    margin: 45px auto 0 auto;
}

.history-title {

    color: #111827;

    font-size: 18px;

    font-weight: 750;

    margin-bottom: 14px;
}

.history-card {

    max-width: 1080px;

    padding: 16px;

    margin: 0 auto 10px auto;

    background: #ffffff;

    border: 1px solid #e5e7eb;

    border-radius: 12px;

    box-shadow:
        0 1px 2px rgba(0, 0, 0, 0.03);
}

.history-language {

    color: #2563eb;

    font-size: 12px;

    font-weight: 750;

    margin-bottom: 8px;
}

.history-language span {

    color: #9ca3af;

    margin: 0 6px;
}

.history-original {

    color: #6b7280;

    font-size: 13px;

    margin-bottom: 6px;
}

.history-translation {

    color: #111827;

    font-size: 14px;

    font-weight: 650;

    line-height: 1.6;

    overflow-wrap: break-word;
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


# ============================================================
# HEADER
# ============================================================

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


# ============================================================
# HERO
# ============================================================

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


# ============================================================
# LANGUAGE CONTROLS
# ============================================================

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

    swap_clicked = st.button(
        "⇄",
        use_container_width=True,
        help="Swap translation direction",
        key="swap_language_button",
    )


with target_col:

    st.html(
        """
        <div class="language-label">
            TO
        </div>
        """
    )

    language_list = list(
        LANGUAGES.keys()
    )

    current_target = (
        st.session_state.target_language
    )

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


# ============================================================
# INPUT / OUTPUT
# ============================================================

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
        <div class="character-count">
            {len(source_text):,} characters
        </div>
        """
    )


# ============================================================
# AUTO LANGUAGE DETECTION
# ============================================================

if (
    source_text.strip()
    and is_meaningful_text(source_text)
):

    try:

        detected_code = (
            language_detector.detect(
                source_text
            )
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


# ============================================================
# SWAP
# ============================================================

if swap_clicked:

    detected_code = (
        st.session_state.detected_code
    )

    detected_name = (
        st.session_state.detected_language
    )

    if not detected_code or not detected_name:

        st.warning(
            "Enter some text first so LinguaFlow "
            "can detect the language."
        )

    elif detected_name not in language_list:

        st.warning(
            "The detected language is not available "
            "as a target language."
        )

    else:

        # Store swap values first.
        swapped_text = (
            st.session_state.translated_text
        )

        if swapped_text:

            st.session_state.translation_input = (
                swapped_text
            )

            st.session_state.translated_text = ""

        st.session_state.target_language = (
            detected_name
        )

        st.rerun()


# ============================================================
# ACTION ROW
# ============================================================

with st.form(
    "translation_form",
    clear_on_submit=False,
):

    submitted = st.form_submit_button(
        "Translate",
        use_container_width=True,
    )


# ============================================================
# TRANSLATION
# ============================================================

if submitted:

    # --------------------------------------------------------
    # EMPTY INPUT
    # --------------------------------------------------------

    if not source_text.strip():

        st.session_state.translated_text = ""

        st.warning(
            "Please enter some text to translate."
        )

    # --------------------------------------------------------
    # GIBBERISH / INVALID INPUT
    # --------------------------------------------------------

    elif not is_meaningful_text(source_text):

        st.session_state.translated_text = ""

        st.warning(
            "We couldn't understand this input. "
            "Please enter a meaningful word or sentence."
        )

    # --------------------------------------------------------
    # LANGUAGE NOT DETECTED
    # --------------------------------------------------------

    elif not st.session_state.detected_code:

        st.session_state.translated_text = ""

        st.warning(
            "Unable to detect the language. "
            "Try entering a longer sentence."
        )

    # --------------------------------------------------------
    # TRANSLATION
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # SAME LANGUAGE
        # ----------------------------------------------------

        elif source_code == target_code:

            translated = (
                source_text.strip()
            )

            st.session_state.translated_text = (
                translated
            )

            # Save to history
            st.session_state.translation_history.insert(
                0,
                {
                    "source_text": source_text.strip(),
                    "source_language": source_code,
                    "target_language": target_code,
                    "translated_text": translated,
                },
            )

            # Keep latest 10
            st.session_state.translation_history = (
                st.session_state.translation_history[:10]
            )

            st.rerun()

        # ----------------------------------------------------
        # LOCAL TRANSLATION SERVICE
        # ----------------------------------------------------

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

                    # ========================================
                    # SAVE SUCCESSFUL TRANSLATION
                    # ========================================

                    st.session_state.translation_history.insert(
                        0,
                        {
                            "source_text": source_text.strip(),
                            "source_language": source_code,
                            "target_language": target_code,
                            "translated_text": translated,
                        },
                    )

                    # Keep only latest 10
                    st.session_state.translation_history = (
                        st.session_state.translation_history[:10]
                    )

                    st.rerun()

                except TranslationError as exc:

                    st.session_state.translated_text = ""

                    st.error(str(exc))

                except Exception as exc:

                    st.session_state.translated_text = ""

                    st.error(
                        f"Translation failed: {exc}"
                    )


# ============================================================
# RESULT ACTIONS
# ============================================================

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

    js_text = json.dumps(
        translation_to_copy,
        ensure_ascii=False,
    )

    target_code = LANGUAGES.get(
        st.session_state.target_language,
        "en",
    )

    js_target_code = json.dumps(
        target_code,
        ensure_ascii=False,
    )

    # ========================================================
    # THREE BUTTONS IN ONE ROW
    # ========================================================

    action_col1, action_col2, action_col3 = st.columns(
        3,
        gap="small",
    )

    # ========================================================
    # COPY
    # ========================================================

    with action_col1:

        components.html(
            f"""
            <style>

                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}

                .action-button {{
                    width: 100%;
                    height: 42px;

                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 7px;

                    background: #ffffff;

                    border: 1px solid #d1d5db;

                    border-radius: 9px;

                    color: #374151;

                    font-family:
                        -apple-system,
                        BlinkMacSystemFont,
                        "Segoe UI",
                        sans-serif;

                    font-size: 13px;
                    font-weight: 700;

                    cursor: pointer;
                }}

                .action-button:hover {{
                    background: #f8fbff;
                    border-color: #93c5fd;
                    color: #2563eb;
                }}

                .success {{
                    background: #f0fdf4 !important;
                    border-color: #bbf7d0 !important;
                    color: #15803d !important;
                }}

            </style>

            <button
                id="copyButton"
                class="action-button"
                type="button"
            >
                📋 Copy
            </button>

            <script>

                const copyText = {js_text};

                const copyButton =
                    document.getElementById(
                        "copyButton"
                    );

                copyButton.onclick = async function () {{

                    let copied = false;

                    try {{

                        if (navigator.clipboard) {{

                            await navigator.clipboard.writeText(
                                copyText
                            );

                            copied = true;
                        }}

                    }} catch (error) {{

                        copied = false;

                    }}

                    if (!copied) {{

                        try {{

                            const textarea =
                                document.createElement(
                                    "textarea"
                                );

                            textarea.value =
                                copyText;

                            textarea.style.position =
                                "fixed";

                            textarea.style.left =
                                "-9999px";

                            document.body.appendChild(
                                textarea
                            );

                            textarea.focus();

                            textarea.select();

                            copied =
                                document.execCommand(
                                    "copy"
                                );

                            textarea.remove();

                        }} catch (error) {{

                            copied = false;

                        }}

                    }}

                    if (copied) {{

                        copyButton.classList.add(
                            "success"
                        );

                        copyButton.textContent =
                            "✓ Copied!";

                        setTimeout(
                            function () {{

                                copyButton.classList.remove(
                                    "success"
                                );

                                copyButton.textContent =
                                    "📋 Copy";

                            }},
                            1600
                        );

                    }}

                }};

            </script>
            """,
            height=48,
            scrolling=False,
        )

    # ========================================================
    # LISTEN
    # ========================================================

    with action_col2:

        components.html(
            f"""
            <style>

                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}

                .listen-button {{
                    width: 100%;
                    height: 42px;

                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 7px;

                    background: #ffffff;

                    border: 1px solid #d1d5db;

                    border-radius: 9px;

                    color: #374151;

                    font-family:
                        -apple-system,
                        BlinkMacSystemFont,
                        "Segoe UI",
                        sans-serif;

                    font-size: 13px;
                    font-weight: 700;

                    cursor: pointer;
                }}

                .listen-button:hover {{
                    background: #f8fbff;
                    border-color: #93c5fd;
                    color: #2563eb;
                }}

                .speaking {{
                    background: #eff6ff !important;
                    border-color: #bfdbfe !important;
                    color: #2563eb !important;
                }}

            </style>

            <button
                id="listenButton"
                class="listen-button"
                type="button"
            >
                🔊 Listen
            </button>

            <script>

                const speechText = {js_text};

                const speechLanguage =
                    {js_target_code};

                const listenButton =
                    document.getElementById(
                        "listenButton"
                    );

                let speaking = false;

                function stopSpeaking() {{

                    window.speechSynthesis.cancel();

                    speaking = false;

                    listenButton.classList.remove(
                        "speaking"
                    );

                    listenButton.textContent =
                        "🔊 Listen";
                }}

                listenButton.onclick = function () {{

                    if (
                        !("speechSynthesis" in window)
                    ) {{

                        listenButton.textContent =
                            "Not supported";

                        return;

                    }}

                    if (speaking) {{

                        stopSpeaking();

                        return;

                    }}

                    window.speechSynthesis.cancel();

                    const utterance =
                        new SpeechSynthesisUtterance(
                            speechText
                        );

                    utterance.lang =
                        speechLanguage;

                    utterance.rate = 0.95;

                    utterance.pitch = 1;

                    utterance.onstart =
                        function () {{

                            speaking = true;

                            listenButton.classList.add(
                                "speaking"
                            );

                            listenButton.textContent =
                                "⏹ Stop";

                        }};

                    utterance.onend =
                        function () {{

                            stopSpeaking();

                        }};

                    utterance.onerror =
                        function () {{

                            stopSpeaking();

                        }};

                    window.speechSynthesis.speak(
                        utterance
                    );

                }};

            </script>
            """,
            height=48,
            scrolling=False,
        )

    # ========================================================
    # CLEAR
    # ========================================================

    with action_col3:

        if st.button(
            "🗑️ Clear",
            use_container_width=True,
            key="clear_result_button",
        ):

            st.session_state.translated_text = ""

            st.rerun()


# ============================================================
# TRANSLATION HISTORY
# ============================================================

if st.session_state.translation_history:

    st.html(
        """
        <div class="history-section">

            <div class="history-title">
                Translation history
            </div>

        </div>
        """
    )

    for item in (
        st.session_state.translation_history
    ):

        source_name = LANGUAGE_NAMES.get(
            item["source_language"],
            item["source_language"],
        )

        target_name = LANGUAGE_NAMES.get(
            item["target_language"],
            item["target_language"],
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

                <div class="history-language">
                    {source_name}
                    <span>→</span>
                    {target_name}
                </div>

                <div class="history-original">
                    {safe_source}
                </div>

                <div class="history-translation">
                    {safe_translation}
                </div>

            </div>
            """
        )

    # ========================================================
    # CLEAR HISTORY
    # ========================================================

    if st.button(
        "Clear History",
        use_container_width=True,
        key="clear_history_button",
    ):

        st.session_state.translation_history = []

        st.rerun()


# ============================================================
# POPULAR LANGUAGES
# ============================================================

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
            )


# ============================================================
# INFORMATION
# ============================================================

st.html(
    """
    <div class="info-section">

        <div class="info-title">
            Simple translation, focused on the text.
        </div>

        <div class="info-text">
            LinguaFlow automatically detects the language
            of your text and translates it into your selected
            destination language using a local translation
            service.
        </div>

    </div>
    """
)


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="lingua-footer">
        LinguaFlow · Language made simple
    </div>
    """
)