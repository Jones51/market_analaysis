# Pipeline de Dados (2013-atual): análise de APIs gratuitas para marcadores de commodities industriais

## Objetivo
Avaliar a viabilidade de coleta automatizada e gratuita dos seguintes marcadores de commodities industriais e energéticas, complementando o pipeline macro já existente:

1. LME Nickel 3-Month
2. Iron Ore Futures (SGX)
3. Naphtha Crack Spread
4. Natural Gas Futures (Henry Hub)
5. China Fluorspar Price
6. Ethylene Futures (NYMEX)
7. Shanghai Rebar Futures (SHFE)
8. Shanghai Stainless Steel Futures (SHFE)
9. Molybdenum Oxide (China)
10. Manganese Ore (China Port)
11. Crude Oil Brent
12. Coking Coal Futures (Dalian DCE)
13. Zinc Futures (LME)

---

## Pré-condição: marcadores já cobertos no pipeline v1

Os itens 4 (Natural Gas Henry Hub → `NG=F`) e 11 (Crude Oil Brent → `BZ=F`) já são extraídos por `run_extraction.py`. Esta análise foca nos 11 restantes.

---

## Critérios de avaliação (mesmos da análise macro)

1. Acesso histórico >= 2013 (diário ou mensal, conforme a série).
2. Estabilidade razoável para uso automatizado.
3. Documentação clara e sem custo para baixa/média frequência.
4. Formato padronizado (JSON/CSV).

---

## Fontes candidatas

### 1) FRED / ALFRED — séries IMF Primary Commodity Prices espelhadas

**Pontos fortes**
- Confirmar disponibilidade: séries PNICKUSDM, PZINCUSDM, PIORECRUSDM, PCOALAUUSDM, todas verificadas como ativas no FRED com histórico desde jan/1992.
- Dados mensais em USD, sourced from IMF. Cobertura uniforme de 1992 ao presente.
- Usa a mesma infraestrutura (`fredapi`) já presente no pipeline v1.

**Limitações**
- Frequência mensal apenas (não há equivalente diário para metais LME no FRED).
- Carvão australiano (`PCOALAUUSDM`) é proxy para coking coal da DCE; não é o contrato Dalian diretamente.
- Iron ore é spot FOB de minério 62% Fe (preço de referência), não o futuro exato do SGX.

**Uso ideal**
- Fonte principal para Nickel, Zinc, Iron Ore, Coking Coal em análises macro mensais.

---

### 2) Yahoo Finance (`yfinance`) — futuros diários

**Pontos fortes**
- `ZN=F` (COMEX High Grade Zinc) disponível com histórico diário. Altamente correlacionado com LME Zinc 3-month (mesma commodity, bolsa diferente).
- Infraestrutura já presente no pipeline v1.

**Limitações**
- `NI=F` (Nickel) não tem cobertura confiável no Yahoo Finance para LME.
- SHFE (Rebar, Stainless Steel) e DCE (Coking Coal) não estão disponíveis via yfinance.
- Não há ticker gratuito confiável para SGX Iron Ore futures diários.

**Uso ideal**
- Proxy diário para Zinc (`ZN=F`). Não usar para Nickel ou contratos asiáticos.

---

### 3) EIA API (api.eia.gov) — petróleo e derivados

**Pontos fortes**
- API pública gratuita com registro de chave gratuito em eia.gov/opendata.
- Cobre preços de produtos petroquímicos como nafta (naphtha).
- Dados semanais/mensais com histórico robusto.

**Limitações**
- Naphtha Crack Spread não é uma série direta; precisa ser calculado: `Spread = Naphtha ($/bbl) - Brent ($/bbl)`.
- O ID exato da série de nafta deve ser validado via EIA API explorer (`api.eia.gov/v2/`), pois os códigos de produto mudam entre versões da API.
- Brent já está no pipeline — só o componente de nafta precisa ser adicionado.

**Uso ideal**
- Ingestão do preço de nafta para cálculo do crack spread como métrica derivada.

---

### 4) Bolsas asiáticas (SHFE, DCE) — sem API gratuita

**SHFE (Shanghai Futures Exchange):** Publica especificação de API (SMDP2.0) mas exige licença de vendor pago. Dados em tempo real/histórico disponíveis somente via LSEG, Bloomberg, e semelhantes.

**DCE (Dalian Commodity Exchange):** Mesma situação. Cotas atrasadas disponíveis em Barchart.com, TradingView, Investing.com para uso manual, mas sem API programática gratuita.

**Uso ideal:** Nenhum para pipeline automatizado. Marcar como pending para futura integração com provedor comercial.

---

### 5) Preços de especialidade (Fluorspar, Molybdênio, Manganês)

Estas commodities têm preços publicados por provedores industriais (Shanghai Metals Market / SMM, Asian Metal, Fastmarkets, CRU). O SMM publica preços na web gratuitamente, mas não oferece API programática sem assinatura. O USGS publica dados anuais em relatórios PDF.

**Uso ideal:** Sem pipeline automatizado viável. Marcar como pending.

---

## Mapeamento por marcador

| Marcador | Fonte principal | Código/Ticker | Frequência | Tipo |
|---|---|---|---|---|
| LME Nickel 3-Month | FRED | `PNICKUSDM` | Mensal | Direto (IMF/LME) |
| Iron Ore Futures (SGX) | FRED | `PIORECRUSDM` | Mensal | Proxy (spot 62% Fe) |
| Naphtha Crack Spread | EIA + Derivado | EIA naphtha + `BRENT` | Mensal | Calculado |
| Natural Gas (Henry Hub) | **Já no pipeline v1** | `NG=F` | Diária | — |
| China Fluorspar Price | ❌ Sem API gratuita | — | — | Pending |
| Ethylene Futures (NYMEX) | ❌ Sem API gratuita | — | — | Pending |
| Shanghai Rebar Futures | ❌ Sem API gratuita | — | — | Pending |
| Shanghai Stainless Steel | ❌ Sem API gratuita | — | — | Pending |
| Molybdenum Oxide (China) | ❌ Sem API gratuita | — | — | Pending |
| Manganese Ore (China Port) | ❌ Sem API gratuita | — | — | Pending |
| Crude Oil Brent | **Já no pipeline v1** | `BZ=F` | Diária | — |
| Coking Coal Futures (Dalian) | FRED | `PCOALAUUSDM` | Mensal | Proxy (AUS carvão) |
| Zinc Futures (LME) | FRED + Yahoo Finance | `PZINCUSDM` / `ZN=F` | Mensal + Diária | FRED direto; Yahoo proxy |

---

## Arquitetura do script (`run_extraction_commodities.py`)

Segue o mesmo padrão do pipeline v1:

### Camadas

1. **Ingestão (Bronze)**
   - `yfinance_commodities.csv` — Zinc diário via `ZN=F`
   - `fred_commodities.csv` — Nickel, Iron Ore, Coking Coal, Zinc mensais
   - `eia_commodities.csv` — Nafta mensal (se chave EIA disponível)

2. **Curadoria (Gold)**
   - `commodity_indicators.csv` — combinação de todas as fontes
   - `naphtha_crack_spread` derivado inline
   - `pending_commodities_v2.csv` — lista de marcadores sem fonte gratuita
   - `failed_commodities.csv` — falhas de extração

### Requisitos de configuração

| Variável | Obrigatório | Fonte |
|---|---|---|
| `FRED_API_KEY` | Sim | fred.stlouisfed.org/docs/api |
| `EIA_API_KEY` | Opcional | eia.gov/opendata (gratuito com registro) |

---

## Pontos de atenção

- **Coking Coal**: `PCOALAUUSDM` é carvão australiano (HCC premium); serve como proxy de mercado para DCE, mas diverge em spreads de arbitragem China-global.
- **Iron Ore**: `PIORECRUSDM` é preço de referência spot; futuros SGX podem apresentar basis diferente.
- **Naphtha Crack Spread**: A conversão de $/mt para $/bbl usa fator 8,9 bbl/mt (nafta leve); validar contra unidade real da série EIA antes de usar.
- **Zinc diário**: `ZN=F` (COMEX) diverge esporadicamente de LME 3-month por basis e diferenças de contrato; adequado para análise de tendência, não para precificação exata LME.
- **IDs EIA**: Validar o series_id de nafta em `api.eia.gov/v2/petroleum/pri/spt/data/` antes de ativar em produção.

---

## Conclusão

Para pipeline gratuito e viável a partir de 2013:

- **FRED** cobre 4 dos 11 marcadores novos com histórico mensal de alta qualidade (IMF PCP).
- **Yahoo Finance** (`ZN=F`) adiciona resolução diária para Zinc.
- **EIA API** (chave gratuita) habilita o cálculo do Naphtha Crack Spread.
- **6 marcadores** (Fluorspar, Ethylene, Rebar, Stainless Steel, Molybdenum, Manganese) não possuem API gratuita programática adequada e ficam como `pending_source_validation` para futura integração comercial.
