"""
Utilitários gerais para o projeto.
"""

import json
import random
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Union


def load_dataset(path: Union[str, Path]) -> pd.DataFrame:
    """Carrega dataset (parquet ou csv)."""
    path = Path(path)
    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix == '.csv':
        return pd.read_csv(path)
    else:
        raise ValueError(f"Formato não suportado: {path.suffix}")


def save_json(path: Union[str, Path], data: Dict[str, Any]) -> None:
    """Salva dicionário como JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def set_seed(seed: int = 42) -> None:
    """Fixa seed para reprodutibilidade."""
    random.seed(seed)
    np.random.seed(seed)


def get_logger(name: str) -> logging.Logger:
    """Retorna logger configurado."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
