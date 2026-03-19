FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]