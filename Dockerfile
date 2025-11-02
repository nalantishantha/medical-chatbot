FROM python:3.10-slim-buster

WORKDIR /app

# Copy requirements first for better caching
COPY medical-chatbot/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the medical-chatbot source code
COPY medical-chatbot/ .

# Copy the frontend folder
COPY frontend/ ./frontend/

# Expose port
EXPOSE 5000

# Set environment variable
ENV PORT=5000

# Run the application
CMD ["python3", "app.py"]