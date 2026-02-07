"""
Validador de Regras de Negócio - Indicadores PEDE/INDE.

Este módulo implementa as regras oficiais de cálculo dos indicadores
educacionais da Associação Passos Mágicos, conforme documentação.

Indicadores:
- IAN: Indicador de Adequação de Nível (escala 10/5/2.5)
- IDA: Indicador de Desempenho Acadêmico (média das notas)
- IEG: Indicador de Engajamento
- IAA: Indicador de Autoavaliação
- IPS: Indicador Psicossocial
- IPP: Indicador Psicopedagógico
- IPV: Indicador de Ponto de Virada
- INDE: Índice de Desenvolvimento Educacional (ponderação)

Referência: Documento de Mensuração PEDE 2024
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Resultado de uma validação de regra de negócio."""
    rule_name: str
    passed: bool
    message: str
    pct_valid: Optional[float] = None
    n_invalid: Optional[int] = None
    details: Optional[Dict] = None


class INDECalculator:
    """
    Calculadora oficial do INDE e seus componentes.
    
    Implementa as regras de negócio documentadas para cálculo dos
    indicadores educacionais do programa Passos Mágicos.
    """
    
    # Pesos para cálculo do INDE - Fases 0 a 7
    WEIGHTS_STANDARD = {
        'ian': 0.10,
        'ida': 0.20,
        'ieg': 0.20,
        'iaa': 0.10,
        'ips': 0.10,
        'ipp': 0.10,
        'ipv': 0.20,
    }
    
    # Pesos para cálculo do INDE - Fase 8 (Universitários)
    # IPP e IPV não entram no cálculo!
    WEIGHTS_FASE8 = {
        'ian': 0.10,
        'ida': 0.40,
        'ieg': 0.20,
        'iaa': 0.10,
        'ips': 0.20,
    }
    
    # Escala do IAN baseada na defasagem
    IAN_SCALE = {
        'em_fase': 10.0,    # D >= 0
        'moderada': 5.0,     # -2 < D < 0
        'severa': 2.5,       # D <= -2
    }
    
    # Faixas de classificação (Pedras)
    PEDRA_RANGES = [
        ('Quartzo', 3.0, 6.1),
        ('Ágata', 6.1, 7.2),
        ('Ametista', 7.2, 8.2),
        ('Topázio', 8.2, 10.0),
    ]
    
    # Escala IAA para Fases 0-2 (3 opções)
    IAA_SCALE_JUNIOR = {
        'A': 1.00,  # 100%
        'B': 0.70,  # 70%
        'C': 0.35,  # 35%
    }
    
    # Escala IAA para Fases 3-8 (4 opções)
    IAA_SCALE_SENIOR = {
        'A': 1.00,  # 100%
        'B': 0.75,  # 75%
        'C': 0.50,  # 50%
        'D': 0.25,  # 25%
    }
    
    @staticmethod
    def compute_ian(defasagem: float) -> float:
        """
        Calcula IAN (Indicador de Adequação de Nível) a partir da defasagem.
        
        Regra:
        - D >= 0 → Em fase → IAN = 10
        - -2 < D < 0 → Moderada → IAN = 5
        - D <= -2 → Severa → IAN = 2.5
        
        Args:
            defasagem: Diferença entre fase efetiva e fase ideal
            
        Returns:
            Valor do IAN (10, 5 ou 2.5)
        """
        if pd.isna(defasagem):
            return np.nan
        
        if defasagem >= 0:
            return 10.0  # Em fase ou avançado
        elif defasagem > -2:
            return 5.0   # Defasagem moderada
        else:
            return 2.5   # Defasagem severa
    
    @staticmethod
    def compute_ida(mat: float, por: float, ing: float = None) -> float:
        """
        Calcula IDA (Indicador de Desempenho Acadêmico).
        
        Fórmula: IDA = (Nota_Mat + Nota_Por + Nota_Ing) / 3
        
        Para Fase 8, deveria usar média universitária, mas aqui
        usamos a mesma lógica por falta de dados específicos.
        
        Args:
            mat: Nota de Matemática
            por: Nota de Português
            ing: Nota de Inglês (opcional, alto missing)
            
        Returns:
            Média das notas disponíveis
        """
        notas = [n for n in [mat, por, ing] if pd.notna(n)]
        
        if not notas:
            return np.nan
        
        return sum(notas) / len(notas)
    
    @classmethod
    def compute_inde(
        cls,
        row: pd.Series,
        fase: Optional[int] = None,
        indicator_suffix: str = '',
    ) -> float:
        """
        Calcula INDE (Índice de Desenvolvimento Educacional).
        
        Fórmula Fases 0-7:
        INDE = IAN×0.1 + IDA×0.2 + IEG×0.2 + IAA×0.1 + IPS×0.1 + IPP×0.1 + IPV×0.2
        
        Fórmula Fase 8:
        INDE = IAN×0.1 + IDA×0.4 + IEG×0.2 + IAA×0.1 + IPS×0.2
        
        Args:
            row: Linha do DataFrame com indicadores
            fase: Fase do aluno (se None, busca na row)
            indicator_suffix: Sufixo das colunas (ex: '_2023')
            
        Returns:
            Valor calculado do INDE
        """
        if fase is None:
            fase_col = f'fase{indicator_suffix}' if indicator_suffix else 'fase'
            fase = row.get(fase_col, 0)
            
            # Tenta converter fase para int se for string
            if isinstance(fase, str):
                fase_map = {
                    'ALFA': 0, 'alfa': 0,
                    'F1': 1, 'f1': 1, '1': 1,
                    'F2': 2, 'f2': 2, '2': 2,
                    'F3': 3, 'f3': 3, '3': 3,
                    'F4': 4, 'f4': 4, '4': 4,
                    'F5': 5, 'f5': 5, '5': 5,
                    'F6': 6, 'f6': 6, '6': 6,
                    'F7': 7, 'f7': 7, '7': 7,
                    'F8': 8, 'f8': 8, '8': 8,
                }
                fase = fase_map.get(str(fase).strip(), 0)
        
        # Seleciona pesos conforme fase
        weights = cls.WEIGHTS_FASE8 if fase == 8 else cls.WEIGHTS_STANDARD
        
        # Calcula INDE ponderado
        inde = 0.0
        valid_weight = 0.0
        
        for indicator, weight in weights.items():
            col_name = f'{indicator}{indicator_suffix}' if indicator_suffix else indicator
            value = row.get(col_name)
            
            if pd.notna(value):
                inde += float(value) * weight
                valid_weight += weight
        
        # Se não temos todos os indicadores, ajusta proporcionalmente
        if valid_weight > 0 and valid_weight < sum(weights.values()):
            inde = inde / valid_weight * sum(weights.values())
        
        return round(inde, 2) if valid_weight > 0 else np.nan
    
    @classmethod
    def classify_pedra(cls, inde: float) -> Optional[str]:
        """
        Classifica INDE em faixa de pedra (conceito).
        
        Faixas:
        - Quartzo: 3.0 - 6.1
        - Ágata: 6.1 - 7.2
        - Ametista: 7.2 - 8.2
        - Topázio: 8.2 - 10.0
        
        Args:
            inde: Valor do INDE
            
        Returns:
            Nome da pedra ou None se inválido
        """
        if pd.isna(inde):
            return None
        
        for pedra, low, high in cls.PEDRA_RANGES:
            if low <= inde < high:
                return pedra
        
        # Casos de borda
        if inde >= 10.0:
            return 'Topázio'
        elif inde < 3.0:
            return 'Quartzo'
        
        return None
    
    @staticmethod
    def get_defasagem_category(defasagem: float) -> str:
        """
        Categoriza defasagem em texto descritivo.
        
        Args:
            defasagem: Valor numérico da defasagem
            
        Returns:
            Categoria textual
        """
        if pd.isna(defasagem):
            return 'Desconhecido'
        
        if defasagem >= 0:
            return 'Em Fase'
        elif defasagem > -2:
            return 'Defasagem Moderada'
        else:
            return 'Defasagem Severa'


class BusinessRulesValidator:
    """
    Validador de conformidade com regras de negócio.
    
    Verifica se os dados do Excel estão de acordo com as
    fórmulas oficiais dos indicadores PEDE.
    """
    
    def __init__(self, tolerance: float = 0.5):
        """
        Inicializa o validador.
        
        Args:
            tolerance: Tolerância para diferenças numéricas
        """
        self.tolerance = tolerance
        self.calculator = INDECalculator()
    
    def validate_ian(
        self,
        df: pd.DataFrame,
        ian_col: str = 'ian',
        defasagem_col: str = 'defasagem',
    ) -> ValidationResult:
        """
        Valida se IAN está calculado corretamente.
        
        Compara IAN do Excel com valor esperado baseado na defasagem.
        
        Args:
            df: DataFrame com dados
            ian_col: Nome da coluna IAN
            defasagem_col: Nome da coluna defasagem
            
        Returns:
            ValidationResult com detalhes
        """
        if ian_col not in df.columns or defasagem_col not in df.columns:
            return ValidationResult(
                rule_name='IAN',
                passed=False,
                message=f'Colunas {ian_col} ou {defasagem_col} não encontradas',
            )
        
        # Calcula IAN esperado
        ian_expected = df[defasagem_col].apply(self.calculator.compute_ian)
        ian_actual = df[ian_col]
        
        # Compara
        valid_mask = (
            (ian_expected.isna() & ian_actual.isna()) |
            (abs(ian_expected - ian_actual) <= self.tolerance)
        )
        
        n_total = len(df)
        n_valid = valid_mask.sum()
        n_invalid = n_total - n_valid
        pct_valid = n_valid / n_total if n_total > 0 else 0
        
        # Detalhes dos inválidos
        invalid_df = df[~valid_mask][[ian_col, defasagem_col]].copy()
        invalid_df['ian_expected'] = ian_expected[~valid_mask]
        
        return ValidationResult(
            rule_name='IAN (escala 10/5/2.5)',
            passed=(pct_valid >= 0.95),
            message=f'{pct_valid*100:.1f}% conformes ({n_invalid} divergências)',
            pct_valid=pct_valid,
            n_invalid=n_invalid,
            details={
                'invalid_samples': invalid_df.head(10).to_dict('records'),
                'expected_scale': self.calculator.IAN_SCALE,
            }
        )
    
    def validate_ida(
        self,
        df: pd.DataFrame,
        ida_col: str = 'ida',
        mat_col: str = 'mat',
        por_col: str = 'por',
        ing_col: str = 'ing',
    ) -> ValidationResult:
        """
        Valida se IDA é a média das notas.
        
        Args:
            df: DataFrame com dados
            ida_col, mat_col, por_col, ing_col: Nomes das colunas
            
        Returns:
            ValidationResult com detalhes
        """
        required_cols = [ida_col, mat_col, por_col]
        missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            return ValidationResult(
                rule_name='IDA',
                passed=False,
                message=f'Colunas não encontradas: {missing}',
            )
        
        # Calcula IDA esperado
        ing_values = df[ing_col] if ing_col in df.columns else pd.Series([np.nan] * len(df))
        
        ida_expected = df.apply(
            lambda row: self.calculator.compute_ida(
                row[mat_col], row[por_col], 
                row[ing_col] if ing_col in df.columns else np.nan
            ),
            axis=1
        )
        
        ida_actual = df[ida_col]
        
        # Compara
        valid_mask = (
            (ida_expected.isna() & ida_actual.isna()) |
            (abs(ida_expected - ida_actual) <= self.tolerance)
        )
        
        n_total = len(df)
        n_valid = valid_mask.sum()
        n_invalid = n_total - n_valid
        pct_valid = n_valid / n_total if n_total > 0 else 0
        
        return ValidationResult(
            rule_name='IDA (média notas)',
            passed=(pct_valid >= 0.95),
            message=f'{pct_valid*100:.1f}% conformes ({n_invalid} divergências)',
            pct_valid=pct_valid,
            n_invalid=n_invalid,
            details={
                'formula': 'IDA = (mat + por + ing) / 3',
                'ing_missing_rate': ing_values.isna().mean() if ing_col in df.columns else 1.0,
            }
        )
    
    def validate_inde(
        self,
        df: pd.DataFrame,
        inde_col: str = 'inde',
        fase_col: str = 'fase',
        indicator_suffix: str = '',
    ) -> ValidationResult:
        """
        Valida se INDE está calculado com ponderação correta.
        
        Args:
            df: DataFrame com dados
            inde_col: Coluna do INDE
            fase_col: Coluna da fase
            indicator_suffix: Sufixo das colunas de indicadores
            
        Returns:
            ValidationResult com detalhes
        """
        if inde_col not in df.columns:
            return ValidationResult(
                rule_name='INDE',
                passed=False,
                message=f'Coluna {inde_col} não encontrada',
            )
        
        # Calcula INDE esperado
        inde_expected = df.apply(
            lambda row: self.calculator.compute_inde(row, indicator_suffix=indicator_suffix),
            axis=1
        )
        
        inde_actual = df[inde_col]
        
        # Compara
        valid_mask = (
            (inde_expected.isna() & inde_actual.isna()) |
            (abs(inde_expected - inde_actual) <= self.tolerance)
        )
        
        n_total = len(df)
        n_valid = valid_mask.sum()
        n_invalid = n_total - n_valid
        pct_valid = n_valid / n_total if n_total > 0 else 0
        
        # Analisa por fase
        fase_analysis = {}
        if fase_col in df.columns:
            for fase in df[fase_col].dropna().unique():
                fase_mask = df[fase_col] == fase
                fase_valid = valid_mask[fase_mask].mean()
                fase_analysis[str(fase)] = f'{fase_valid*100:.1f}%'
        
        return ValidationResult(
            rule_name='INDE (ponderação)',
            passed=(pct_valid >= 0.90),
            message=f'{pct_valid*100:.1f}% conformes ({n_invalid} divergências)',
            pct_valid=pct_valid,
            n_invalid=n_invalid,
            details={
                'weights_standard': self.calculator.WEIGHTS_STANDARD,
                'weights_fase8': self.calculator.WEIGHTS_FASE8,
                'by_fase': fase_analysis,
            }
        )
    
    def validate_all(
        self,
        df: pd.DataFrame,
        verbose: bool = True,
    ) -> List[ValidationResult]:
        """
        Executa todas as validações de regras de negócio.
        
        Args:
            df: DataFrame com dados
            verbose: Se True, imprime resultados
            
        Returns:
            Lista de ValidationResult
        """
        results = []
        
        # Detecta sufixos de colunas
        suffix = ''
        for col in df.columns:
            if '_2023' in col or '_23' in col:
                suffix = '_2023' if '_2023' in col else '_23'
                break
        
        # Ajusta nomes de colunas
        ian_col = f'ian{suffix}' if f'ian{suffix}' in df.columns else 'ian'
        ida_col = f'ida{suffix}' if f'ida{suffix}' in df.columns else 'ida'
        inde_col = f'inde{suffix}' if f'inde{suffix}' in df.columns else 'inde'
        fase_col = f'fase{suffix}' if f'fase{suffix}' in df.columns else 'fase'
        
        # Valida IAN
        if 'defasagem' in df.columns:
            results.append(self.validate_ian(df, ian_col, 'defasagem'))
        
        # Valida IDA
        mat_col = 'mat' if 'mat' in df.columns else 'matem'
        por_col = 'por' if 'por' in df.columns else 'portug'
        ing_col = 'ing' if 'ing' in df.columns else 'ingles'
        
        if mat_col in df.columns and por_col in df.columns:
            results.append(self.validate_ida(df, ida_col, mat_col, por_col, ing_col))
        
        # Valida INDE
        if inde_col in df.columns:
            results.append(self.validate_inde(df, inde_col, fase_col, suffix))
        
        # Imprime resumo
        if verbose:
            print("\n" + "="*60)
            print("VALIDAÇÃO DE REGRAS DE NEGÓCIO")
            print("="*60)
            for result in results:
                status = "✅" if result.passed else "❌"
                print(f"\n{status} {result.rule_name}")
                print(f"   {result.message}")
                if result.details and 'by_fase' in result.details:
                    print(f"   Por fase: {result.details['by_fase']}")
            print("\n" + "="*60)
        
        return results


def run_validation(data_path: str) -> List[ValidationResult]:
    """
    Função de conveniência para executar validação.
    
    Args:
        data_path: Caminho para arquivo parquet ou Excel
        
    Returns:
        Lista de resultados
    """
    import pandas as pd
    from pathlib import Path
    
    path = Path(data_path)
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Formato não suportado: {path.suffix}")
    
    validator = BusinessRulesValidator(tolerance=0.5)
    return validator.validate_all(df)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        results = run_validation(sys.argv[1])
        
        # Resumo final
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        print(f"\nResumo: {passed}/{total} regras validadas")
    else:
        print("Uso: python business_rules.py <caminho_dados>")
        print("Exemplo: python business_rules.py data/interim/2023_normalized.parquet")
