FROM python:3.11-slim

# Tesseract is a system package, not a Python one — this is the part
# a plain "pip install" can never give you, on Render or anywhere else.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Render sets $PORT at runtime; gunicorn binds to whatever it's given.
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5000}"]
