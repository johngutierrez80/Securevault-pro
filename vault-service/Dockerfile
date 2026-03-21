FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# slowapi/starlette expects an env file path and fails hard if it does not exist.
RUN touch .env

RUN useradd -m appuser

COPY app/ ./app/

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', 8002)); s.close()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]