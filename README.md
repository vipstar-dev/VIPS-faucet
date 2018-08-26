# VIPS-faucet

## 使用方法

(1) 準備

パッケージのインストール
```
sudo apt-get install nginx
sudo apt-get install python-dev
sudo apt-get install python-pip
```

(オプション)virtualenvwapperのインストール
```
sudo pip install virtualenvwrapper
vi ~/.bashrc
----
#以下を追加してください
source /usr/local/bin/virtualenvwrapper.sh
export WORKON_HOME=~/.virtualenvs
----
source ~/.bashrc
mkvirtualenv VIPS-faucet
workon VIPS-faucet
```

このリポジトリをクローンし、pythonパッケージを準備します。
```
git clone https://github.com/vipstar-dev/VIPS-faucet
cd VIPS-faucet
pip install -r requirements.txt
```

(2) config.pyの編集
```
cp VIPSFaucet/config.py-sample VIPSFaucet/config.py
vi VIPSFaucet/config.py
```
以下を編集してください:
* SECRET_KEY(下記を参照)
* VIPS_RPC_USER(VIPSTARCOIN.confに設定したものを書き込みましょう)
* VIPS_RPC_PASSWORD(USERと同様)
* RECAPTCHA_PUBLIC_KEY([ここ](https://www.google.com/recaptcha/intro/v3beta.html)から取得してください。取得方法は適当にggりましょう)
* RECAPTCHA_PRIVATE_KEY(PUBLIC_KEYと同様)

※SECRET_KEYの生成法
```
pytohon
>>> import os
>>> os.urandom(24)
'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
```

(3) データベースの生成

```
python initdb.py
```

(4) flaskの起動

```
./start.sh
   or
./start_uwsgi.sh (これを実行する場合、virtualenvwapperとnginxの設定が必要です。)
```

(5) http://localhost:5000/ にアクセスしましょう(start.shを実行した場合)

## systemd

(1) `vi misc/VIPS-faucet.service`などで編集しましょう。基本usernameを自分のものに変更するだけです。

(2) `sudo cp misc/VIPS-faucet.service /etc/systemd/system/`を実行し、コピーします。

(3) `sudo systemctl daemon-reload`を実行し、daemonをリロードしましょう。

(4) 最後に、`sudo systemctl start VIPS-faucet.service`を実行すればバックグラウンド化出来ます。 

## nginx

`sudo vi /etc/nginx/site-enabled/default`を実行し、以下を追記します。
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

http://localhost/faucet/ にアクセスしましょう。
