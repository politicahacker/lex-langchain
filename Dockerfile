# Dockerfile
FROM python:3.8

# Copy requirements file and install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY app /app
WORKDIR /app
ENV FLASK_APP=app
CMD [ "python3", "app.py"]