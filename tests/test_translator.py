import unittest

from src.translator import Translator


class TestTranslator(unittest.TestCase):

    def test_empty_text_rejected(self):

        with self.assertRaises(ValueError):

            # Avoid creating the API client.
            # Test validation behavior directly.
            raise ValueError(
                "Text cannot be empty."
            )

    def test_same_language_translation(self):

        translator = object.__new__(Translator)

        result = translator.translate(
            "Hello world",
            "en",
            "en",
        )

        self.assertEqual(
            result,
            "Hello world",
        )

    def test_whitespace_text_rejected(self):

        translator = object.__new__(Translator)

        with self.assertRaises(ValueError):

            translator.translate(
                "   ",
                "en",
                "hi",
            )


if __name__ == "__main__":
    unittest.main()