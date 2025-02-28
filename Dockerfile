# Usando a imagem do Python slim
FROM python:3.10-slim
# Define o diretório de trabalho
WORKDIR /app
# Copia os requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copia o resto do código para o diretório de trabalho
COPY . .
# Expõe a porta 8080 para acesso externo
EXPOSE 8080
# Comando para iniciar a aplicação
CMD ["python", "manage.py", "runserver","0.0.0.0:8080"]