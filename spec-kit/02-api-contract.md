# API Contract

## Endpoint

`POST /v1/extract`

`POST /v1/extract-url`

Content type:

`multipart/form-data`

Profile:

`default`

## Request Fields

- `file`: file yang akan diproses
- `include_empty_pages`: boolean, optional, default `true`
- `paginate_strategy`: optional, default `auto`

Nilai `paginate_strategy`:

- `auto`: pakai strategi default per format
- `virtual`: paksa virtual pagination bila extractor mengizinkan

Supported file types:

- `pdf`
- `docx`
- `pptx`
- `md`
- `txt`
- `doc`
- `ppt`
- `xls`

## URL Request

Endpoint:

`POST /v1/extract-url`

Content type:

`application/json`

Request body:

```json
{
  "url": "https://example.com/report.pdf",
  "include_empty_pages": true,
  "paginate_strategy": "auto"
}
```

Field:

- `url`: URL file remote dengan scheme `http` atau `https`

## Success Response

Status:

`200 OK`

Response body:

```json
{
  "file_name": "sample.pdf",
  "file_type": "pdf",
  "mime_type": "application/pdf",
  "document_category": "report",
  "document_domain": "finance",
  "summary": "Laporan ini merangkum performa keuangan kuartalan dan sorotan anggaran utama.",
  "tags": ["quarterly_report", "finance", "budget"],
  "classification": {
    "confidence": 0.92,
    "method": "rules",
    "model": "rules-v1"
  },
  "enrichment": {
    "status": "applied",
    "ai_used": true,
    "provider": "openai",
    "model": "openai-model-id"
  },
  "page_count": 3,
  "pages": [
    {
      "page": 1,
      "text": "Isi halaman pertama",
      "char_count": 20,
      "is_empty": false,
      "page_kind": "native"
    },
    {
      "page": 2,
      "text": "Isi halaman kedua",
      "char_count": 18,
      "is_empty": false,
      "page_kind": "native"
    },
    {
      "page": 3,
      "text": "",
      "char_count": 0,
      "is_empty": true,
      "page_kind": "native"
    }
  ]
}
```

## Response Schema

### Top-Level

- `file_name`: nama file asli
- `file_type`: extension yang sudah dinormalisasi, misal `pdf`
- `mime_type`: MIME type hasil deteksi server
- `document_category`: label klasifikasi utama dokumen, misal `invoice` atau `report`
- `document_domain`: label domain atau fungsi bisnis utama, misal `finance`, `accounting`, atau `it`
- `summary`: ringkasan singkat dokumen; boleh `null` jika AI tidak dipakai atau ringkasan tidak dibuat
- `tags`: array tag hasil klasifikasi dokumen
- `classification`: metadata hasil klasifikasi
- `enrichment`: metadata apakah AI dipakai, dilewati, atau fallback
- `page_count`: total panjang array `pages`; untuk format non-native nilainya boleh berbeda dari jumlah halaman visual asli
- `pages`: array of page

Catatan:

- `file_type` menjawab "format file ini apa"
- `document_category` menjawab "isi dokumen ini termasuk jenis apa"
- `document_domain` menjawab "dokumen ini paling dekat ke domain kerja mana"
- `summary` adalah ringkasan opsional di level dokumen
- `page_count` dan `page` memodelkan hasil segmentasi response, bukan jaminan pagination asli dokumen sumber

### Classification Object

- `confidence`: angka `0.0 - 1.0`
- `method`: enum `rules | ml | llm`
- `model`: identifier classifier, misal `rules-v1`

### Enrichment Object

- `status`: enum `applied | skipped | fallback`
- `ai_used`: boolean
- `provider`: string atau `null`, untuk sekarang `openai` atau `null`
- `model`: string atau `null`

### Page Object

- `page`: integer, nomor urut item pada response mulai dari `1`
- `text`: string hasil ekstraksi item tersebut
- `char_count`: integer jumlah karakter di `text`
- `is_empty`: boolean
- `page_kind`: enum `native | rendered | virtual`

## Error Responses

### Unsupported Media Type

Status:

`415 Unsupported Media Type`

```json
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Supported file types: pdf, docx, pptx, md, txt, doc, ppt, xls"
  }
}
```

### Invalid or Corrupted File

Status:

`422 Unprocessable Entity`

```json
{
  "error": {
    "code": "EXTRACTION_FAILED",
    "message": "File could not be parsed"
  }
}
```

### File Too Large

Status:

`413 Payload Too Large`

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "Maximum file size is 50 MB"
  }
}
```

## AI Enrichment Behavior

- jika server memiliki `OPENAI_API_KEY` yang valid, service boleh memakai OpenAI untuk membuat `summary` dan memperbaiki `tags`
- jika `OPENAI_API_KEY` tidak ada, service tetap sukses tanpa AI
- jika OpenAI gagal, timeout, atau responsnya tidak bisa dipakai, service tidak boleh gagal hanya karena enrichment; response harus fallback ke hasil non-AI
- `OPENAI_API_KEY` tidak boleh disimpan atau dicatat ke log

## URL Fetch Rules

- hanya URL `http` dan `https` yang diterima
- target localhost atau private network harus ditolak
- file hasil fetch tetap memakai response contract yang sama dengan upload file

## API Decision

Spec ini memilih wrapper object dengan field `pages` alih-alih top-level array murni, karena:

- Metadata file tetap bisa dikembalikan tanpa memecah contract
- Metadata klasifikasi seperti `document_category`, `document_domain`, `summary`, `tags`, dan `enrichment` bisa ikut dikembalikan
- Lebih mudah dikembangkan untuk async mode, checksum, dan processing time
- Tetap memenuhi requirement bahwa hasil utama berbentuk array of page

Catatan tambahan:

- untuk format non-`pdf`, service boleh mengembalikan best-effort pagination
- akurasi nomor halaman sumber tidak menjadi requirement utama selama urutan output tetap konsisten
