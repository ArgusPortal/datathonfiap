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

# Format: (mean, std, min, max) — sampled via truncated normal
# Integer features use round(); binary features use weighted coin.
TRAINING_DISTS = {
    # -- PEDE indicators (continuous 0-10) --
    "iaa_2023": (7.00, 3.57, 0.0, 10.0),
    "ian_2023": (7.41, 2.52, 2.5, 10.0),
    "ida_2023": (6.83, 1.48, 2.2, 10.0),
    "ieg_2023": (8.87, 0.97, 3.7, 10.0),
    "ipp_2023": (7.62, 0.98, 4.38, 9.79),
    "ips_2023": (5.16, 2.09, 2.52, 9.38),
    "ipv_2023": (8.12, 0.92, 3.32, 10.01),
    # -- Deltas 2022→2023 --
    "delta_iaa_2022_2023": (-1.78, 3.84, -10.0, 9.6),
    "delta_ian_2022_2023": (0.49, 2.70, -5.0, 7.5),
    "delta_ida_2022_2023": (0.08, 1.56, -5.7, 5.3),
    "delta_ieg_2022_2023": (0.22, 0.99, -2.8, 4.7),
    "delta_ips_2022_2023": (-1.92, 2.04, -6.88, 3.12),
    "delta_ipv_2022_2023": (0.55, 0.93, -2.08, 2.78),
    # -- Demographics --
    "idade_2023": (12.29, 3.37, 7, 26),
    "ano_ingresso_2023": (2021.29, 1.89, 2016, 2023),
    "anos_pm_2023": (1.71, 1.89, 0, 7),
    "fase_2023": (3, 2.5, 1, 8),  # ordinal 1-8
}

# Binary / discrete features with their P(=1) from training data
BINARY_DISTS = {
    "genero_2023": 0.46,  # P(male)=46%
    "has_prev_year_data": 0.61,  # 61% have previous year data
}

# Missing indicators — all default to 0, set to 1 when indicator is None
MISSING_FLAGS = [
    "iaa_2023_missing",
    "ida_2023_missing",
    "ieg_2023_missing",
    "ipp_2023_missing",
    "ips_2023_missing",
    "ipv_2023_missing",
]

# Categorical feature — sampled proportionally to training distribution
INSTITUICAO_WEIGHTS = {
    0: 0.762,  # Publica (583/765)
    1: 0.118,  # Privada_Apadrinhamento (90/765)
    2: 0.084,  # Privada_Bolsa (64/765)
    3: 0.029,  # Privada (22/765)
    4: 0.007,  # Concluiu_EM (5/765)
}

# ---------- predefined profiles (shift mean/std for each archetype) ----------
PROFILES = [
    {
        "label": "Alto risco - indicadores baixos",
        "overrides": {
            "iaa_2023": (2.5, 2.0, 0.0, 5.0),
            "ian_2023": (3.0, 1.5, 2.5, 5.5),
            "ida_2023": (4.0, 1.2, 2.2, 6.0),
            "ieg_2023": (5.5, 1.5, 3.7, 7.5),
            "ipp_2023": (5.5, 1.0, 4.38, 7.0),
            "ips_2023": (3.0, 0.8, 2.52, 4.5),
            "ipv_2023": (5.5, 1.5, 3.32, 7.5),
            "delta_iaa_2022_2023": (-3.5, 2.5, -10.0, 0.0),
            "delta_ian_2022_2023": (-1.5, 2.0, -5.0, 1.0),
        },
    },
    {
        "label": "Baixo risco - indicadores altos",
        "overrides": {
            "iaa_2023": (9.0, 1.0, 7.0, 10.0),
            "ian_2023": (9.0, 1.0, 7.5, 10.0),
            "ida_2023": (8.5, 1.0, 6.5, 10.0),
            "ieg_2023": (9.5, 0.4, 8.5, 10.0),
            "ipp_2023": (8.5, 0.6, 7.5, 9.79),
            "ips_2023": (7.5, 1.2, 5.0, 9.38),
            "ipv_2023": (9.0, 0.5, 7.5, 10.01),
            "delta_iaa_2022_2023": (1.5, 2.0, 0.0, 9.6),
            "delta_ian_2022_2023": (1.5, 1.5, 0.0, 7.5),
        },
    },
    {
        "label": "Risco moderado - indicadores medianos",
        "overrides": {
            "iaa_2023": (6.0, 2.0, 3.0, 8.5),
            "ian_2023": (6.5, 1.5, 4.0, 8.5),
            "ida_2023": (6.0, 1.0, 4.5, 7.5),
            "ieg_2023": (8.0, 0.8, 6.5, 9.5),
            "ipp_2023": (7.0, 0.8, 5.5, 8.5),
            "ips_2023": (4.5, 1.5, 2.52, 7.0),
            "ipv_2023": (7.5, 0.8, 5.5, 9.0),
        },
    },
    {
        "label": "Aluno novo sem historico",
        "overrides": {
            "has_prev_year_data": 0,  # fixed value, not a distribution
            "anos_pm_2023": (0.5, 0.5, 0, 1),
            "ano_ingresso_2023": (2023, 0.3, 2022, 2023),
            "delta_iaa_2022_2023": (0, 0.01, 0, 0),
            "delta_ian_2022_2023": (0, 0.01, 0, 0),
            "delta_ida_2022_2023": (0, 0.01, 0, 0),
            "delta_ieg_2022_2023": (0, 0.01, 0, 0),
            "delta_ips_2022_2023": (0, 0.01, 0, 0),
            "delta_ipv_2022_2023": (0, 0.01, 0, 0),
        },
        "force_missing": True,  # force all _missing flags = 1
    },
    {
        "label": "Aluno veterano fase avancada",
        "overrides": {
            "fase_2023": (7, 1.0, 6, 8),
            "anos_pm_2023": (5, 1.5, 3, 7),
            "idade_2023": (17, 2.0, 15, 26),
            "ano_ingresso_2023": (2018, 1.5, 2016, 2021),
            "has_prev_year_data": 1,  # fixed value
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


# Features that can realistically be missing (indicators from assessments)
NULLABLE_FEATURES = [
    "iaa_2023",
    "ian_2023",
    "ida_2023",
    "ieg_2023",
    "ipp_2023",
    "ips_2023",
    "ipv_2023",
]


def generate_instance(profile=None):
    overrides = profile.get("overrides", {}) if profile else {}
    force_missing = profile.get("force_missing", False) if profile else False
    inst = {}

    # 1. Sample continuous/integer features from truncated normals
    for feat, (mean, std, lo, hi) in TRAINING_DISTS.items():
        if feat in overrides:
            ov = overrides[feat]
            if isinstance(ov, (int, float)):
                # Fixed value override
                inst[feat] = ov
            else:
                inst[feat] = round(trunc_normal(*ov), 2)
        else:
            inst[feat] = round(trunc_normal(mean, std, lo, hi), 2)

    # Round integer-type features
    for int_feat in ("idade_2023", "ano_ingresso_2023", "anos_pm_2023", "fase_2023"):
        if int_feat in inst:
            inst[int_feat] = int(round(inst[int_feat]))

    # 2. Binary features
    for feat, p_one in BINARY_DISTS.items():
        if feat in overrides:
            ov = overrides[feat]
            inst[feat] = (
                ov if isinstance(ov, int) else (1 if random.random() < ov else 0)
            )
        else:
            inst[feat] = 1 if random.random() < p_one else 0

    # 3. Categorical: instituicao
    inst["instituicao_2023"] = random.choices(
        list(INSTITUICAO_WEIGHTS.keys()),
        weights=list(INSTITUICAO_WEIGHTS.values()),
    )[0]

    # 4. Missing indicator flags (default 0)
    for flag in MISSING_FLAGS:
        inst[flag] = 0

    # 5. Simulate missing PEDE indicators (~9-10% missing, matching training data)
    if force_missing:
        for feat in NULLABLE_FEATURES:
            inst[feat] = None
            flag = feat + "_missing"
            if flag in inst:
                inst[flag] = 1
    elif random.random() < 0.15:
        n_missing = random.randint(1, 3)
        for feat in random.sample(
            NULLABLE_FEATURES, min(n_missing, len(NULLABLE_FEATURES))
        ):
            inst[feat] = None
            flag = feat + "_missing"
            if flag in inst:
                inst[flag] = 1

    # 6. Compute derived features from individual indicators (consistent)
    indicator_keys = [
        "iaa_2023",
        "ian_2023",
        "ida_2023",
        "ieg_2023",
        "ipp_2023",
        "ips_2023",
        "ipv_2023",
    ]
    indicators = [inst[k] for k in indicator_keys if inst.get(k) is not None]
    if indicators:
        inst["media_indicadores"] = round(sum(indicators) / len(indicators), 2)
        inst["max_indicador"] = round(max(indicators), 2)
        inst["min_indicador"] = round(min(indicators), 2)
        inst["range_indicadores"] = round(max(indicators) - min(indicators), 2)
        if len(indicators) > 1:
            mean_ind = sum(indicators) / len(indicators)
            inst["std_indicadores"] = round(
                (sum((x - mean_ind) ** 2 for x in indicators) / len(indicators)) ** 0.5,
                2,
            )
        else:
            inst["std_indicadores"] = 0.0
    else:
        inst["media_indicadores"] = None
        inst["max_indicador"] = None
        inst["min_indicador"] = None
        inst["range_indicadores"] = None
        inst["std_indicadores"] = None

    # 7. Compute fase_x_media interaction
    if inst.get("media_indicadores") is not None:
        inst["fase_x_media"] = round(inst["fase_2023"] * inst["media_indicadores"], 2)
    else:
        inst["fase_x_media"] = None

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
                        "model_version": pred.get("model_version", "v1.1.0"),
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
