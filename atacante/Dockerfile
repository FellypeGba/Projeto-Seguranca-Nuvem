FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir requests aiohttp

COPY . /app/

ENTRYPOINT ["python", "atacar.py"]