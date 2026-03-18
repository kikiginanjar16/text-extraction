# Architecture

## High-Level Flow

1. Client mengirim file ke `POST /v1/extract` atau URL ke `POST /v1/extract-url`
2. API validasi ukuran file, extension, MIME type, atau URL target
3. File upload atau hasil fetch URL disimpan ke temporary directory
4. Strategy resolver memilih extractor
5. Extractor menghasilkan `pages[]`
6. Classification service membuat `document_category`, `document_domain`, dan baseline `tags[]`
7. Optional enrichment service membuat `summary` dan dapat memperbaiki `tags[]` jika `OPENAI_API_KEY` tersedia
8. API mengembalikan JSON response
9. Temporary file dibersihkan

Dokumen ini mendeskripsikan baseline arsitektur untuk format `pdf`, `docx`, `pptx`, `md`, `txt`, `doc`, `ppt`, dan `xls` dengan pagination best-effort.

## Arsitektur yang Direkomendasikan

```text
app/
  api/
    routes/
      extract.py
  core/
    config.py
    logging.py
    errors.py
  schemas/
    request.py
    response.py
  services/
    extraction/
      service.py
      resolver.py
      base.py
      strategies/
        pdf.py
        office_modern.py
        office_legacy.py
        text_virtual.py
    classification/
      service.py
      rules.py
      taxonomy.py
    enrichment/
      service.py
      base.py
      openai_provider.py
      fallback.py
    storage/
      temp_files.py
  main.py
```

## Strategy Matrix

| File Type | Strategy | Page Kind | Notes |
| --- | --- | --- | --- |
| `pdf` | direct extract via PDF library | `native` | paling akurat untuk page boundary |
| `md` | parse plain text lalu virtual paginate | `virtual` | default tanpa render engine |
| `txt` | plain text lalu virtual paginate | `virtual` | deterministic split |
| `docx`, `pptx` | direct text extraction, lalu segmentasi best-effort | `rendered` atau `virtual` | nomor halaman tidak harus sama dengan aplikasi asal |
| `doc`, `ppt` | legacy fallback extractor atau conversion service | `rendered` atau `virtual` | format biner lama, variasi tinggi |
| `xls` | extract per sheet / print area lalu segmentasi | `rendered` atau `virtual` | fokus pada teks, bukan fidelity layout |

## Library Recommendation

### Core API

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings`
- `python-multipart`
- `orjson`

### File Detection and Safety

- `python-magic`
- `pathlib` dan `tempfile` dari standard library

### Extraction

- `pymupdf`
  - ekstraksi text per page untuk PDF
  - cukup untuk baseline tanpa OCR

### Markdown and Text Normalization

- `markdown-it-py` untuk normalisasi `md` bila dibutuhkan
- untuk fase awal, `md` dapat diperlakukan sebagai text document tanpa render HTML

### Office Document Handling

- `python-docx` untuk ekstraksi text `docx`
- `python-pptx` untuk ekstraksi text `pptx`
- `xlrd` untuk membaca `xls`
- fallback conversion service atau `LibreOffice` CLI direkomendasikan untuk `doc` dan `ppt`

### Classification

- fase awal: rules engine berbasis keyword, heading, dan filename hint
- `rapidfuzz` optional untuk fuzzy tag matching
- `scikit-learn` optional jika classifier ingin dinaikkan dari rule-based ke model terlatih

### Optional AI Enrichment

- `openai` package optional untuk enrichment `summary` dan `tags`
- provider harus dipanggil hanya jika environment memiliki `OPENAI_API_KEY`
- jika provider gagal, service wajib fallback ke hasil non-AI

## Baseline Benefits

- bisa menutup seluruh format target sejak awal
- pagination non-`pdf` boleh best-effort sehingga implementasi tidak perlu mengejar fidelity visual penuh
- `tesseract-ocr` tidak dibutuhkan pada baseline awal
- tetap cukup ringan bila conversion fallback hanya diaktifkan untuk format legacy

## Remote Fetch Guard

- endpoint URL hanya menerima `http` dan `https`
- hostname yang resolve ke private, loopback, link-local, atau reserved IP harus ditolak
- hasil download diperlakukan sama seperti upload file biasa setelah tersimpan di temp file

## Classification and Enrichment Pipeline

Urutan yang direkomendasikan:

1. gabungkan teks dari `pages[]`
2. normalisasi whitespace dan lowercase
3. ambil sinyal dari judul, heading, kata dominan, dan nama file
4. skor kandidat `document_category`
5. skor kandidat `document_domain`
6. pilih primary label untuk category dan domain
7. generate baseline `tags[]` non-AI
8. jika `OPENAI_API_KEY` tersedia, panggil enrichment provider untuk `summary` dan `tags[]`
9. jika provider gagal, pakai baseline `tags[]` dan set `summary = null`
10. kembalikan `unknown` jika confidence di bawah threshold

Taxonomy category awal yang direkomendasikan:

- `invoice`
- `receipt`
- `contract`
- `proposal`
- `report`
- `presentation`
- `resume`
- `memo`
- `meeting_notes`
- `letter`
- `form`
- `spreadsheet`
- `manual`
- `unknown`

Taxonomy domain awal yang direkomendasikan:

- `finance`
- `accounting`
- `it`
- `hr`
- `legal`
- `procurement`
- `operations`
- `sales`
- `marketing`
- `customer_support`
- `executive`
- `general`
- `unknown`

## Pagination Tradeoff

Beberapa format memang tidak menyimpan page boundary yang stabil untuk diekstrak langsung:

- `docx` dan `doc` sangat bergantung pada font, printer profile, dan rendering engine
- `xls` punya layout print yang bisa berubah berdasarkan sheet setting
- `ppt` dan `doc` adalah format biner lama dengan tooling parser yang lebih terbatas

Karena itu arsitektur ini memprioritaskan urutan teks dan coverage format. Jika extractor tidak bisa memberi page boundary yang presisi, service boleh fallback ke `rendered` atau `virtual` pages.

## Normalized Domain Model

```json
{
  "file_name": "report.pdf",
  "file_type": "pdf",
  "mime_type": "application/pdf",
  "document_category": "report",
  "document_domain": "finance",
  "summary": "Laporan ini menjelaskan hasil keuangan dan sorotan utama kuartal berjalan.",
  "tags": ["quarterly_report", "finance", "budget"],
  "classification": {
    "confidence": 0.88,
    "method": "rules",
    "model": "rules-v1"
  },
  "enrichment": {
    "status": "applied",
    "ai_used": true,
    "provider": "openai",
    "model": "openai-model-id"
  },
  "page_count": 2,
  "pages": [
    {
      "page": 1,
      "text": "....",
      "char_count": 1000,
      "is_empty": false,
      "page_kind": "native"
    }
  ]
}
```

## Error Handling

Gunakan error domain yang eksplisit:

- `UNSUPPORTED_FILE_TYPE`
- `FILE_TOO_LARGE`
- `PASSWORD_PROTECTED_FILE`
- `EXTRACTION_FAILED`

## Observability

Log minimal:

- `request_id`
- `file_name`
- `file_type`
- `mime_type`
- `page_count`
- `processing_time_ms`
- `strategy`
- `page_kind_summary`
- `document_category`
- `document_domain`
- `enrichment_status`
- `classification_method`
- `classification_confidence`

## Deployment Notes

Jika service dijalankan di container:

- base image Python
- install `file` / libmagic
- `LibreOffice` opsional, tetapi direkomendasikan bila `doc` dan `ppt` harus didukung konsisten
- package `openai` opsional; hanya dibutuhkan bila fitur AI enrichment diaktifkan
- `tesseract-ocr` tidak dibutuhkan pada baseline awal

## Security Notes

- `OPENAI_API_KEY` harus dianggap secret environment
- key tidak boleh dipersist ke database, cache, atau log
- kegagalan provider AI tidak boleh menggagalkan ekstraksi inti
