# --------------------------
# 1. Base image
# --------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# --------------------------
# 2. System dependencies
# --------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    git \
    && apt-get clean

# --------------------------
# 3. Install Python packages
# --------------------------
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# --------------------------
# 4. Copy project
# --------------------------
COPY . .

RUN mkdir -p /app/static_cdn

# Create database directory and set permissions
RUN mkdir -p /app/db_data && touch /app/db_data/db.sqlite3 && chmod 666 /app/db_data/db.sqlite3

# --------------------------
# 5. Expose port
# --------------------------
EXPOSE 8000

# --------------------------
# 6. Add entrypoint
# --------------------------
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
