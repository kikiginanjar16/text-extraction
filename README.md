# Text Extraction

Repo ini sekarang berisi dua hal:

- implementasi baseline layanan text extraction berbasis `FastAPI`
- dokumen spec di folder [`spec-kit`](./spec-kit)
- panduan integrasi frontend di [`APIDOC.md`](./APIDOC.md)

## Supported Formats

- `pdf`
- `docx`
- `pptx`
- `md`
- `txt`
- `doc`
- `ppt`
- `xls`

## Current Behavior

- response utama berbentuk `pages[]`
- pagination non-`pdf` bersifat best-effort
- klasifikasi menghasilkan `document_category` dan `document_domain`
- `summary` dan perbaikan `tags` bisa memakai OpenAI secara opsional
- jika `OPENAI_API_KEY` tidak diisi di `.env`, service tetap berjalan tanpa AI
- tersedia endpoint file upload dan endpoint URL fetch server-side

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn --env-file .env app.main:app --reload
```

## Docker

Build dan jalankan dengan Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

Service akan tersedia di:

```text
http://127.0.0.1:8000
```

Catatan:

- image memasang `libmagic` dan `LibreOffice`
- `docker-compose.yml` memakai bind mount project dan `--reload` untuk workflow lokal
- kalau ingin mode yang lebih production-like, hapus volume mount dan flag `--reload`

Optional OpenAI enrichment:

- isi `OPENAI_API_KEY` di `.env`
- atau install extra dependency dengan `pip install -e .[ai]` bila Anda ingin menandai dependency AI secara eksplisit

## URL Endpoint

Anda juga bisa ekstraksi dari URL:

```bash
curl -X POST http://127.0.0.1:8000/v1/extract-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/report.pdf",
    "include_empty_pages": true,
    "paginate_strategy": "auto"
  }'
```

Catatan:

- hanya `http` dan `https` yang diterima
- target `localhost` dan private IP ditolak sebagai guard dasar SSRF

## Tests

Test yang tidak butuh dependency eksternal bisa dijalankan dengan:

```bash
python3 -m unittest discover -s tests
```

Dokumen utama ada di folder [`spec-kit`](./spec-kit):

- `01-product-spec.md`
- `02-api-contract.md`
- `03-architecture.md`
- `04-implementation-plan.md`
- `openapi.yaml`
