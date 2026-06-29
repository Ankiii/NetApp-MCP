FROM python:3.11-slim-bookworm
WORKDIR /app
COPY requirements.txt .
# 1. Patch OS-level vulnerabilities
RUN apt-get update && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
# 2. Upgrade pip and explicitly install the secure version of wheel
RUN pip install --upgrade pip "wheel>=0.46.2"
# 3. Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 4. Copy application code
COPY agent.py .
COPY server.py .
CMD ["python", "-u", "agent.py"]