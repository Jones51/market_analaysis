from __future__ import annotations

# Market assets (Yahoo Finance tickers)
YFINANCE_SERIES = {
    "BRENT": "BZ=F",
    "WTI": "CL=F",
    "GAS_NATURAL_HENRY_HUB": "NG=F",
    "VIX": "^VIX",
    "OVX": "^OVX",
    "USD_BRL": "BRL=X",
    "DXY": "DX-Y.NYB",
    "SP500": "^GSPC",
    "MSCI_WORLD_PROXY": "URTH",
    "MSCI_EM_PROXY": "EEM",
    "IBOVESPA": "^BVSP",
    "BITCOIN": "BTC-USD",
    "ETHEREUM": "ETH-USD",
    "GOLD": "GC=F",
    "COPPER": "HG=F",
}

# Macro rates and spreads (FRED series ids)
FRED_SERIES = {
    "US_TREASURY_2Y": "DGS2",
    "US_TREASURY_10Y": "DGS10",
    "CURVA_10Y_2Y_FRED": "T10Y2Y",  # explicit spread from source
    "TED_SPREAD": "TEDRATE",
    "EPU_USA": "USEPUINDXD",
}

# Brazil Central Bank SGS series codes
BCB_SGS_SERIES = {
    "SELIC": 432,
}

# These require custom connectors or licensing checks; kept for roadmap.
PENDING_SERIES = [
    "MOVE",
    "DI_FUTURO",
    "BALTIC_DRY_INDEX",
    "OPEC_SPARE_CAPACITY",
]
