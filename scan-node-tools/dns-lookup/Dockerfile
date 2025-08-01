FROM python:3.11-slim
WORKDIR /app

# Chỉ cài thư viện cần thiết
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy code và user không root
COPY dns_lookup.py ./
USER 1000:1000

ENTRYPOINT ["python", "dns_lookup.py"]
