import requests


class TranslationError(Exception):
    """Raised when translation fails."""
    pass


class Translator:
    """
    Local LibreTranslate client.

    LibreTranslate runs locally and exposes
    a REST API on localhost.
    """

    def __init__(
        self,
        base_url="http://127.0.0.1:5000",
    ):
        self.base_url = base_url.rstrip("/")

    def translate(
        self,
        text,
        source_language,
        target_language,
    ):
        """
        Translate text using local LibreTranslate.
        """

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        if not source_language:
            raise ValueError(
                "Source language is required."
            )

        if not target_language:
            raise ValueError(
                "Target language is required."
            )

        if source_language == target_language:
            return text.strip()

        payload = {
            "q": text.strip(),
            "source": source_language,
            "target": target_language,
            "format": "text",
        }

        try:
            response = requests.post(
                f"{self.base_url}/translate",
                json=payload,
                timeout=30,
            )

            response.raise_for_status()

            response.encoding = "utf-8"

            data = response.json()

            translated_text = data.get(
                "translatedText"
            )

            if not translated_text:
                raise TranslationError(
                    "Translation service returned "
                    "an empty response."
                )

            return translated_text

        except requests.RequestException as exc:
            raise TranslationError(
                "Unable to connect to the local "
                "translation service. Make sure "
                "LibreTranslate is running."
            ) from exc

        except ValueError as exc:
            raise TranslationError(
                "The translation service returned "
                "an invalid response."
            ) from exc