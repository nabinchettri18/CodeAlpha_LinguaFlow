from src.vak_translator import VakTranslator


TESTS = [
    ("hi", "Hindi", "नमस्ते, आज आपका दिन कैसा है?"),
    ("bn", "Bengali", "নমস্কার, আজ আপনার দিন কেমন যাচ্ছে?"),
    ("mr", "Marathi", "नमस्कार, आज तुमचा दिवस कसा आहे?"),
    ("gu", "Gujarati", "નમસ્તે, આજે તમારો દિવસ કેવો છે?"),
    ("ur", "Urdu", "السلام علیکم، آج آپ کا دن کیسا ہے؟"),
    ("or", "Odia", "ନମସ୍କାର, ଆଜି ଆପଣଙ୍କ ଦିନ କେମିତି ଚାଲିଛି?"),
    ("pa", "Punjabi", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਅੱਜ ਤੁਹਾਡਾ ਦਿਨ ਕਿਵੇਂ ਹੈ?"),
    ("as", "Assamese", "নমস্কাৰ, আজি আপোনাৰ দিনটো কেনেকুৱা?"),
    ("ne", "Nepali", "नमस्ते, आज तपाईंको दिन कस्तो छ?"),
    ("ta", "Tamil", "வணக்கம், இன்று உங்கள் நாள் எப்படி இருக்கிறது?"),
    ("te", "Telugu", "నమస్కారం, ఈ రోజు మీ రోజు ఎలా ఉంది?"),
    ("kn", "Kannada", "ನಮಸ್ಕಾರ, ಇಂದು ನಿಮ್ಮ ದಿನ ಹೇಗಿದೆ?"),
    ("ml", "Malayalam", "നമസ്കാരം, ഇന്ന് നിങ്ങളുടെ ദിവസം എങ്ങനെയുണ്ട്?"),
]


def main():
    print("=" * 70)
    print("LINGUAFLOW - VĀĶ INDIAN LANGUAGE TEST")
    print("=" * 70)

    translator = VakTranslator(device="cpu")

    passed = 0
    failed = 0

    for lang, name, text in TESTS:
        print()
        print("-" * 70)
        print(f"English → {name}")
        print(f"Target code: {lang}")

        try:
            result = translator.translate(
                text,
                lang,
                "en",
            )

            if result and result.strip():
                print(f"Input:  {text}")
                print(f"Output: {result}")
                print("[PASS]")
                passed += 1
            else:
                print("[FAIL] Empty result")
                failed += 1

        except Exception as exc:
            print(f"[ERROR] {exc}")
            failed += 1

    print()
    print("=" * 70)
    print(
        f"RESULTS: {passed}/{passed + failed} passed, "
        f"{failed} failed"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()