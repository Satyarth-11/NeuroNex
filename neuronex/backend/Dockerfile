FROM python:3.11-slim

WORKDIR /app

# Install system deps for pdfplumber and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy NER model (en_core_web_sm ~12MB)
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY app/ ./app/

# Create data directory for SQLite
RUN mkdir -p /app/data/synthetic

# Copy synthetic data (or generate during build)
COPY data/synthetic/ ./data/synthetic/
RUN python data/synthetic/generate_synthetic_data.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
