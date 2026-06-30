# Pipeline de Commodities via Yfinance

## Objetivo

Extrair dados historicos diarios de commodities e empresas relacionadas ao setor via
`yfinance`, usando apenas os tickers definidos em `src/series_catalog_commodities.py`.

## Tickers cobertos

| Marker | Ticker yfinance | Fonte | Inicio minimo yfinance |
|---|---|---|---|
| JJN | `JJN` | yfinance | `2018-01-17` |
| VALE | `VALE` | yfinance | `2013-01-01` |
| SLX | `SLX` | yfinance | `2013-01-01` |
| CLF | `CLF` | yfinance | `2013-01-01` |
| FTI | `FTI` | yfinance | `2017-01-03` |

## Arquitetura do script

`src/run_extraction_commodities.py` segue uma rotina simples:

1. Le `--start-date`, `--end-date` e `--output-dir`.
2. Aplica o inicio minimo por marcador quando existir.
3. Baixa as series com `fetch_yfinance_series(...)`.
4. Salva os dados brutos em `data/raw/yfinance_commodities.csv`.
5. Salva os dados normalizados e ordenados em `data/curated/commodity_indicators.csv`.
6. Salva eventuais falhas em `data/curated/failed_commodities.csv`.

Os CSVs de dados mantem o schema:

| Coluna | Descricao |
|---|---|
| `date` | Data da observacao no formato `YYYY-MM-DD` |
| `marker` | Ticker usado como marcador (`JJN`, `VALE`, `SLX`, `CLF`, `FTI`) |
| `value` | Preco de fechamento retornado pelo yfinance |
| `source` | Sempre `yfinance` para dados extraidos com sucesso |

## Configuracao

Esta rotina nao exige `FRED_API_KEY`, `EIA_API_KEY` ou qualquer outra chave externa.

Exemplo de execucao:

```bash
python src/run_extraction_commodities.py --start-date 2024-01-01 --end-date 2024-01-10
```

Por padrao, o periodo vai de `2013-01-01` ate a data atual. Para `JJN`, a
consulta comeca em `2018-01-17` quando a data pedida for anterior. Para `FTI`,
a consulta comeca em `2017-01-03` quando a data pedida for anterior.
