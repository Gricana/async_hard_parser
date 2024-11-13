from celery import Celery
from kombu import Exchange, Queue

from config import RABBITMQ_URL

app = Celery('super_hard_parser', broker=RABBITMQ_URL,
             backend='redis://localhost:6379/0')

fetch_exchange = Exchange('fetch', type='topic')
prices_exchange = Exchange('prices', type='topic')
combine_exchange = Exchange('combine', type='topic')
logging_exchange = Exchange('logs', type='topic')
save_exchange = Exchange('save', type='direct')

app.conf.task_queues = [
    Queue('fetch.products', exchange=fetch_exchange,
          routing_key='fetch.products.#'),
    Queue('fetch.prices', exchange=prices_exchange,
          routing_key='fetch.prices.#'),
    Queue('combine.products', exchange=combine_exchange,
          routing_key='combine.products.#'),
    Queue('save.products', exchange=save_exchange, routing_key='save.products')
]

app.conf.task_queues += [
    Queue('log.info', exchange=logging_exchange, routing_key='log.info'),
    Queue('log.warning', exchange=logging_exchange, routing_key='log.warning'),
    Queue('log.error', exchange=logging_exchange, routing_key='log.error')
]

app.conf.task_routes = {
    'tasks.fetch_products_task': {
        'queue': 'fetch.products',
        'exchange': fetch_exchange,
        'routing_key': 'fetch.products.{city_id}.{category_id}'
    },
    'tasks.fetch_prices_task': {
        'queue': 'fetch.prices',
        'exchange': prices_exchange,
        'routing_key': 'fetch.prices.{city_id}.{category_id}'
    },
    'tasks.combine_products_and_prices_task': {
        'queue': 'combine.products',
        'exchange': combine_exchange,
        'routing_key': 'combine.products.{city_id}.{category_id}'
    },
    'tasks.save_products': {
        'queue': 'save.products',
        'exchange': save_exchange,
        'routing_key': 'save.products'
    }
}

app.conf.update(
    imports=('tasks',),
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json'
)
