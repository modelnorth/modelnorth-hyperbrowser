"""Unit tests for StructuredExtractor."""

from pydantic import BaseModel
from typing import Optional
from modelnorth.engine.extractor import StructuredExtractor


class FlightCard(BaseModel):
    airline: Optional[str] = None
    price: Optional[str] = None
    stops: Optional[str] = None


def test_extractor_raw_and_schema():
    extractor = StructuredExtractor()
    mock_elements = [
        {"id": 1, "name": "Flight from DXB to LHE AED 1,040 operated by Air India Express Nonstop 02:15 – 06:30"},
        {"id": 2, "name": "Flight from DXB to LHE AED 1,420 operated by Emirates Nonstop 03:00 – 07:15"},
        {"id": 3, "name": "Explore destinations"},
    ]

    records = extractor.extract_records(mock_elements, schema=FlightCard)
    assert len(records) == 2
    assert records[0].airline == "Air India Express"
    assert "1,040" in records[0].price
    assert records[0].stops == "Nonstop"
    assert records[1].airline == "Emirates"
    assert "1,420" in records[1].price
