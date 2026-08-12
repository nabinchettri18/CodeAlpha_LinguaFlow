import hashlib
import os
import sqlite3
import time

import requests
from dotenv import load_dotenv

load_dotenv()


class TranslationError(Exception):
    """Raised when translation fails."""
    pass


class Translator:
    """
    LinguaFlow translation engine.

    Provider order:

        1. SQLite cache
        2. Gemini 2.5 Flash
        3. Gemini Flash-Lite
        4. NVIDIA Nemotron 3 Ultra

    VAK and LibreTranslate are intentionally removed.

    Gemini runs through the local Node.js service on port 8765.
    Nemotron uses NVIDIA's OpenAI-compatible cloud API.
    """

    # ==========================================================
    # CONFIGURATION
    # ==========================================================

    GEMINI_URL = os.getenv(
        "GEMINI_URL",
        "http://127.0.0.1:8765/translate",
    )

    GEMINI_HEALTH_URL = os.getenv(
        "GEMINI_HEALTH_URL",
        "http://127.0.0.1:8765/health",
    )

    GEMINI_PRIMARY_MODEL = os.getenv(
        "GEMINI_PRIMARY_MODEL",
        "gemini-2.5-flash",
    )

    GEMINI_FALLBACK_MODEL = os.getenv(
        "GEMINI_FALLBACK_MODEL",
        "gemini-3.1-flash-lite",
    )

    NVIDIA_URL = os.getenv(
        "NVIDIA_CHAT_URL",
        "https://integrate.api.nvidia.com/v1/chat/completions",
    )

    NEMOTRON_MODEL = os.getenv(
        "NEMOTRON_MODEL",
        "nvidia/nemotron-3-ultra-550b-a55b",
    )


    GEMINI_TIMEOUT = int(
        os.getenv("GEMINI_TIMEOUT", "60")
    )

    NEMOTRON_TIMEOUT = int(
        os.getenv("NEMOTRON_TIMEOUT", "60")
    )


    # Retry only transient Gemini network/5xx failures.
    # Quota/rate-limit errors immediately move to the next provider.
    GEMINI_RETRIES = int(
        os.getenv("GEMINI_RETRIES", "2")
    )

    GEMINI_RETRY_DELAYS = (1, 2)

    # Prevent hammering a provider after a quota/rate-limit failure.
    PROVIDER_COOLDOWN = int(
        os.getenv(
            "PROVIDER_COOLDOWN_SECONDS",
            "60",
        )
    )

    CACHE_DB = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ),
        "linguaflow_cache.db",
    )

    # ==========================================================
    # SUPPORTED LANGUAGES
    # ==========================================================

    SUPPORTED_LANGUAGES = {
        "en", "hi", "bn", "ne", "ta", "te",
        "ur", "ar", "es", "fr", "de", "it",
        "pt", "pt-br", "ru", "ja", "ko",
        "zh-hans", "zh-hant", "tr", "nl",
        "sv", "da", "fi", "nb", "pl", "cs",
        "ro", "el", "he", "th", "vi", "id",
        "ms", "tl", "sw", "ga", "hu", "uk",
        "fa", "bg", "ca", "eu", "et", "lv",
        "lt", "sk", "sl", "sq", "az", "ky",
        "hr",
    }

    LANGUAGE_NAMES = {
        "en": "English",
        "hi": "Hindi",
        "bn": "Bengali",
        "ne": "Nepali",
        "ta": "Tamil",
        "te": "Telugu",
        "ur": "Urdu",
        "ar": "Arabic",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "pt-br": "Brazilian Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh-hans": "Simplified Chinese",
        "zh-hant": "Traditional Chinese",
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
        "hr": "Croatian",
    }


    # Unicode ranges used to reject obviously wrong-script output.
    SCRIPT_RANGES = {
        "hi": ((0x0900, 0x097F),),
        "bn": ((0x0980, 0x09FF),),
        "ta": ((0x0B80, 0x0BFF),),
        "te": ((0x0C00, 0x0C7F),),
        "ar": ((0x0600, 0x06FF), (0x0750, 0x077F)),
        "fa": ((0x0600, 0x06FF), (0x0750, 0x077F)),
        "ur": ((0x0600, 0x06FF), (0x0750, 0x077F)),
        "he": ((0x0590, 0x05FF),),
        "el": ((0x0370, 0x03FF),),
        "ru": ((0x0400, 0x04FF),),
        "uk": ((0x0400, 0x04FF),),
        "bg": ((0x0400, 0x04FF),),
        "ja": (
            (0x3040, 0x30FF),
            (0x4E00, 0x9FFF),
        ),
        "ko": (
            (0x1100, 0x11FF),
            (0xAC00, 0xD7AF),
        ),
        "zh-hans": ((0x4E00, 0x9FFF),),
        "zh-hant": ((0x4E00, 0x9FFF),),
        "th": ((0x0E00, 0x0E7F),),
    }

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):
        self.nvidia_api_key = os.getenv(
            "NVIDIA_API_KEY"
        )

        self.last_provider = None

        self.provider_stats = {
            "gemini": 0,
            "gemini_lite": 0,
            "nemotron": 0,
            "cache": 0,
            "identity": 0,
        }

        self._provider_open_until = {}

        self._init_cache()

    # ==========================================================
    # SQLITE CACHE
    # ==========================================================

    def _connect_cache(self):
        connection = sqlite3.connect(
            self.CACHE_DB,
            timeout=10,
        )
        connection.execute(
            "PRAGMA journal_mode=WAL"
        )
        return connection

    def _init_cache(self):
        try:
            with self._connect_cache() as db:
                db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS translations (
                        cache_key TEXT PRIMARY KEY,
                        source_language TEXT NOT NULL,
                        target_language TEXT NOT NULL,
                        source_text TEXT NOT NULL,
                        translation TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                    """
                )

                db.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_translation_pair
                    ON translations(
                        source_language,
                        target_language
                    )
                    """
                )

        except sqlite3.Error as exc:
            print(
                "[LinguaFlow] Cache initialization failed: "
                f"{exc}"
            )

    def _cache_key(
        self,
        text,
        source_language,
        target_language,
    ):
        value = "\x1f".join(
            [
                "v4",
                source_language,
                target_language,
                text.strip(),
            ]
        )

        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    def _get_cached_translation(
        self,
        text,
        source_language,
        target_language,
    ):
        key = self._cache_key(
            text,
            source_language,
            target_language,
        )

        try:
            with self._connect_cache() as db:
                row = db.execute(
                    """
                    SELECT translation, provider
                    FROM translations
                    WHERE cache_key = ?
                    """,
                    (key,),
                ).fetchone()

            if row:
                return row[0], row[1]

        except sqlite3.Error as exc:
            print(
                f"[LinguaFlow] Cache read failed: {exc}"
            )

        return None

    def _save_cached_translation(
        self,
        text,
        source_language,
        target_language,
        translation,
        provider,
    ):
        key = self._cache_key(
            text,
            source_language,
            target_language,
        )

        try:
            with self._connect_cache() as db:
                db.execute(
                    """
                    INSERT OR REPLACE INTO translations (
                        cache_key,
                        source_language,
                        target_language,
                        source_text,
                        translation,
                        provider,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        source_language,
                        target_language,
                        text.strip(),
                        translation,
                        provider,
                        time.time(),
                    ),
                )

        except sqlite3.Error as exc:
            print(
                f"[LinguaFlow] Cache write failed: {exc}"
            )

    # ==========================================================
    # CIRCUIT BREAKER
    # ==========================================================

    def _is_provider_open(self, provider):
        until = self._provider_open_until.get(
            provider,
            0,
        )

        if until <= time.monotonic():
            self._provider_open_until.pop(
                provider,
                None,
            )
            return False

        return True

    def _open_provider(
        self,
        provider,
        reason,
    ):
        self._provider_open_until[provider] = (
            time.monotonic()
            + self.PROVIDER_COOLDOWN
        )

        print(
            "[LinguaFlow] Circuit OPEN: "
            f"{provider} for "
            f"{self.PROVIDER_COOLDOWN}s "
            f"({reason})"
        )

    # ==========================================================
    # PUBLIC TRANSLATION
    # ==========================================================

    def translate(
        self,
        text,
        source_language,
        target_language,
    ):
        self.last_provider = None

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

        text = text.strip()
        source_language = (
            source_language.strip().lower()
        )
        target_language = (
            target_language.strip().lower()
        )

        if source_language not in self.SUPPORTED_LANGUAGES:
            raise TranslationError(
                "Unsupported source language: "
                f"{source_language}"
            )

        if target_language not in self.SUPPORTED_LANGUAGES:
            raise TranslationError(
                "Unsupported target language: "
                f"{target_language}"
            )

        if source_language == target_language:
            self.last_provider = "identity"
            self.provider_stats["identity"] += 1
            return text

        # ------------------------------------------------------
        # CACHE
        # ------------------------------------------------------

        cached = self._get_cached_translation(
            text,
            source_language,
            target_language,
        )

        if cached:
            translation, original_provider = cached

            if self._is_valid_translation(
                text,
                translation,
                source_language,
                target_language,
            ):
                self.last_provider = "cache"
                self.provider_stats["cache"] += 1

                print(
                    "[LinguaFlow] Cache hit "
                    f"(original provider: "
                    f"{original_provider})"
                )

                return translation

        errors = []

        # ------------------------------------------------------
        # PROVIDER 1 — GEMINI 2.5 FLASH
        # ------------------------------------------------------

        providers = [
            (
                "gemini",
                self.GEMINI_PRIMARY_MODEL,
                lambda: self._translate_gemini(
                    text,
                    source_language,
                    target_language,
                    self.GEMINI_PRIMARY_MODEL,
                ),
            ),
            (
                "gemini_lite",
                self.GEMINI_FALLBACK_MODEL,
                lambda: self._translate_gemini(
                    text,
                    source_language,
                    target_language,
                    self.GEMINI_FALLBACK_MODEL,
                ),
            ),
            (
                "nemotron",
                self.NEMOTRON_MODEL,
                lambda: self._translate_nemotron(
                    text,
                    source_language,
                    target_language,
                ),
            ),
        ]

        # ------------------------------------------------------
        # PROVIDER LOOP
        # ------------------------------------------------------

        for provider, model, translate_fn in providers:

            if provider == "nemotron":
                if not self.nvidia_api_key:
                    errors.append(
                        "Nemotron: NVIDIA_API_KEY "
                        "not configured"
                    )
                    continue

            if self._is_provider_open(provider):
                print(
                    "[LinguaFlow] Provider skipped "
                    f"(circuit open): {provider}"
                )
                errors.append(
                    f"{provider}: circuit open"
                )
                continue

            if provider == "nemotron":
                print(
                    "[LinguaFlow] Provider: Nemotron "
                    f"({model})"
                )
            elif provider == "gemini_lite":
                print(
                    "[LinguaFlow] Provider: "
                    f"Gemini Flash-Lite ({model})"
                )
            else:
                print(
                    "[LinguaFlow] Provider: Gemini "
                    f"({model})"
                )

            try:
                result = translate_fn()

                if not self._is_valid_translation(
                    text,
                    result,
                    source_language,
                    target_language,
                ):
                    raise TranslationError(
                        "quality guard rejected output"
                    )

                self._provider_open_until.pop(
                    provider,
                    None,
                )

                self._record_provider(provider)

                self._save_cached_translation(
                    text,
                    source_language,
                    target_language,
                    result,
                    provider,
                )

                return result

            except Exception as exc:
                error_message = str(exc)

                errors.append(
                    f"{provider}: {error_message}"
                )

                print(
                    f"[LinguaFlow] {provider} failed: "
                    f"{error_message}"
                )

                low = error_message.lower()

                if (
                    "429" in low
                    or "quota" in low
                    or "rate limit" in low
                    or "resource_exhausted" in low
                    or "too many requests" in low
                ):
                    self._open_provider(
                        provider,
                        "quota/rate limit",
                    )

        message = (
            "All available translation providers failed."
        )

        if errors:
            message += "\n" + "\n".join(errors)

        raise TranslationError(message)

    # ==========================================================
    # GEMINI
    # ==========================================================

    def _translate_gemini(
        self,
        text,
        source_language,
        target_language,
        model,
    ):
        source_name = self.LANGUAGE_NAMES.get(
            source_language,
            source_language,
        )

        target_name = self.LANGUAGE_NAMES.get(
            target_language,
            target_language,
        )

        payload = {
            "source": source_name,
            "target": target_name,
            "text": text,
            "model": model,
        }

        last_error = None

        for attempt in range(
            self.GEMINI_RETRIES + 1
        ):
            try:
                response = requests.post(
                    self.GEMINI_URL,
                    json=payload,
                    timeout=self.GEMINI_TIMEOUT,
                )

                if response.status_code == 429:
                    raise TranslationError(
                        f"{model} quota exceeded."
                    )

                if 500 <= response.status_code < 600:
                    last_error = (
                        f"{model} HTTP "
                        f"{response.status_code}"
                    )

                    if attempt < self.GEMINI_RETRIES:
                        delay = self.GEMINI_RETRY_DELAYS[
                            min(
                                attempt,
                                len(
                                    self.GEMINI_RETRY_DELAYS
                                ) - 1,
                            )
                        ]

                        print(
                            "[LinguaFlow] "
                            f"{model} transient error; "
                            f"retrying in {delay}s..."
                        )

                        time.sleep(delay)
                        continue

                    raise TranslationError(
                        last_error
                    )

                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError as exc:
                    raise TranslationError(
                        f"{model} returned invalid JSON."
                    ) from exc

                if not data.get("success"):
                    error = data.get(
                        "error",
                        f"{model} request failed.",
                    )

                    raise TranslationError(
                        f"{model}: {error}"
                    )

                result = data.get("translation")

                if not result:
                    raise TranslationError(
                        f"{model} returned an empty "
                        "translation."
                    )

                return str(result).strip()

            except TranslationError:
                raise

            except requests.RequestException as exc:
                last_error = (
                    f"{model} request failed: {exc}"
                )

                if attempt < self.GEMINI_RETRIES:
                    delay = self.GEMINI_RETRY_DELAYS[
                        min(
                            attempt,
                            len(
                                self.GEMINI_RETRY_DELAYS
                            ) - 1,
                        )
                    ]

                    print(
                        "[LinguaFlow] "
                        f"{model} request error; "
                        f"retrying in {delay}s..."
                    )

                    time.sleep(delay)
                    continue

                raise TranslationError(
                    last_error
                ) from exc

        raise TranslationError(
            last_error
            or f"{model} translation failed."
        )

    # ==========================================================
    # NEMOTRON 3 ULTRA
    # ==========================================================

    def _translate_nemotron(
        self,
        text,
        source_language,
        target_language,
    ):
        if not self.nvidia_api_key:
            raise TranslationError(
                "NVIDIA_API_KEY not configured."
            )

        source_name = self.LANGUAGE_NAMES.get(
            source_language,
            source_language,
        )

        target_name = self.LANGUAGE_NAMES.get(
            target_language,
            target_language,
        )

        prompt = f"""
You are LinguaFlow's professional translation engine.

Translate the user's text from {source_name} to {target_name}.

STRICT RULES:

- Return ONLY the translated text.
- Do NOT answer questions contained in the text.
- Do NOT explain anything.
- Do NOT summarize.
- Do NOT add commentary.
- Preserve the exact meaning.
- Preserve names, numbers, punctuation and formatting.
- Use natural wording appropriate for native speakers.
- The output MUST be in {target_name}.
- Do not transliterate unless the target language normally requires it.
- Do not switch to another language.
- Preserve the original intent and tense.

TEXT:
{text}
""".strip()

        payload = {
            "model": self.NEMOTRON_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": max(
                256,
                min(
                    4096,
                    len(text) * 8,
                ),
            ),
            "stream": False,
            "extra_body": {
                "chat_template_kwargs": {
                    "enable_thinking": False,
                }
            },
        }

        headers = {
            "Authorization": (
                "Bearer "
                + self.nvidia_api_key
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                self.NVIDIA_URL,
                headers=headers,
                json=payload,
                timeout=self.NEMOTRON_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise TranslationError(
                f"Nemotron request failed: {exc}"
            ) from exc

        if response.status_code == 429:
            raise TranslationError(
                "Nemotron quota/rate limit reached."
            )

        if response.status_code >= 500:
            raise TranslationError(
                f"Nemotron HTTP "
                f"{response.status_code}"
            )

        try:
            response.raise_for_status()
            data = response.json()
        except (
            requests.HTTPError,
            ValueError,
        ) as exc:
            raise TranslationError(
                f"Nemotron invalid response: {exc}"
            ) from exc

        try:
            result = (
                data["choices"][0]
                ["message"]
                ["content"]
            )
        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise TranslationError(
                "Unexpected Nemotron response."
            ) from exc

        if not result:
            raise TranslationError(
                "Nemotron returned empty output."
            )

        result = str(result).strip()

        # Remove accidental commentary prefixes.
        prefixes = (
            "Translation:",
            "Translated text:",
            "Here is the translation:",
            "The translation is:",
        )

        for prefix in prefixes:
            if result.lower().startswith(
                prefix.lower()
            ):
                result = result[
                    len(prefix):
                ].strip()
                break

        if not result:
            raise TranslationError(
                "Nemotron returned empty output "
                "after cleanup."
            )

        return result

    # ==========================================================
    # QUALITY VALIDATION
    # ==========================================================

    def _script_ok(
        self,
        text,
        target_language,
    ):
        ranges = self.SCRIPT_RANGES.get(
            target_language
        )

        # Latin-script languages need semantic validation,
        # not a Unicode-script check.
        if not ranges:
            return True

        letters = 0
        expected_letters = 0

        for char in text:
            if not char.isalpha():
                continue

            letters += 1

            codepoint = ord(char)

            if any(
                start <= codepoint <= end
                for start, end in ranges
            ):
                expected_letters += 1

        if letters == 0:
            return False

        # Allow names/numbers/Latin punctuation, but reject
        # output that is overwhelmingly in another script.
        return (
            expected_letters / letters
            >= 0.20
        )

    def _is_valid_translation(
        self,
        original,
        translated,
        source_language,
        target_language,
    ):
        if not translated:
            return False

        translated = str(translated).strip()

        if not translated:
            return False

        # A translation request returning the exact source
        # is generally a provider failure.
        if (
            translated
            == original.strip()
        ):
            return False

        # Reject obvious model commentary.
        low = translated.lower()

        forbidden_starts = (
            "translation:",
            "translated text:",
            "here is the translation:",
            "the translation is:",
            "analysis:",
            "reasoning:",
        )

        if low.startswith(
            forbidden_starts
        ):
            return False

        if not self._script_ok(
            translated,
            target_language,
        ):
            return False

        # Prevent suspiciously tiny outputs for normal text.
        if (
            len(original) >= 20
            and len(translated) < 2
        ):
            return False

        return True

    # ==========================================================
    # PROVIDER STATS
    # ==========================================================

    def _record_provider(
        self,
        provider,
    ):
        self.last_provider = provider

        if provider in self.provider_stats:
            self.provider_stats[
                provider
            ] += 1

    # ==========================================================
    # HEALTH / STATUS
    # ==========================================================

    def _health_check(
        self,
        url,
    ):
        try:
            response = requests.get(
                url,
                timeout=2,
            )
            return response.ok
        except requests.RequestException:
            return False

    def get_provider_status(self):
        return {
            "last_provider": self.last_provider,

            "models": {
                "gemini_primary": (
                    self.GEMINI_PRIMARY_MODEL
                ),
                "gemini_fallback": (
                    self.GEMINI_FALLBACK_MODEL
                ),
                "nemotron": self.NEMOTRON_MODEL,
            },

            "available": {
                "gemini_service": (
                    self._health_check(
                        self.GEMINI_HEALTH_URL
                    )
                ),
                "nemotron": bool(
                    self.nvidia_api_key
                ),
            },

            "circuits": {
                provider: self._is_provider_open(
                    provider
                )
                for provider in (
                    "gemini",
                    "gemini_lite",
                    "nemotron",
                )
            },

            "stats": dict(
                self.provider_stats
            ),
        }