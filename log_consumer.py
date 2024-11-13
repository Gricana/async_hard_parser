import logging

from kombu import Connection, Queue
from kombu.mixins import ConsumerMixin

logger = logging.getLogger('rabbitmq_logger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class LogConsumer(ConsumerMixin):
    def __init__(self, connection, queue_name):
        self.connection = connection
        self.queue = Queue(queue_name, durable=True)

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(
                queues=self.queue,
                accept=['application/json'],
                callbacks=[self.handle_log]
            )
        ]

    def handle_log(self, body, message):
        print(f"Received message: {body}")
        log_level = body.get('level')
        log_message = body.get('log')
        if log_level == 'INFO':
            logger.info(log_message)
        elif log_level == 'WARNING':
            logger.warning(log_message)
        elif log_level == 'ERROR':
            logger.error(log_message)

        message.ack()


def start_listening():
    with Connection('amqp://admin:masHristosson76@localhost//') as conn:
        log_consumer = LogConsumer(conn, 'log.info')
        log_consumer1 = LogConsumer(conn, 'log.warning')
        log_consumer2 = LogConsumer(conn, 'log.error')
        log_consumer.run()
        log_consumer1.run()
        log_consumer2.run()


if __name__ == "__main__":
    start_listening()
