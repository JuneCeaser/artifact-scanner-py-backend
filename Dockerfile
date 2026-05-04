FROM python:3.10-slim

# Install system dependencies for OpenCV/PIL
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--timeout", "120", "--workers", "1", "server:app"]
```

### `.gitignore` (create this new file):
```
__pycache__/
*.pyc
.env
*.log
.DS_Store