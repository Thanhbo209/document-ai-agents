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
- Repository ZIP archives
- Web page connector ingestion
- YouTube transcript connector ingestion

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
OCR engine unavailable. Install Tesseract, set RAG_PLATFORM_OCR_TESSERACT_CMD, or disable OCR.
```

On Windows, install Tesseract and either add it to `PATH` or set:

```txt
RAG_PLATFORM_OCR_TESSERACT_CMD="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

For local development without OCR, set:

```txt
RAG_PLATFORM_OCR_ENABLED=false
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

## Connectors Ingestion

Connector ingestion lets a workspace owner or member with upload permission turn
external source metadata into the same normalized `ExtractedTextBlock` format as
file uploads. Connector blocks are chunked, stored, indexed, and cited through
the same pipeline as PDFs, Office files, OCR text, and media transcripts.

Connector API:

```txt
POST /api/v1/workspaces/{workspace_id}/connectors/ingest
```

Supported request shapes:

```json
{
  "source_type": "web",
  "url": "https://example.com/page"
}
```

```json
{
  "source_type": "youtube",
  "url": "https://www.youtube.com/watch?v=abcDEF123_4"
}
```

### Web URL Ingestion

Web ingestion uses a safe fetch policy and a small standard-library HTML text
extractor. It does not run browser automation and does not execute JavaScript.

Default safety behavior:

- Allows `https` URLs only.
- Rejects empty URLs and embedded URL credentials.
- Rejects non-HTTP schemes such as `file`, `ftp`, `gopher`, `data`, and
  `javascript`.
- Rejects localhost and private/internal IP ranges.
- Supports configured domain allowlists and blocklists.
- Enforces response byte limits and request timeouts.
- Manually validates redirect targets before following them.

Web metadata includes:

- `source_type: "web"`
- `url`
- `final_url`
- `title`
- `content_type`

Future citation labels can use:

```txt
Website: example.com/page
```

### YouTube Transcript Ingestion

YouTube ingestion uses `youtube-transcript-api` to fetch available transcripts.
It does not call paid APIs and does not download video/audio. Unit tests use fake
transcript clients and do not call YouTube.

Supported inputs:

- Raw YouTube video IDs
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`

Transcript segments are grouped into readable timestamp windows.

YouTube metadata includes:

- `source_type: "youtube"`
- `video_id`
- `url`
- `title`
- `language`
- `start_seconds`
- `end_seconds`
- `timestamp_start`
- `timestamp_end`
- `segment_count`

Future citation labels can use:

```txt
YouTube: 00:01:12-00:02:03
```

### Repository ZIP Ingestion

Repository ingestion supports uploaded `.zip` files through the normal document
upload endpoint. In this phase, all `.zip` uploads are treated as repository
archives.

ZIP safety behavior:

- Validates every member path before reading files.
- Rejects path traversal such as `../evil.py`.
- Rejects absolute paths and Windows drive paths such as `C:\evil.py`.
- Reads files from ZIP memory without extracting the archive to disk.
- Enforces max file count, max per-file bytes, and max total bytes.
- Skips likely binary files.

Default repo filters include common code and documentation extensions:

- `.py`, `.ts`, `.tsx`, `.js`, `.jsx`
- `.md`, `.txt`, `.json`, `.yml`, `.yaml`, `.toml`, `.sql`, `.html`, `.css`

Default exclusions include dependency/build/cache folders and common secret or
lock files:

- `.git`, `node_modules`, `.next`, `dist`, `build`, `__pycache__`
- `.venv`, `venv`, `.pytest_cache`, `.ruff_cache`
- `.env`, `.env.local`, `.env.production`, private key filenames
- `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `poetry.lock`

Repo metadata includes:

- `source_type: "repo"`
- `repo_name`
- `file_path`
- `language`
- `line_start`
- `line_end`

Future citation labels can use:

```txt
Repo: src/main.py, Lines 10-45
```

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
- `Website: example.com/page`
- `YouTube: 00:01:12-00:02:03`
- `Repo: src/main.py, Lines 10-45`

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
- Web extraction is simple readable text, not browser-rendered JavaScript.
- YouTube ingestion requires transcript availability; private videos may not
  work.
- Repository ingestion supports ZIP uploads, not Git clone yet.
- Secret-like filenames are skipped by default, but this is not a full secret
  scanner.
- Very large repositories should eventually move to async worker processing.
- Images inside Office files are not extracted.
- Speaker notes and comments are not extracted.
- Complex nested Word tables may be simplified.
- Merged spreadsheet cells may be normalized imperfectly.
- Formula cells are read as available parser values.
- PDF extraction remains text-based and depends on embedded text.
