FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn

COPY . .
# chuyển CRLF -> LF và cấp quyền chạy cho boot.sh
RUN sed -i 's/\r$//' boot.sh && chmod +x boot.sh

ENV FLASK_APP=microblog.py
EXPOSE 5000
ENTRYPOINT ["sh","./boot.sh"]
