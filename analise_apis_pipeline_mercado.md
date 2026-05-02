# Pipeline de Dados (2013-atual): análise de APIs gratuitas para marcadores macro/mercado

## Objetivo
Construir um pipeline para coletar e manter histórico (de 2013 até hoje) dos seguintes marcadores:

- BRENT
- WTI
- Gás Natural (Henry Hub)
- VIX
- OVX
- MOVE
- USD/BRL
- DXY (Dollar Index)
- US Treasury 2Y
- US Treasury 10Y
- Inclinação da curva (10Y-2Y)
- SELIC
- DI Futuro
- S&P 500
- MSCI World
- MSCI Emerging Markets
- Ibovespa
- Bitcoin
- Ethereum
- Gold
- Copper
- EPU (Economic Policy Uncertainty)
- Baltic Dry Index
- TED Spread
- OPEC Spare Capacity

---

## Critérios de escolha de fonte gratuita
Para este escopo, uma API/fonte gratuita é considerada viável se:

1. Permite acesso histórico >= 2013 (diário ou mensal, dependendo da série).
2. Tem estabilidade razoável para uso automatizado.
3. Possui documentação clara ou comunidade ativa.
4. Tem políticas de uso sem custo para baixa/média frequência.
5. Preferencialmente oferece formatos fáceis (JSON/CSV).

---

## APIs/fontes gratuitas candidatas (visão geral)

## 1) Yahoo Finance (biblioteca `yfinance`)
**Pontos fortes**
- Cobre boa parte dos ativos financeiros (commodities, índices, moedas, ETFs, cripto).
- Retorna histórico com granularidade diária e ajuste de preços.
- Simples de implementar em Python.

**Limitações**
- Não é API oficial pública com SLA.
- Pode ter mudanças de endpoint/instabilidade esporádica.
- Nem todos os marcadores macro especializados estão disponíveis (ex.: TED, OPEC spare capacity, algumas séries institucionais).

**Uso ideal no pipeline**
- Fonte principal para ativos de mercado (Brent, WTI, VIX, S&P, Ibovespa, BTC, ETH, Gold, Copper, USD/BRL via par cambial etc.).
- Sempre com fonte de contingência para reduzir risco operacional.

---

## 2) FRED / ALFRED (Federal Reserve Economic Data)
**Pontos fortes**
- API oficial gratuita, muito estável para séries macro dos EUA.
- Excelente para yields (2Y, 10Y), spread 10Y-2Y, índices de dólar em algumas versões, TED Spread (quando disponível), taxas e indicadores macro.
- Metadados ricos e versionamento histórico via ALFRED.

**Limitações**
- Não cobre bem ativos de bolsa globais em nível de ticker.
- Algumas séries podem ter descontinuidade/metodologia alterada.

**Uso ideal no pipeline**
- Fonte principal para séries macro/juros dos EUA e spreads.

---

## 3) Banco Central do Brasil (SGS API) e B3 (fontes públicas/arquivos)
**Pontos fortes**
- SGS (BCB) tem séries oficiais para SELIC e indicadores domésticos.
- Alta confiabilidade institucional.

**Limitações**
- DI Futuro nem sempre está prontamente disponível via API pública simples (muitas vezes exige dados B3, arquivos de mercado, ou provedores comerciais).
- Formato/estrutura pode variar por série.

**Uso ideal no pipeline**
- Fonte principal para SELIC.
- Para DI Futuro, avaliar proxy com taxas de juros locais quando não houver feed gratuito robusto.

---

## 4) Stooq / Investing (via scraping com cautela)
**Pontos fortes**
- Pode servir como fallback para alguns ativos.
- Gratuito em muitos casos.

**Limitações**
- Scraping pode violar termos se mal implementado.
- Maior fragilidade e risco de quebra.

**Uso ideal no pipeline**
- Somente fallback técnico, nunca fonte primária crítica.

---

## 5) APIs públicas específicas
- **EIA (US Energy Information Administration)**: energia (inclui dados que podem complementar petróleo/gás e fundamentos).
- **Quandl/Nasdaq Data Link (free datasets)**: alguns datasets gratuitos úteis, porém cobertura heterogênea.
- **policyuncertainty.com**: fonte do EPU (normalmente via arquivos/planilhas públicas).
- **FRED / outras fontes institucionais** para Baltic Dry (quando houver série espelhada) ou alternativa por dataset público.

---

## Mapeamento por marcador: melhor fonte gratuita sugerida

> Nota: alguns itens têm ticker/fonte que pode variar por provedor e região. A validação final deve testar disponibilidade histórica desde 2013 e continuidade.

| Marcador | Fonte principal sugerida | Fallback sugerido | Observações |
|---|---|---|---|
| BRENT | Yahoo Finance (`yfinance`) | Stooq/Investing/EIA | Geralmente via futuros/continuous contracts |
| WTI | Yahoo Finance (`yfinance`) | Stooq/Investing/EIA | Mesmo racional do Brent |
| Gás Natural (Henry Hub) | Yahoo Finance (`yfinance`) ou EIA | FRED (série relacionada) | Validar unidade e contrato |
| VIX | Yahoo Finance (`^VIX`) | FRED (série equivalente, se aplicável) | Boa cobertura no Yahoo |
| OVX | Yahoo Finance (`^OVX`) | CBOE (se público) | Verificar histórico completo |
| MOVE | FRED (se série disponível) / fonte ICE/BofA pública | Yahoo (se houver proxy) | Pode exigir proxy se série oficial não aberta |
| USD/BRL | Yahoo Finance (`BRL=X`) | BCB/PTAX | Definir taxa de fechamento desejada |
| DXY | Yahoo Finance (`DX-Y.NYB` ou equivalente) | FRED (índice dólar alternativo) | Conferir ticker ativo |
| US Treasury 2Y | FRED (DGS2) | Treasury.gov | Série diária padrão |
| US Treasury 10Y | FRED (DGS10) | Treasury.gov | Série diária padrão |
| Inclinação (10Y-2Y) | Derivada no pipeline (`DGS10 - DGS2`) | FRED (série pronta, se preferir) | Melhor calcular internamente |
| SELIC | BCB SGS | FRED (série espelho, se existir) | Preferir fonte oficial BCB |
| DI Futuro | B3 (arquivos públicos quando disponíveis) | Proxy por curva local | Ponto mais desafiador no gratuito |
| S&P 500 | Yahoo Finance (`^GSPC`) | Stooq/FRED (índice) | Alta robustez no Yahoo |
| MSCI World | ETF proxy no Yahoo (ex.: `URTH`) | Stooq/Investing | Série MSCI oficial costuma ser licenciada |
| MSCI Emerging Markets | ETF proxy no Yahoo (ex.: `EEM`) | Stooq/Investing | Mesmo ponto de licenciamento |
| Ibovespa | Yahoo Finance (`^BVSP`) | B3/Investing | Boa disponibilidade no Yahoo |
| Bitcoin | Yahoo Finance (`BTC-USD`) | CoinGecko / exchanges | CoinGecko também é boa opção gratuita |
| Ethereum | Yahoo Finance (`ETH-USD`) | CoinGecko / exchanges | Corrigir nome para Ethereum |
| Gold | Yahoo Finance (futuros/spot proxy) | FRED/Quandl free | Validar ativo escolhido (spot x futuro) |
| Copper | Yahoo Finance (futuros) | FRED/Quandl free | Verificar continuidade contratual |
| EPU | policyuncertainty.com (arquivos públicos) | FRED (algumas versões) | Frequência normalmente mensal |
| Baltic Dry Index | FRED (se série disponível) / fonte pública marítima | Investing/Stooq | Confirmar licença e frequência |
| TED Spread | FRED | Derivação (LIBOR-OIS proxies) | FRED costuma ser caminho natural |
| OPEC Spare Capacity | EIA/OPEC relatórios públicos | IEA (se acesso permitido) | Muitas vezes é série mensal e não API “pronta” |

---

## Recomendação de arquitetura do pipeline

## Camadas
1. **Ingestão (Bronze)**
   - Coletores por fonte (`collector_yfinance`, `collector_fred`, `collector_bcb`, `collector_files_publicos`).
   - Persistência bruta em `parquet/csv` particionado por `fonte` e `data_coleta`.

2. **Padronização (Silver)**
   - Normalizar colunas: `date`, `symbol`, `value`, `currency`, `frequency`, `source`.
   - Ajustar timezone e calendário (mercado vs macro).
   - Tratar faltantes e duplicatas.

3. **Curadoria (Gold)**
   - Série final por marcador com regra de prioridade de fontes.
   - Criação de derivados (ex.: inclinação `10Y-2Y`).
   - Features opcionais: retornos log, médias móveis, volatilidade rolling.

---

## Orquestração recomendada
- **Frequência diária** (madrugada BRT, ex.: 06:00).
- **Backfill inicial**: 2013-01-01 até hoje.
- **Atualização incremental**: do último ponto válido + janela de segurança de 7 dias (reprocessamento curto para corrigir revisões).
- **Ferramentas**:
  - Simples: `cron` + scripts Python.
  - Escalável: Prefect/Airflow.

---

## Regras de qualidade de dados (essenciais)
1. Checar monotonicidade de datas por série.
2. Limites plausíveis (ex.: juros não absurdos, preços não negativos quando não fizer sentido).
3. Percentual de missing por janela.
4. Detecção de “saltos” extremos para revisão manual.
5. Auditoria de fonte (hash do payload bruto + timestamp de coleta).

---

## Pontos de atenção por indicador
- **MSCI World / MSCI EM**: índice oficial geralmente é licenciado. Em pipeline gratuito, usar proxy via ETF.
- **DI Futuro**: pode demandar engenharia extra com dados B3 ou proxy de curva local.
- **OPEC Spare Capacity**: frequentemente vem de relatórios/tabelas, não API REST simples.
- **MOVE / OVX / Baltic / TED**: confirmar continuidade histórica desde 2013 antes do go-live.

---

## Estratégia prática de implementação (MVP em 2 fases)

## Fase 1 (rápida, alta cobertura)
- Fonte primária: `yfinance` + `FRED` + `BCB SGS`.
- Entrega de ~80-90% dos marcadores com histórico 2013+.
- Para itens difíceis (DI Futuro, OPEC spare capacity), usar coluna de status: `pending_source_validation`.

## Fase 2 (robustez e completude)
- Incorporar coletores específicos para OPEC/EIA/arquivos públicos.
- Refinar proxies (MSCI/DI) e documentação metodológica.
- Monitoramento automático de quebra de coletor.

---

## Exemplo de stack técnica sugerida
- **Linguagem**: Python
- **Bibliotecas**: `pandas`, `yfinance`, `fredapi`, `requests`, `pyarrow`
- **Armazenamento local**: `parquet` particionado
- **Catálogo**: arquivo YAML/JSON de séries (símbolo, fonte, frequência, transformação)
- **Observabilidade**: logs estruturados + alertas (falha de coleta, missing elevado)

---

## Conclusão
Para um pipeline gratuito e viável de 2013 até o presente, a combinação mais pragmática é:

1. **Yahoo Finance (`yfinance`)** para ativos de mercado.
2. **FRED** para macro/juros/spreads dos EUA.
3. **BCB SGS** para SELIC e séries brasileiras oficiais.
4. **Fontes públicas específicas (EIA/OPEC/EPU)** para marcadores setoriais e institucionais.

Essa abordagem equilibra cobertura, custo zero e simplicidade operacional, com fallback para reduzir risco de indisponibilidade.

