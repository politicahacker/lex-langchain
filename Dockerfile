# Dockerfile
FROM python:3.8

# Instale as dependências necessárias para OpenBLAS e pip (se precisar)
RUN apt-get update && apt-get install -y \
    libopenblas-dev trickle ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY app/requirements.txt .
RUN trickle -d 20480 pip install --no-cache-dir -r requirements.txt

# Instale o pacote Python com os argumentos CMake
RUN CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python

# Copy your application code
WORKDIR /app
ENV FLASK_APP=app
CMD ["gunicorn", "-w 1", "-k eventlet", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]