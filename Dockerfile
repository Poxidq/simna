FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ backend/
COPY frontend/ frontend/
COPY .streamlit/ .streamlit/

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV USE_MOCK_TRANSLATION=True
ENV DATABASE_URL=sqlite:///./data/notes.db

# Expose ports for backend and frontend
EXPOSE 8000 8501

# Create startup script
RUN echo '#!/bin/bash\n\
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \n\
sleep 5 \n\
streamlit run frontend/app.py\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"] 