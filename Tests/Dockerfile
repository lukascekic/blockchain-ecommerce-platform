FROM python:3.9-slim

WORKDIR /tests

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Default command (can be overridden)
CMD ["python", "main.py", "--help"]
