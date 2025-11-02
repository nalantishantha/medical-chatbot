FROM python:3.10-slim-buster

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose port
EXPOSE 5000

# Set environment variable
ENV PORT=5000

# Run the application
CMD ["python3", "app.py"]