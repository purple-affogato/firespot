FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r backend/requirements.txt

COPY . .

EXPOSE 7860

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:7860"]
