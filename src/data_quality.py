"""
Data Quality Checks para Passos Mágicos.

Implementa validações de qualidade de dados conforme data_contract.md.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class QualityCheckResult:
    """Resultado de uma verificação de qualidade."""
    check_name: str
    passed: bool
    message: str
    details: Dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class DataQualityChecker:
    """
    Executa verificações de qualidade nos dados.
    
    Verificações implementadas:
    1. Duplicatas por RA/ano
    2. Valores fora de range para indicadores
    3. Missing values acima do threshold
    4. Consistência de tipos
    5. Leakage check (colunas proibidas)
    """
    
    # Ranges válidos para indicadores (min, max)
    INDICATOR_RANGES = {
        'inde': (0, 10),
        'ian': (0, 10),
        'ida': (0, 10),
        'ieg': (0, 10),
        'iaa': (0, 10),
        'ips': (0, 10),
        'ipp': (0, 10),
        'ipv': (0, 10),
        'ipm': (0, 10),
        'indicador_nutricional': (0, 100),
        'defasagem': (-10, 10),
        'fase': (0, 10),
        'fase_ideal': (0, 10),
    }
    
    # Threshold máximo de missing values (proporção)
    MAX_MISSING_RATIO = 0.3
    
    # Colunas que indicam leakage se presentes no dataset de features
    LEAKAGE_COLUMNS = [
        'defasagem',
        'ponto_virada', 
        'pedra',
        'destaque_inde',
        'destaque_ida',
        'destaque_ieg',
        'rec_ava',
        'rec_inde',
    ]
    
    def __init__(self, df: pd.DataFrame, year: int = None):
        """
        Inicializa o checker.
        
        Args:
            df: DataFrame a ser verificado
            year: Ano dos dados (opcional, para contexto)
        """
        self.df = df.copy()
        self.year = year
        self.results: List[QualityCheckResult] = []
        
    def check_duplicates(self, key_column: str = 'ra') -> QualityCheckResult:
        """
        Verifica duplicatas por chave.
        
        Args:
            key_column: Coluna de identificação (default: 'ra')
            
        Returns:
            QualityCheckResult
        """
        if key_column not in self.df.columns:
            return QualityCheckResult(
                check_name='duplicates',
                passed=False,
                message=f"Coluna '{key_column}' não encontrada",
                details={'column': key_column}
            )
        
        duplicates = self.df[self.df.duplicated(subset=[key_column], keep=False)]
        n_duplicates = len(duplicates)
        
        result = QualityCheckResult(
            check_name='duplicates',
            passed=(n_duplicates == 0),
            message=f"Encontradas {n_duplicates} linhas duplicadas por '{key_column}'" 
                    if n_duplicates > 0 else "Sem duplicatas",
            details={
                'n_duplicates': n_duplicates,
                'duplicate_keys': duplicates[key_column].unique().tolist()[:10]  # Primeiros 10
            }
        )
        self.results.append(result)
        return result
    
    def check_ranges(self) -> QualityCheckResult:
        """
        Verifica se indicadores estão dentro dos ranges válidos.
        
        Returns:
            QualityCheckResult
        """
        violations = {}
        
        for col, (min_val, max_val) in self.INDICATOR_RANGES.items():
            # Busca coluna (case insensitive)
            col_lower = col.lower()
            matching_cols = [c for c in self.df.columns if c.lower() == col_lower]
            
            if not matching_cols:
                continue
                
            actual_col = matching_cols[0]
            series = self.df[actual_col]
            
            # Tenta converter para numérico se necessário
            if not np.issubdtype(series.dtype, np.number):
                series = pd.to_numeric(series, errors='coerce')
            
            # Ignora NaN na verificação de range
            valid_data = series.dropna()
            
            if len(valid_data) == 0:
                continue
            
            out_of_range = valid_data[(valid_data < min_val) | (valid_data > max_val)]
            
            if len(out_of_range) > 0:
                violations[actual_col] = {
                    'expected_range': (min_val, max_val),
                    'actual_min': float(valid_data.min()),
                    'actual_max': float(valid_data.max()),
                    'n_violations': len(out_of_range),
                    'violation_values': out_of_range.head(5).tolist()
                }
        
        result = QualityCheckResult(
            check_name='ranges',
            passed=(len(violations) == 0),
            message=f"Encontradas violações de range em {len(violations)} colunas"
                    if violations else "Todos indicadores dentro do range",
            details={'violations': violations}
        )
        self.results.append(result)
        return result
    
    def check_missing_values(self, critical_columns: List[str] = None) -> QualityCheckResult:
        """
        Verifica proporção de missing values.
        
        Args:
            critical_columns: Colunas críticas que não podem ter missing
            
        Returns:
            QualityCheckResult
        """
        if critical_columns is None:
            critical_columns = ['ra']
        
        missing_stats = {}
        critical_failures = []
        high_missing = []
        
        for col in self.df.columns:
            n_missing = self.df[col].isna().sum()
            ratio = n_missing / len(self.df)
            
            if ratio > 0:
                missing_stats[col] = {
                    'n_missing': int(n_missing),
                    'ratio': round(ratio, 4)
                }
                
            # Verifica colunas críticas
            if col.lower() in [c.lower() for c in critical_columns]:
                if n_missing > 0:
                    critical_failures.append(col)
                    
            # Verifica threshold
            if ratio > self.MAX_MISSING_RATIO:
                high_missing.append((col, ratio))
        
        passed = (len(critical_failures) == 0 and len(high_missing) == 0)
        
        message_parts = []
        if critical_failures:
            message_parts.append(f"Colunas críticas com missing: {critical_failures}")
        if high_missing:
            message_parts.append(f"Colunas acima de {self.MAX_MISSING_RATIO*100}% missing: {len(high_missing)}")
        
        result = QualityCheckResult(
            check_name='missing_values',
            passed=passed,
            message=" | ".join(message_parts) if message_parts else "Missing values dentro do aceitável",
            details={
                'critical_failures': critical_failures,
                'high_missing': [(col, f"{ratio:.1%}") for col, ratio in high_missing],
                'all_missing': missing_stats
            }
        )
        self.results.append(result)
        return result
    
    def check_leakage(self, feature_columns: List[str] = None) -> QualityCheckResult:
        """
        Verifica se há colunas que causariam leakage.
        
        Args:
            feature_columns: Lista de colunas de features a verificar
                           Se None, verifica todas as colunas do DataFrame
        
        Returns:
            QualityCheckResult
        """
        if feature_columns is None:
            feature_columns = self.df.columns.tolist()
        
        # Normaliza para lowercase
        feature_cols_lower = [c.lower() for c in feature_columns]
        leakage_cols_lower = [c.lower() for c in self.LEAKAGE_COLUMNS]
        
        found_leakage = []
        for i, col_lower in enumerate(feature_cols_lower):
            if col_lower in leakage_cols_lower:
                found_leakage.append(feature_columns[i])
        
        result = QualityCheckResult(
            check_name='leakage',
            passed=(len(found_leakage) == 0),
            message=f"LEAKAGE DETECTADO! Colunas proibidas: {found_leakage}"
                    if found_leakage else "Sem leakage detectado",
            details={
                'leakage_columns': found_leakage,
                'checked_columns': len(feature_columns)
            }
        )
        self.results.append(result)
        return result
    
    def check_dtypes(self, expected_numeric: List[str] = None) -> QualityCheckResult:
        """
        Verifica se tipos de dados estão corretos.
        
        Args:
            expected_numeric: Colunas que devem ser numéricas
            
        Returns:
            QualityCheckResult
        """
        if expected_numeric is None:
            # Indicadores que devem ser numéricos
            expected_numeric = list(self.INDICATOR_RANGES.keys())
        
        type_issues = []
        
        for col_name in expected_numeric:
            col_lower = col_name.lower()
            matching_cols = [c for c in self.df.columns if c.lower() == col_lower]
            
            if not matching_cols:
                continue
                
            actual_col = matching_cols[0]
            dtype = self.df[actual_col].dtype
            
            if not np.issubdtype(dtype, np.number):
                type_issues.append({
                    'column': actual_col,
                    'expected': 'numeric',
                    'actual': str(dtype)
                })
        
        result = QualityCheckResult(
            check_name='dtypes',
            passed=(len(type_issues) == 0),
            message=f"Encontrados {len(type_issues)} problemas de tipo"
                    if type_issues else "Tipos de dados OK",
            details={'type_issues': type_issues}
        )
        self.results.append(result)
        return result
    
    def run_all_checks(self, critical_columns: List[str] = None) -> Tuple[bool, List[QualityCheckResult]]:
        """
        Executa todas as verificações.
        
        Args:
            critical_columns: Colunas críticas para check de missing
            
        Returns:
            Tuple[all_passed, list_of_results]
        """
        self.results = []  # Reset
        
        self.check_duplicates()
        self.check_ranges()
        self.check_missing_values(critical_columns)
        self.check_dtypes()
        # Leakage check deve ser chamado separadamente com lista de features
        
        all_passed = all(r.passed for r in self.results)
        return all_passed, self.results
    
    def get_summary(self) -> str:
        """
        Retorna resumo textual das verificações.
        
        Returns:
            String com resumo
        """
        if not self.results:
            return "Nenhuma verificação executada."
        
        lines = [f"=== Data Quality Report ==="]
        if self.year:
            lines.append(f"Ano: {self.year}")
        lines.append(f"Registros: {len(self.df)}")
        lines.append("")
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            lines.append(f"{status} [{result.check_name}] {result.message}")
        
        n_passed = sum(1 for r in self.results if r.passed)
        n_total = len(self.results)
        lines.append("")
        lines.append(f"Resultado: {n_passed}/{n_total} verificações passaram")
        
        return "\n".join(lines)


def validate_modeling_dataset(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    feature_year: int,
    label_year: int
) -> Tuple[bool, str]:
    """
    Validação completa do dataset de modelagem.
    
    Args:
        features_df: DataFrame com features
        labels_df: DataFrame com labels
        feature_year: Ano das features
        label_year: Ano dos labels
        
    Returns:
        Tuple[passed, report]
    """
    reports = []
    all_passed = True
    
    # Verifica features
    checker_features = DataQualityChecker(features_df, year=feature_year)
    passed, _ = checker_features.run_all_checks(critical_columns=['ra'])
    
    # Verifica leakage nas features
    leakage_result = checker_features.check_leakage(features_df.columns.tolist())
    if not leakage_result.passed:
        all_passed = False
    
    reports.append(f"=== Features ({feature_year}) ===")
    reports.append(checker_features.get_summary())
    
    # Verifica labels
    checker_labels = DataQualityChecker(labels_df, year=label_year)
    passed_labels, _ = checker_labels.run_all_checks(critical_columns=['ra', 'em_risco'])
    
    if not passed_labels:
        all_passed = False
        
    reports.append("")
    reports.append(f"=== Labels ({label_year}) ===")
    reports.append(checker_labels.get_summary())
    
    # Verifica join
    features_ras = set(features_df['ra'].unique())
    labels_ras = set(labels_df['ra'].unique())
    
    common_ras = features_ras & labels_ras
    only_features = features_ras - labels_ras
    only_labels = labels_ras - features_ras
    
    reports.append("")
    reports.append("=== Join Check ===")
    reports.append(f"RAs em comum: {len(common_ras)}")
    reports.append(f"RAs só em features: {len(only_features)}")
    reports.append(f"RAs só em labels: {len(only_labels)}")
    
    if len(common_ras) == 0:
        all_passed = False
        reports.append("❌ FAIL: Nenhum RA em comum entre features e labels!")
    else:
        reports.append("✅ PASS: Join possível")
    
    return all_passed, "\n".join(reports)


if __name__ == "__main__":
    # Exemplo de uso
    import sys
    
    print("Data Quality Checker - Passos Mágicos")
    print("=" * 40)
    
    # Criar dados de exemplo
    df_example = pd.DataFrame({
        'ra': [1, 2, 3, 4, 5],
        'nome': ['A', 'B', 'C', 'D', 'E'],
        'inde': [7.5, 8.0, None, 9.0, 6.5],
        'ida': [6.0, 7.0, 8.0, 5.0, 7.5],
        'defasagem': [-1, 0, 1, -2, 0],  # Esta coluna causaria leakage em features
    })
    
    checker = DataQualityChecker(df_example, year=2023)
    passed, results = checker.run_all_checks()
    
    print(checker.get_summary())
    
    print("\n--- Leakage Check ---")
    feature_cols = ['nome', 'inde', 'ida', 'defasagem']  # defasagem é leakage!
    leakage_result = checker.check_leakage(feature_cols)
    print(f"{'✅' if leakage_result.passed else '❌'} {leakage_result.message}")
