"""
Testes para make_dataset.py - Pipeline de criação do dataset de modelagem.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from make_dataset import (
    normalize_column_name,
    remove_accents,
    fix_excel_date_as_number,
    normalize_instituicao,
    compute_target,
    COLUMN_MAPPING,
    ALLOWED_FEATURE_COLUMNS,
)


class TestRemoveAccents:
    """Testes para remoção de acentos."""
    
    def test_remove_simple_accents(self):
        """Testa remoção de acentos simples."""
        assert remove_accents("gênero") == "genero"
        assert remove_accents("instituição") == "instituicao"
        assert remove_accents("ação") == "acao"
    
    def test_remove_multiple_accents(self):
        """Testa remoção de múltiplos acentos."""
        assert remove_accents("avaliação") == "avaliacao"
        assert remove_accents("índice") == "indice"
    
    def test_no_accents_unchanged(self):
        """Testa que strings sem acento não mudam."""
        assert remove_accents("idade") == "idade"
        assert remove_accents("fase") == "fase"


class TestNormalizeColumnName:
    """Testes para normalização de nomes de colunas."""
    
    def test_normalize_genero_with_accent(self):
        """Testa que gênero com acento é normalizado."""
        assert normalize_column_name("Gênero") == "genero"
        assert normalize_column_name("GÊNERO") == "genero"
        assert normalize_column_name("gênero") == "genero"
    
    def test_normalize_genero_without_accent(self):
        """Testa que genero sem acento também funciona."""
        assert normalize_column_name("genero") == "genero"
        assert normalize_column_name("Genero") == "genero"
    
    def test_normalize_instituicao(self):
        """Testa normalização de instituição."""
        assert normalize_column_name("instituicao") == "instituicao"
        assert normalize_column_name("Instituição de Ensino") == "instituicao"
    
    def test_normalize_with_spaces_and_underscores(self):
        """Testa normalização com espaços e underscores."""
        assert normalize_column_name("ano_ingresso") == "ano_ingresso"
        assert normalize_column_name("Ano Ingresso") == "ano_ingresso"


class TestFixExcelDateAsNumber:
    """Testes para correção de idade corrompida pelo Excel."""
    
    def test_fix_string_number(self):
        """Testa conversão de string numérica."""
        assert fix_excel_date_as_number("8") == 8
        assert fix_excel_date_as_number("15") == 15
        assert fix_excel_date_as_number("10.0") == 10
    
    def test_fix_excel_date_format(self):
        """Testa correção de data serializada do Excel."""
        assert fix_excel_date_as_number("1900-01-07") == 7
        assert fix_excel_date_as_number("1900-01-15") == 15
        assert fix_excel_date_as_number("1900-01-08") == 8
        assert fix_excel_date_as_number("1900-01-12") == 12
    
    def test_fix_integer_input(self):
        """Testa que inteiros válidos são mantidos."""
        assert fix_excel_date_as_number(8) == 8
        assert fix_excel_date_as_number(15) == 15
        assert fix_excel_date_as_number(10) == 10
    
    def test_fix_float_input(self):
        """Testa que floats são convertidos para int."""
        assert fix_excel_date_as_number(8.0) == 8
        assert fix_excel_date_as_number(15.5) == 15
    
    def test_invalid_values_return_none(self):
        """Testa que valores inválidos retornam None."""
        assert fix_excel_date_as_number(None) is None
        assert fix_excel_date_as_number(np.nan) is None
        assert fix_excel_date_as_number("texto") is None
        assert fix_excel_date_as_number("2023-05-10") is None  # Data não-1900
    
    def test_out_of_range_returns_none(self):
        """Testa que idades fora do range retornam None."""
        assert fix_excel_date_as_number(2) is None  # Muito baixo
        assert fix_excel_date_as_number(50) is None  # Muito alto
        assert fix_excel_date_as_number("1900-01-02") is None  # Dia 2 = idade 2 (inválido)


class TestNormalizeInstituicao:
    """Testes para normalização de instituição."""
    
    def test_publica(self):
        """Testa normalização de escola pública."""
        assert normalize_instituicao("Pública") == "Publica"
        assert normalize_instituicao("PÚBLICA") == "Publica"
        assert normalize_instituicao("pública") == "Publica"
    
    def test_privada_simple(self):
        """Testa normalização de escola privada simples."""
        assert normalize_instituicao("Privada") == "Privada"
        assert normalize_instituicao("PRIVADA") == "Privada"
    
    def test_privada_apadrinhamento(self):
        """Testa normalização de apadrinhamento."""
        assert normalize_instituicao("Privada - Programa de Apadrinhamento") == "Privada_Apadrinhamento"
        assert normalize_instituicao("Privada - Programa de apadrinhamento") == "Privada_Apadrinhamento"
    
    def test_privada_bolsa(self):
        """Testa normalização de bolsa."""
        assert normalize_instituicao("Privada *Parcerias com Bolsa 100%") == "Privada_Bolsa"
        assert normalize_instituicao("Privada - Pagamento por *Empresa Parceira") == "Privada_Bolsa"
    
    def test_concluiu_em(self):
        """Testa normalização de conclusão do EM."""
        assert normalize_instituicao("Concluiu o 3º EM") == "Concluiu_EM"
    
    def test_outros(self):
        """Testa normalização de outros valores."""
        assert normalize_instituicao("Nenhuma das opções acima") == "Outro"
        assert normalize_instituicao("Valor desconhecido") == "Outro"
    
    def test_missing_values(self):
        """Testa tratamento de valores ausentes."""
        assert normalize_instituicao(None) == "Desconhecido"
        assert normalize_instituicao(np.nan) == "Desconhecido"


class TestComputeTarget:
    """Testes para computação do target."""
    
    def test_negative_defasagem_is_risk(self):
        """Testa que defasagem negativa = em risco."""
        defasagem = pd.Series([-1, -2, -3])
        target = compute_target(defasagem)
        assert all(target == 1)
    
    def test_zero_or_positive_is_no_risk(self):
        """Testa que defasagem >= 0 = sem risco."""
        defasagem = pd.Series([0, 1, 2, 3])
        target = compute_target(defasagem)
        assert all(target == 0)
    
    def test_mixed_values(self):
        """Testa valores mistos."""
        defasagem = pd.Series([-2, -1, 0, 1, 2])
        target = compute_target(defasagem)
        expected = pd.Series([1, 1, 0, 0, 0])
        # Apenas verifica valores, não dtype
        np.testing.assert_array_equal(target.values, expected.values)


class TestAllowedFeatureColumns:
    """Testes para lista de features permitidas."""
    
    def test_genero_in_allowed(self):
        """Testa que gênero está na lista de permitidos."""
        assert 'genero' in ALLOWED_FEATURE_COLUMNS
    
    def test_ano_ingresso_in_allowed(self):
        """Testa que ano_ingresso está na lista de permitidos."""
        assert 'ano_ingresso' in ALLOWED_FEATURE_COLUMNS
    
    def test_idade_in_allowed(self):
        """Testa que idade está na lista de permitidos."""
        assert 'idade' in ALLOWED_FEATURE_COLUMNS
    
    def test_indicadores_in_allowed(self):
        """Testa que indicadores estão na lista de permitidos."""
        indicadores = ['ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv']
        for ind in indicadores:
            assert ind in ALLOWED_FEATURE_COLUMNS, f"{ind} não está em ALLOWED_FEATURE_COLUMNS"


class TestColumnMapping:
    """Testes para mapeamento de colunas."""
    
    def test_genero_with_accent_mapped(self):
        """Testa que gênero com acento está mapeado."""
        assert 'gênero' in COLUMN_MAPPING
        assert COLUMN_MAPPING['gênero'] == 'genero'
    
    def test_genero_without_accent_mapped(self):
        """Testa que genero sem acento está mapeado."""
        assert 'genero' in COLUMN_MAPPING
        assert COLUMN_MAPPING['genero'] == 'genero'
    
    def test_ano_ingresso_mapped(self):
        """Testa que ano_ingresso está mapeado."""
        assert 'ano_ingresso' in COLUMN_MAPPING or 'ano ingresso' in COLUMN_MAPPING
