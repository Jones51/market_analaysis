from __future__ import annotations

import time
from datetime import datetime
from typing import Dict

import pandas as pd
import requests

from extractors import _empty_failures_frame, _empty_series_frame, _normalize_output
from series_catalog_commodities import NAPHTHA_BBL_PER_MT


def fetch_eia_series(
    catalog: Dict[str, str],
    start_date: str,
    end_date: str,
    eia_api_key: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetches monthly petroleum product price series from the EIA API v1."""
    all_rows = []
    failures = []

    start_ym = start_date[:7].replace("-", "")  # YYYYMM
    end_ym = end_date[:7].replace("-", "")

    for marker, series_id in catalog.items():
        params = {
            "api_key": eia_api_key,
            "series_id": series_id,
            "start": start_ym,
            "end": end_ym,
            "out": "json",
        }

        payload = None
        last_error = ""
        for attempt in range(3):
            try:
                resp = requests.get(
                    "https://api.eia.gov/series/",
                    params=params,
                    timeout=30,
                )
                resp.raise_for_status()
                payload = resp.json()
                break
            except Exception as exc:
                last_error = str(exc)
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))

        if payload is None:
            failures.append(
                {
                    "marker": marker,
                    "source": "eia",
                    "status": "fetch_error",
                    "detail": f"series_id={series_id}; error={last_error}",
                }
            )
            continue

        series_list = payload.get("series") or []
        raw_data = series_list[0].get("data", []) if series_list else []
        if not raw_data:
            failures.append(
                {
                    "marker": marker,
                    "source": "eia",
                    "status": "no_data",
                    "detail": f"series_id={series_id}",
                }
            )
            continue

        frame = pd.DataFrame(raw_data, columns=["date", "value"])
        frame["date"] = pd.to_datetime(frame["date"], format="%Y%m", errors="coerce")
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame = frame.dropna()

        if frame.empty:
            failures.append(
                {
                    "marker": marker,
                    "source": "eia",
                    "status": "no_numeric_values",
                    "detail": f"series_id={series_id}",
                }
            )
            continue

        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        frame = frame[(frame["date"] >= start_dt) & (frame["date"] <= end_dt)]

        if frame.empty:
            failures.append(
                {
                    "marker": marker,
                    "source": "eia",
                    "status": "no_data_in_range",
                    "detail": f"series_id={series_id}",
                }
            )
            continue

        all_rows.append(_normalize_output(frame, marker=marker, source="eia"))

    failures_df = pd.DataFrame(failures) if failures else _empty_failures_frame()
    if not all_rows:
        return _empty_series_frame(), failures_df
    return pd.concat(all_rows, ignore_index=True), failures_df


def build_derived_naphtha_crack_spread(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Naphtha Crack Spread ($/bbl) = Naphtha ($/mt ÷ 8.9) - Brent monthly avg ($/bbl).

    Requer marcadores NAPHTHA_US_GULF_COAST (EIA, mensal) e BRENT (yfinance, diário)
    no dataset combinado. Resultado tem frequência mensal.
    """
    empty = pd.DataFrame(columns=["date", "marker", "value", "source"])

    naphtha = dataset[dataset["marker"] == "NAPHTHA_US_GULF_COAST"].copy()
    brent = dataset[dataset["marker"] == "BRENT"].copy()

    if naphtha.empty or brent.empty:
        return empty

    naphtha["date"] = pd.to_datetime(naphtha["date"])
    brent["date"] = pd.to_datetime(brent["date"])

    brent_monthly = (
        brent.set_index("date")["value"]
        .resample("MS")
        .mean()
        .reset_index()
        .rename(columns={"value": "brent_bbl"})
    )

    naphtha["naphtha_bbl"] = naphtha["value"] / NAPHTHA_BBL_PER_MT
    naphtha_m = naphtha[["date", "naphtha_bbl"]].copy()
    naphtha_m["date"] = naphtha_m["date"].dt.to_period("M").dt.to_timestamp()

    merged = pd.merge(naphtha_m, brent_monthly, on="date", how="inner")
    if merged.empty:
        return empty

    merged["value"] = merged["naphtha_bbl"] - merged["brent_bbl"]
    merged["marker"] = "NAPHTHA_CRACK_SPREAD_DERIVED"
    merged["source"] = "derived"
    merged["date"] = pd.to_datetime(merged["date"]).dt.date
    return merged[["date", "marker", "value", "source"]].dropna()
