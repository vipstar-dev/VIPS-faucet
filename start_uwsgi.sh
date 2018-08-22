#!/bin/bash
. /usr/local/bin/virtualenvwrapper.sh
export WORKON_HOME=~/.virtualenvs
workon VIPS-faucet
uwsgi --ini uwsgi.ini
