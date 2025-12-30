#!/bin/bash
# Railway startup script for Guardian Route

# Use Railway's PORT or default to 8501
PORT=${PORT:-8501}

echo "Starting Streamlit on port $PORT..."

streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
