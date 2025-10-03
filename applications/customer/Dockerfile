FROM python:3.9-slim

WORKDIR /app

# Copy shared models and config first
COPY ../configuration.py ../models.py ./

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=application.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "application.py"]
