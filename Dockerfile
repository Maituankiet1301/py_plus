FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Cài deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn

# Copy mã nguồn
COPY . .
# Fix xuống dòng CRLF của boot.sh và cấp quyền chạy (chạy trong container)
RUN sed -i 's/\r$//' boot.sh && chmod +x boot.sh

ENV FLASK_APP=microblog.py
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
