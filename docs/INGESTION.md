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
- Scanned PDFs through OCR fallback
- Images through OCR (`PNG`, `JPG`, `JPEG`, `TIFF`, `BMP`)
- Audio transcription (`MP3`, `WAV`, `M4A`, `FLAC`, `OGG`)
- Video transcription (`MP4`, `MOV`, `MKV`, `WEBM`)

## OCR Ingestion

OCR ingestion makes scanned PDFs and image-based documents searchable. The
implementation uses an adapter pattern so the default OCR engine can be replaced
later without rewriting the ingestion pipeline.

Default adapter:

- `pytesseract`
- `Pillow`
- `PyMuPDF` for rendering scanned PDF pages to images

Tesseract also requires a system-wide Tesseract binary. If the binary is not
installed and OCR is required, ingestion fails with a clear error:

```txt
OCR engine unavailable. Install Tesseract or disable OCR.
```

### Scanned PDFs

PDF ingestion first tries normal embedded-text extraction. If meaningful text is
available, the normal PDF path is used and OCR is skipped. If no text is found,
the OCR worker renders each page to a PNG artifact, preprocesses it, runs OCR,
and converts the OCR result into `ExtractedTextBlock` records.

OCR blocks include readable text such as:

```txt
OCR Page 2

Scanned refund policy allows cancellation within 14 days.
```

Useful metadata:

- `source_type: "ocr_pdf"`
- `page_number`
- `ocr: true`
- `ocr_confidence`
- `low_confidence`
- `image_path`
- `bounding_boxes`

### Images

Image ingestion routes supported image extensions through the same OCR worker.
The original image is copied to artifact storage, a preprocessed PNG is created,
and the OCR result is converted into searchable text blocks.

### Image Preprocessing

Preprocessing is intentionally simple and deterministic:

- Open with Pillow.
- Convert to grayscale.
- Apply autocontrast.
- Save a separate PNG artifact for OCR.

The original rendered page/image artifact is preserved.

### Confidence And Low-Confidence Flagging

Tesseract token confidence values are normalized to `0.0` through `1.0`.
Page confidence is the average confidence across valid OCR tokens. Pages below
the configured threshold are flagged:

```python
{
    "ocr_confidence": 0.58,
    "low_confidence": True
}
```

The current minimum behavior is metadata preservation. Future UI/review work can
use this metadata to show manual review warnings.

### Bounding Box Metadata

OCR stores line-level bounding boxes to keep metadata useful without exploding
chunk size:

```python
{
    "text": "Scanned refund policy...",
    "confidence": 0.91,
    "bbox": {
        "x": 10,
        "y": 20,
        "width": 260,
        "height": 24
    }
}
```

### Artifact Storage

Generated OCR artifacts are stored under:

```txt
storage/artifacts/{workspace_id}/{document_id}/ocr/page-001.png
storage/artifacts/{workspace_id}/{document_id}/ocr/page-001-ocr.png
storage/artifacts/{workspace_id}/{document_id}/ocr/ocr.json
```

The JSON artifact stores OCR page results, confidence, line text, and bounding
box metadata.

## Media Transcription Ingestion

Media ingestion turns uploaded audio and video files into timestamped transcript
blocks. The implementation uses adapter interfaces for both audio extraction and
transcription so FFmpeg and Whisper can be replaced later without changing the
upload or chunking pipeline.

Default adapters:

- `FFmpegAudioExtractor` calls the local `ffmpeg` binary.
- `WhisperTranscriber` loads a local Whisper model lazily.

No hosted transcription API is used. Real media processing requires FFmpeg to be
installed system-wide and a local Whisper dependency/model available to the API
process.

### Audio And Video Behavior

Supported audio files are transcribed directly:

- `MP3`
- `WAV`
- `M4A`
- `FLAC`
- `OGG`

Supported video files first extract mono 16 kHz WAV audio with FFmpeg:

```txt
ffmpeg -y -i input_file -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav
```

Supported video extensions:

- `MP4`
- `MOV`
- `MKV`
- `WEBM`

Media uploads are processed asynchronously with FastAPI background tasks in this
phase. The upload response creates the document, file, and ingestion job quickly;
the background task then transcribes, chunks, indexes, and marks the job
`succeeded` or `failed`.

### Transcript Blocks And Timestamps

Whisper segments are grouped into readable windows, usually around one minute,
instead of creating one giant transcript block or one tiny block per word.

Example block text:

```txt
Transcript 00:01:12-00:02:03

The refund policy allows cancellation within fourteen days...
```

Useful metadata:

- `source_type: "audio"` or `"video"`
- `transcript: true`
- `start_seconds`
- `end_seconds`
- `timestamp_start`
- `timestamp_end`
- `language`
- `duration_seconds`
- `segment_count`
- `segments`

This metadata supports future citation labels such as:

```txt
Video.mp4, 00:01:12-00:02:03
```

The frontend source drawer displays transcript timestamps in a friendly form and
does not render raw transcript JSON.

### Media Artifacts

Generated media artifacts are stored under:

```txt
storage/artifacts/{workspace_id}/{document_id}/media/audio.wav
storage/artifacts/{workspace_id}/{document_id}/media/transcript.json
```

The transcript JSON is an operational artifact for debugging and reprocessing,
not a user-facing raw JSON view.

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
- `Video.mp4, 00:01:12-00:02:03`

## Known Limitations

- OCR quality depends on scan quality.
- Handwriting may extract poorly.
- Tables in scanned PDFs may not preserve row/column structure yet.
- Images inside Office files are not OCR'd unless separately extracted.
- Tesseract must be installed locally/system-wide for real OCR execution.
- Tests use a fake OCR engine and do not require the real Tesseract binary.
- FFmpeg must be installed locally/system-wide for real video audio extraction.
- Local Whisper model size affects transcription speed, CPU, and memory usage.
- Tests use fake media adapters and do not require real FFmpeg or Whisper.
- Speaker diarization is not implemented.
- Transcription quality depends on audio quality and the selected local model.
- Very large media should eventually move from in-process background tasks to a
  real worker queue.
- Images inside Office files are not extracted.
- Speaker notes and comments are not extracted.
- Complex nested Word tables may be simplified.
- Merged spreadsheet cells may be normalized imperfectly.
- Formula cells are read as available parser values.
- PDF extraction remains text-based and depends on embedded text.
