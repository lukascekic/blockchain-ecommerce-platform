FROM python:3.9-slim

WORKDIR /app

# Copy shared configuration and models
COPY applications/configuration.py applications/models.py ./

# Copy owner application
COPY applications/owner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY applications/owner/application.py .

ENV FLASK_APP=application.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "application.py"]
