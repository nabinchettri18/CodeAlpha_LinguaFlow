from langdetect import (
    DetectorFactory,
    detect_langs,
    LangDetectException,
)

DetectorFactory.seed = 0


class LanguageDetectionError(Exception):
    """Raised when language detection fails."""
    pass


class LanguageDetector:
    """
    Detect the language of user-provided text.

    Uses:
    1. Unicode/script detection
    2. Common English phrase detection
    3. Short informal English normalization
    4. langdetect for normal text
    5. Confidence protection
    """

    ENGLISH_HINTS = {
        "the",
        "and",
        "is",
        "are",
        "am",
        "you",
        "your",
        "how",
        "hello",
        "hi",
        "welcome",
        "to",
        "from",
        "what",
        "where",
        "when",
        "why",
        "who",
        "this",
        "that",
        "my",
        "me",
        "we",
        "they",
        "can",
        "will",
        "good",
        "morning",
        "evening",
        "night",
        "india",
        "language",
        "please",
        "thank",
        "thanks",
    }

    # Common informal/typo English inputs.
    # These are intentionally limited to very common cases.
    SHORT_ENGLISH = {
        "hlo": "en",
        "helo": "en",
        "helloo": "en",
        "hellooo": "en",
        "hii": "en",
        "hiii": "en",
        "heyy": "en",
        "heyyy": "en",
        "hru": "en",
        "hwru": "en",
        "gm": "en",
        "gud": "en",
        "gudmorning": "en",
        "thx": "en",
        "ty": "en",
        "tnx": "en",
        "pls": "en",
        "plz": "en",
        "u": "en",
        "ur": "en",
        "ya": "en",
        "yo": "en",
    }

    @staticmethod
    def _detect_script(text: str):
        """
        Detect languages that have distinctive Unicode scripts.
        """

        for char in text:

            code = ord(char)

            # Devanagari
            if 0x0900 <= code <= 0x097F:
                return "hi"

            # Bengali
            if 0x0980 <= code <= 0x09FF:
                return "bn"

            # Gurmukhi
            if 0x0A00 <= code <= 0x0A7F:
                return "pa"

            # Gujarati
            if 0x0A80 <= code <= 0x0AFF:
                return "gu"

            # Tamil
            if 0x0B80 <= code <= 0x0BFF:
                return "ta"

            # Telugu
            if 0x0C00 <= code <= 0x0C7F:
                return "te"

            # Kannada
            if 0x0C80 <= code <= 0x0CFF:
                return "kn"

            # Malayalam
            if 0x0D00 <= code <= 0x0D7F:
                return "ml"

            # Thai
            if 0x0E00 <= code <= 0x0E7F:
                return "th"

            # Hebrew
            if 0x0590 <= code <= 0x05FF:
                return "he"

            # Greek
            if 0x0370 <= code <= 0x03FF:
                return "el"

        return None

    def detect(self, text: str) -> str:
        """
        Detect and return an ISO language code.

        Raises:
            ValueError:
                If text is empty.

            LanguageDetectionError:
                If detection is not reliable.
        """

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        cleaned_text = text.strip()

        # --------------------------------------------------
        # 1. Unicode/script detection
        # --------------------------------------------------

        script_language = self._detect_script(
            cleaned_text
        )

        if script_language:
            return script_language

        # --------------------------------------------------
        # 2. Normalize words
        # --------------------------------------------------

        words = {
            word.strip(
                ".,!?;:\"'()[]{}"
            ).lower()
            for word in cleaned_text.split()
            if word.strip(
                ".,!?;:\"'()[]{}"
            )
        }

        # --------------------------------------------------
        # 3. Common short English inputs
        # --------------------------------------------------

        if len(words) == 1:

            single_word = next(iter(words))

            if single_word in self.SHORT_ENGLISH:
                return "en"

        # --------------------------------------------------
        # 4. English hints
        # --------------------------------------------------

        english_matches = (
            words & self.ENGLISH_HINTS
        )

        if len(english_matches) >= 2:
            return "en"

        if (
            len(words) == 1
            and english_matches
        ):
            return "en"

        # --------------------------------------------------
        # 5. Statistical detection
        # --------------------------------------------------

        try:

            results = detect_langs(
                cleaned_text
            )

        except LangDetectException as exc:

            raise LanguageDetectionError(
                "Unable to detect the language."
            ) from exc

        except Exception as exc:

            raise LanguageDetectionError(
                "Language detection failed."
            ) from exc

        if not results:

            raise LanguageDetectionError(
                "Unable to detect the language."
            )

        best = results[0]

        detected_code = best.lang
        confidence = best.prob

        # --------------------------------------------------
        # 6. Confidence protection
        # --------------------------------------------------

        character_count = sum(
            char.isalpha()
            for char in cleaned_text
        )

        # Very short text
        if character_count <= 3:

            if confidence < 0.90:

                raise LanguageDetectionError(
                    "Unable to confidently detect "
                    "the language. Please enter "
                    "a longer text."
                )

        # Short text
        elif character_count < 10:

            if confidence < 0.80:

                raise LanguageDetectionError(
                    "Unable to confidently detect "
                    "the language. Please enter "
                    "a longer text."
                )

        # Medium text
        elif character_count < 25:

            if confidence < 0.65:

                raise LanguageDetectionError(
                    "Language detection confidence "
                    "is too low. Please enter a "
                    "longer sentence."
                )

        # Longer text
        else:

            if confidence < 0.50:

                raise LanguageDetectionError(
                    "Language detection confidence "
                    "is too low."
                )

        return detected_code