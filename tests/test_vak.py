from src.vak_translator import VakTranslator


translator = VakTranslator(
    device="cpu"
)

tests = [
    (
        "Hello, how are you today?",
        "en",
        "hi",
    ),
    (
        "The weather is beautiful today.",
        "en",
        "bn",
    ),
    (
        "India is a land of diverse cultures.",
        "en",
        "ne",
    ),
    (
        "Machine learning is transforming technology.",
        "en",
        "ta",
    ),
    (
        "Education is the key to success.",
        "en",
        "te",
    ),
    (
        "नमस्ते, आज आप कैसे हैं?",
        "hi",
        "en",
    ),
]


for text, source, target in tests:

    print("=" * 60)

    print(
        f"{source} → {target}"
    )

    print(
        "Input:",
        text
    )

    try:

        result = translator.translate(
            text,
            source,
            target,
        )

        print(
            "Output:",
            result
        )

    except Exception as exc:

        print(
            "ERROR:",
            exc
        )