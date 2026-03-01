"""Tests for src/feature_stability.py — feature stability analysis utilities."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

from src.feature_stability import (
    compute_psi,
    compute_temporal_psi,
    compute_cross_fold_stability,
    assess_feature_stability,
    generate_stability_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rng():
    """Seeded random generator for reproducibility."""
    return np.random.RandomState(42)


@pytest.fixture
def sample_X(rng):
    """Simple numeric DataFrame with 100 rows / 4 features."""
    return pd.DataFrame(
        {
            "feat_a": rng.normal(0, 1, 100),
            "feat_b": rng.normal(5, 2, 100),
            "feat_c": rng.uniform(0, 10, 100),
            "feat_d": rng.randint(0, 2, 100).astype(float),
        }
    )


@pytest.fixture
def sample_y(rng):
    """Binary target aligned with sample_X (100 rows)."""
    return pd.Series(rng.randint(0, 2, 100), name="target")


@pytest.fixture
def simple_model(sample_X, sample_y):
    """A fast LogisticRegression fitted on sample data."""
    model = LogisticRegression(max_iter=200, random_state=42)
    model.fit(sample_X, sample_y)
    return model


@pytest.fixture
def dummy_model(sample_X, sample_y):
    """DummyClassifier (constant strategy) — fastest possible model."""
    model = DummyClassifier(strategy="most_frequent")
    model.fit(sample_X, sample_y)
    return model


@pytest.fixture
def mixed_df(rng):
    """DataFrame with numeric + categorical columns."""
    return pd.DataFrame(
        {
            "num1": rng.normal(0, 1, 80),
            "num2": rng.uniform(0, 5, 80),
            "cat1": np.random.choice(["a", "b", "c"], 80),
            "cat2": np.random.choice(["x", "y"], 80),
        }
    )


@pytest.fixture
def stability_df():
    """Pre-built stability DataFrame matching assess_feature_stability output."""
    return pd.DataFrame(
        {
            "feature": ["feat_a", "feat_b", "feat_c", "feat_d"],
            "perm_importance": [0.15, 0.12, 0.01, 0.005],
            "temporal_psi": [0.02, 0.25, 0.30, 0.03],
            "missing_rate": [0.0, 0.05, 0.10, 0.0],
            "quadrant": ["ROBUST", "VOLATILE", "NOISE", "STABLE"],
            "action": ["keep", "investigate", "consider_removal", "keep"],
        }
    )


# ===========================================================================
# compute_psi
# ===========================================================================


class TestComputePsi:
    """Tests for compute_psi."""

    @pytest.mark.unit
    def test_identical_distributions_psi_near_zero(self, rng):
        arr = rng.normal(0, 1, 500)
        psi = compute_psi(arr, arr.copy())
        assert psi < 0.01, f"PSI for identical arrays should be ~0, got {psi}"

    @pytest.mark.unit
    def test_similar_distributions_low_psi(self, rng):
        baseline = rng.normal(0, 1, 1000)
        current = rng.normal(0, 1, 1000)
        psi = compute_psi(baseline, current)
        assert psi < 0.1, f"PSI for similar normals should be low, got {psi}"

    @pytest.mark.unit
    def test_very_different_distributions_high_psi(self, rng):
        baseline = rng.normal(0, 1, 500)
        current = rng.normal(10, 1, 500)
        psi = compute_psi(baseline, current)
        assert psi > 0.2, f"PSI for shifted normals should be high, got {psi}"

    @pytest.mark.unit
    def test_empty_array_returns_zero(self):
        psi = compute_psi(np.array([]), np.array([]))
        assert psi == 0.0

    @pytest.mark.unit
    def test_single_element_returns_zero(self):
        psi = compute_psi(np.array([1.0]), np.array([2.0]))
        assert psi == 0.0

    @pytest.mark.unit
    def test_two_elements_returns_value(self, rng):
        baseline = rng.normal(0, 1, 50)
        current = rng.normal(0, 1, 50)
        psi = compute_psi(baseline, current)
        assert isinstance(psi, float)
        assert psi >= 0.0

    @pytest.mark.unit
    def test_nan_values_are_removed(self, rng):
        baseline = np.concatenate([rng.normal(0, 1, 100), [np.nan] * 10])
        current = np.concatenate([rng.normal(0, 1, 100), [np.nan] * 5])
        psi = compute_psi(baseline, current)
        assert np.isfinite(psi), "PSI should be finite after NaN removal"
        assert psi >= 0.0

    @pytest.mark.unit
    def test_all_nan_returns_zero(self):
        psi = compute_psi(np.array([np.nan, np.nan]), np.array([np.nan, np.nan]))
        assert psi == 0.0

    @pytest.mark.unit
    def test_n_bins_parameter(self, rng):
        baseline = rng.normal(0, 1, 200)
        current = rng.normal(0.5, 1, 200)
        psi_2 = compute_psi(baseline, current, n_bins=2)
        psi_20 = compute_psi(baseline, current, n_bins=20)
        # Both should be non-negative floats
        assert psi_2 >= 0.0
        assert psi_20 >= 0.0

    @pytest.mark.unit
    def test_psi_is_non_negative(self, rng):
        baseline = rng.uniform(0, 10, 300)
        current = rng.uniform(2, 8, 300)
        psi = compute_psi(baseline, current)
        assert psi >= 0.0, "PSI must be non-negative"

    @pytest.mark.unit
    def test_psi_returns_float(self, rng):
        psi = compute_psi(rng.normal(0, 1, 50), rng.normal(0, 1, 50))
        assert isinstance(psi, float)

    @pytest.mark.unit
    @pytest.mark.parametrize("size", [2, 5, 10, 50])
    def test_various_array_sizes(self, rng, size):
        baseline = rng.normal(0, 1, size)
        current = rng.normal(0, 1, size)
        psi = compute_psi(baseline, current)
        assert isinstance(psi, float)
        assert psi >= 0.0


# ===========================================================================
# compute_temporal_psi
# ===========================================================================


class TestComputeTemporalPsi:
    """Tests for compute_temporal_psi."""

    @pytest.mark.unit
    def test_returns_dict(self, sample_X):
        result = compute_temporal_psi(sample_X)
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_keys_match_numeric_columns(self, sample_X):
        result = compute_temporal_psi(sample_X)
        numeric_cols = sample_X.select_dtypes(include=[np.number]).columns.tolist()
        assert set(result.keys()) == set(numeric_cols)

    @pytest.mark.unit
    def test_excludes_categorical_columns(self, mixed_df):
        result = compute_temporal_psi(mixed_df)
        assert "cat1" not in result
        assert "cat2" not in result
        assert "num1" in result
        assert "num2" in result

    @pytest.mark.unit
    def test_values_are_non_negative(self, sample_X):
        result = compute_temporal_psi(sample_X)
        for feat, psi_val in result.items():
            assert psi_val >= 0.0, f"PSI for {feat} should be >= 0, got {psi_val}"

    @pytest.mark.unit
    def test_identical_halves_low_psi(self):
        """When first half == second half, PSI should be ~0."""
        half = np.arange(50, dtype=float)
        df = pd.DataFrame({"x": np.tile(half, 2)})
        result = compute_temporal_psi(df)
        assert result["x"] < 0.05

    @pytest.mark.unit
    def test_custom_split_ratio(self, sample_X):
        result = compute_temporal_psi(sample_X, split_ratio=0.3)
        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.unit
    def test_single_column_df(self, rng):
        df = pd.DataFrame({"only": rng.normal(0, 1, 60)})
        result = compute_temporal_psi(df)
        assert "only" in result

    @pytest.mark.unit
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = compute_temporal_psi(df)
        assert result == {}


# ===========================================================================
# compute_cross_fold_stability
# ===========================================================================


class TestComputeCrossFoldStability:
    """Tests for compute_cross_fold_stability."""

    @pytest.mark.unit
    def test_returns_dict(self, sample_X, sample_y, dummy_model):
        result = compute_cross_fold_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_keys_are_features(self, sample_X, sample_y, dummy_model):
        result = compute_cross_fold_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        for col in sample_X.columns:
            assert col in result, f"Feature {col} should be in result"

    @pytest.mark.unit
    def test_per_feature_stats_structure(self, sample_X, sample_y, dummy_model):
        result = compute_cross_fold_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        for feat, stats in result.items():
            assert "mean_importance" in stats, f"Missing 'mean_importance' for {feat}"
            assert "std_importance" in stats, f"Missing 'std_importance' for {feat}"
            assert "cv_importance" in stats, f"Missing 'cv_importance' for {feat}"
            assert "fold_importances" in stats, f"Missing 'fold_importances' for {feat}"

    @pytest.mark.unit
    def test_mean_is_numeric(self, sample_X, sample_y, dummy_model):
        result = compute_cross_fold_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        for feat, stats in result.items():
            assert isinstance(
                stats["mean_importance"], (float, np.floating)
            ), f"mean_importance for {feat} should be float"

    @pytest.mark.unit
    def test_std_non_negative(self, sample_X, sample_y, dummy_model):
        result = compute_cross_fold_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        for feat, stats in result.items():
            assert (
                stats["std_importance"] >= 0.0
            ), f"std_importance for {feat} should be >= 0"

    @pytest.mark.slow
    def test_more_splits(self, sample_X, sample_y, simple_model):
        result = compute_cross_fold_stability(
            sample_X, sample_y, simple_model, n_splits=5, seed=42
        )
        assert len(result) == len(sample_X.columns)


# ===========================================================================
# assess_feature_stability
# ===========================================================================


class TestAssessFeatureStability:
    """Tests for assess_feature_stability."""

    @pytest.mark.unit
    def test_returns_dataframe(self, sample_X, sample_y, dummy_model):
        result = assess_feature_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.unit
    def test_output_columns(self, sample_X, sample_y, dummy_model):
        result = assess_feature_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        expected_cols = {
            "feature",
            "perm_importance",
            "temporal_psi",
            "missing_rate",
            "quadrant",
            "action",
        }
        assert expected_cols.issubset(
            set(result.columns)
        ), f"Missing columns: {expected_cols - set(result.columns)}"

    @pytest.mark.unit
    def test_row_count_matches_features(self, sample_X, sample_y, dummy_model):
        result = assess_feature_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        assert len(result) == len(sample_X.columns)

    @pytest.mark.unit
    def test_quadrant_values_are_valid(self, sample_X, sample_y, dummy_model):
        result = assess_feature_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        valid_quadrants = {"ROBUST", "VOLATILE", "NOISE", "STABLE"}
        for q in result["quadrant"]:
            assert q in valid_quadrants, f"Invalid quadrant: {q}"

    @pytest.mark.unit
    def test_quadrant_robust(self, sample_X, sample_y, dummy_model):
        """High importance + low PSI → ROBUST."""
        perm_imp = {col: 0.5 for col in sample_X.columns}
        with patch("src.feature_stability.compute_temporal_psi") as mock_psi:
            mock_psi.return_value = {col: 0.01 for col in sample_X.columns}
            result = assess_feature_stability(
                sample_X,
                sample_y,
                dummy_model,
                perm_importances=perm_imp,
                n_splits=2,
                seed=42,
            )
        robust_rows = result[result["quadrant"] == "ROBUST"]
        assert len(robust_rows) > 0, "Expected at least one ROBUST feature"

    @pytest.mark.unit
    def test_quadrant_volatile(self, sample_X, sample_y, dummy_model):
        """High importance + high PSI → VOLATILE."""
        perm_imp = {col: 0.5 for col in sample_X.columns}
        with patch("src.feature_stability.compute_temporal_psi") as mock_psi:
            mock_psi.return_value = {col: 0.5 for col in sample_X.columns}
            result = assess_feature_stability(
                sample_X,
                sample_y,
                dummy_model,
                perm_importances=perm_imp,
                n_splits=2,
                seed=42,
            )
        volatile_rows = result[result["quadrant"] == "VOLATILE"]
        assert len(volatile_rows) > 0, "Expected at least one VOLATILE feature"

    @pytest.mark.unit
    def test_quadrant_noise(self, sample_X, sample_y, dummy_model):
        """Low importance + high PSI → NOISE."""
        perm_imp = {col: 0.001 for col in sample_X.columns}
        with patch("src.feature_stability.compute_temporal_psi") as mock_psi:
            mock_psi.return_value = {col: 0.5 for col in sample_X.columns}
            result = assess_feature_stability(
                sample_X,
                sample_y,
                dummy_model,
                perm_importances=perm_imp,
                n_splits=2,
                seed=42,
            )
        noise_rows = result[result["quadrant"] == "NOISE"]
        assert len(noise_rows) > 0, "Expected at least one NOISE feature"

    @pytest.mark.unit
    def test_quadrant_stable(self, sample_X, sample_y, dummy_model):
        """Low importance + low PSI → STABLE."""
        perm_imp = {col: 0.001 for col in sample_X.columns}
        with patch("src.feature_stability.compute_temporal_psi") as mock_psi:
            mock_psi.return_value = {col: 0.01 for col in sample_X.columns}
            result = assess_feature_stability(
                sample_X,
                sample_y,
                dummy_model,
                perm_importances=perm_imp,
                n_splits=2,
                seed=42,
            )
        stable_rows = result[result["quadrant"] == "STABLE"]
        assert len(stable_rows) > 0, "Expected at least one STABLE feature"

    @pytest.mark.unit
    def test_missing_rate_column(self, sample_X, sample_y, dummy_model):
        result = assess_feature_stability(
            sample_X, sample_y, dummy_model, n_splits=2, seed=42
        )
        assert (result["missing_rate"] >= 0.0).all()
        assert (result["missing_rate"] <= 1.0).all()

    @pytest.mark.unit
    def test_with_missing_values(self, sample_y, dummy_model, rng):
        X_with_nan = pd.DataFrame(
            {
                "a": np.concatenate([rng.normal(0, 1, 90), [np.nan] * 10]),
                "b": rng.normal(0, 1, 100),
            }
        )
        result = assess_feature_stability(
            X_with_nan, sample_y, dummy_model, n_splits=2, seed=42
        )
        row_a = result[result["feature"] == "a"]
        assert row_a["missing_rate"].values[0] > 0.0

    @pytest.mark.unit
    def test_perm_importances_parameter_skips_computation(
        self, sample_X, sample_y, dummy_model
    ):
        """When perm_importances is provided, permutation_importance is not called."""
        perm_imp = {col: 0.1 for col in sample_X.columns}
        with patch("src.feature_stability.permutation_importance") as mock_perm:
            result = assess_feature_stability(
                sample_X,
                sample_y,
                dummy_model,
                perm_importances=perm_imp,
                n_splits=2,
                seed=42,
            )
            mock_perm.assert_not_called()
        assert len(result) == len(sample_X.columns)


# ===========================================================================
# generate_stability_report
# ===========================================================================


class TestGenerateStabilityReport:
    """Tests for generate_stability_report."""

    @pytest.mark.unit
    def test_returns_string(self, stability_df):
        report = generate_stability_report(stability_df)
        assert isinstance(report, str)

    @pytest.mark.unit
    def test_contains_markdown_header(self, stability_df):
        report = generate_stability_report(stability_df)
        assert "#" in report, "Report should contain Markdown headers"

    @pytest.mark.unit
    def test_contains_model_version(self, stability_df):
        report = generate_stability_report(stability_df, model_version="v2.0.0")
        assert "v2.0.0" in report

    @pytest.mark.unit
    def test_contains_default_version(self, stability_df):
        report = generate_stability_report(stability_df)
        assert "v1.1.0" in report

    @pytest.mark.unit
    def test_contains_feature_names(self, stability_df):
        report = generate_stability_report(stability_df)
        for feat in stability_df["feature"]:
            assert feat in report, f"Report should mention feature '{feat}'"

    @pytest.mark.unit
    def test_contains_quadrant_names(self, stability_df):
        report = generate_stability_report(stability_df)
        for quadrant in ["ROBUST", "VOLATILE", "NOISE", "STABLE"]:
            assert quadrant in report, f"Report should mention quadrant '{quadrant}'"

    @pytest.mark.unit
    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(
            columns=[
                "feature",
                "perm_importance",
                "temporal_psi",
                "missing_rate",
                "quadrant",
                "action",
            ]
        )
        report = generate_stability_report(empty_df)
        assert isinstance(report, str)
        assert len(report) > 0, "Report should not be empty even with no features"

    @pytest.mark.unit
    def test_single_feature(self):
        df = pd.DataFrame(
            {
                "feature": ["only_feat"],
                "perm_importance": [0.1],
                "temporal_psi": [0.05],
                "missing_rate": [0.0],
                "quadrant": ["ROBUST"],
                "action": ["keep"],
            }
        )
        report = generate_stability_report(df)
        assert "only_feat" in report

    @pytest.mark.unit
    def test_report_is_nonempty(self, stability_df):
        report = generate_stability_report(stability_df)
        assert len(report) > 50, "Report should be a substantial Markdown document"
