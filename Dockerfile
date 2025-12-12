# Usando Python 3.12 oficial
FROM python:3.12-slim

# Diretório da app
WORKDIR /app

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da app
COPY . .

# Expõe a porta do Render
EXPOSE 10000

# Comando para iniciar a app
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
