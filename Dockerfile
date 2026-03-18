FROM python:3.13-slim
COPY backend/ /app/
COPY frontend/dist /app/static
COPY ml/data/gridmet.csv /app/gridmet.csv
COPY ml/data/land_cover.csv /app/land_cover.csv
COPY ml/model2.ubj /app/model2.ubj
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 7860
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:7860"]
