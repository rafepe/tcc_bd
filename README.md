git clone https://github.com/rafepe/tcc_bd.git
cd tcc_bd
python -m venv venv
venv\Scripts\activate
pip install django
pip install -r requirements.txt
django-admin startproject prestaconta
cd prestaconta
python manage.py startapp contrapartida
cd ..
git restore .
cd prestaconta
python manage.py makemigrations
python manage.py migrate
