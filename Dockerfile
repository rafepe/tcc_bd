# Usando a imagem do Python slim
FROM python:3.10-slim

# Instalando as dependências para localidade
RUN apt-get update && apt-get install -y locales && \
    locale-gen pt_BR.UTF-8

# Definindo a localidade
ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8

# Define o diretório de trabalho
WORKDIR /tcc_bd

# Copia os requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código para o diretório de trabalho
COPY . .

# Expõe a porta 8080 para acesso externo
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["python", "prestaconta/manage.py", "runserver", "0.0.0.0:8080"]
