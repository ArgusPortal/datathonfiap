# Feature Stability Report — v1.1.0

## Resumo por Quadrante

| Quadrante | Qtd | Descrição |
|-----------|-----|-----------|
| ROBUST | 0 | Alta importância + baixo PSI → **manter** |
| VOLATILE | 11 | Alta importância + alto PSI → **monitorar/retreinar** |
| NOISE | 17 | Baixa importância + alto PSI → **candidata a remoção** |
| STABLE | 4 | Baixa importância + baixo PSI → **manter se leve** |

## Detalhamento por Feature

| Feature | Importance | PSI | Missing | Quadrante | Ação |
|---------|-----------|-----|---------|-----------|------|
| ips_2023 | +0.0737 | 0.5363 | 8.1% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| ipp_2023 | +0.0671 | 0.6137 | 9.4% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| delta_ipv_2022_2023 | +0.0439 | 0.1344 | 42.0% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| std_indicadores | +0.0320 | 4.4425 | 0.0% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| delta_iaa_2022_2023 | +0.0215 | 0.3276 | 41.0% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| media_indicadores | +0.0192 | 0.1920 | 0.0% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| ida_2023 | +0.0186 | 0.4561 | 9.4% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| ian_2023 | +0.0183 | 0.1867 | 0.0% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| delta_ieg_2022_2023 | +0.0169 | 0.1221 | 42.0% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| delta_ian_2022_2023 | +0.0119 | 0.2989 | 38.8% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| idade_2023 | +0.0103 | 9.6678 | 0.0% | VOLATILE | Monitorar — preditiva mas sensível a drift, retreinar se necessário |
| delta_ida_2022_2023 | +0.0090 | 0.3270 | 42.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| delta_ips_2022_2023 | +0.0077 | 0.2359 | 41.2% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| genero_2023 | +0.0073 | 0.0000 | 0.0% | STABLE | Manter — contribuição marginal mas estável |
| ano_ingresso_2023 | +0.0071 | 1.0296 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| ieg_2023 | +0.0049 | 0.1198 | 9.4% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| has_prev_year_data | +0.0014 | 0.1405 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| instituicao_2023 | +0.0012 | 0.0000 | 0.0% | STABLE | Manter — contribuição marginal mas estável |
| iaa_2023 | +0.0003 | 0.3866 | 7.7% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| fase_2023 | +0.0000 | 0.0000 | 77.3% | STABLE | Avaliar remoção — importância nula ou negativa |
| ipp_2023_missing | +0.0000 | 2.5741 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| iaa_2023_missing | +0.0000 | 2.0723 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| ieg_2023_missing | +0.0000 | 2.5741 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| ida_2023_missing | +0.0000 | 2.5741 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| min_indicador | +0.0000 | 2.0723 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| ips_2023_missing | +0.0000 | 2.1872 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| anos_pm_2023 | +0.0000 | 1.0296 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| ipv_2023_missing | +0.0000 | 2.5741 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| fase_x_media | +0.0000 | 0.0000 | 77.3% | STABLE | Avaliar remoção — importância nula ou negativa |
| range_indicadores | +0.0000 | 6.1054 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| max_indicador | -0.0046 | 6.1054 | 0.0% | NOISE | Considerar remoção — causa drift sem contribuir para predição |
| ipv_2023 | -0.0067 | 0.3728 | 9.4% | NOISE | Considerar remoção — causa drift sem contribuir para predição |

## Recomendações

### Features Voláteis (alta importância + drift)

- **ips_2023** (imp=+0.0737, PSI=0.5363)
- **ipp_2023** (imp=+0.0671, PSI=0.6137)
- **delta_ipv_2022_2023** (imp=+0.0439, PSI=0.1344)
- **std_indicadores** (imp=+0.0320, PSI=4.4425)
- **delta_iaa_2022_2023** (imp=+0.0215, PSI=0.3276)
- **media_indicadores** (imp=+0.0192, PSI=0.1920)
- **ida_2023** (imp=+0.0186, PSI=0.4561)
- **ian_2023** (imp=+0.0183, PSI=0.1867)
- **delta_ieg_2022_2023** (imp=+0.0169, PSI=0.1221)
- **delta_ian_2022_2023** (imp=+0.0119, PSI=0.2989)
- **idade_2023** (imp=+0.0103, PSI=9.6678)

**Ação**: Manter no modelo mas com monitoramento ativo de drift. Se PSI > 0.25 em produção, disparar retreinamento automático.

### Features Ruidosas (baixa importância + drift)

- **delta_ida_2022_2023** (imp=+0.0090, PSI=0.3270)
- **delta_ips_2022_2023** (imp=+0.0077, PSI=0.2359)
- **ano_ingresso_2023** (imp=+0.0071, PSI=1.0296)
- **ieg_2023** (imp=+0.0049, PSI=0.1198)
- **has_prev_year_data** (imp=+0.0014, PSI=0.1405)
- **iaa_2023** (imp=+0.0003, PSI=0.3866)
- **ipp_2023_missing** (imp=+0.0000, PSI=2.5741)
- **iaa_2023_missing** (imp=+0.0000, PSI=2.0723)
- **ieg_2023_missing** (imp=+0.0000, PSI=2.5741)
- **ida_2023_missing** (imp=+0.0000, PSI=2.5741)
- **min_indicador** (imp=+0.0000, PSI=2.0723)
- **ips_2023_missing** (imp=+0.0000, PSI=2.1872)
- **anos_pm_2023** (imp=+0.0000, PSI=1.0296)
- **ipv_2023_missing** (imp=+0.0000, PSI=2.5741)
- **range_indicadores** (imp=+0.0000, PSI=6.1054)
- **max_indicador** (imp=-0.0046, PSI=6.1054)
- **ipv_2023** (imp=-0.0067, PSI=0.3728)

**Ação**: Testar remoção destas features. Elas contribuem pouco para o modelo mas geram alertas de drift desnecessários. Retreinar sem elas e comparar F2-score — se não degradar, remover.

### Features com Importância Negativa

- **max_indicador** (imp=-0.0046)
- **ipv_2023** (imp=-0.0067)

**Ação**: Remover imediatamente — estas features prejudicam o modelo. O F2-score **melhora** quando removidas.
