FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN python -m pip install --upgrade pip \
  && python -m pip install -e ".[dev]"

COPY . /app

RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
