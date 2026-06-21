# Ingestion

RAG Platform normalizes uploaded files into text blocks with source metadata.
Those blocks are then chunked, stored, indexed, and later used for grounded
answers and citations.

## Supported File Types

- TXT
- Markdown
- PDF
- DOCX
- PPTX
- CSV
- XLSX

## Office And Table Ingestion

Office and table ingestion extends the existing loader architecture. Uploads are
routed by file extension, then parsed into `ExtractedTextBlock` records with
metadata rich enough for later citation display.

### DOCX

DOCX ingestion uses `python-docx`.

Behavior:

- Extracts non-empty paragraphs.
- Preserves heading text as section metadata when paragraph styles indicate a
  heading.
- Extracts tables.
- Preserves table headers.
- Skips empty paragraphs and empty table rows.

Table blocks use readable text such as:

```txt
Table 1
Headers: Name | Role | Start Date
Row 1: Thanh | AI Intern | 2026-06-01
```

Useful metadata:

- `source_type: "docx"`
- `paragraph_index`
- `style_name`
- `section`
- `table_index`
- `row_start`
- `row_end`
- `column_names`

### PPTX

PPTX ingestion uses `python-pptx`.

Behavior:

- Extracts slide titles.
- Extracts text box content.
- Extracts tables when present.
- Preserves slide number and slide title.
- Groups slide content into logical slide blocks.

Slide blocks use readable text such as:

```txt
Slide 2: Product Roadmap

Title: Product Roadmap
Content:
- Phase 1: Upload
- Phase 2: Retrieval
```

Useful metadata:

- `source_type: "pptx"`
- `slide_number`
- `slide_title`
- `table_index`
- `row_start`
- `row_end`
- `column_names`

### CSV And XLSX

Table ingestion uses `pandas`; XLSX loading uses `openpyxl`.

Behavior:

- Preserves column headers.
- Preserves sheet names for XLSX.
- Supports multiple sheets in one workbook.
- Splits tables into row-range blocks, defaulting to 25 data rows per block.
- Uses human spreadsheet row numbers: header row is row 1, first data row is
  row 2.
- Handles empty cells and unnamed columns deterministically.
- Adds a lightweight table profile for numeric, date-like, and text columns.

Table blocks use readable text such as:

```txt
Sheet: Sales
Rows: 2-6
Columns: Date | Customer | Amount | Status

Row 2: Date=2026-01-01 | Customer=Acme | Amount=1200 | Status=Paid
```

Useful metadata:

- `source_type: "csv"` or `"xlsx"`
- `sheet_name`
- `row_start`
- `row_end`
- `column_names`
- `row_count`
- `column_count`
- `empty_cell_count`
- `profile.numeric_columns`
- `profile.date_like_columns`
- `profile.text_columns`

## Citation Metadata

The current UI may not render all Office/table citation labels yet, but the
ingestion blocks include enough metadata to support labels such as:

- `Slide 2 — Product Roadmap`
- `Sheet Sales, Rows 2–6`
- `Table 1, Rows 2–4`

## Known Limitations

- No OCR.
- Images inside Office files are not extracted.
- Speaker notes and comments are not extracted.
- Complex nested Word tables may be simplified.
- Merged spreadsheet cells may be normalized imperfectly.
- Formula cells are read as available parser values.
- PDF extraction remains text-based and depends on embedded text.
