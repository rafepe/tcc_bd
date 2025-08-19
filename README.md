# Projeto TCC_BD

Este repositório contém o projeto **Prestaconta**, desenvolvido em Django como parte do Trabalho de Conclusão de Curso (TCC).

## 📦 Pré-requisitos

- [Python 3.x](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- Virtualenv (opcional, mas recomendado)

---

## ⚙️ Instalação e Configuração

### 1. Clone o repositório
```bash
git clone https://github.com/rafepe/tcc_bd.git
cd tcc_bd
```

### 2. Crie e ative o ambiente virtual
No Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

No Linux/MacOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install django
pip install -r requirements.txt
```

### 4. Crie o projeto Django
```bash
django-admin startproject prestaconta
cd prestaconta
```

### 5. Crie o aplicativo principal
```bash
python manage.py startapp contrapartida
```

### 6. Restaure alterações (se necessário)
```bash
cd ..
git restore .
cd prestaconta
```

### 7. Migrações do banco de dados
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## ▶️ Executando o servidor

Dentro da pasta `prestaconta`:
```bash
python manage.py runserver
```

O sistema ficará disponível em:  
👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 📂 Estrutura esperada do projeto

```
tcc_bd/
│── prestaconta/        # Projeto Django principal
│   ├── contrapartida/  # Aplicativo principal
│   ├── manage.py
│   └── ...
│── requirements.txt
│── README.md
└── venv/               # Ambiente virtual (ignorado no git)
```

---

## 📝 Observações

- Em produção, configure variáveis de ambiente (`DEBUG`, `SECRET_KEY`, `DATABASES`).
- Gere um superusuário para acessar o Django Admin:
  ```bash
  python manage.py createsuperuser
  ```

---
