"""
Testes para validação de regras de negócio dos indicadores PEDE.
"""

import pytest
import pandas as pd
import numpy as np
from src.business_rules import (
    INDECalculator,
    BusinessRulesValidator,
    ValidationResult,
)


class TestINDECalculator:
    """Testes para o calculador de indicadores INDE."""

    # ==================== Testes IAN ====================

    def test_ian_em_fase(self):
        """IAN = 10 quando defasagem >= 0."""
        assert INDECalculator.compute_ian(0) == 10.0
        assert INDECalculator.compute_ian(1) == 10.0
        assert INDECalculator.compute_ian(2) == 10.0

    def test_ian_defasagem_moderada(self):
        """IAN = 5 quando -2 < defasagem < 0."""
        assert INDECalculator.compute_ian(-1) == 5.0
        assert INDECalculator.compute_ian(-0.5) == 5.0
        assert INDECalculator.compute_ian(-1.9) == 5.0

    def test_ian_defasagem_severa(self):
        """IAN = 2.5 quando defasagem <= -2."""
        assert INDECalculator.compute_ian(-2) == 2.5
        assert INDECalculator.compute_ian(-3) == 2.5
        assert INDECalculator.compute_ian(-10) == 2.5

    def test_ian_nan(self):
        """IAN retorna NaN para entrada NaN."""
        assert pd.isna(INDECalculator.compute_ian(np.nan))

    # ==================== Testes IDA ====================

    def test_ida_media_completa(self):
        """IDA = média das 3 notas quando disponíveis."""
        result = INDECalculator.compute_ida(8.0, 7.0, 9.0)
        assert result == 8.0  # (8+7+9)/3

    def test_ida_sem_ingles(self):
        """IDA = média de mat e por quando inglês ausente."""
        result = INDECalculator.compute_ida(8.0, 6.0, np.nan)
        assert result == 7.0  # (8+6)/2

    def test_ida_apenas_matematica(self):
        """IDA = nota quando apenas uma disponível."""
        result = INDECalculator.compute_ida(8.0, np.nan, np.nan)
        assert result == 8.0

    def test_ida_todas_nan(self):
        """IDA retorna NaN quando todas notas ausentes."""
        result = INDECalculator.compute_ida(np.nan, np.nan, np.nan)
        assert pd.isna(result)

    # ==================== Testes INDE Fases 0-7 ====================

    def test_inde_standard_completo(self):
        """INDE fases 0-7 com todos indicadores."""
        row = pd.Series(
            {
                "ian": 10.0,  # peso 0.1
                "ida": 8.0,  # peso 0.2
                "ieg": 7.0,  # peso 0.2
                "iaa": 6.0,  # peso 0.1
                "ips": 8.0,  # peso 0.1
                "ipp": 7.0,  # peso 0.1
                "ipv": 9.0,  # peso 0.2
                "fase": 5,
            }
        )

        expected = (
            10.0 * 0.1
            + 8.0 * 0.2  # ian
            + 7.0 * 0.2  # ida
            + 6.0 * 0.1  # ieg
            + 8.0 * 0.1  # iaa
            + 7.0 * 0.1  # ips
            + 9.0 * 0.2  # ipp  # ipv
        )  # = 1.0 + 1.6 + 1.4 + 0.6 + 0.8 + 0.7 + 1.8 = 7.9

        result = INDECalculator.compute_inde(row, fase=5)
        assert abs(result - expected) < 0.01

    # ==================== Testes INDE Fase 8 ====================

    def test_inde_fase8_pesos_diferentes(self):
        """INDE fase 8 usa pesos diferentes (sem IPP e IPV)."""
        row = pd.Series(
            {
                "ian": 10.0,  # peso 0.1
                "ida": 9.0,  # peso 0.4 (maior!)
                "ieg": 8.0,  # peso 0.2
                "iaa": 7.0,  # peso 0.1
                "ips": 8.0,  # peso 0.2 (maior!)
                "ipp": 5.0,  # NÃO ENTRA
                "ipv": 5.0,  # NÃO ENTRA
                "fase": 8,
            }
        )

        expected = (
            10.0 * 0.1
            + 9.0 * 0.4  # ian
            + 8.0 * 0.2  # ida (peso maior)
            + 7.0 * 0.1  # ieg
            + 8.0 * 0.2  # iaa  # ips (peso maior)
        )  # = 1.0 + 3.6 + 1.6 + 0.7 + 1.6 = 8.5

        result = INDECalculator.compute_inde(row, fase=8)
        assert abs(result - expected) < 0.01

    def test_inde_fase8_ignora_ipp_ipv(self):
        """Verifica que IPP e IPV são ignorados na Fase 8."""
        row_base = pd.Series(
            {
                "ian": 8.0,
                "ida": 8.0,
                "ieg": 8.0,
                "iaa": 8.0,
                "ips": 8.0,
                "ipp": 0.0,  # Valor baixo
                "ipv": 0.0,  # Valor baixo
                "fase": 8,
            }
        )

        row_alta = pd.Series(
            {
                "ian": 8.0,
                "ida": 8.0,
                "ieg": 8.0,
                "iaa": 8.0,
                "ips": 8.0,
                "ipp": 10.0,  # Valor alto
                "ipv": 10.0,  # Valor alto
                "fase": 8,
            }
        )

        # Se IPP/IPV são ignorados, resultados devem ser iguais
        result_base = INDECalculator.compute_inde(row_base, fase=8)
        result_alta = INDECalculator.compute_inde(row_alta, fase=8)

        assert result_base == result_alta

    # ==================== Testes Pedra ====================

    def test_classify_pedra_quartzo(self):
        """Quartzo: 3.0 - 6.1"""
        assert INDECalculator.classify_pedra(3.0) == "Quartzo"
        assert INDECalculator.classify_pedra(5.5) == "Quartzo"
        assert INDECalculator.classify_pedra(6.0) == "Quartzo"

    def test_classify_pedra_agata(self):
        """Ágata: 6.1 - 7.2"""
        assert INDECalculator.classify_pedra(6.1) == "Ágata"
        assert INDECalculator.classify_pedra(6.5) == "Ágata"
        assert INDECalculator.classify_pedra(7.1) == "Ágata"

    def test_classify_pedra_ametista(self):
        """Ametista: 7.2 - 8.2"""
        assert INDECalculator.classify_pedra(7.2) == "Ametista"
        assert INDECalculator.classify_pedra(7.5) == "Ametista"
        assert INDECalculator.classify_pedra(8.1) == "Ametista"

    def test_classify_pedra_topazio(self):
        """Topázio: 8.2 - 10.0"""
        assert INDECalculator.classify_pedra(8.2) == "Topázio"
        assert INDECalculator.classify_pedra(9.0) == "Topázio"
        assert INDECalculator.classify_pedra(10.0) == "Topázio"

    def test_classify_pedra_extremos(self):
        """Testa valores extremos."""
        assert INDECalculator.classify_pedra(0.0) == "Quartzo"
        assert INDECalculator.classify_pedra(2.9) == "Quartzo"
        assert INDECalculator.classify_pedra(10.5) == "Topázio"

    def test_classify_pedra_nan(self):
        """Pedra retorna None para NaN."""
        assert INDECalculator.classify_pedra(np.nan) is None


class TestBusinessRulesValidator:
    """Testes para o validador de regras de negócio."""

    @pytest.fixture
    def sample_data(self):
        """DataFrame de exemplo para testes."""
        return pd.DataFrame(
            {
                "ra": [1, 2, 3, 4, 5],
                "defasagem": [0, -1, -2, -3, 1],
                "ian": [10.0, 5.0, 2.5, 2.5, 10.0],  # Valores corretos
                "ida": [8.0, 7.0, 6.0, 5.0, 9.0],
                "ieg": [7.0, 6.5, 6.0, 5.5, 8.0],
                "iaa": [7.0, 6.0, 5.0, 4.0, 8.0],
                "ips": [8.0, 7.0, 6.0, 5.0, 9.0],
                "ipp": [7.5, 6.5, 5.5, 4.5, 8.5],
                "ipv": [8.0, 7.0, 6.0, 5.0, 9.0],
                "fase": [5, 6, 7, 3, 4],
                "mat": [8.0, 7.0, 6.0, 5.0, 9.0],
                "por": [8.0, 7.0, 6.0, 5.0, 9.0],
                "ing": [8.0, 7.0, 6.0, 5.0, 9.0],
            }
        )

    def test_validate_ian_all_correct(self, sample_data):
        """Valida IAN quando todos valores estão corretos."""
        validator = BusinessRulesValidator(tolerance=0.1)
        result = validator.validate_ian(sample_data)

        assert result.passed is True
        assert result.pct_valid == 1.0

    def test_validate_ian_with_errors(self):
        """Detecta erros quando IAN não segue a regra."""
        df = pd.DataFrame(
            {
                "defasagem": [0, -1, -3],
                "ian": [10.0, 10.0, 10.0],  # Segundo e terceiro errados!
            }
        )

        validator = BusinessRulesValidator(tolerance=0.1)
        result = validator.validate_ian(df)

        assert result.passed is False
        assert result.n_invalid == 2

    def test_validate_ida_with_tolerance(self):
        """IDA deve aceitar pequenas diferenças."""
        df = pd.DataFrame(
            {
                "ida": [8.0, 7.0, 6.0],
                "mat": [8.0, 7.0, 6.0],
                "por": [8.0, 7.0, 6.0],
                "ing": [8.0, 7.0, 6.0],
            }
        )

        validator = BusinessRulesValidator(tolerance=0.5)
        result = validator.validate_ida(df)

        assert result.passed is True

    def test_validate_all_returns_list(self, sample_data):
        """validate_all retorna lista de resultados."""
        validator = BusinessRulesValidator()
        results = validator.validate_all(sample_data, verbose=False)

        assert isinstance(results, list)
        assert all(isinstance(r, ValidationResult) for r in results)


class TestDefasagemCategory:
    """Testes para categorização de defasagem."""

    def test_em_fase(self):
        """Defasagem >= 0 é 'Em Fase'."""
        assert INDECalculator.get_defasagem_category(0) == "Em Fase"
        assert INDECalculator.get_defasagem_category(1) == "Em Fase"

    def test_moderada(self):
        """Defasagem entre -2 e 0 é 'Moderada'."""
        assert INDECalculator.get_defasagem_category(-1) == "Defasagem Moderada"
        assert INDECalculator.get_defasagem_category(-1.5) == "Defasagem Moderada"

    def test_severa(self):
        """Defasagem <= -2 é 'Severa'."""
        assert INDECalculator.get_defasagem_category(-2) == "Defasagem Severa"
        assert INDECalculator.get_defasagem_category(-5) == "Defasagem Severa"


class TestWeightsConsistency:
    """Verifica que os pesos somam 1.0."""

    def test_weights_standard_sum_to_one(self):
        """Pesos padrão devem somar 1.0."""
        total = sum(INDECalculator.WEIGHTS_STANDARD.values())
        assert abs(total - 1.0) < 0.001

    def test_weights_fase8_sum_to_one(self):
        """Pesos fase 8 devem somar 1.0."""
        total = sum(INDECalculator.WEIGHTS_FASE8.values())
        assert abs(total - 1.0) < 0.001

    def test_fase8_has_fewer_indicators(self):
        """Fase 8 usa menos indicadores (sem IPP e IPV)."""
        assert "ipp" not in INDECalculator.WEIGHTS_FASE8
        assert "ipv" not in INDECalculator.WEIGHTS_FASE8
        assert "ipp" in INDECalculator.WEIGHTS_STANDARD
        assert "ipv" in INDECalculator.WEIGHTS_STANDARD

    def test_ida_weight_higher_in_fase8(self):
        """IDA tem peso maior na Fase 8 (universitários)."""
        assert (
            INDECalculator.WEIGHTS_FASE8["ida"] > INDECalculator.WEIGHTS_STANDARD["ida"]
        )
        assert INDECalculator.WEIGHTS_FASE8["ida"] == 0.4
        assert INDECalculator.WEIGHTS_STANDARD["ida"] == 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
