FROM python:3.9-slim

WORKDIR /app

# Copy shared configuration and models
COPY applications/configuration.py applications/models.py ./

# Copy blockchain folder
COPY blockchain ./blockchain

# Copy courier application
COPY applications/courier/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY applications/courier/application.py .

ENV FLASK_APP=application.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "application.py"]
