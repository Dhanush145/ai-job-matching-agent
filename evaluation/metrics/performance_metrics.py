from statistics import mean
from time import perf_counter


def benchmark(callable_fn, iterations=5, warmup=1):
    for _ in range(max(0, warmup)):
        callable_fn()

    durations_ms = []
    for _ in range(max(1, iterations)):
        start = perf_counter()
        callable_fn()
        durations_ms.append((perf_counter() - start) * 1000)

    ordered = sorted(durations_ms)
    p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
    return {
        "iterations": len(durations_ms),
        "mean_latency_ms": round(mean(durations_ms), 2),
        "min_latency_ms": round(min(durations_ms), 2),
        "max_latency_ms": round(max(durations_ms), 2),
        "p95_latency_ms": round(ordered[p95_index], 2),
    }
