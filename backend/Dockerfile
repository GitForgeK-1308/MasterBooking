FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv

RUN uv sync --frozen --no-dev

COPY . .

CMD ["uv", "run", "--frozen", "--no-dev", "fastapi", "run", "src/main.py", "--host", "0.0.0.0"]