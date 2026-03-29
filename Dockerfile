FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV DATABASE_URL=sqlite:////tmp/smart_ticket_classifier.db

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY docs ./docs
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 7860

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
