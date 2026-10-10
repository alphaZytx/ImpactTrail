FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY src ./src
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY configs ./configs
COPY data ./data
COPY dashboard ./dashboard
COPY scripts ./scripts
COPY .streamlit ./.streamlit

EXPOSE 8000 8501
CMD ["uvicorn", "impacttrail.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
