FROM python:3.13-slim

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:7860"]
