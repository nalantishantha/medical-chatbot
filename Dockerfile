FROM python:3.10-slim-buster

WORKDIR /app

# Copy requirements first for better caching
COPY medical-chatbot/requirements.txt ./medical-chatbot/

# Install dependencies
RUN pip install --no-cache-dir -r medical-chatbot/requirements.txt

# Copy the medical-chatbot folder
COPY medical-chatbot/ ./medical-chatbot/

# Copy the frontend folder
COPY frontend/ ./frontend/

# Set working directory to where app.py is
WORKDIR /app/medical-chatbot

# Expose port
EXPOSE 5000

# Set environment variable
ENV PORT=5000

# Run the application
CMD ["python3", "app.py"]