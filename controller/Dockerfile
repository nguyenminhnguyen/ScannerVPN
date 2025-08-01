FROM python:3.11-slim
WORKDIR /app

# Copy cả tools.yaml và requirements từ controller directory
COPY controller/requirements.txt controller/tools.yaml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy code ứng dụng từ controller/app
COPY controller/app/ ./app/

# Tạo thư mục /data để chứa SQLite file
RUN mkdir /data && chmod a+rwx /data

ENV DATABASE_URL=sqlite:///./data/scan_results.db

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
