from src.vak_translator import VakTranslator


TESTS = {
    "hi": [
        "नमस्ते, आज आप कैसे हैं?",
        "भारत एक ऐसा देश है जहां कई अलग-अलग संस्कृतियां मौजूद हैं।",
        "बेहतर भविष्य के लिए शिक्षा महत्वपूर्ण है।",
    ],
    "bn": [
        "আবহাওয়া আজ খুব সুন্দর।",
        "ভারতবর্ষ এমন একটি দেশ যেখানে রয়েছে অসংখ্য বৈচিত্র্যময় সংস্কৃতি।",
        "উন্নত ভবিষ্যতের জন্য শিক্ষা অত্যন্ত গুরুত্বপূর্ণ।",
    ],
    "ne": [
        "भारत विभिन्न संस्कृतिको देश हो।",
        "शुभ प्रभात, तपाईं कसरी हुनुहुन्छ?",
        "टेक्नोलोजीले संसारलाई परिवर्तन गरिरहेको छ।",
    ],
    "ta": [
        "இயந்திர கற்றல் என்பது மாற்றும் தொழில்நுட்பமாகும்.",
        "சிறந்த எதிர்காலத்திற்காக கல்வி முக்கியமானது.",
        "இந்தியா பல கலாச்சாரங்களை கொண்ட நாடு.",
    ],
    "te": [
        "విద్య విజయానికి కీలకం.",
        "టెక్నాలజీ ప్రపంచాన్ని మారుస్తోంది.",
        "గుడ్ మార్నింగ్, మీరు ఎలా ఉన్నారు?",
    ],
}


LANGUAGE_NAMES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "ne": "Nepali",
    "ta": "Tamil",
    "te": "Telugu",
}


def main():
    print("=" * 70)
    print("LINGUAFLOW - VĀĶ REVERSE QUALITY TEST")
    print("=" * 70)

    translator = VakTranslator(device="cpu")

    for source, sentences in TESTS.items():

        print("\n" + "=" * 70)
        print(f"{LANGUAGE_NAMES[source]} → ENGLISH")
        print("=" * 70)

        for sentence in sentences:

            print("\nInput:")
            print(sentence)

            try:
                result = translator.translate(
                    sentence,
                    source,
                    "en",
                )

                print("\nOutput:")
                print(result)

                if not result or not result.strip():
                    print("[FAIL] Empty output")
                    continue

                if result.strip() == sentence.strip():
                    print("[FAIL] Output unchanged")
                    continue

                print("[REVIEW] Inspect translation manually.")

            except Exception as exc:
                print(f"[ERROR] {exc}")


if __name__ == "__main__":
    main()