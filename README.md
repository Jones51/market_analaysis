# Extração de Indicadores de Mercado (2013–Atual)

## 🛠️ Introdução
Desenvolvimento de um pipeline de extração de dados financeiros e macroeconômicos automatizado, cobrindo indicadores de mercado desde 2013 até a data atual. O projeto consolida dados de múltiplas fontes públicas (Yahoo Finance, FRED e Banco Central do Brasil) em um dataset unificado e normalizado, voltado para análise de mercado com foco em commodities de energia, moedas, índices e taxas de juros.

## 📝 Problema de Negócios
A coleta manual de indicadores financeiros e macroeconômicos a partir de portais e planilhas é lenta, sujeita a erros humanos e difícil de reproduzir. Este projeto propõe a automação completa da extração dessas séries históricas, garantindo padronização de formato, rastreabilidade de falhas e baixo custo operacional por meio de APIs gratuitas e de fácil acesso.

## 🎓 Metodologia
A implementação segue o ciclo de vida da extração de dados, abrangendo as seguintes etapas técnicas:

**Extração (E):** Consumo programático de dados via APIs públicas — Yahoo Finance (yfinance), Federal Reserve (FRED) e Banco Central do Brasil (BCB SGS) — cobrindo 20 séries primárias (commodities, índices, moedas, criptoativos, juros e spreads).

**Transformação (T):** Normalização dos dados brutos em formato longo padronizado (`date`, `marker`, `value`, `source`) com Python e Pandas, incluindo cálculo de métricas derivadas como o spread da curva de juros americana (10Y − 2Y).

**Carregamento (L):** Persistência em arquivos CSV separados por camada — `raw/` (dados brutos por fonte) e `curated/` (dataset consolidado, séries pendentes e falhas de coleta).

**Rastreabilidade:** Separação explícita entre indicadores coletados com sucesso, pendentes de fonte alternativa (MOVE, DI Futuro, Baltic Dry Index, OPEC Spare Capacity) e falhas de execução, registradas em arquivos dedicados.

## 📊 Habilidades
- **Linguagens & Ambientes:** Python (scripting, CLI com argparse, variáveis de ambiente)

- **Engenharia de Dados:** Extração via API (yfinance, FRED HTTP API, requests), Data Wrangling com Pandas, normalização em formato longo, tratamento de erros com retry e backoff exponencial

- **Fontes de Dados:** Yahoo Finance, FRED (Federal Reserve), BCB SGS (Banco Central do Brasil)

- **Boas Práticas:** Separação de camadas raw/curated, rastreamento de falhas, configuração via `.env`, estrutura modular com catálogo de séries

## 🛫 Como Rodar o Projeto

**1) Instalar dependências**
```bash
pip install -r requirements.txt
```

**2) Definir a chave da API FRED**

Opção A (recomendada) — arquivo `.env` na raiz do projeto:
```env
FRED_API_KEY=sua_chave_aqui
```

Opção B — variável de ambiente no PowerShell (sessão atual):
```powershell
$env:FRED_API_KEY="sua_chave_aqui"
```

**3) Rodar a extração**
```bash
python src/run_extraction.py --start-date 2013-01-01 --end-date 2026-12-31 --output-dir data
```

Omitindo `--end-date`, a data atual é usada automaticamente.

## 🪄 Saídas Geradas

| Arquivo | Camada | Descrição |
|---|---|---|
| `data/raw/yfinance.csv` | Raw | Preços de ativos do Yahoo Finance |
| `data/raw/fred.csv` | Raw | Séries macro do Federal Reserve |
| `data/raw/bcb_sgs.csv` | Raw | Dados do Banco Central do Brasil |
| `data/curated/market_indicators.csv` | Curated | Dataset consolidado com todos os indicadores |
| `data/curated/pending_series.csv` | Curated | Séries aguardando fonte alternativa |
| `data/curated/failed_series.csv` | Curated | Séries com falha na coleta |

> **Séries pendentes:** MOVE, DI_FUTURO, BALTIC_DRY_INDEX e OPEC_SPARE_CAPACITY dependem de fontes adicionais ainda não implementadas.
