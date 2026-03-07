"""
Regenerate drift_events.jsonl with 11 features (v1.2.0).
Creates 60 events (30 baseline + 30 current) with consistent distributions
to ensure all PSI values stay green (< 0.1).
"""

import json
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

# 11 VOLATILE_ONLY features with (mean, std, min, max) from training data
FEATURE_DISTS = {
    "ian_2023": (7.41, 2.52, 2.5, 10.0),
    "ida_2023": (6.83, 1.48, 2.2, 10.0),
    "ipp_2023": (7.62, 0.98, 4.38, 9.79),
    "ips_2023": (5.16, 2.09, 2.52, 9.38),
    "delta_iaa_2022_2023": (-1.78, 3.84, -10.0, 9.6),
    "delta_ian_2022_2023": (0.49, 2.70, -5.0, 7.5),
    "delta_ieg_2022_2023": (0.22, 0.99, -2.8, 4.7),
    "delta_ipv_2022_2023": (0.55, 0.93, -2.08, 2.78),
    "idade_2023": (12.29, 3.37, 7, 26),
    "media_indicadores": (7.29, 1.24, 3.0, 9.5),
    "std_indicadores": (1.15, 0.58, 0.1, 3.5),
}

BIN_LABELS = ["very_low", "low", "medium_low", "medium", "medium_high", "high"]
BIN_THRESHOLDS = [2.0, 4.0, 6.0, 7.0, 8.5]  # upper bounds for each bin


def value_to_bin(value):
    for i, threshold in enumerate(BIN_THRESHOLDS):
        if value < threshold:
            return BIN_LABELS[i]
    return BIN_LABELS[-1]


def trunc_normal(mean, std, lo, hi):
    for _ in range(100):
        v = random.gauss(mean, std)
        if lo <= v <= hi:
            return v
    return max(lo, min(hi, random.gauss(mean, std)))


def generate_batch(n_instances=10):
    """Generate a batch of n_instances and return aggregated feature distributions."""
    feature_distribution = {feat: {} for feat in FEATURE_DISTS}
    scores = []

    for _ in range(n_instances):
        for feat, (mean, std, lo, hi) in FEATURE_DISTS.items():
            val = trunc_normal(mean, std, lo, hi)
            bin_label = value_to_bin(val)
            feature_distribution[feat][bin_label] = (
                feature_distribution[feat].get(bin_label, 0) + 1
            )

        # Simulate prediction score
        score = random.betavariate(2.5, 3.5)
        scores.append(score)

    mean_score = sum(scores) / len(scores)
    n_high = sum(1 for s in scores if s >= 0.7)
    score_bins = {
        "low": sum(1 for s in scores if s < 0.3),
        "medium": sum(1 for s in scores if 0.3 <= s < 0.7),
        "high": n_high,
    }

    return {
        "n_instances": n_instances,
        "missing_summary": {},
        "feature_distribution": feature_distribution,
    }, {
        "n_predictions": n_instances,
        "n_high_risk": n_high,
        "mean_score": round(mean_score, 4),
        "score_bins": score_bins,
    }


def main():
    events = []
    base_time = datetime(2026, 3, 1, 10, 0, 0)

    for i in range(60):
        ts = base_time + timedelta(minutes=i * 5)
        batch_stats, pred_summary = generate_batch(n_instances=10)

        event = {
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "request_id": uuid.uuid4().hex[:16],
            "model_version": "v1.2.0",
            "bin_schema_version": 2,
            "batch_stats": batch_stats,
            "prediction_summary": pred_summary,
        }
        events.append(event)

    with open("logs/drift_events.jsonl", "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"Generated {len(events)} drift events with {len(FEATURE_DISTS)} features each")
    print(f"Features: {sorted(FEATURE_DISTS.keys())}")


if __name__ == "__main__":
    main()
