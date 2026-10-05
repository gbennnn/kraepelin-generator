# Kraepelin Test Generator

Web app sederhana untuk membuat angka latihan tes Kraepelin menggunakan:

- Python
- Flask
- Bootstrap 5 CDN
- JavaScript
- ReportLab

## Fitur

- Generate angka random 0–9
- Custom range, misalnya 5–9
- Preset range 0–9, 1–9, 5–9, dan 0–5
- Jumlah baris custom
- Jumlah kolom custom
- Preview angka
- Pengaturan font
- Pengaturan margin
- Pengaturan jarak baris
- Pengaturan jarak kolom
- A4 Portrait / Landscape
- Download PDF
- PDF dibuat langsung oleh server menggunakan ReportLab

## Instalasi

Pastikan Python 3.10+ sudah terpasang.

### 1. Masuk ke folder

```bash
cd kraepelin-generator
```

### 2. Buat virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependency

```bash
pip install -r requirements.txt
```

### 4. Jalankan

```bash
python app.py
```

Kemudian buka:

http://127.0.0.1:5000

## Catatan

PDF menggunakan ukuran A4 dari ReportLab. Jika grid terlalu besar untuk halaman,
aplikasi akan mengurangi spacing dan/atau font agar tetap muat.

Versi ini menghasilkan satu halaman PDF per generate. Fitur lanjutan seperti timer,
beberapa halaman, paket latihan, answer sheet, scoring, dan penyimpanan konfigurasi
dapat ditambahkan kemudian.
