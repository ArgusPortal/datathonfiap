"""
Make Dataset: Pipeline de criação do dataset de modelagem.

Este script transforma os dados brutos (PEDE2024.xlsx) em datasets
normalizados e prontos para modelagem.

Outputs:
- data/interim/{year}_normalized.parquet
- data/interim/{year}_schema.json
- data/processed/modeling_dataset.parquet
- data/processed/data_card.json
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Adiciona src ao path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from data_quality import DataQualityChecker, validate_modeling_dataset


# Configuração de paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Arquivo fonte
SOURCE_FILE = PROJECT_ROOT / "PEDE2024.xlsx"

# Mapeamento de colunas para normalização (lowercase, sem espaços)
COLUMN_MAPPING = {
    # Identificadores
    'ra': 'ra',
    'nome': 'nome',
    'instituicao_ensino_aluno': 'instituicao',
    'instituição de ensino': 'instituicao',
    
    # Indicadores principais
    'inde': 'inde',
    'ian': 'ian',
    'ida': 'ida',
    'ieg': 'ieg',
    'iaa': 'iaa',
    'ips': 'ips',
    'ipp': 'ipp',
    'ipv': 'ipv',
    'ipm': 'ipm',
    
    # Fase e defasagem
    'fase': 'fase',
    'fase_ideal': 'fase_ideal',
    'fase ideal': 'fase_ideal',
    'defasagem': 'defasagem',
    
    # Outros
    'idade_aluno': 'idade',
    'anos_pm': 'anos_pm',
    'anos pm': 'anos_pm',
    'bolsista': 'bolsista',
    'ponto_virada': 'ponto_virada',
    'ponto de virada': 'ponto_virada',
    'pedra': 'pedra',
    
    # Indicadores de destaque (2024)
    'destaque_inde': 'destaque_inde',
    'destaque inde': 'destaque_inde',
    'destaque_ida': 'destaque_ida',
    'destaque ida': 'destaque_ida',
    'destaque_ieg': 'destaque_ieg',
    'destaque ieg': 'destaque_ieg',
    
    # Recomendações
    'rec_ava': 'rec_ava',
    'rec ava': 'rec_ava',
    'rec_inde': 'rec_inde',
    'rec inde': 'rec_inde',
    
    # Indicador nutricional
    'indicador_nutricional': 'indicador_nutricional',
    'indicador nutricional': 'indicador_nutricional',
    
    # Gênero
    'genero': 'genero',
    'sexo': 'genero',
}

# Colunas que são permitidas como features (sem risco de leakage)
ALLOWED_FEATURE_COLUMNS = [
    'ra', 'nome', 'instituicao', 'idade', 'genero',
    'fase', 'anos_pm', 'bolsista',
    'inde', 'ian', 'ida', 'ieg', 'iaa', 'ips', 'ipp', 'ipv', 'ipm',
    'indicador_nutricional',
]

# Colunas bloqueadas (causam leakage)
BLOCKED_COLUMNS = [
    'defasagem', 'fase_ideal', 'ponto_virada', 'pedra',
    'destaque_inde', 'destaque_ida', 'destaque_ieg',
    'rec_ava', 'rec_inde',
]


def normalize_column_name(col: str) -> str:
    """
    Normaliza nome de coluna.
    
    Args:
        col: Nome original da coluna
        
    Returns:
        Nome normalizado
    """
    # Lowercase e strip
    col_clean = col.lower().strip()
    
    # Remove caracteres especiais
    col_clean = col_clean.replace('_', ' ')
    
    # Busca no mapeamento
    if col_clean in COLUMN_MAPPING:
        return COLUMN_MAPPING[col_clean]
    
    # Se não encontrou, retorna versão limpa
    return col_clean.replace(' ', '_')


def load_and_normalize_sheet(
    filepath: Path, 
    sheet_name: str,
    year: int
) -> Tuple[pd.DataFrame, Dict]:
    """
    Carrega e normaliza uma aba do Excel.
    
    Args:
        filepath: Caminho do arquivo Excel
        sheet_name: Nome da aba
        year: Ano dos dados
        
    Returns:
        Tuple[DataFrame normalizado, schema dict]
    """
    print(f"  Carregando {sheet_name}...")
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    
    original_columns = df.columns.tolist()
    
    # Normaliza nomes de colunas
    new_columns = {}
    for col in df.columns:
        new_name = normalize_column_name(col)
        new_columns[col] = new_name
    
    df = df.rename(columns=new_columns)
    
    # Remove colunas duplicadas (mantém primeira)
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Trata colunas com tipos mistos para evitar erros no parquet
    from datetime import datetime as dt
    for col in df.columns:
        if df[col].dtype == 'object':
            # Tenta converter para numérico primeiro
            numeric_converted = pd.to_numeric(df[col], errors='coerce')
            non_null_original = df[col].notna().sum()
            non_null_numeric = numeric_converted.notna().sum()
            
            # Se maioria converteu para numérico, usa versão numérica
            if non_null_numeric >= non_null_original * 0.8:
                df[col] = numeric_converted
            else:
                # Senão, converte tudo para string de forma segura
                def safe_str(x):
                    if pd.isna(x):
                        return None
                    if isinstance(x, dt):
                        return x.strftime('%Y-%m-%d')
                    return str(x)
                df[col] = df[col].apply(safe_str)
    
    # Adiciona coluna de ano
    df['ano'] = year
    
    # Gera schema
    schema = {
        'year': year,
        'original_columns': original_columns,
        'normalized_columns': df.columns.tolist(),
        'n_rows': len(df),
        'n_columns': len(df.columns),
        'column_types': {col: str(df[col].dtype) for col in df.columns},
        'created_at': datetime.now().isoformat()
    }
    
    print(f"    {len(df)} registros, {len(df.columns)} colunas")
    
    return df, schema


def compute_target(defasagem: pd.Series) -> pd.Series:
    """
    Computa target binário baseado na defasagem.
    
    Regra: em_risco = 1 se Defasagem < 0, senão 0
    
    Args:
        defasagem: Série com valores de defasagem
        
    Returns:
        Série com target binário
    """
    return (defasagem < 0).astype(int)


def create_modeling_dataset(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    feature_year: int,
    label_year: int
) -> pd.DataFrame:
    """
    Cria dataset de modelagem juntando features e labels.
    
    Args:
        features_df: DataFrame com features (ano t)
        labels_df: DataFrame com labels (ano t+1)
        feature_year: Ano das features
        label_year: Ano dos labels
        
    Returns:
        DataFrame de modelagem
    """
    print(f"\nCriando dataset de modelagem: features {feature_year} → labels {label_year}")
    
    # Seleciona apenas colunas permitidas para features
    available_features = [col for col in ALLOWED_FEATURE_COLUMNS if col in features_df.columns]
    features_clean = features_df[available_features].copy()
    
    # Renomeia colunas com sufixo do ano
    rename_map = {col: f"{col}_{feature_year}" for col in features_clean.columns if col != 'ra'}
    features_clean = features_clean.rename(columns=rename_map)
    
    # Prepara labels
    labels_clean = labels_df[['ra', 'defasagem']].copy()
    labels_clean['em_risco'] = compute_target(labels_clean['defasagem'])
    labels_clean = labels_clean.drop(columns=['defasagem'])
    labels_clean = labels_clean.rename(columns={'em_risco': f'em_risco_{label_year}'})
    
    # Join por RA
    modeling_df = features_clean.merge(labels_clean, on='ra', how='inner')
    
    print(f"  Features disponíveis: {len(available_features)}")
    print(f"  RAs com match: {len(modeling_df)}")
    print(f"  Target distribution:")
    target_col = f'em_risco_{label_year}'
    print(f"    em_risco=1: {modeling_df[target_col].sum()} ({modeling_df[target_col].mean():.1%})")
    print(f"    em_risco=0: {(modeling_df[target_col]==0).sum()} ({(modeling_df[target_col]==0).mean():.1%})")
    
    return modeling_df


def generate_data_card(
    datasets: Dict[int, pd.DataFrame],
    modeling_df: pd.DataFrame,
    output_path: Path
) -> Dict:
    """
    Gera data card com metadados do pipeline.
    
    Args:
        datasets: Dict de ano -> DataFrame normalizado
        modeling_df: DataFrame de modelagem
        output_path: Caminho para salvar
        
    Returns:
        Dict com data card
    """
    data_card = {
        'pipeline_version': '1.0.0',
        'created_at': datetime.now().isoformat(),
        'source_file': str(SOURCE_FILE),
        
        'interim_datasets': {},
        'modeling_dataset': {},
        
        'quality_checks': {},
    }
    
    # Info dos datasets intermediários
    for year, df in datasets.items():
        data_card['interim_datasets'][year] = {
            'n_rows': len(df),
            'n_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'missing_by_column': df.isnull().sum().to_dict(),
        }
    
    # Info do dataset de modelagem
    target_col = [c for c in modeling_df.columns if c.startswith('em_risco')][0]
    feature_cols = [c for c in modeling_df.columns if c not in ['ra', target_col]]
    
    data_card['modeling_dataset'] = {
        'n_rows': len(modeling_df),
        'n_features': len(feature_cols),
        'features': feature_cols,
        'target_column': target_col,
        'target_distribution': {
            'em_risco_1': int(modeling_df[target_col].sum()),
            'em_risco_0': int((modeling_df[target_col] == 0).sum()),
            'ratio_em_risco': float(modeling_df[target_col].mean()),
        },
        'missing_features': modeling_df[feature_cols].isnull().sum().to_dict(),
    }
    
    # Salva
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_card, f, indent=2, ensure_ascii=False, default=str)
    
    return data_card


def run_pipeline(
    source_file: Path = SOURCE_FILE,
    output_interim: Path = DATA_INTERIM,
    output_processed: Path = DATA_PROCESSED,
    feature_year: int = 2023,
    label_year: int = 2024,
    validate: bool = True
) -> Tuple[bool, pd.DataFrame]:
    """
    Executa pipeline completo de criação do dataset.
    
    Args:
        source_file: Arquivo Excel fonte
        output_interim: Pasta para arquivos intermediários
        output_processed: Pasta para arquivos processados
        feature_year: Ano para extrair features
        label_year: Ano para extrair labels (target)
        validate: Se True, executa validações de qualidade
        
    Returns:
        Tuple[success, modeling_dataframe]
    """
    print("=" * 60)
    print("PIPELINE: Make Dataset - Passos Mágicos")
    print("=" * 60)
    
    # Cria diretórios
    output_interim.mkdir(parents=True, exist_ok=True)
    output_processed.mkdir(parents=True, exist_ok=True)
    
    # Verifica arquivo fonte
    if not source_file.exists():
        print(f"❌ ERRO: Arquivo fonte não encontrado: {source_file}")
        return False, None
    
    print(f"\nFonte: {source_file}")
    print(f"Feature year: {feature_year}")
    print(f"Label year: {label_year}")
    
    # Step 1: Carrega e normaliza cada aba
    print("\n[Step 1] Carregando e normalizando abas...")
    datasets = {}
    schemas = {}
    
    for year in [2022, 2023, 2024]:
        sheet_name = f"PEDE{year}"
        try:
            df, schema = load_and_normalize_sheet(source_file, sheet_name, year)
            datasets[year] = df
            schemas[year] = schema
            
            # Salva parquet
            parquet_path = output_interim / f"{year}_normalized.parquet"
            df.to_parquet(parquet_path, index=False)
            print(f"    Salvo: {parquet_path.name}")
            
            # Salva schema
            schema_path = output_interim / f"{year}_schema.json"
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {sheet_name}: {e}")
            return False, None
    
    # Step 2: Validação de qualidade
    if validate:
        print("\n[Step 2] Validação de qualidade...")
        all_passed = True
        
        for year, df in datasets.items():
            checker = DataQualityChecker(df, year=year)
            passed, _ = checker.run_all_checks(critical_columns=['ra'])
            
            status = "✅" if passed else "❌"
            print(f"  {status} {year}: {len(df)} registros")
            
            if not passed:
                all_passed = False
                print(checker.get_summary())
        
        if not all_passed:
            print("\n⚠️ AVISO: Algumas validações falharam, mas continuando...")
    
    # Step 3: Cria dataset de modelagem
    print("\n[Step 3] Criando dataset de modelagem...")
    
    if feature_year not in datasets or label_year not in datasets:
        print(f"❌ ERRO: Anos {feature_year} ou {label_year} não disponíveis")
        return False, None
    
    modeling_df = create_modeling_dataset(
        features_df=datasets[feature_year],
        labels_df=datasets[label_year],
        feature_year=feature_year,
        label_year=label_year
    )
    
    # Step 4: Validação final do dataset de modelagem
    print("\n[Step 4] Validação final...")
    
    # Verifica leakage
    feature_cols = [c for c in modeling_df.columns if not c.startswith('em_risco') and c != 'ra']
    checker = DataQualityChecker(modeling_df)
    leakage_result = checker.check_leakage(feature_cols)
    
    if not leakage_result.passed:
        print(f"❌ LEAKAGE DETECTADO: {leakage_result.details}")
        return False, None
    else:
        print("  ✅ Sem leakage nas features")
    
    # Step 5: Salva dataset final
    print("\n[Step 5] Salvando outputs...")
    
    # Salva parquet
    modeling_path = output_processed / "modeling_dataset.parquet"
    modeling_df.to_parquet(modeling_path, index=False)
    print(f"  ✅ Salvo: {modeling_path}")
    
    # Gera e salva data card
    data_card_path = output_processed / "data_card.json"
    data_card = generate_data_card(datasets, modeling_df, data_card_path)
    print(f"  ✅ Salvo: {data_card_path}")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO DO PIPELINE")
    print("=" * 60)
    print(f"Datasets intermediários: {len(datasets)}")
    print(f"Dataset de modelagem: {len(modeling_df)} registros")
    target_col = [c for c in modeling_df.columns if c.startswith('em_risco')][0]
    print(f"Target distribution: {modeling_df[target_col].mean():.1%} em risco")
    print(f"Features: {len([c for c in modeling_df.columns if c not in ['ra', target_col]])}")
    print("\n✅ Pipeline concluído com sucesso!")
    
    return True, modeling_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline de criação do dataset de modelagem")
    parser.add_argument("--source", type=str, default=str(SOURCE_FILE), help="Arquivo Excel fonte")
    parser.add_argument("--feature-year", type=int, default=2023, help="Ano para features")
    parser.add_argument("--label-year", type=int, default=2024, help="Ano para labels")
    parser.add_argument("--no-validate", action="store_true", help="Pula validações")
    
    args = parser.parse_args()
    
    success, df = run_pipeline(
        source_file=Path(args.source),
        feature_year=args.feature_year,
        label_year=args.label_year,
        validate=not args.no_validate
    )
    
    exit(0 if success else 1)
