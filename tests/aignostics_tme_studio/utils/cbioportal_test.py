"""Unit tests for the cBioPortal survival loader."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from aignostics_tme_studio.utils import cbioportal

_STUDY = "blca_tcga_pan_can_atlas_2018"
_MODULE = "aignostics_tme_studio.utils.cbioportal"

_RECORDS = [
    {"patientId": "TCGA-AA-0001", "clinicalAttributeId": "OS_MONTHS", "value": "12.3"},
    {"patientId": "TCGA-AA-0001", "clinicalAttributeId": "OS_STATUS", "value": "1:DECEASED"},
    {"patientId": "TCGA-AA-0002", "clinicalAttributeId": "OS_MONTHS", "value": "40.0"},
    {"patientId": "TCGA-AA-0002", "clinicalAttributeId": "OS_STATUS", "value": "0:LIVING"},
]


def _mock_response(records: list[dict]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = records
    response.raise_for_status.return_value = None
    return response


@pytest.mark.unit
@patch(f"{_MODULE}.requests.get")
def test_load_survival_pivots_records(mock_get) -> None:
    """load_survival pivots clinical records into one row per patient with survival columns."""
    mock_get.return_value = _mock_response(_RECORDS)

    result = cbioportal.load_survival([_STUDY])

    assert list(result[cbioportal.PATIENT_ID_COLUMN]) == ["TCGA-AA-0001", "TCGA-AA-0002"]
    assert cbioportal.OS_MONTHS_COLUMN in result.columns
    assert cbioportal.OS_STATUS_COLUMN in result.columns
    assert len(result) == 2


@pytest.mark.unit
@patch(f"{_MODULE}.requests.get")
def test_load_survival_concatenates_studies(mock_get) -> None:
    """Records from multiple studies are concatenated into one dataframe."""
    other = [
        {"patientId": "TCGA-BB-0003", "clinicalAttributeId": "OS_MONTHS", "value": "5.0"},
        {"patientId": "TCGA-BB-0003", "clinicalAttributeId": "OS_STATUS", "value": "1:DECEASED"},
    ]
    mock_get.side_effect = [_mock_response(_RECORDS), _mock_response(other)]

    result = cbioportal.load_survival([_STUDY, "lusc_tcga_pan_can_atlas_2018"])

    assert len(result) == 3
    assert "TCGA-BB-0003" in set(result[cbioportal.PATIENT_ID_COLUMN])


@pytest.mark.unit
@patch(f"{_MODULE}.requests.get")
def test_load_survival_uses_and_writes_cache(mock_get, tmp_path) -> None:
    """A cached response is written on first fetch and re-used without hitting the network again."""
    mock_get.return_value = _mock_response(_RECORDS)

    first = cbioportal.load_survival([_STUDY], cache_dir=tmp_path)
    cache_file = tmp_path / f"{_STUDY}.json"
    assert cache_file.exists()
    assert json.loads(cache_file.read_text(encoding="utf-8")) == _RECORDS

    mock_get.reset_mock()
    second = cbioportal.load_survival([_STUDY], cache_dir=tmp_path)
    mock_get.assert_not_called()
    assert first.equals(second)


@pytest.mark.unit
@patch(f"{_MODULE}.time.sleep")
@patch(f"{_MODULE}.requests.get")
def test_request_retries_then_succeeds(mock_get, mock_sleep) -> None:
    """A transient failure is retried before the successful response is returned."""
    mock_get.side_effect = [requests.ConnectionError("boom"), _mock_response(_RECORDS)]

    result = cbioportal.load_survival([_STUDY])

    assert len(result) == 2
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()


@pytest.mark.unit
@patch(f"{_MODULE}.time.sleep")
@patch(f"{_MODULE}.requests.get")
def test_request_raises_after_exhausting_retries(mock_get, mock_sleep) -> None:
    """When every attempt fails, the last exception propagates."""
    mock_get.side_effect = requests.ConnectionError("boom")

    with pytest.raises(requests.ConnectionError):
        cbioportal.load_survival([_STUDY])

    assert mock_get.call_count == 6
    assert mock_sleep.call_count == 5
