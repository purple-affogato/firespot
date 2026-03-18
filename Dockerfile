FROM python:3.13-slim
COPY backend/ app/
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 7860
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:7860"]
