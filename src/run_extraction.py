from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from extractors import (
    build_derived_curva_10y_2y,
    fetch_bcb_sgs_series,
    fetch_fred_series,
    fetch_yfinance_series,
)
from series_catalog import BCB_SGS_SERIES, FRED_SERIES, PENDING_SERIES, YFINANCE_SERIES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extracao direta de series de mercado/macro (2013-atual)."
    )
    parser.add_argument("--start-date", default="2013-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--output-dir", default="data")
    parser.add_argument(
        "--fred-api-key",
        default=os.getenv("FRED_API_KEY", ""),
        help="Pode ser passado por argumento ou variavel de ambiente FRED_API_KEY.",
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

    yf_df, yf_failures = fetch_yfinance_series(
        catalog=YFINANCE_SERIES,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    save_raw(yf_df, output_dir / "raw" / "yfinance.csv")

    if not args.fred_api_key:
        raise ValueError(
            "FRED API key ausente. Defina FRED_API_KEY ou passe --fred-api-key."
        )
    fred_df, fred_failures = fetch_fred_series(
        catalog=FRED_SERIES,
        start_date=args.start_date,
        end_date=args.end_date,
        fred_api_key=args.fred_api_key,
    )
    save_raw(fred_df, output_dir / "raw" / "fred.csv")

    bcb_df, bcb_failures = fetch_bcb_sgs_series(
        catalog=BCB_SGS_SERIES,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    save_raw(bcb_df, output_dir / "raw" / "bcb_sgs.csv")

    combined = pd.concat([yf_df, fred_df, bcb_df], ignore_index=True)
    derived_spread = build_derived_curva_10y_2y(combined)
    curated = pd.concat([combined, derived_spread], ignore_index=True)
    curated["date"] = pd.to_datetime(curated["date"])
    curated = curated.sort_values(["marker", "date"]).reset_index(drop=True)
    curated["date"] = curated["date"].dt.strftime("%Y-%m-%d")
    curated.to_csv(output_dir / "curated" / "market_indicators.csv", index=False)

    pending_df = pd.DataFrame(
        {
            "marker": PENDING_SERIES,
            "status": "pending_source_validation",
        }
    )
    pending_df.to_csv(output_dir / "curated" / "pending_series.csv", index=False)

    failed_df = pd.concat([yf_failures, fred_failures, bcb_failures], ignore_index=True)
    failed_df.to_csv(output_dir / "curated" / "failed_series.csv", index=False)


if __name__ == "__main__":
    main()
