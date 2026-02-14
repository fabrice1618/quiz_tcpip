FROM python:3.12-slim

RUN pip install --no-cache-dir flask gunicorn

WORKDIR /app

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "--timeout", "120", "app:app"]
