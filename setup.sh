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

install_rabbitmq() {
    echo "Installing RabbitMQ..."
    sudo apt-get update
    sudo apt-get install -y rabbitmq-server

    sudo systemctl start rabbitmq-server
    sudo systemctl enable rabbitmq-server
    echo "RabbitMQ installed and started."

    echo "Enabling RabbitMQ Management Plugin..."
    sudo rabbitmq-plugins enable rabbitmq_management
    echo "RabbitMQ Management Plugin enabled."
}

check_rabbitmq() {
    if pgrep rabbitmq-server > /dev/null; then
        echo "RabbitMQ is already running."
    else
        echo "RabbitMQ is not running."
        install_rabbitmq
    fi
}

start_celery() {
    echo "Starting Celery worker..."
    pkill -f 'celery'
    celery -A celery_app worker --loglevel=info > celery.log 2>&1 &
    echo "Celery worker started."
}

start_flower() {
    echo "Starting Flower..."
    celery -A celery_app flower > flower.log 2>&1 &
    echo "Flower started."
}

if ! command -v redis-server &> /dev/null; then
    echo "Redis is not installed. Installing now..."
    install_redis
else
    echo "Redis is installed."
    check_redis
fi

if ! command -v rabbitmq-server &> /dev/null; then
    echo "RabbitMQ is not installed. Installing now..."
    install_rabbitmq
else
    echo "RabbitMQ is installed."
    check_rabbitmq
fi

install_req
start_celery
start_flower

echo "Setup complete. Celery, Flower, Redis, and RabbitMQ are running."
echo "RabbitMQ Web GUI is available at http://localhost:15672 (default login: guest/guest)"
