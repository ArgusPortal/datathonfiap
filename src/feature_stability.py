"""
Feature Stability Analysis — avalia estabilidade e robustez de features para produção.

Identifica features com alta importância + baixa estabilidade temporal,
sugerindo ações de mitigação para um modelo production-ready.

Uso:
    from src.feature_stability import assess_feature_stability, generate_stability_report
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import fbeta_score, make_scorer
from sklearn.model_selection import KFold

logger = logging.getLogger(__name__)


def compute_psi(
    baseline: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """
    Calcula Population Stability Index entre duas distribuições.

    Args:
        baseline: Array de valores de referência (treino)
        current: Array de valores atuais
        n_bins: Número de bins para discretização
        epsilon: Valor mínimo para evitar log(0)

    Returns:
        PSI value (0=estável, >0.2=drift significativo)
    """
    # Remove NaN
    baseline = baseline[~np.isnan(baseline)]
    current = current[~np.isnan(current)]

    if len(baseline) < 2 or len(current) < 2:
        return 0.0

    # Usa bins do baseline para ambas distribuições
    _, bin_edges = np.histogram(baseline, bins=n_bins)
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    baseline_counts = np.histogram(baseline, bins=bin_edges)[0] + epsilon
    current_counts = np.histogram(current, bins=bin_edges)[0] + epsilon

    baseline_pct = baseline_counts / baseline_counts.sum()
    current_pct = current_counts / current_counts.sum()

    psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    return float(psi)


def compute_cross_fold_stability(
    X: pd.DataFrame,
    y: pd.Series,
    model,
    n_splits: int = 5,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    """
    Avalia estabilidade de importância de features entre folds de cross-validation.

    Uma feature estável tem importância similar em todos os folds.
    Alta variância indica que a feature é instável e pode ser sensível a drift.

    Args:
        X: Features
        y: Target
        model: Modelo sklearn (ou Pipeline)
        n_splits: Número de folds
        seed: Random seed

    Returns:
        Dict com mean_importance, std_importance, cv_importance por feature
    """
    f2_scorer = make_scorer(fbeta_score, beta=2)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)

    fold_importances = []

    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # Clone and fit model
        from sklearn.base import clone

        fold_model = clone(model)
        fold_model.fit(X_train, y_train)

        # Permutation importance on test fold
        result = permutation_importance(
            fold_model,
            X_test,
            y_test,
            n_repeats=10,
            random_state=seed,
            scoring=f2_scorer,
        )

        fold_imp = dict(zip(X.columns, result.importances_mean))
        fold_importances.append(fold_imp)
        logger.debug(
            f"Fold {fold_idx + 1}: computed importances for {len(fold_imp)} features"
        )

    # Aggregate across folds
    stability = {}
    for feat in X.columns:
        values = [fi[feat] for fi in fold_importances]
        mean_imp = np.mean(values)
        std_imp = np.std(values)
        cv_imp = std_imp / max(abs(mean_imp), 1e-8)  # Coefficient of variation
        stability[feat] = {
            "mean_importance": float(mean_imp),
            "std_importance": float(std_imp),
            "cv_importance": float(cv_imp),
            "fold_importances": [float(v) for v in values],
        }

    return stability


def compute_temporal_psi(
    X: pd.DataFrame,
    split_ratio: float = 0.5,
) -> Dict[str, float]:
    """
    Calcula PSI entre primeira e segunda metade do dataset
    (simula drift temporal quando dados históricos não estão disponíveis).

    Args:
        X: DataFrame de features (ordenado temporalmente)
        split_ratio: Ratio de split (default: 50/50)

    Returns:
        Dict feature_name → PSI value
    """
    split_idx = int(len(X) * split_ratio)
    baseline = X.iloc[:split_idx]
    current = X.iloc[split_idx:]

    psi_scores = {}
    for col in X.select_dtypes(include=[np.number]).columns:
        psi_scores[col] = compute_psi(baseline[col].values, current[col].values)

    return psi_scores


def assess_feature_stability(
    X: pd.DataFrame,
    y: pd.Series,
    model,
    perm_importances: Optional[Dict[str, float]] = None,
    n_splits: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Análise completa de estabilidade de features combinando:
    1. Permutation importance (impacto no F2)
    2. Estabilidade cross-fold (variância da importância)
    3. PSI temporal (estabilidade da distribuição)
    4. Missing rate

    Features são classificadas em quadrantes:
    - ROBUST: alta importância + baixo PSI → manter
    - VOLATILE: alta importância + alto PSI → monitorar/retreinar
    - NOISE: baixa importância + alto PSI → candidata a remoção
    - STABLE: baixa importância + baixo PSI → manter se leve, avaliar remoção

    Args:
        X: Features DataFrame
        y: Target Series
        model: Modelo sklearn
        perm_importances: Dict pré-computado de importâncias (se None, calcula)
        n_splits: Folds para cross-fold stability
        seed: Random seed

    Returns:
        DataFrame com assessment por feature
    """
    logger.info(f"Assessing stability for {len(X.columns)} features...")

    # 1. Permutation importance
    if perm_importances is None:
        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=seed, stratify=y
        )
        f2_scorer = make_scorer(fbeta_score, beta=2)
        result = permutation_importance(
            model, X_test, y_test, n_repeats=30, random_state=seed, scoring=f2_scorer
        )
        perm_importances = dict(zip(X.columns, result.importances_mean))

    # 2. Temporal PSI
    psi_scores = compute_temporal_psi(X)

    # 3. Missing rate
    missing_rates = X.isna().mean().to_dict()

    # 4. Build assessment DataFrame
    rows = []
    for feat in X.columns:
        imp = perm_importances.get(feat, 0.0)
        psi = psi_scores.get(feat, 0.0)
        miss = missing_rates.get(feat, 0.0)

        # Classify into quadrant
        high_importance = imp > 0.01
        high_psi = psi > 0.1

        if high_importance and not high_psi:
            quadrant = "ROBUST"
        elif high_importance and high_psi:
            quadrant = "VOLATILE"
        elif not high_importance and high_psi:
            quadrant = "NOISE"
        else:
            quadrant = "STABLE"

        # Action recommendation
        if quadrant == "ROBUST":
            action = "Manter — feature estável e preditiva"
        elif quadrant == "VOLATILE":
            action = (
                "Monitorar — preditiva mas sensível a drift, retreinar se necessário"
            )
        elif quadrant == "NOISE":
            action = "Considerar remoção — causa drift sem contribuir para predição"
        else:
            if imp <= 0:
                action = "Avaliar remoção — importância nula ou negativa"
            else:
                action = "Manter — contribuição marginal mas estável"

        rows.append(
            {
                "feature": feat,
                "perm_importance": round(imp, 6),
                "temporal_psi": round(psi, 4),
                "missing_rate": round(miss, 3),
                "quadrant": quadrant,
                "action": action,
            }
        )

    df_result = pd.DataFrame(rows).sort_values("perm_importance", ascending=False)
    df_result = df_result.reset_index(drop=True)

    # Log summary
    for q in ["ROBUST", "VOLATILE", "NOISE", "STABLE"]:
        count = len(df_result[df_result["quadrant"] == q])
        feats = df_result[df_result["quadrant"] == q]["feature"].tolist()
        if feats:
            logger.info(f"  {q} ({count}): {feats}")

    return df_result


def generate_stability_report(
    stability_df: pd.DataFrame,
    model_version: str = "v1.1.0",
) -> str:
    """
    Gera relatório textual de estabilidade de features.

    Args:
        stability_df: Output de assess_feature_stability()
        model_version: Versão do modelo

    Returns:
        Relatório em Markdown
    """
    lines = [
        f"# Feature Stability Report — {model_version}",
        "",
        "## Resumo por Quadrante",
        "",
        "| Quadrante | Qtd | Descrição |",
        "|-----------|-----|-----------|",
    ]

    for q, desc in [
        ("ROBUST", "Alta importância + baixo PSI → **manter**"),
        ("VOLATILE", "Alta importância + alto PSI → **monitorar/retreinar**"),
        ("NOISE", "Baixa importância + alto PSI → **candidata a remoção**"),
        ("STABLE", "Baixa importância + baixo PSI → **manter se leve**"),
    ]:
        count = len(stability_df[stability_df["quadrant"] == q])
        lines.append(f"| {q} | {count} | {desc} |")

    lines.extend(["", "## Detalhamento por Feature", ""])
    lines.append("| Feature | Importance | PSI | Missing | Quadrante | Ação |")
    lines.append("|---------|-----------|-----|---------|-----------|------|")

    for _, row in stability_df.iterrows():
        lines.append(
            f"| {row['feature']} | {row['perm_importance']:+.4f} | "
            f"{row['temporal_psi']:.4f} | {row['missing_rate']:.1%} | "
            f"{row['quadrant']} | {row['action']} |"
        )

    # Recommendations
    volatile = stability_df[stability_df["quadrant"] == "VOLATILE"]
    noise = stability_df[stability_df["quadrant"] == "NOISE"]

    lines.extend(["", "## Recomendações", ""])

    if len(volatile) > 0:
        lines.append("### Features Voláteis (alta importância + drift)")
        lines.append("")
        for _, row in volatile.iterrows():
            lines.append(
                f"- **{row['feature']}** (imp={row['perm_importance']:+.4f}, PSI={row['temporal_psi']:.4f})"
            )
        lines.append("")
        lines.append(
            "**Ação**: Manter no modelo mas com monitoramento ativo de drift. "
            "Se PSI > 0.25 em produção, disparar retreinamento automático."
        )
        lines.append("")

    if len(noise) > 0:
        lines.append("### Features Ruidosas (baixa importância + drift)")
        lines.append("")
        for _, row in noise.iterrows():
            lines.append(
                f"- **{row['feature']}** (imp={row['perm_importance']:+.4f}, PSI={row['temporal_psi']:.4f})"
            )
        lines.append("")
        lines.append(
            "**Ação**: Testar remoção destas features. Elas contribuem pouco para "
            "o modelo mas geram alertas de drift desnecessários. Retreinar sem elas "
            "e comparar F2-score — se não degradar, remover."
        )
        lines.append("")

    negative = stability_df[stability_df["perm_importance"] < 0]
    if len(negative) > 0:
        lines.append("### Features com Importância Negativa")
        lines.append("")
        for _, row in negative.iterrows():
            lines.append(f"- **{row['feature']}** (imp={row['perm_importance']:+.4f})")
        lines.append("")
        lines.append(
            "**Ação**: Remover imediatamente — estas features prejudicam o modelo. "
            "O F2-score **melhora** quando removidas."
        )
        lines.append("")

    return "\n".join(lines)
