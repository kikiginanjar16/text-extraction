# Implementation Plan

Dokumen ini memprioritaskan coverage format penuh pada baseline awal, dengan kompromi bahwa pagination non-`pdf` boleh best-effort.

## Phase 1

Tujuan:

- Menyediakan FastAPI app dasar
- Endpoint upload tunggal
- Support `pdf`, `docx`, `pptx`, `md`, `txt`, `doc`, `ppt`, `xls`
- Menormalkan semua format ke contract `pages[]`
- Tanpa OCR

Deliverables:

- schema request/response
- extractor PDF per page
- adapter extractor untuk `docx`, `pptx`, `doc`, `ppt`, dan `xls`
- virtual paginator untuk format yang tidak punya page boundary stabil
- endpoint URL fetch untuk ekstraksi dari remote file
- taxonomy `document_category` dan `document_domain`
- baseline auto-tagging dan classifier rule-based
- field `summary` dan `enrichment` di response
- config plumbing untuk `OPENAI_API_KEY` opsional
- fallback strategy untuk legacy Office bila direct parser terbatas
- deployment baseline pragmatis
- test dasar untuk contract `pages[]`

## Phase 2

Tujuan:

- Meningkatkan robustness extractor dan konsistensi hasil

Deliverables:

- hardening conversion fallback untuk `doc` dan `ppt`
- normalisasi segmentasi `page_kind` antar format
- perluasan coverage klasifikasi untuk dokumen Office
- perluasan coverage domain seperti `finance`, `accounting`, `it`, `hr`, dan `legal`
- integrasi optional OpenAI untuk `summary` dan `tags`
- fallback non-AI jika key tidak ada atau provider gagal
- error handling conversion dan parser failure
- partial-fidelity tests untuk pagination best-effort

## Phase 3

Tujuan:

- Meningkatkan kualitas operasional dan fidelity bila nanti dibutuhkan

Deliverables:

- OCR fallback opsional untuk scanned PDF
- peningkatan rendered pagination untuk format Office tertentu
- request timeout handling
- metrics dan structured logging
- upgrade classifier ke ML bila baseline rule-based tidak cukup
- evaluasi prompt dan guardrail untuk enrichment AI
- test file corrupt dan unsupported

## Acceptance Criteria

1. Service menerima `pdf`, `docx`, `pptx`, `md`, `txt`, `doc`, `ppt`, dan `xls`
2. Service menyediakan endpoint upload file dan endpoint extract via URL
3. Response selalu punya `page_count` dan `pages`
4. Setiap item `pages` selalu punya `page` dan `text`
5. `page` selalu berurutan mulai dari `1`
6. `page_count` sama dengan panjang `pages`
7. Untuk `pdf`, page boundary native dipakai jika tersedia
8. Untuk format non-`pdf`, page boundary boleh best-effort dan tidak wajib sama dengan pagination visual dokumen sumber
9. `page_kind` membedakan minimal `native`, `rendered`, atau `virtual`
10. Response selalu punya `document_category`, `document_domain`, `summary`, `tags`, `classification`, dan `enrichment`
11. Jika `OPENAI_API_KEY` tidak diisi, service tetap sukses tanpa AI dan `enrichment.status = skipped`
12. Jika `OPENAI_API_KEY` diisi valid, service boleh memakai OpenAI untuk `summary` dan `tags`
13. Jika provider AI gagal, service tetap sukses dengan fallback non-AI dan `enrichment.status = fallback`
14. Endpoint URL menolak target localhost dan private address
15. Jika confidence klasifikasi rendah, `document_category` dan/atau `document_domain` bernilai `unknown`
16. Secret seperti `OPENAI_API_KEY` tidak masuk ke log atau storage persisten
17. Service memprioritaskan keberhasilan ekstraksi teks dan urutan output dibanding akurasi nomor halaman sumber

## Test Matrix

- `pdf` dengan text layer
- `docx` dokumen naratif
- `pptx` deck presentasi
- `md` dengan form feed
- `txt` panjang tanpa form feed
- `doc` legacy sample
- `ppt` legacy sample
- `xls` sample dengan beberapa sheet atau print region
- extract via public URL
- reject localhost/private URL
- invoice sample
- contract sample
- report sample
- resume sample
- finance sample
- accounting sample
- IT sample
- service tanpa `OPENAI_API_KEY`
- service dengan `OPENAI_API_KEY` valid memakai mock provider
- provider OpenAI timeout atau failure lalu fallback
- verifikasi key tidak muncul di log
- file corrupt
- mismatch antara page output dan page visual sumber untuk format non-native
- file kosong

## Dependency Baseline

Python packages:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings`
- `python-multipart`
- `python-magic`
- `pymupdf`
- `orjson`
- `markdown-it-py`
- `python-docx`
- `python-pptx`
- `xlrd`
- `openai` optional
- `rapidfuzz` optional
- `scikit-learn` optional

System packages:

- `libmagic`
- `libreoffice` optional untuk fallback `doc` dan `ppt`

## Catatan Implementasi

Karena akurasi page bukan requirement utama, implementasi sebaiknya memprioritaskan teks yang stabil dan contract response yang konsisten. Untuk `docx`, `pptx`, dan `xls`, direct text extraction lalu virtual atau rendered pagination sudah cukup selama output tetap berurutan dan mudah dikonsumsi.

Untuk `doc` dan `ppt`, pendekatan paling pragmatis adalah fallback converter atau parser legacy. Jika boundary visual tidak bisa dipertahankan, tetap kembalikan `pages[]` best-effort daripada memaksa fidelity tinggi sejak awal.

Untuk klasifikasi dokumen, mulai dari rules engine dulu. Itu lebih mudah diaudit, murah, dan cukup untuk taxonomy awal seperti `invoice`, `contract`, `report`, `resume`, serta domain seperti `finance`, `accounting`, dan `it`. AI diposisikan sebagai enrichment opsional untuk `summary` dan `tags`, bukan dependency wajib agar service tetap berjalan saat user tidak memberikan key.
