FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.org/simple

WORKDIR /app
RUN pip install --upgrade pip setuptools wheel
COPY pyproject.toml ./
RUN pip install --no-cache-dir --no-build-isolation -e .

COPY app ./app
EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
