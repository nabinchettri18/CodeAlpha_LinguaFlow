from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .translator import Translator


# ---------------------------------------------------------
# LinguaFlow API
# ---------------------------------------------------------

app = FastAPI(
    title="LinguaFlow API",
    description="Indian language translation API",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Translator
# ---------------------------------------------------------

translator = Translator()


# ---------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_language: str = "auto"
    target_language: str


class TranslationResponse(BaseModel):
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    provider: str


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "name": "LinguaFlow",
        "status": "online",
        "version": "1.0.0",
        "message": "LinguaFlow translation API is running.",
    }


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "provider_status": translator.get_provider_status(),
    }


# ---------------------------------------------------------
# Languages
# ---------------------------------------------------------

@app.get("/languages")
def languages():
    try:
        from .languages import LANGUAGES

        if isinstance(LANGUAGES, dict):
            return LANGUAGES

        return {
            "languages": LANGUAGES
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load languages: {exc}",
        )


# ---------------------------------------------------------
# Provider status
# ---------------------------------------------------------

@app.get("/providers")
def providers():
    return translator.get_provider_status()


# ---------------------------------------------------------
# Translation
# ---------------------------------------------------------

@app.post("/translate", response_model=TranslationResponse)
def translate(request: TranslationRequest):

    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    source = request.source_language.strip().lower()
    target = request.target_language.strip().lower()

    if not target:
        raise HTTPException(
            status_code=400,
            detail="Target language is required.",
        )

    try:

        # Automatic language detection
        if source == "auto":

            try:
                from .language_detector import detect_language

                detected = detect_language(text)

                if detected:
                    source = detected
                else:
                    source = "en"

            except Exception:
                # Safe default
                source = "en"

        translated = translator.translate(
            text,
            source,
            target,
        )

        return TranslationResponse(
            source_language=source,
            target_language=target,
            original_text=text,
            translated_text=translated,
            provider=translator.last_provider or "unknown",
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ---------------------------------------------------------
# Simple GET translation endpoint
# Useful for quick browser testing
# ---------------------------------------------------------

@app.get("/translate")
def translate_get(
    text: str,
    source: str = "en",
    target: str = "hi",
):

    try:

        translated = translator.translate(
            text,
            source,
            target,
        )

        return {
            "source_language": source,
            "target_language": target,
            "original_text": text,
            "translated_text": translated,
            "provider": translator.last_provider,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )