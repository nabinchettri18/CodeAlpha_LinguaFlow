from src.vak_translator import VakTranslator


TESTS = {
    "hi": [
        "Hello, how are you today?",
        "India is a country with many different cultures.",
        "Education is important for a better future.",
    ],
    "bn": [
        "The weather is beautiful today.",
        "India is a country with many different cultures.",
        "Education is important for a better future.",
    ],
    "ne": [
        "India is a country with many different cultures.",
        "Good morning, how are you?",
        "Technology is changing the world.",
    ],
    "ta": [
        "Machine learning is transforming technology.",
        "Education is important for a better future.",
        "India is a country with many different cultures.",
    ],
    "te": [
        "Education is the key to success.",
        "Technology is changing the world.",
        "Good morning, how are you?",
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
    print("LINGUAFLOW - VĀĶ MULTI-SENTENCE QUALITY TEST")
    print("=" * 70)

    translator = VakTranslator(device="cpu")

    total = 0
    passed = 0
    failed = 0

    for target, sentences in TESTS.items():

        print("\n" + "=" * 70)
        print(
            f"ENGLISH → {LANGUAGE_NAMES[target]}"
        )
        print("=" * 70)

        language_passed = 0

        for sentence in sentences:

            total += 1

            print("\nInput:")
            print(sentence)

            try:
                result = translator.translate(
                    sentence,
                    "en",
                    target,
                )

                print("\nOutput:")
                print(result)

                if not result or not result.strip():
                    print("[FAIL] Empty output")
                    failed += 1
                    continue

                if result.strip().lower() == sentence.lower():
                    print(
                        "[FAIL] Output is identical "
                        "to source"
                    )
                    failed += 1
                    continue

                # Basic hallucination/repetition protection
                words = result.split()

                if len(words) >= 8:
                    unique_ratio = (
                        len(set(words))
                        / len(words)
                    )

                    if unique_ratio < 0.35:
                        print(
                            "[FAIL] Excessive repetition"
                        )
                        failed += 1
                        continue

                print("[PASS] Basic quality checks")
                passed += 1
                language_passed += 1

            except Exception as exc:
                print(f"[ERROR] {exc}")
                failed += 1

        print(
            f"\n{LANGUAGE_NAMES[target]} result: "
            f"{language_passed}/{len(sentences)}"
        )

    print("\n" + "=" * 70)
    print(
        f"TOTAL: {passed}/{total} passed, "
        f"{failed} failed"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()