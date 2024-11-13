import logging

from kombu import Producer

from celery_app import app, logging_exchange


class RabbitMQLogHandler(logging.Handler):
    def __init__(self, routing_key: str):
        super().__init__()
        self.routing_key = routing_key

    def emit(self, record):
        message = self.format(record)
        try:
            with app.connection() as connection:
                with connection.channel() as channel:
                    producer = Producer(channel, exchange=logging_exchange,
                                        routing_key=self.routing_key)
                    producer.publish(
                        {'log': message, 'level': record.levelname},
                        serializer='json'
                    )
        except Exception as e:
            print(f'Failed to send log to RabbitMQ: {e}')


info_handler = RabbitMQLogHandler('log.info')
warning_handler = RabbitMQLogHandler('log.warning')
error_handler = RabbitMQLogHandler('log.error')

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
info_handler.setFormatter(formatter)
warning_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

info_handler.setLevel(logging.INFO)
warning_handler.setLevel(logging.WARNING)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(info_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)
