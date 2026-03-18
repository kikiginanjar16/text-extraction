# Product Spec

## Ringkasan

Layanan ini menerima satu file dokumen, mengekstrak teks, lalu mengembalikan hasil dalam bentuk array of page-like chunk agar downstream service bisa mengonsumsi konten secara konsisten, meskipun pagination sumber tidak selalu presisi.

## Goal

- Menyediakan satu endpoint HTTP untuk upload file dan ekstraksi teks
- Menormalkan berbagai format dokumen ke satu response contract
- Menjaga urutan page output secara eksplisit
- Menambahkan klasifikasi otomatis untuk mengenali dokumen ini termasuk jenis apa
- Menyeimbangkan coverage format dengan akurasi pagination yang bersifat best-effort
- Memungkinkan ekspansi ke OCR, peningkatan fidelity pagination, dan asynchronous job di fase berikutnya

## Supported Formats

- `pdf`
- `docx`
- `pptx`
- `md`
- `txt`
- `doc`
- `ppt`
- `xls`

## Output Principle

Response utama harus mengandung `pages`, yaitu array yang urut dari item pertama sampai terakhir.

Untuk format yang tidak punya page boundary native yang stabil, `pages` diperlakukan sebagai best-effort segmentation. Artinya:

- `page` adalah nomor urut pada response, bukan janji identik dengan nomor halaman visual dari aplikasi asal
- `page_count` adalah jumlah item pada `pages`, bukan selalu jumlah halaman asli dokumen
- prioritas utama adalah urutan hasil ekstraksi yang stabil dan teks tetap terbaca

Setiap item page minimal berisi:

- `page`: nomor urut output, mulai dari `1`
- `text`: teks hasil ekstraksi pada item tersebut

Metadata tambahan yang direkomendasikan:

- `char_count`
- `is_empty`
- `page_kind`

Metadata level dokumen yang direkomendasikan:

- `document_category`
- `document_domain`
- `summary`
- `tags`
- `classification`
- `enrichment`

## Definisi "Page"

Karena tidak semua format punya konsep halaman yang sama, layanan memakai aturan berikut:

- `pdf`: halaman native dari file PDF jika tersedia
- `md`, `txt`: tidak punya halaman native, sehingga dipakai virtual pagination yang deterministik
- `docx`, `doc`: hasil segmentasi best-effort dari teks dokumen; boleh berasal dari render, section split, atau virtual pagination
- `pptx`, `ppt`: idealnya per slide atau hasil render presentasi; jika tidak tersedia, boleh fallback ke segmentasi best-effort
- `xls`: hasil segmentasi best-effort dari sheet, print area, atau teks tabular yang diekstrak

Nilai `page_kind` yang direkomendasikan:

- `native`: benar-benar berasal dari page boundary asli
- `rendered`: berasal dari hasil render atau representasi visual lain
- `virtual`: berasal dari chunk sintetis yang dibuat service

## Aturan Pagination untuk `md` dan `txt`

Format `md` dan `txt` tidak memiliki page boundary bawaan. Spec ini menetapkan:

- Jika file mengandung form feed `\f`, maka `\f` dipakai sebagai page break
- Jika tidak ada `\f`, sistem membuat virtual page berdasarkan batas baris atau karakter yang konsisten
- Default yang direkomendasikan:
  - `max_lines_per_page = 50`
  - `max_chars_per_page = 3500`

`page_kind` untuk hasil seperti ini bernilai `virtual`.

## Automatic Document Classification, Domain Detection, Tagging, and Optional AI Summary

Setelah teks berhasil diekstrak, sistem dapat mengklasifikasikan isi dokumen secara otomatis.

Output klasifikasi berada di level dokumen, bukan level halaman:

- `document_category`: label utama dokumen
- `document_domain`: label domain atau fungsi bisnis utama dokumen
- `summary`: ringkasan singkat isi dokumen
- `tags`: array tag singkat yang membantu filtering dan pencarian
- `classification`: metadata classifier seperti confidence dan method
- `enrichment`: metadata apakah summary dan tags diperkaya oleh AI atau tidak

Kategori awal yang direkomendasikan:

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

Domain awal yang direkomendasikan:

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

Aturan desain:

- `document_category` adalah single primary label untuk bentuk dokumen
- `document_domain` adalah single primary label untuk area bisnis atau fungsi kerja
- `summary` boleh `null` jika AI tidak dipakai atau summary tidak berhasil dibuat
- `tags` boleh multi-label
- Jika confidence rendah, sistem harus mengembalikan `document_category = unknown` dan/atau `document_domain = unknown`
- Tag sebaiknya berbentuk lowercase snake_case atau lowercase kebab-case yang konsisten

Sumber sinyal klasifikasi yang direkomendasikan:

- nama file
- extension dan MIME type
- teks gabungan dari seluruh halaman atau halaman awal
- nama departemen, unit kerja, atau istilah domain seperti finance, accounting, IT, HR, legal
- keyword dominan, heading, dan pola domain

## Optional OpenAI Enrichment

Layanan dapat secara opsional memakai OpenAI untuk memperbaiki kualitas `summary` dan `tags`.

Aturannya:

- jika environment server mengandung `OPENAI_API_KEY`, sistem boleh memanggil OpenAI
- jika `OPENAI_API_KEY` tidak diisi, sistem dianggap berjalan tanpa AI
- tanpa AI, `tags` tetap dihasilkan oleh rules engine atau heuristic lokal
- tanpa AI, `summary` boleh `null`
- jika pemanggilan OpenAI gagal, timeout, atau respons tidak valid, ekstraksi utama tidak boleh gagal; sistem harus fallback ke hasil non-AI
- `OPENAI_API_KEY` harus diperlakukan sebagai secret, tidak disimpan permanen, dan tidak boleh masuk ke log

## Functional Requirements

1. Sistem menerima upload satu file per request
2. Sistem menerima URL dokumen pada endpoint terpisah untuk server-side fetch
3. Sistem melakukan validasi extension dan MIME type
4. Sistem menyimpan file ke temporary storage selama proses ekstraksi
5. Sistem memilih extractor berdasarkan tipe file
6. Sistem mengembalikan response JSON yang konsisten
7. Sistem tetap mengembalikan halaman kosong jika `include_empty_pages=true`
8. Sistem mendukung `pdf`, `docx`, `pptx`, `md`, `txt`, `doc`, `ppt`, dan `xls`
9. Sistem boleh mengembalikan pagination best-effort untuk format yang tidak punya page boundary stabil
10. Sistem menyediakan fallback error yang jelas untuk file corrupt, password-protected, atau unsupported
11. Endpoint URL harus menolak scheme non-HTTP(S), localhost, dan private address
12. Sistem mengembalikan `document_category`, `document_domain`, `tags`, dan metadata `enrichment` setelah ekstraksi berhasil
13. Sistem mengembalikan `summary` jika berhasil dibuat; jika tidak, `summary` boleh `null`
14. Jika server memiliki `OPENAI_API_KEY`, sistem boleh memakai OpenAI untuk memperkaya `summary` dan `tags`
15. Jika server tidak memiliki `OPENAI_API_KEY`, sistem harus berjalan penuh tanpa AI
16. Sistem mengembalikan `unknown` jika isi dokumen tidak bisa diklasifikasikan dengan confidence memadai

## Non-Functional Requirements

- Response konsisten antar format
- Urutan item `pages` tidak boleh berubah untuk hasil extractor yang sama
- Proses harus idempotent untuk file yang sama
- Pagination untuk format non-native boleh approximate selama urutan dan konten tetap stabil
- Hasil klasifikasi harus stabil untuk input yang sama pada classifier version yang sama
- Logging harus punya `request_id` dan `file_type`
- Secret seperti `OPENAI_API_KEY` tidak boleh dicatat ke log atau disimpan permanen
- Temporary file harus dibersihkan setelah request selesai

## Out of Scope

- Rekonstruksi layout visual penuh
- Kesesuaian 1:1 dengan nomor halaman di Microsoft Office, LibreOffice, atau viewer lain
- Ekstraksi tabel terstruktur ke format sel
- OCR akurasi tinggi untuk semua bahasa pada fase awal
- Batch upload multi-file dalam satu request
- Dukungan file terenkripsi yang memerlukan password
- Klasifikasi semantik yang sangat spesifik per industri pada fase awal
- Rekonstruksi print layout spreadsheet secara presisi tinggi

## Batasan Teknis yang Direkomendasikan

- Maksimum ukuran file: `50 MB`
- Timeout request sinkron: `60 detik`
- Maksimum jumlah item `pages` yang diproses sinkron: `500`

Untuk file yang melampaui batas ini, fase berikutnya dapat memakai async job queue.
