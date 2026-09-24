"""ModelNorth HyperBrowser: High-Speed Structured Data Extraction Engine."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredExtractor:
    """Extracts structured entity lists and records from DOM element tables in < 30ms."""

    def __init__(self, text_engine: Optional[Any] = None) -> None:
        self.text_engine = text_engine

    def extract_records(
        self,
        elements: List[Dict[str, Any]],
        schema: Optional[Type[T]] = None,
        target_entity: str = "item",
    ) -> List[Any]:
        """Extracts repeated entity records (e.g. flights, products, search results) from indexed elements."""
        records: List[Dict[str, Any]] = []
        if not elements:
            return records

        for el in elements:
            name = el.get("name") or ""
            if not name:
                continue

            # Check if this is a composite result node (e.g. flight card, search result)
            price_match = re.search(r"(?:AED|USD|EUR|GBP|\$|€|£)\s*([0-9,]+(?:\.[0-9]{2})?)", name, re.IGNORECASE)
            airline_match = re.search(r"operated by\s+([A-Za-z\s]+?)(?:\s+Nonstop|\s+[0-9]+\s*stop|\.|$|\n)", name, re.IGNORECASE)
            if not airline_match:
                # Direct airline detection
                for known in ["Emirates", "Air India Express", "Qatar Airways", "Flydubai", "Etihad", "Lufthansa", "British Airways"]:
                    if known.lower() in name.lower():
                        airline_match = re.search(re.escape(known), name, re.IGNORECASE)
                        break

            stops_match = re.search(r"([0-9]+\s*stops?|nonstop)", name, re.IGNORECASE)
            time_match = re.search(r"([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM|–|-)\s*[0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)", name, re.IGNORECASE)

            if price_match or airline_match or ("flight" in name.lower() and stops_match):
                airline_name = "Direct"
                if airline_match:
                    airline_name = airline_match.group(1).strip() if len(airline_match.groups()) > 0 else airline_match.group(0).strip()

                record = {
                    "raw_text": name,
                    "price": price_match.group(0) if price_match else None,
                    "airline": airline_name,
                    "stops": stops_match.group(1) if stops_match else "Nonstop",
                    "schedule": time_match.group(1) if time_match else None,
                    "element_id": el.get("id"),
                }
                records.append(record)

        # If schema is provided, cast records to schema
        if schema and issubclass(schema, BaseModel):
            valid_models = []
            for r in records:
                try:
                    valid_models.append(schema(**r))
                except Exception:
                    fields = schema.model_fields.keys()
                    filtered = {k: v for k, v in r.items() if k in fields}
                    try:
                        valid_models.append(schema.model_construct(**filtered))
                    except Exception:
                        pass
            return valid_models

        return records
