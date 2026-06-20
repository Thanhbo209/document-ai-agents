import json

from app.answers.types import AnswerSource
from app.extraction.exporters import export_extraction_result_csv, export_extraction_result_json
from app.extraction.runner import LocalStructuredExtractionClient, StructuredExtractionRunner
from app.extraction.schemas import ExtractionFieldSpec, ExtractionFieldType, ExtractionSchema


def test_export_extraction_result_json_and_csv() -> None:
    source = AnswerSource(
        source_id="S1",
        chunk_id="chunk-1",
        document_id="doc-1",
        workspace_id="workspace-1",
        text="Party: Acme Corp.",
        source_page=1,
        source_start_offset=0,
        source_end_offset=18,
        score=0.9,
        metadata={},
    )
    schema = ExtractionSchema(
        name="basic",
        fields=[
            ExtractionFieldSpec(
                name="party",
                description="Party name",
                field_type=ExtractionFieldType.TEXT,
            )
        ],
    )
    runner = StructuredExtractionRunner(LocalStructuredExtractionClient())
    result = runner.run(schema=schema, sources=[source])

    json_output = export_extraction_result_json(result)
    csv_output = export_extraction_result_csv(result)

    parsed = json.loads(json_output)

    assert parsed["schema_name"] == "basic"
    assert "party" in csv_output
    assert "Acme Corp." in csv_output
    assert "S1" in csv_output
