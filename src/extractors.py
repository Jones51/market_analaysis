from __future__ import annotations

from datetime import datetime, timedelta
from io import StringIO
import time
from typing import Dict

import pandas as pd
import requests
import yfinance as yf
from fredapi import Fred


def _empty_series_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["date", "marker", "value", "source"])


def _empty_failures_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["marker", "source", "status", "detail"])


def _bcb_date_chunks(start_dt: datetime, end_dt: datetime) -> list[tuple[datetime, datetime]]:
    chunks: list[tuple[datetime, datetime]] = []
    current_start = start_dt
    max_days = 3650  # BCB accepts at most ~10 years for daily series
    while current_start <= end_dt:
        current_end = min(current_start + timedelta(days=max_days - 1), end_dt)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return chunks


def _normalize_output(
    frame: pd.DataFrame, marker: str, source: str, value_col: str = "value"
) -> pd.DataFrame:
    base = frame.copy()
    base["date"] = pd.to_datetime(base["date"]).dt.date
    base["marker"] = marker
    base["source"] = source
    return base[["date", "marker", value_col, "source"]]


def fetch_yfinance_series(
    catalog: Dict[str, str], start_date: str, end_date: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows = []
    failures = []
    for marker, ticker in catalog.items():
        try:
            data = yf.download(
                tickers=ticker,
                start=start_date,
                end=end_date,
                interval="1d",
                progress=False,
                auto_adjust=False,
            )
        except Exception as exc:
            failures.append(
                {
                    "marker": marker,
                    "source": "yfinance",
                    "status": "fetch_error",
                    "detail": str(exc),
                }
            )
            continue

        if data.empty:
            failures.append(
                {
                    "marker": marker,
                    "source": "yfinance",
                    "status": "no_data",
                    "detail": f"ticker={ticker}",
                }
            )
            continue

        if isinstance(data.columns, pd.MultiIndex):
            if "Close" not in data.columns.get_level_values(0):
                failures.append(
                    {
                        "marker": marker,
                        "source": "yfinance",
                        "status": "missing_close",
                        "detail": f"ticker={ticker}",
                    }
                )
                continue
            close_values = data.xs("Close", axis=1, level=0).iloc[:, 0]
        else:
            if "Close" not in data.columns:
                failures.append(
                    {
                        "marker": marker,
                        "source": "yfinance",
                        "status": "missing_close",
                        "detail": f"ticker={ticker}",
                    }
                )
                continue
            close_values = data["Close"]

        close = close_values.rename("value").reset_index().rename(columns={"Date": "date"})
        close["value"] = pd.to_numeric(close["value"], errors="coerce")
        close = close.dropna(subset=["value"])
        if close.empty:
            failures.append(
                {
                    "marker": marker,
                    "source": "yfinance",
                    "status": "no_numeric_close",
                    "detail": f"ticker={ticker}",
                }
            )
            continue
        all_rows.append(_normalize_output(close, marker=marker, source="yfinance"))

    failures_df = pd.DataFrame(failures) if failures else _empty_failures_frame()
    if not all_rows:
        return _empty_series_frame(), failures_df
    return pd.concat(all_rows, ignore_index=True), failures_df


def fetch_fred_series(
    catalog: Dict[str, str], start_date: str, end_date: str, fred_api_key: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fred = Fred(api_key=fred_api_key)
    all_rows = []
    failures = []

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    for marker, series_id in catalog.items():
        series = None
        last_error = ""
        for attempt in range(3):
            try:
                series = fred.get_series(
                    series_id, observation_start=start, observation_end=end
                )
                break
            except Exception as exc:
                last_error = str(exc)
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    series = None

        if series is None or series.empty:
            failures.append(
                {
                    "marker": marker,
                    "source": "fred",
                    "status": "no_data_or_fetch_error",
                    "detail": f"series_id={series_id}; error={last_error}",
                }
            )
            continue

        frame = series.reset_index()
        frame.columns = ["date", "value"]
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame = frame.dropna(subset=["value"])
        if frame.empty:
            failures.append(
                {
                    "marker": marker,
                    "source": "fred",
                    "status": "no_numeric_values",
                    "detail": f"series_id={series_id}",
                }
            )
            continue
        all_rows.append(_normalize_output(frame, marker=marker, source="fred"))

    failures_df = pd.DataFrame(failures) if failures else _empty_failures_frame()
    if not all_rows:
        return _empty_series_frame(), failures_df
    return pd.concat(all_rows, ignore_index=True), failures_df


def fetch_bcb_sgs_series(
    catalog: Dict[str, int], start_date: str, end_date: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows = []
    failures = []
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    for marker, code in catalog.items():
        base_url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0",
        }

        frame = None
        last_error = ""

        chunk_frames = []
        for chunk_start, chunk_end in _bcb_date_chunks(start_dt, end_dt):
            chunk_ini = chunk_start.strftime("%d/%m/%Y")
            chunk_end_s = chunk_end.strftime("%d/%m/%Y")

            request_variants = [
                {
                    "url": base_url,
                    "params": {
                        "formato": "json",
                        "dataInicial": chunk_ini,
                        "dataFinal": chunk_end_s,
                    },
                    "parser": "json",
                },
                {
                    "url": (
                        f"{base_url}?formato=json&dataInicial={chunk_ini}&dataFinal={chunk_end_s}"
                    ),
                    "params": None,
                    "parser": "json",
                },
                {
                    "url": (
                        f"{base_url}?formato=csv&dataInicial={chunk_ini}&dataFinal={chunk_end_s}"
                    ),
                    "params": None,
                    "parser": "csv",
                },
            ]

            chunk_frame = None
            for variant in request_variants:
                success = False
                for attempt in range(3):
                    try:
                        response = requests.get(
                            variant["url"],
                            params=variant["params"],
                            headers=headers,
                            timeout=60,
                        )
                        response.raise_for_status()

                        if variant["parser"] == "json":
                            payload = response.json()
                            if payload:
                                chunk_frame = pd.DataFrame(payload).rename(
                                    columns={"data": "date", "valor": "value"}
                                )
                        else:
                            chunk_frame = pd.read_csv(StringIO(response.text), sep=";").rename(
                                columns={"data": "date", "valor": "value"}
                            )

                        if chunk_frame is None or chunk_frame.empty:
                            last_error = "empty_response"
                            break

                        chunk_frame["date"] = pd.to_datetime(
                            chunk_frame["date"], format="%d/%m/%Y", errors="coerce"
                        )
                        chunk_frame["value"] = (
                            chunk_frame["value"]
                            .astype(str)
                            .str.replace(",", ".", regex=False)
                            .astype(float)
                        )
                        chunk_frame = chunk_frame.dropna(subset=["date", "value"])
                        if not chunk_frame.empty:
                            success = True
                            break
                        last_error = "empty_after_parse"
                        break
                    except Exception as exc:
                        last_error = str(exc)
                        if attempt < 2:
                            time.sleep(1.5 * (attempt + 1))
                if success:
                    break

            if chunk_frame is None or chunk_frame.empty:
                chunk_frames = []
                break

            chunk_frames.append(chunk_frame)

        if not chunk_frames:
            failures.append(
                {
                    "marker": marker,
                    "source": "bcb_sgs",
                    "status": "no_data_or_fetch_error",
                    "detail": f"series_code={code}; error={last_error}",
                }
            )
            continue

        frame = pd.concat(chunk_frames, ignore_index=True)
        frame = frame[(frame["date"] >= start_dt) & (frame["date"] <= end_dt)]
        frame = frame.drop_duplicates(subset=["date"], keep="last")
        if frame.empty:
            failures.append(
                {
                    "marker": marker,
                    "source": "bcb_sgs",
                    "status": "empty_after_merge",
                    "detail": f"series_code={code}",
                }
            )
            continue

        all_rows.append(_normalize_output(frame, marker=marker, source="bcb_sgs"))

    failures_df = pd.DataFrame(failures) if failures else _empty_failures_frame()
    if not all_rows:
        return _empty_series_frame(), failures_df
    return pd.concat(all_rows, ignore_index=True), failures_df


def build_derived_curva_10y_2y(dataset: pd.DataFrame) -> pd.DataFrame:
    if dataset.empty:
        return pd.DataFrame(columns=["date", "marker", "value", "source"])

    rates = dataset[dataset["marker"].isin(["US_TREASURY_2Y", "US_TREASURY_10Y"])].copy()
    if rates.empty:
        return pd.DataFrame(columns=["date", "marker", "value", "source"])

    pivot = rates.pivot_table(index="date", columns="marker", values="value", aggfunc="last")
    if "US_TREASURY_2Y" not in pivot.columns or "US_TREASURY_10Y" not in pivot.columns:
        return pd.DataFrame(columns=["date", "marker", "value", "source"])

    spread = (pivot["US_TREASURY_10Y"] - pivot["US_TREASURY_2Y"]).reset_index()
    spread.columns = ["date", "value"]
    spread["marker"] = "CURVA_10Y_2Y_DERIVED"
    spread["source"] = "derived"
    return spread[["date", "marker", "value", "source"]]
