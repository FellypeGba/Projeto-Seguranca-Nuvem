FROM python:3.9-slim

WORKDIR /app

RUN pip install requests flask

COPY . /app/

CMD ["python", "app_painel.py"]