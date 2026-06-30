from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from extractors import fetch_yfinance_series
from series_catalog_commodities import (
    YFINANCE_COMMODITIES_SERIES,
    YFINANCE_COMMODITIES_START_DATES,
)


SERIES_COLUMNS = ["date", "marker", "value", "source"]
FAILURE_COLUMNS = ["marker", "source", "status", "detail"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extracao de commodities via yfinance."
    )
    parser.add_argument("--start-date", default="2013-01-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--output-dir", default="data")
    return parser.parse_args()


def ensure_dirs(base_dir: Path) -> None:
    (base_dir / "raw").mkdir(parents=True, exist_ok=True)
    (base_dir / "curated").mkdir(parents=True, exist_ok=True)


def save_series(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        pd.DataFrame(columns=SERIES_COLUMNS).to_csv(path, index=False)
        return

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)


def build_curated(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=SERIES_COLUMNS)

    curated = df.copy()
    curated["date"] = pd.to_datetime(curated["date"])
    curated = curated.sort_values(["marker", "date"]).reset_index(drop=True)
    return curated


def apply_marker_start_date(marker: str, requested_start_date: str) -> str:
    marker_start_date = YFINANCE_COMMODITIES_START_DATES.get(marker)
    if marker_start_date is None:
        return requested_start_date

    requested_start = datetime.fromisoformat(requested_start_date).date()
    marker_start = datetime.fromisoformat(marker_start_date).date()
    return max(requested_start, marker_start).isoformat()


def fetch_commodity_yfinance_series(
    start_date: str, end_date: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows = []
    all_failures = []
    end_dt = datetime.fromisoformat(end_date).date()

    for marker, ticker in YFINANCE_COMMODITIES_SERIES.items():
        effective_start_date = apply_marker_start_date(marker, start_date)
        effective_start_dt = datetime.fromisoformat(effective_start_date).date()

        if effective_start_dt > end_dt:
            available_from = YFINANCE_COMMODITIES_START_DATES.get(
                marker, effective_start_date
            )
            all_failures.append(
                pd.DataFrame(
                    [
                        {
                            "marker": marker,
                            "source": "yfinance",
                            "status": "no_data_in_requested_range",
                            "detail": (
                                f"ticker={ticker}; "
                                f"available_from={available_from}"
                            ),
                        }
                    ]
                )
            )
            continue

        data, failures = fetch_yfinance_series(
            catalog={marker: ticker},
            start_date=effective_start_date,
            end_date=end_date,
        )

        if not data.empty:
            all_rows.append(data)
        if not failures.empty:
            all_failures.append(failures)

    data_df = (
        pd.concat(all_rows, ignore_index=True)
        if all_rows
        else pd.DataFrame(columns=SERIES_COLUMNS)
    )
    failures_df = (
        pd.concat(all_failures, ignore_index=True)
        if all_failures
        else pd.DataFrame(columns=FAILURE_COLUMNS)
    )
    return data_df, failures_df


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    ensure_dirs(output_dir)

    yf_df, yf_failures = fetch_commodity_yfinance_series(
        start_date=args.start_date,
        end_date=args.end_date,
    )

    save_series(yf_df, output_dir / "raw" / "yfinance_commodities.csv")

    curated = build_curated(yf_df)
    save_series(curated, output_dir / "curated" / "commodity_indicators.csv")

    yf_failures.to_csv(output_dir / "curated" / "failed_commodities.csv", index=False)

    n_markers = curated["marker"].nunique() if not curated.empty else 0
    n_rows = len(curated)
    print(f"[OK] {n_rows} linhas extraidas para {n_markers} marcadores.")
    if not yf_failures.empty:
        print(f"[WARN] {len(yf_failures)} falha(s) - ver failed_commodities.csv")


if __name__ == "__main__":
    main()
