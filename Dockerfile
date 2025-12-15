# Gunakan image Python yang ringan (slim)
FROM python:3.11-slim

# Set folder kerja di dalam container
WORKDIR /app

# Salin file requirements.txt terlebih dahulu (untuk optimasi cache)
COPY requirements.txt .

# Instal library yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi (main.py, dll)
COPY . .

# Ekspos port 8000 (port default uvicorn)
EXPOSE 8000

# Jalankan aplikasi
CMD ["python", "main.py"]