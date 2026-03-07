"""Tests for src/utils.py."""

import pytest
import pandas as pd

from src.utils import load_dataset, save_json, set_seed, get_logger


class TestLoadDataset:
    """Tests for load_dataset."""

    def test_load_csv(self, tmp_path):
        """Should load CSV files."""
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df.to_csv(csv_path, index=False)

        result = load_dataset(csv_path)
        assert len(result) == 2
        assert list(result.columns) == ["a", "b"]

    def test_load_parquet(self, tmp_path):
        """Should load Parquet files."""
        parquet_path = tmp_path / "data.parquet"
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df.to_parquet(parquet_path)

        result = load_dataset(parquet_path)
        assert len(result) == 2

    def test_unsupported_format_raises(self, tmp_path):
        """Should raise ValueError for unsupported formats."""
        txt_path = tmp_path / "data.txt"
        txt_path.write_text("data")

        with pytest.raises(ValueError, match="Formato não suportado"):
            load_dataset(txt_path)


class TestSaveJson:
    """Tests for save_json."""

    def test_save_and_read(self, tmp_path):
        """Should save JSON file."""
        import json

        path = tmp_path / "sub" / "output.json"
        data = {"key": "value", "num": 42}
        save_json(path, data)

        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["key"] == "value"
        assert loaded["num"] == 42


class TestSetSeed:
    """Tests for set_seed."""

    def test_reproducibility(self):
        """Seeds should produce reproducible results."""
        import numpy as np

        set_seed(42)
        a = np.random.rand()
        set_seed(42)
        b = np.random.rand()
        assert a == b


class TestGetLogger:
    """Tests for get_logger."""

    def test_returns_logger(self):
        """Should return a configured logger."""
        import logging

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
