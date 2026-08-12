import concurrent.futures
import statistics
import time

from src.translator import Translator


TESTS = [
    ("Today we are testing request number 1.", "en", "hi"),
    ("Today we are testing request number 2.", "en", "bn"),
    ("Today we are testing request number 3.", "en", "ne"),
    ("Today we are testing request number 4.", "en", "ta"),
    ("Today we are testing request number 5.", "en", "te"),
    ("Today we are testing request number 6.", "en", "ur"),
    ("Today we are testing request number 7.", "en", "fr"),
    ("Today we are testing request number 8.", "en", "de"),
    ("Today we are testing request number 9.", "en", "ja"),
    ("Today we are testing request number 10.", "en", "it"),
    ("Today we are testing request number 11.", "en", "es"),
    ("Today we are testing request number 12.", "en", "pt"),
    ("Today we are testing request number 13.", "en", "ko"),
    ("Today we are testing request number 14.", "en", "ar"),
    ("Today we are testing request number 15.", "en", "ru"),
    ("Today we are testing request number 16.", "en", "tr"),
    ("Today we are testing request number 17.", "en", "nl"),
    ("Today we are testing request number 18.", "en", "vi"),
    ("Today we are testing request number 19.", "en", "id"),
    ("Today we are testing request number 20.", "en", "ms"),
    ("Today we are testing request number 21.", "en", "sw"),
    ("Today we are testing request number 22.", "en", "pl"),
    ("Today we are testing request number 23.", "en", "uk"),
    ("Today we are testing request number 24.", "en", "el"),
    ("Today we are testing request number 25.", "en", "fa"),
]


def translate_one(index):
    text, source, target = TESTS[index]

    translator = Translator()

    start = time.perf_counter()

    try:
        result = translator.translate(
            text,
            source,
            target,
        )

        latency = time.perf_counter() - start

        return {
            "index": index + 1,
            "success": True,
            "provider": translator.last_provider,
            "latency": latency,
            "result": result,
        }

    except Exception as exc:
        latency = time.perf_counter() - start

        return {
            "index": index + 1,
            "success": False,
            "provider": translator.last_provider,
            "latency": latency,
            "error": str(exc),
        }


def percentile(values, percentage):
    if not values:
        return 0.0

    values = sorted(values)

    position = (
        (len(values) - 1)
        * percentage
        / 100
    )

    lower = int(position)
    upper = min(
        lower + 1,
        len(values) - 1,
    )

    fraction = position - lower

    return (
        values[lower]
        + (
            values[upper]
            - values[lower]
        )
        * fraction
    )


def main():
    workers = 25

    print("=" * 70)
    print("LINGUAFLOW — 25 UNIQUE REQUEST CONCURRENCY TEST")
    print("=" * 70)

    overall_start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers
    ) as executor:
        results = list(
            executor.map(
                translate_one,
                range(len(TESTS)),
            )
        )

    total_time = (
        time.perf_counter()
        - overall_start
    )

    print("\nRESULTS")
    print("-" * 70)

    for result in results:
        if result["success"]:
            print(
                f"{result['index']:02d} | "
                f"PASS | "
                f"{result['provider']:<12} | "
                f"{result['latency']:.2f}s | "
                f"{result['result']}"
            )
        else:
            print(
                f"{result['index']:02d} | "
                f"FAIL | "
                f"{result['provider'] or '-':<12} | "
                f"{result['latency']:.2f}s | "
                f"{result['error']}"
            )

    successful = [
        r for r in results
        if r["success"]
    ]

    failed = [
        r for r in results
        if not r["success"]
    ]

    latencies = [
        r["latency"]
        for r in successful
    ]

    print("\nSUMMARY")
    print("-" * 70)

    print(
        f"Total requests : {len(results)}"
    )

    print(
        f"Successful     : {len(successful)}"
    )

    print(
        f"Failed         : {len(failed)}"
    )

    print(
        f"Total time     : {total_time:.2f}s"
    )

    if latencies:
        print(
            f"Average latency: "
            f"{statistics.mean(latencies):.2f}s"
        )

        print(
            f"Fastest        : "
            f"{min(latencies):.2f}s"
        )

        print(
            f"Slowest        : "
            f"{max(latencies):.2f}s"
        )

        print(
            f"P50 latency    : "
            f"{percentile(latencies, 50):.2f}s"
        )

        print(
            f"P95 latency    : "
            f"{percentile(latencies, 95):.2f}s"
        )

        print(
            f"P99 latency    : "
            f"{percentile(latencies, 99):.2f}s"
        )

    if total_time > 0:
        print(
            f"Throughput     : "
            f"{len(results) / total_time:.2f} req/s"
        )

    # ----------------------------------------------------------
    # PROVIDER DISTRIBUTION
    # ----------------------------------------------------------

    providers = {}

    for result in results:
        provider = (
            result["provider"]
            if result["provider"]
            else "failed"
        )

        providers[provider] = (
            providers.get(provider, 0) + 1
        )

    print("\nPROVIDERS")
    print("-" * 70)

    for provider, count in sorted(
        providers.items()
    ):
        print(
            f"{provider:<15}: {count}"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()