from __future__ import annotations

# ── Já cobertos no pipeline v1 (run_extraction.py) ───────────────────────────
# Natural Gas Henry Hub  → GAS_NATURAL_HENRY_HUB via NG=F
# Crude Oil Brent        → BRENT via BZ=F
ALREADY_IN_PIPELINE_V1 = ["GAS_NATURAL_HENRY_HUB", "BRENT"]

# ── Grupo B: diários via Yahoo Finance ───────────────────────────────────────
# ZN=F → COMEX High Grade Zinc continuous futures
#         Alta correlação com LME Zinc 3-month; basis esporádico por diferença de bolsa.
YFINANCE_COMMODITIES_SERIES = {
    "ZINC_COMEX_DAILY_PROXY": "ZN=F",
}

# ── Grupo C: mensais via FRED (IMF Primary Commodity Prices espelhadas) ──────
# Séries verificadas no FRED com histórico desde jan/1992, frequência mensal, USD.
FRED_COMMODITIES_SERIES = {
    "LME_NICKEL_3M_MONTHLY":    "PNICKUSDM",    # $/mt  — LME Nickel cash (IMF)
    "IRON_ORE_62FE_MONTHLY":    "PIORECRUSDM",  # $/dmt — Iron Ore 62% Fe, China import (IMF)
    "COKING_COAL_AUS_MONTHLY":  "PCOALAUUSDM",  # $/mt  — Australian coking coal; proxy para DCE
    "ZINC_LME_MONTHLY":         "PZINCUSDM",    # $/mt  — LME Zinc cash (IMF); backup mensal
}

# ── Grupo D: EIA API — componente para Naphtha Crack Spread ──────────────────
# Registre chave gratuita em: https://www.eia.gov/opendata/
# Valide o series_id exato em: https://api.eia.gov/v2/petroleum/pri/spt/data/
# Crack Spread = Naphtha ($/bbl) – Brent ($/bbl); Brent já no pipeline v1.
EIA_COMMODITIES_SERIES = {
    "NAPHTHA_US_GULF_COAST": "PET.EER_EPD2DXK0_PFO_Y05LO_DPG.M",
}

# Fator de conversão naphtha: $/metric ton → $/barrel (nafta leve ≈ 8,9 bbl/mt)
NAPHTHA_BBL_PER_MT: float = 8.9

# ── Grupo E: sem API programática gratuita disponível ────────────────────────
PENDING_COMMODITIES_V2 = [
    "CHINA_FLUORSPAR_PRICE",       # USGS apenas anual; SMM/Asian Metal requerem assinatura
    "ETHYLENE_FUTURES_NYMEX",      # CME Group subscription; sem alternativa gratuita
    "SHANGHAI_REBAR_FUTURES",      # SHFE SMDP2.0 requer licença vendor; sem API gratuita
    "SHANGHAI_STAINLESS_STEEL",    # SHFE idem; listado desde set/2019
    "MOLYBDENUM_OXIDE_CHINA",      # Fastmarkets/SMM requerem assinatura
    "MANGANESE_ORE_CHINA_PORT",    # CRU/Fastmarkets; índices de porto sem API gratuita
]
