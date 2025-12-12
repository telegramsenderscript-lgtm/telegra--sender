# Base Python 3.12 slim
FROM python:3.12-slim

# Diretório da app
WORKDIR /app

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY . .

# Usa a porta que o Render define
ENV PORT=10000
EXPOSE $PORT

# Inicia a app com gunicorn
CMD sh -c "gunicorn app:app -b 0.0.0.0:$PORT"
