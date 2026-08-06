"""Fetch harmonized TCGA survival endpoints from the public cBioPortal REST API.

OpenTME ships the spatial readouts but not the clinical outcomes. Overall survival is linked back to
each slide through the TCGA barcode (the first 12 characters of ``TCGA_FILE_NAME`` equal the
``TCGA_CASE_ID``, which in turn equals the cBioPortal ``patientId``). This module downloads the
PATIENT-level clinical table for one or more studies, with retries and on-disk caching so a notebook
can be re-run offline once the data has been fetched.
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests

from .config import CBIOPORTAL_API_URL, NEOADJUVANT_COLUMN

PATIENT_ID_COLUMN = "patientId"
OS_MONTHS_COLUMN = "OS_MONTHS"
OS_STATUS_COLUMN = "OS_STATUS"

_SURVIVAL_COLUMNS = [OS_MONTHS_COLUMN, OS_STATUS_COLUMN, NEOADJUVANT_COLUMN]
_CLINICAL_DATA_PARAMS = {"clinicalDataType": "PATIENT", "projection": "SUMMARY"}
_REQUEST_TIMEOUT_SECONDS = 180


def _request_with_retries(url: str, params: dict, *, tries: int = 6, backoff_seconds: float = 3.0) -> requests.Response:
    """Perform a GET request, retrying transient failures with linear backoff.

    Args:
        url: The endpoint to request.
        params: Query parameters for the request.
        tries: Maximum number of attempts before giving up.
        backoff_seconds: Base wait; attempt ``i`` sleeps ``backoff_seconds * (i + 1)`` on failure.

    Returns:
        The successful HTTP response.

    Raises:
        requests.RequestException: If all attempts fail.
        RuntimeError: Defensive guard; unreachable while ``tries >= 1``.
    """
    for attempt in range(tries):
        try:
            response = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == tries - 1:
                raise
            time.sleep(backoff_seconds * (attempt + 1))
    msg = "Unreachable: retry loop exited without returning or raising."  # pragma: no cover
    raise RuntimeError(msg)  # pragma: no cover


def _load_study_clinical_data(study: str, cache_dir: Path | None) -> list[dict]:
    """Return the raw PATIENT clinical records for a single study, using the cache when available.

    Args:
        study: The cBioPortal study identifier (e.g. ``blca_tcga_pan_can_atlas_2018``).
        cache_dir: Directory to read/write the cached JSON, or ``None`` to skip caching.

    Returns:
        The list of clinical-data records as returned by the cBioPortal API.
    """
    cache_file = cache_dir / f"{study}.json" if cache_dir is not None else None
    if cache_file is not None and cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    url = f"{CBIOPORTAL_API_URL}/studies/{study}/clinical-data"
    data = _request_with_retries(url, _CLINICAL_DATA_PARAMS).json()

    if cache_file is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data), encoding="utf-8")
    return data


def load_survival(studies: list[str], cache_dir: str | Path | None = None) -> pd.DataFrame:
    """Load patient-level overall-survival data for one or more cBioPortal studies.

    Records from multiple studies are concatenated, so pooling e.g. LUAD and LUSC into a single lung
    cohort is a matter of passing both study ids.

    Args:
        studies: One or more cBioPortal study identifiers to fetch and concatenate.
        cache_dir: Optional directory for caching the raw API responses between runs.

    Returns:
        A dataframe with one row per patient and the columns ``patientId``, ``OS_MONTHS``,
        ``OS_STATUS`` and (when present) the neoadjuvant-history flag.
    """
    cache_path = Path(cache_dir) if cache_dir is not None else None

    frames = []
    for study in studies:
        records = _load_study_clinical_data(study, cache_path)
        pivoted = pd.DataFrame(records).pivot_table(
            index=PATIENT_ID_COLUMN, columns="clinicalAttributeId", values="value", aggfunc="first"
        )
        frames.append(pivoted)

    combined = pd.concat(frames)
    available = [column for column in _SURVIVAL_COLUMNS if column in combined.columns]
    return combined[available].reset_index()
