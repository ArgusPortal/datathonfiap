"""
Seed predictions – sends diverse inference requests to the running API
and generates localStorage-compatible JSON so the Students page is populated.

Usage:
    python scripts/seed_predictions.py [--url http://localhost:8080/api] [--n 30]
"""

import argparse
import json
import random
import sys
import time
import uuid

import requests

# ---------- realistic value ranges per feature ----------
# Ranges designed to match training distribution so drift detection stays green.
# Drift bins: <4 = low, 4-7 = medium, >=7 = high.
# fase_x_media is derived (fase_2023 * media_indicadores), not independent.
FEATURE_RANGES = {
    "ano_ingresso_2023": (2016, 2023),
    "anos_pm_2023": (1, 8),
    "delta_iaa_2022_2023": (-3.0, 3.0),
    "delta_ian_2022_2023": (-3.0, 3.0),
    "delta_ida_2022_2023": (-3.0, 3.0),
    "delta_ieg_2022_2023": (-3.0, 3.0),
    "delta_ips_2022_2023": (-3.0, 3.0),
    "delta_ipv_2022_2023": (-3.0, 3.0),
    "fase_2023": (1, 8),
    # fase_x_media is computed from fase_2023 * media_indicadores
    "genero_2023": (0, 1),
    "has_prev_year_data": (0, 1),
    "iaa_2023": (0.0, 10.0),
    "iaa_2023_missing": (0, 1),
    "ian_2023": (0.0, 10.0),
    "ida_2023": (0.0, 10.0),
    "ida_2023_missing": (0, 1),
    "idade_2023": (7, 20),
    "ieg_2023": (0.0, 10.0),
    "ieg_2023_missing": (0, 1),
    "instituicao_2023": (0, 5),
    "ipp_2023": (0.0, 10.0),
    "ipp_2023_missing": (0, 1),
    "ips_2023": (0.0, 10.0),
    "ips_2023_missing": (0, 1),
    "ipv_2023": (0.0, 10.0),
    "ipv_2023_missing": (0, 1),
    "max_indicador": (0.0, 10.0),
    "media_indicadores": (0.0, 10.0),
    "min_indicador": (0.0, 10.0),
    "range_indicadores": (0.0, 8.0),
    "std_indicadores": (0.0, 4.0),
}

# ---------- predefined profiles ----------
PROFILES = [
    {
        "label": "Alto risco - indicadores baixos",
        "overrides": {
            "iaa_2023": (0.5, 3.0),
            "ian_2023": (0.5, 3.0),
            "ida_2023": (0.5, 3.0),
            "ieg_2023": (0.5, 3.0),
            "ipp_2023": (0.5, 3.0),
            "ips_2023": (0.5, 3.0),
            "ipv_2023": (0.5, 3.0),
            "media_indicadores": (0.5, 3.0),
            "max_indicador": (1.0, 4.0),
            "min_indicador": (0.0, 2.0),
            "delta_iaa_2022_2023": (-3.0, -0.5),
            "delta_ian_2022_2023": (-3.0, -0.5),
        },
    },
    {
        "label": "Baixo risco - indicadores altos",
        "overrides": {
            "iaa_2023": (7.0, 10.0),
            "ian_2023": (7.0, 10.0),
            "ida_2023": (7.0, 10.0),
            "ieg_2023": (7.0, 10.0),
            "ipp_2023": (7.0, 10.0),
            "ips_2023": (7.0, 10.0),
            "ipv_2023": (7.0, 10.0),
            "media_indicadores": (7.0, 10.0),
            "max_indicador": (8.0, 10.0),
            "min_indicador": (5.0, 8.0),
            "delta_iaa_2022_2023": (0.5, 3.0),
            "delta_ian_2022_2023": (0.5, 3.0),
        },
    },
    {
        "label": "Risco moderado - indicadores medianos",
        "overrides": {
            "iaa_2023": (4.0, 6.0),
            "ian_2023": (4.0, 6.0),
            "ida_2023": (4.0, 6.0),
            "ieg_2023": (4.0, 6.0),
            "ipp_2023": (4.0, 6.0),
            "ips_2023": (4.0, 6.0),
            "ipv_2023": (4.0, 6.0),
            "media_indicadores": (4.0, 6.0),
        },
    },
    {
        "label": "Aluno novo sem historico",
        "overrides": {
            "has_prev_year_data": (0, 0),
            "anos_pm_2023": (1, 1),
            "delta_iaa_2022_2023": (0, 0),
            "delta_ian_2022_2023": (0, 0),
            "delta_ida_2022_2023": (0, 0),
            "delta_ieg_2022_2023": (0, 0),
            "delta_ips_2022_2023": (0, 0),
            "delta_ipv_2022_2023": (0, 0),
            "iaa_2023_missing": (1, 1),
            "ida_2023_missing": (1, 1),
            "ieg_2023_missing": (1, 1),
            "ipp_2023_missing": (1, 1),
            "ips_2023_missing": (1, 1),
            "ipv_2023_missing": (1, 1),
        },
    },
    {
        "label": "Aluno veterano fase avancada",
        "overrides": {
            "fase_2023": (6, 8),
            "anos_pm_2023": (5, 8),
            "idade_2023": (15, 20),
            "ano_ingresso_2023": (2016, 2019),
            "has_prev_year_data": (1, 1),
        },
    },
]


def rand_val(lo, hi):
    if isinstance(lo, int) and isinstance(hi, int):
        return random.randint(lo, hi)
    return round(random.uniform(lo, hi), 2)


def generate_instance(profile=None):
    ranges = dict(FEATURE_RANGES)
    if profile:
        ranges.update(profile["overrides"])
    inst = {feat: rand_val(*rng) for feat, rng in ranges.items()}
    # Derive fase_x_media from actual feature values (keeps internal consistency)
    inst["fase_x_media"] = round(inst["fase_2023"] * inst["media_indicadores"], 2)
    # Ensure aggregated indicators are consistent with individual ones
    indicators = [inst.get(k, 5.0) for k in
                  ["iaa_2023", "ian_2023", "ida_2023", "ieg_2023",
                   "ipp_2023", "ips_2023", "ipv_2023"]]
    inst["media_indicadores"] = round(sum(indicators) / len(indicators), 2)
    inst["max_indicador"] = round(max(indicators), 2)
    inst["min_indicador"] = round(min(indicators), 2)
    inst["range_indicadores"] = round(max(indicators) - min(indicators), 2)
    inst["std_indicadores"] = round(
        (sum((x - inst["media_indicadores"])**2 for x in indicators)
         / len(indicators)) ** 0.5, 2)
    # Recompute fase_x_media with corrected media
    inst["fase_x_media"] = round(inst["fase_2023"] * inst["media_indicadores"], 2)
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
    print(f"  Resultado:")
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
    print(f"     Abra o portal, pressione F12, cole o conteudo e Enter.\n")
    print(f"  Ou acesse: http://localhost:8080 > Predicao > use o formulario.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed prediction data for the portal"
    )
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
