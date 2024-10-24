#!/bin/bash

install_req () {
  pip install -r requirements.txt
}

install_redis() {
    echo "Installing Redis..."
    sudo apt-get update
    sudo apt-get install -y redis-server

    sudo systemctl start redis
    sudo systemctl enable redis
    echo "Redis installed and started."
}

check_redis() {
    if pgrep redis-server > /dev/null; then
        echo "Redis is already running."
    else
        echo "Redis is not running."
        install_redis
    fi
}

start_celery() {
    echo "Starting Celery worker..."
    celery -A tasks worker -l info -P gevent > celery.log 2>&1 &
    echo "Celery worker started."
}

start_flower() {
    echo "Starting Flower..."
    celery -A tasks flower > flower.log 2>&1 &
    echo "Flower started."
}

if ! command -v redis-server &> /dev/null; then
    echo "Redis is not installed. Installing now..."
    install_redis
else
    echo "Redis is installed."
    check_redis
fi

install_req
start_celery
start_flower

echo "Setup complete. Celery and Flower are running."
