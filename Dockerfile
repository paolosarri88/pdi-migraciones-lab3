FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PDI_DATA_DIR=/tmp/pdi-data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home portal
COPY app.py persistence.py workflow.py document_rules.py document_ai.py portal_v4.py portal_v5.py portal_v6.py portal_v7.py demo_characters.py ./
COPY static ./static
COPY prompts ./prompts
USER portal
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 4 --timeout 120 app:app"]
