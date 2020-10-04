# Jasmin Web Panel
<p>
	<a href="https://travis-ci.org/101t/jasmin-web-panel"><img src="https://travis-ci.org/101t/jasmin-web-panel.svg?branch=master" alt="travis-ci"></a>
</p>

Jasmin SMS Web Interface for [Jasmin SMS Gateway](https://github.com/jookies/jasmin)

# Jasmin SMPP Panel (Server)
Jasmin SMPP Panel for Jasmin SMS Gateway. Need to setup contact with **skype: helios-sw**

# Technology Stack
- Ubuntu 18.04.3 LTS
- Django
- Apache
- SQlite
- Git

## Installation

***1st Phase***
Complete Things To Do After Install Ubuntu:

```shell
sudo apt update && sudo apt-get upgrade --fix-missing 
sudo apt install build-essential checkinstall
sudo apt install ubuntu-restricted-extras
sudo add-apt-repository ppa:nilarimogard/webupd8
sudo apt update
sudo apt install launchpad-getkeys
sudo launchpad-getkeys 
sudo add-apt-repository ppa:git-core/ppa
sudo apt update
sudo apt install git
sudo git config --global user.name "YourName"
sudo git config --global user.email youremail@gmail.com
wget -qO - http://bit.ly/jasmin-deb-repo | sudo bash
sudo apt-get install python-jasmin
sudo systemctl enable jasmind
sudo systemctl start jasmind

sudo apt list --upgradable
sudo apt upgrade -y
sudo apt -y autoclean 
sudo apt -y clean 
sudo apt update
```

***2nd Phase***
Install Apache+clone repository to /var/www/:

```shell

sudo ufw allow 'nginx'
sudo systemctl enable apache2
sudo systemctl restart apache2
sudo systemctl reload apache2
cd /var/www/


git clone https://github.com/101t/jasmin-web-panel.git
sudo rm -rf html
sudo mv jasmin-web-panel html
cd html
pip install -r requirements.txt
cp Sample.env .env

sudo apt install python-pip
sudo pip install -r requirements.pip
python deploy.py migrate
python deploy.py load_new # to load new user
python deploy.py collectstatic

```

Input your new username and password local_settings.py

```shell
sudo touch local_settings.py
sudo nano local_settings.py
```
```shell
TELNET_HOST = '127.0.0.1'
TELNET_PORT = 8990
TELNET_USERNAME = 'root'
TELNET_PW = 'password'
```
To save local_settings.py press Ctrl+x then press "y" and hit Enter


***Run as development***
```shell
sudo python manage.py runserver [::]:8000

# visit http://localhost:8000/
```


***3rd Phase*** To run on production:
```shell

sudo cp 000-default.conf /etc/apache2/sites-available/000-default.conf
sudo nano /etc/apache2/sites-available/000-default.conf

# Remove all text from 000-default.conf and add below lines on it.

<VirtualHost *:80>
        ServerName example.com
        ServerAlias www.example.com
        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        <Directory /var/www/html>
                <Files django.wsgi>
                        Require all granted
                </Files>
        </Directory>
        WSGIDaemonProcess html python-path=/var/www/html:/var/www/html/env/lib/python2.7/site-packages
        WSGIProcessGroup html
        WSGIScriptAlias / /var/www/html/main/wsgi.py
        Alias /static /var/www/html/static/
</VirtualHost>

# press "Ctrl+x" then press "y" and hit "Enter" to save

sudo a2enmod wsgi
sudo a2ensite 000-default.conf
sudo service apache2 restart
sudo chmod a+w db.sqlite3
cd ..
sudo chown root:root html
sudo service apache2 restart
sudo chown www-data:www-data html
cd html
sudo chown www-data:www-data db.sqlite3 
sudo service apache2 reload
```

## visit
http://localhost/


