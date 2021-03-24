# document_control
mkdir /var/www/document_control 
cd /var/www/document_control
sudo update-alternatives --config python3
python3.6 -m venv venv
. venv/bin/activate
pip install flask
pip install flask-mysqldb
set FLASK_APP=main.py
set FLASK_DEBUG=1
sudo apt install mysql-server
sudo mysql_secure_installation

MYSQL:
sudo mysql
>CREATE DATABASE document_control;
>USE document_control;
>CREATE USER 'user'@'localhost' IDENTIFIED BY 'Password123#@!';
>GRANT ALL PRIVILEGES ON *.* TO 'user'@'localhost';
>FLUSH PRIVILEGES;
>source db_sql;
>exit;

flask run