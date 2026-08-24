FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

ENV PORT=8765
ENV WATERMARKS_SERVER_HOST=0.0.0.0

EXPOSE 8765

CMD ["python", "service/scripts/server.py"]
