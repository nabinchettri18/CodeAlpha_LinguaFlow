from langdetect import detect, LangDetectException


class LanguageDetectionError(Exception):
    """Raised when language detection fails."""
    pass


class LanguageDetector:
    """Detects the language of text locally."""

    def detect(self, text):
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        try:
            return detect(text.strip())

        except LangDetectException as exc:
            raise LanguageDetectionError(
                "Unable to detect the language."
            ) from exc
        