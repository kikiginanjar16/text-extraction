# API Doc

Dokumen ini ditulis untuk kebutuhan integrasi frontend.

Base URL lokal:

```text
http://127.0.0.1:8873
```

Available endpoints:

- `GET /health`
- `POST /v1/extract`
- `POST /v1/extract-url`

Catatan penting:

- frontend tidak perlu mengirim OpenAI key
- OpenAI enrichment dikontrol dari server lewat `OPENAI_API_KEY` di `.env`
- `/docs`, `/redoc`, dan `/openapi.json` bisa dilindungi Basic Auth lewat `SWAGGER_USERNAME` dan `SWAGGER_PASSWORD`
- jika backend dijalankan pada origin yang berbeda dari frontend, CORS middleware belum dikonfigurasi saat ini

## Quick Start

Untuk upload file:

```ts
const formData = new FormData();
formData.append("file", file);
formData.append("include_empty_pages", "true");
formData.append("paginate_strategy", "auto");

const response = await fetch("http://127.0.0.1:8873/v1/extract", {
  method: "POST",
  body: formData,
});

const data = await response.json();
```

Untuk ekstraksi dari URL:

```ts
const response = await fetch("http://127.0.0.1:8873/v1/extract-url", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://example.com/report.pdf",
    include_empty_pages: true,
    paginate_strategy: "auto",
  }),
});

const data = await response.json();
```

## Health Check

### `GET /health`

Success response:

```json
{
  "status": "ok"
}
```

## Extract From Upload

### `POST /v1/extract`

Content type:

```text
multipart/form-data
```

Request fields:

- `file`: required, browser `File`
- `include_empty_pages`: optional, default `true`
- `paginate_strategy`: optional, `auto` or `virtual`

Frontend example:

```ts
export async function extractFromFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("include_empty_pages", "true");
  formData.append("paginate_strategy", "auto");

  const response = await fetch("http://127.0.0.1:8873/v1/extract", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw await response.json();
  }

  return response.json() as Promise<ExtractResponse>;
}
```

## Extract From URL

### `POST /v1/extract-url`

Content type:

```text
application/json
```

Request body:

```json
{
  "url": "https://example.com/report.pdf",
  "include_empty_pages": true,
  "paginate_strategy": "auto"
}
```

Request fields:

- `url`: required, public `http` or `https` URL
- `include_empty_pages`: optional, default `true`
- `paginate_strategy`: optional, `auto` or `virtual`

Frontend example:

```ts
export async function extractFromUrl(url: string) {
  const response = await fetch("http://127.0.0.1:8873/v1/extract-url", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url,
      include_empty_pages: true,
      paginate_strategy: "auto",
    }),
  });

  if (!response.ok) {
    throw await response.json();
  }

  return response.json() as Promise<ExtractResponse>;
}
```

URL rules:

- hanya `http` dan `https`
- URL ke `localhost`, `127.0.0.1`, private IP, atau internal network akan ditolak

## Success Response

Kedua endpoint ekstraksi mengembalikan shape yang sama.

```json
{
  "file_name": "finance_report.txt",
  "file_type": "txt",
  "mime_type": "text/plain",
  "document_category": "report",
  "document_domain": "finance",
  "summary": null,
  "tags": ["report", "finance", "budget", "quarterly_report"],
  "classification": {
    "confidence": 0.85,
    "method": "rules",
    "model": "rules-v1"
  },
  "enrichment": {
    "status": "skipped",
    "ai_used": false,
    "provider": null,
    "model": null
  },
  "page_count": 1,
  "pages": [
    {
      "page": 1,
      "text": "Quarterly financial report\nBudget and revenue overview\nCash flow analysis",
      "char_count": 73,
      "is_empty": false,
      "page_kind": "virtual"
    }
  ]
}
```

## TypeScript Types

```ts
export type ClassificationMethod = "rules" | "ml" | "llm";
export type EnrichmentStatus = "applied" | "skipped" | "fallback";
export type PageKind = "native" | "rendered" | "virtual";
export type PaginateStrategy = "auto" | "virtual";

export interface Classification {
  confidence: number;
  method: ClassificationMethod;
  model: string;
}

export interface Enrichment {
  status: EnrichmentStatus;
  ai_used: boolean;
  provider: "openai" | null;
  model: string | null;
}

export interface ExtractPage {
  page: number;
  text: string;
  char_count: number;
  is_empty: boolean;
  page_kind: PageKind;
}

export interface ExtractResponse {
  file_name: string;
  file_type: "pdf" | "docx" | "pptx" | "md" | "txt" | "doc" | "ppt" | "xls";
  mime_type: string;
  document_category:
    | "invoice"
    | "receipt"
    | "contract"
    | "proposal"
    | "report"
    | "presentation"
    | "resume"
    | "memo"
    | "meeting_notes"
    | "letter"
    | "form"
    | "spreadsheet"
    | "manual"
    | "unknown";
  document_domain:
    | "finance"
    | "accounting"
    | "it"
    | "hr"
    | "legal"
    | "procurement"
    | "operations"
    | "sales"
    | "marketing"
    | "customer_support"
    | "executive"
    | "general"
    | "unknown";
  summary: string | null;
  tags: string[];
  classification: Classification;
  enrichment: Enrichment;
  page_count: number;
  pages: ExtractPage[];
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
```

## Error Response

Semua error memakai shape yang sama:

```json
{
  "error": {
    "code": "EXTRACTION_FAILED",
    "message": "File could not be parsed"
  }
}
```

Status code yang umum:

- `413`: file terlalu besar
- `415`: extension tidak didukung
- `422`: file tidak bisa diparse, URL invalid, atau URL target ditolak

Error code yang umum:

- `FILE_TOO_LARGE`
- `UNSUPPORTED_FILE_TYPE`
- `EXTRACTION_FAILED`
- `INVALID_REQUEST`

## Integration Notes

- `summary` bisa `null`, jadi jangan diasumsikan selalu ada
- `page_count` selalu sama dengan `pages.length`
- `page` adalah nomor urut output, bukan jaminan nomor halaman visual asli
- `page_kind` untuk frontend biasanya cukup dipakai sebagai metadata display atau debug
- `enrichment.status = skipped` berarti backend berjalan tanpa AI
- `enrichment.status = fallback` berarti AI dicoba tetapi hasil akhirnya kembali ke non-AI

## Recommended Frontend Flow

1. Upload file atau submit URL.
2. Tampilkan loading state selama request berlangsung.
3. Jika `response.ok === false`, parse body error dan tampilkan `error.message`.
4. Render `summary`, `tags`, dan daftar `pages`.
5. Jika `summary` bernilai `null`, tampilkan fallback UI seperti "Summary not available".

## Supported Extensions

- `pdf`
- `docx`
- `pptx`
- `md`
- `txt`
- `doc`
- `ppt`
- `xls`
