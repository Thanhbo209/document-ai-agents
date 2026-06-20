import csv
import json
from io import StringIO

from app.extraction.schemas import ExtractionResult


def export_extraction_result_json(result: ExtractionResult) -> str:
    return result.model_dump_json(indent=2)


def export_extraction_result_csv(result: ExtractionResult) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "name",
            "value",
            "field_type",
            "confidence",
            "source_id",
            "chunk_id",
            "document_id",
            "source_page",
            "quote",
            "review_flags",
        ],
    )

    writer.writeheader()

    for field in result.fields:
        evidence = field.evidence

        writer.writerow(
            {
                "name": field.name,
                "value": json.dumps(field.value)
                if isinstance(field.value, list | dict)
                else field.value,
                "field_type": field.field_type.value,
                "confidence": field.confidence,
                "source_id": evidence.source_id if evidence else "",
                "chunk_id": evidence.chunk_id if evidence else "",
                "document_id": evidence.document_id if evidence else "",
                "source_page": evidence.source_page if evidence else "",
                "quote": evidence.quote if evidence else "",
                "review_flags": ",".join(field.review_flags),
            }
        )

    return output.getvalue()
