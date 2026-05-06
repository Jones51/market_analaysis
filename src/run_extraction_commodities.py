from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from extractors import fetch_fred_series, fetch_yfinance_series
from extractors_commodities import (
    build_derived_naphtha_crack_spread,
    fetch_eia_series,
)
from series_catalog_commodities import (
    EIA_COMMODITIES_SERIES,
    FRED_COMMODITIES_SERIES,
    PENDING_COMMODITIES_V2,
    YFINANCE_COMMODITIES_SERIES,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline de extração de commodities industriais (Grupo 2): "
            "metais LME, minério de ferro, carvão, zinco, naphtha crack spread."
        )
    )
    parser.add_argument("--start-date", default="2013-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--output-dir", default="data")
    parser.add_argument(
        "--fred-api-key",
        default=os.getenv("FRED_API_KEY", ""),
        help="Obrigatório. Defina FRED_API_KEY ou passe --fred-api-key.",
    )
    parser.add_argument(
        "--eia-api-key",
        default=os.getenv("EIA_API_KEY", ""),
        help=(
            "Opcional. Habilita extração de nafta e cálculo do Naphtha Crack Spread. "
            "Chave gratuita em https://www.eia.gov/opendata/"
        ),
    )
    return parser.parse_args()


def ensure_dirs(base_dir: Path) -> None:
    (base_dir / "raw").mkdir(parents=True, exist_ok=True)
    (base_dir / "curated").mkdir(parents=True, exist_ok=True)


def save_raw(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        pd.DataFrame(columns=["date", "marker", "value", "source"]).to_csv(path, index=False)
        return
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)


def main() -> None:
    load_dotenv()
    args = parse_args()
    output_dir = Path(args.output_dir)
    ensure_dirs(output_dir)

    if not args.fred_api_key:
        raise ValueError(
            "FRED API key ausente. Defina FRED_API_KEY ou passe --fred-api-key."
        )

    # --- Yahoo Finance (diário) -----------------------------------------------
    yf_df, yf_failures = fetch_yfinance_series(
        catalog=YFINANCE_COMMODITIES_SERIES,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    save_raw(yf_df, output_dir / "raw" / "yfinance_commodities.csv")

    # --- FRED mensal (IMF Primary Commodity Prices) ---------------------------
    fred_df, fred_failures = fetch_fred_series(
        catalog=FRED_COMMODITIES_SERIES,
        start_date=args.start_date,
        end_date=args.end_date,
        fred_api_key=args.fred_api_key,
    )
    save_raw(fred_df, output_dir / "raw" / "fred_commodities.csv")

    # --- EIA (nafta, opcional) ------------------------------------------------
    eia_df = pd.DataFrame(columns=["date", "marker", "value", "source"])
    eia_failures = pd.DataFrame(columns=["marker", "source", "status", "detail"])
    if args.eia_api_key:
        eia_df, eia_failures = fetch_eia_series(
            catalog=EIA_COMMODITIES_SERIES,
            start_date=args.start_date,
            end_date=args.end_date,
            eia_api_key=args.eia_api_key,
        )
        save_raw(eia_df, output_dir / "raw" / "eia_commodities.csv")
    else:
        print("[INFO] EIA_API_KEY não fornecida — Naphtha Crack Spread será omitido.")

    # --- Derivado: Naphtha Crack Spread ---------------------------------------
    # Carrega Brent do pipeline v1 se disponível para calcular o spread.
    naphtha_spread = pd.DataFrame(columns=["date", "marker", "value", "source"])
    brent_path = output_dir / "raw" / "yfinance.csv"
    if not eia_df.empty and brent_path.exists():
        existing_yf = pd.read_csv(brent_path)
        naphtha_spread = build_derived_naphtha_crack_spread(
            pd.concat([existing_yf, eia_df], ignore_index=True)
        )

    # --- Consolidação e curadoria ---------------------------------------------
    combined = pd.concat([yf_df, fred_df, eia_df, naphtha_spread], ignore_index=True)
    if not combined.empty:
        combined["date"] = pd.to_datetime(combined["date"])
        combined = combined.sort_values(["marker", "date"]).reset_index(drop=True)
        combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")

    combined.to_csv(output_dir / "curated" / "commodity_indicators.csv", index=False)

    # --- Relatório de pendências ----------------------------------------------
    pd.DataFrame(
        {
            "marker": PENDING_COMMODITIES_V2,
            "status": "no_free_api_available",
        }
    ).to_csv(output_dir / "curated" / "pending_commodities_v2.csv", index=False)

    # --- Relatório de falhas --------------------------------------------------
    all_failures = pd.concat(
        [yf_failures, fred_failures, eia_failures], ignore_index=True
    )
    all_failures.to_csv(output_dir / "curated" / "failed_commodities.csv", index=False)

    n_markers = combined["marker"].nunique() if not combined.empty else 0
    n_rows = len(combined)
    print(f"[OK] {n_rows} linhas extraídas para {n_markers} marcadores.")
    print(
        f"[INFO] {len(PENDING_COMMODITIES_V2)} marcadores sem API gratuita: "
        + ", ".join(PENDING_COMMODITIES_V2)
    )
    if not all_failures.empty:
        print(f"[WARN] {len(all_failures)} falha(s) — ver failed_commodities.csv")


if __name__ == "__main__":
    main()
