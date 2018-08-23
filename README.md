# VIPS-faucet

## Installation

(1) prepare

nginx + python-dev
```
sudo apt-get install nginx
sudo apt-get install python-dev
```

(optional)virtualenvwapper
```
sudo pip install virtualenvwrapper
vi ~/.bashrc
----
#add this
source /usr/local/bin/virtualenvwrapper.sh
export WORKON_HOME=~/.virtualenvs
----
source ~/.bashrc
mkvirtualenv VIPS-faucet
workon VIPS-faucet
```

clone this repo.
```
git clone https://github.com/vipstar-dev/VIPS-faucet
cd VIPS-faucet
pip install -r requirements.txt
```

(2) edit config.py
```
cp VIPSFaucet/config.py-sample VIPSFaucet/config.py
vi VIPSFaucet/config.py
```
edit:
* SECRET_KEY
* VIPS_RPC_USER
* VIPS_RPC_PASSWORD
* RECAPTCHA_PUBLIC_KEY
* RECAPTCHA_PRIVATE_KEY

(3) create db

```
python initdb.py
```

(4) starat flask app

```
./start.sh
   or
./start_uwsgi.sh (this require virtualenvwapper/nginx settings)
```

(5) access http://localhost:5000/ (for start.sh)

## systemd

(1) edit misc/VIPS-faucet.service  
(2) sudo cp misc/VIPS-faucet.service /etc/systemd/system/  
(3) sudo systemctl daemon-reload  
(4) sudo systemctl start VIPS-faucet.service

## nginx

vi /etc/nginx/site-enabled/default
```
service {
      :
    location ~ ^/faucet/(.*)$ {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/VIPS-faucet.sock;
        uwsgi_param SCRIPT_NAME /faucet;
        uwsgi_param PATH_INFO /$1;
    }
}
```

access http://localhost/faucet/
