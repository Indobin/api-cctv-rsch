# ----------------------------------------------------------------------
# STAGE 1: BUILD
# Menginstal dependensi dan membangun artefak (dengan alat build)
# ----------------------------------------------------------------------
FROM python:3.11-slim as builder

# Instal dependensi build (gcc)
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Instal paket Python
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------
# STAGE 2: RUNTIME
# Citra akhir yang hanya berisi aplikasi dan dependensi runtime
# ----------------------------------------------------------------------
FROM python:3.11-slim as runtime

WORKDIR /app

# Salin dependensi Python yang sudah diinstal dari stage 'builder'
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/

# Instal paket runtime yang diperlukan
# Perhatikan: postgresql-client dan iputils-ping tetap ada jika memang dibutuhkan saat runtime
RUN apt-get update && apt-get install -y \
    postgresql-client \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# PENTING: Ganti ke pengguna non-root
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Salin kode aplikasi (memastikan .dockerignore digunakan)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]