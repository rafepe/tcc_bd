# Usando a imagem Python slim
FROM python:3.10-slim

# Instalar pacotes necessários para configurar o idioma
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    locales \
    && echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen pt_BR.UTF-8 \
    && update-locale LANG=pt_BR.UTF-8 LC_ALL=pt_BR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Definir as variáveis de ambiente para localidade
ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8

# Definir o diretório de trabalho
WORKDIR /tcc_bd

# Copiar o arquivo requirements e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor a porta
EXPOSE 8080

# Comando para iniciar o Django
CMD ["python", "prestaconta/manage.py", "runserver", "0.0.0.0:8080"]
