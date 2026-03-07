"""
Seed predictions – sends diverse inference requests to the running API
and generates localStorage-compatible JSON so the Students page is populated.

Usage:
    python scripts/seed_predictions.py [--url http://localhost:8080/api] [--n 30]
"""

import argparse
import json
import random
import time
import uuid

import requests

# ---------- Training-distribution-aware feature sampling ----------
# Parameters extracted from the training dataset (data/processed/modeling_dataset.parquet)
# via feature_engineering.make_features(). Seed instances are sampled from truncated
# normal distributions matching these stats so PSI drift stays minimal.
# v1.2.0 — 11 VOLATILE_ONLY features from ablation experiment.

# Format: (mean, std, min, max) — sampled via truncated normal
# Integer features use round().
TRAINING_DISTS = {
    # -- PEDE indicators (4 of 7, continuous 0-10) --
    "ian_2023": (7.41, 2.52, 2.5, 10.0),
    "ida_2023": (6.83, 1.48, 2.2, 10.0),
    "ipp_2023": (7.62, 0.98, 4.38, 9.79),
    "ips_2023": (5.16, 2.09, 2.52, 9.38),
    # -- Deltas 2022→2023 --
    "delta_iaa_2022_2023": (-1.78, 3.84, -10.0, 9.6),
    "delta_ian_2022_2023": (0.49, 2.70, -5.0, 7.5),
    "delta_ieg_2022_2023": (0.22, 0.99, -2.8, 4.7),
    "delta_ipv_2022_2023": (0.55, 0.93, -2.08, 2.78),
    # -- Demographics --
    "idade_2023": (12.29, 3.37, 7, 26),
    # -- Derived (computed from all 7 PEDE indicators, but sent as features) --
    "media_indicadores": (7.29, 1.24, 3.0, 9.5),
    "std_indicadores": (1.15, 0.58, 0.1, 3.5),
}

# ---------- predefined profiles (shift mean/std for each archetype) ----------
PROFILES = [
    {
        "label": "Alto risco - indicadores baixos",
        "overrides": {
            "ian_2023": (3.0, 1.5, 2.5, 5.5),
            "ida_2023": (4.0, 1.2, 2.2, 6.0),
            "ipp_2023": (5.5, 1.0, 4.38, 7.0),
            "ips_2023": (3.0, 0.8, 2.52, 4.5),
            "delta_iaa_2022_2023": (-3.5, 2.5, -10.0, 0.0),
            "delta_ian_2022_2023": (-1.5, 2.0, -5.0, 1.0),
            "media_indicadores": (4.5, 1.0, 3.0, 6.0),
            "std_indicadores": (1.8, 0.5, 0.5, 3.5),
        },
    },
    {
        "label": "Baixo risco - indicadores altos",
        "overrides": {
            "ian_2023": (9.0, 1.0, 7.5, 10.0),
            "ida_2023": (8.5, 1.0, 6.5, 10.0),
            "ipp_2023": (8.5, 0.6, 7.5, 9.79),
            "ips_2023": (7.5, 1.2, 5.0, 9.38),
            "delta_iaa_2022_2023": (1.5, 2.0, 0.0, 9.6),
            "delta_ian_2022_2023": (1.5, 1.5, 0.0, 7.5),
            "media_indicadores": (8.5, 0.6, 7.0, 9.5),
            "std_indicadores": (0.5, 0.3, 0.1, 1.5),
        },
    },
    {
        "label": "Risco moderado - indicadores medianos",
        "overrides": {
            "ian_2023": (6.5, 1.5, 4.0, 8.5),
            "ida_2023": (6.0, 1.0, 4.5, 7.5),
            "ipp_2023": (7.0, 0.8, 5.5, 8.5),
            "ips_2023": (4.5, 1.5, 2.52, 7.0),
            "media_indicadores": (6.5, 0.8, 5.0, 8.0),
        },
    },
    {
        "label": "Aluno novo sem historico",
        "overrides": {
            "delta_iaa_2022_2023": (0, 0.01, 0, 0),
            "delta_ian_2022_2023": (0, 0.01, 0, 0),
            "delta_ieg_2022_2023": (0, 0.01, 0, 0),
            "delta_ipv_2022_2023": (0, 0.01, 0, 0),
        },
    },
    {
        "label": "Aluno veterano fase avancada",
        "overrides": {
            "idade_2023": (17, 2.0, 15, 26),
            "ian_2023": (8.0, 1.0, 6.0, 10.0),
            "ida_2023": (7.5, 1.0, 5.5, 9.5),
        },
    },
]


def trunc_normal(mean, std, lo, hi):
    """Sample from a truncated normal distribution via rejection sampling."""
    for _ in range(100):
        v = random.gauss(mean, std)
        if lo <= v <= hi:
            return v
    # Fallback: clamp
    return max(lo, min(hi, random.gauss(mean, std)))


def generate_instance(profile=None):
    overrides = profile.get("overrides", {}) if profile else {}
    inst = {}

    # 1. Sample continuous/integer features from truncated normals
    for feat, (mean, std, lo, hi) in TRAINING_DISTS.items():
        if feat in overrides:
            ov = overrides[feat]
            if isinstance(ov, (int, float)):
                inst[feat] = ov
            else:
                inst[feat] = round(trunc_normal(*ov), 2)
        else:
            inst[feat] = round(trunc_normal(mean, std, lo, hi), 2)

    # Round integer-type features
    for int_feat in ("idade_2023",):
        if int_feat in inst:
            inst[int_feat] = int(round(inst[int_feat]))

    return inst


def get_risk_level(score):
    if score >= 0.7:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


def classify_pedra(features):
    """Approximate INDE-based Pedra classification (mirrors frontend logic)."""
    indicators = [
        "ian_2023",
        "ida_2023",
        "ieg_2023",
        "iaa_2023",
        "ips_2023",
        "ipp_2023",
        "ipv_2023",
    ]
    weights = {
        "ian_2023": 0.10,
        "ida_2023": 0.20,
        "ieg_2023": 0.20,
        "iaa_2023": 0.10,
        "ips_2023": 0.10,
        "ipp_2023": 0.10,
        "ipv_2023": 0.20,
    }
    weighted_sum = 0
    total_weight = 0
    for k in indicators:
        val = features.get(k)
        if isinstance(val, (int, float)):
            w = weights.get(k, 0.14)
            weighted_sum += val * w
            total_weight += w
    if total_weight == 0:
        return None
    inde = weighted_sum / total_weight
    if inde < 6.1:
        return "Quartzo"
    if inde < 7.2:
        return "Ágata"
    if inde < 8.2:
        return "Ametista"
    return "Topázio"


def send_predictions(base_url: str, n: int):
    url = f"{base_url}/predict"

    print(f"\n{'='*60}")
    print(f"  Seed Predictions – enviando {n} requisições para {url}")
    print(f"{'='*60}\n")

    stats = {"total": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0, "errors": 0}
    local_storage_items = []

    # Distribute profiles symmetrically so first-half and second-half
    # of drift events have identical profile mixes (prevents PSI drift).
    # Pattern: every 10 events = 1 cycle of 5 profiles + 5 random.
    # Both halves (0-49 and 50-99) contain 5 full cycles each.
    profile_assignments = []
    for i in range(n):
        pos_in_cycle = i % 10
        if pos_in_cycle < len(PROFILES):
            profile_assignments.append(PROFILES[pos_in_cycle])
        else:
            profile_assignments.append(None)

    # Send requests in batches of BATCH_SIZE instances each.
    # Larger batches = more feature values per drift event = lower PSI noise.
    BATCH_SIZE = 10
    batch_instances = []
    batch_labels = []

    def flush_batch(batch_inst, batch_lbl):
        """Send a batch of instances and collect results."""
        if not batch_inst:
            return
        payload = {"instances": batch_inst}
        combined_label = ", ".join(set(batch_lbl))
        try:
            r = requests.post(url, json=payload, timeout=15)
            stats["total"] += len(batch_inst)

            if r.status_code == 200:
                data = r.json()
                request_id = data.get("request_id", uuid.uuid4().hex[:8])
                for idx, pred in enumerate(data.get("predictions", [])):
                    score = pred["risk_score"]
                    risk_level = get_risk_level(score)

                    if risk_level == "high":
                        stats["high_risk"] += 1
                    elif risk_level == "medium":
                        stats["medium_risk"] += 1
                    else:
                        stats["low_risk"] += 1

                    feat = batch_inst[idx] if idx < len(batch_inst) else batch_inst[0]
                    student_pred = {
                        "risk_score": score,
                        "risk_label": pred["risk_label"],
                        "model_version": pred.get("model_version", "v1.2.0"),
                        "id": f"{request_id}-{idx}-{uuid.uuid4().hex[:8]}",
                        "timestamp": time.strftime(
                            "%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()
                        ),
                        "features": feat,
                        "risk_level": risk_level,
                        "pedra": classify_pedra(feat),
                    }
                    local_storage_items.append(student_pred)

                batch_num = (stats["total"] - 1) // BATCH_SIZE + 1
                total_batches = (n + BATCH_SIZE - 1) // BATCH_SIZE
                print(
                    f"  [batch {batch_num:3d}/{total_batches}] "
                    f"{len(batch_inst)} inst  "
                    f"profiles=[{combined_label[:50]}]"
                )
            else:
                stats["errors"] += len(batch_inst)
                print(f"  ERROR {r.status_code}: {r.text[:80]}")
        except Exception as exc:
            stats["errors"] += len(batch_inst)
            print(f"  EXCEPTION: {exc}")
        time.sleep(random.uniform(0.05, 0.15))

    for i in range(n):
        profile = profile_assignments[i]
        instance = generate_instance(profile)
        label = profile["label"] if profile else "Random"
        batch_instances.append(instance)
        batch_labels.append(label)

        if len(batch_instances) >= BATCH_SIZE:
            flush_batch(batch_instances, batch_labels)
            batch_instances = []
            batch_labels = []

    # Flush remaining
    flush_batch(batch_instances, batch_labels)

    print(f"\n{'='*60}")
    print("  Resultado:")
    print(f"    Requisições enviadas : {stats['total']}")
    print(f"    Alto risco           : {stats['high_risk']}")
    print(f"    Risco moderado       : {stats['medium_risk']}")
    print(f"    Baixo risco          : {stats['low_risk']}")
    print(f"    Erros                : {stats['errors']}")
    print(f"{'='*60}\n")

    # Write a JS snippet the user can paste in browser console
    js_path = "scripts/seed_localstorage.js"
    ls_json = json.dumps(local_storage_items, ensure_ascii=False)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(
            "// Cole este script no Console do navegador (F12) na página do portal\n"
            "// Ele injeta as predições no localStorage para popular a aba Alunos\n"
            f"const data = {ls_json};\n"
            "const key = 'passos-magicos-predictions';\n"
            "const existing = JSON.parse(localStorage.getItem(key) || '[]');\n"
            "const merged = [...existing, ...data];\n"
            "localStorage.setItem(key, JSON.stringify(merged));\n"
            f"console.log(`[OK] {len(local_storage_items)} predicoes injetadas! "
            "Recarregue a página.`);\n"
            "location.reload();\n"
        )
    print(f"  Script JS salvo em: {js_path}")
    print("     Abra o portal, pressione F12, cole o conteudo e Enter.\n")
    print("  Ou acesse: http://localhost:8080 > Predicao > use o formulario.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed prediction data for the portal")
    parser.add_argument(
        "--url", default="http://localhost:8080/api", help="Base API URL"
    )
    parser.add_argument(
        "--n", type=int, default=100, help="Number of prediction requests"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    args = parser.parse_args()
    random.seed(args.seed)
    send_predictions(args.url, args.n)
