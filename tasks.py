import asyncio
from dataclasses import asdict
from typing import List, Dict, Any, Tuple

from celery import Celery, shared_task

from importer import save_all
from parser import Product
from parser import fetch_products, fetch_prices, combine_product_and_prices

app = Celery('tasks',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')


@app.task
def save_products(products: List[Dict], filename: str):
    """
    Celery task to save products into a file asynchronously.

    :param products: List of product dictionaries.
    :param filename: Name of the file to save products.
    """
    asyncio.run(save_all(products, filename))


@shared_task
def fetch_products_task(category_id: str, city_id: str, min_goods: int) \
        -> List[Dict]:
    products = asyncio.run(fetch_products(category_id, city_id, min_goods))

    products = [product for product in products if isinstance(product, Product)]

    return [asdict(product) for product in products]


@shared_task
def fetch_prices_task(products: List[Dict]) \
        -> Tuple[List[Dict], Dict[int, Dict[str, int]]]:
    """
    Celery task to fetch prices for a list of products.

    :param products: List of Product objects.
    :return: Tuple with the original products and dictionary with prices for each product.
    """
    product_ids = [product.get('id') for product in products]

    prices = asyncio.run(fetch_prices(product_ids))

    return products, prices


@shared_task
def combine_products_and_prices_task(
        data: Tuple[List[Dict], Dict[int, Dict[str, int]]]) \
        -> List[Dict[str, Any]]:
    """
    Celery task to combine product information with prices.

    :param data: Tuple containing products and prices.
    :return: List of products with updated prices as Product dict.
    """
    products, prices = data
    products = [Product(**prod) for prod in products]
    products = asyncio.run(combine_product_and_prices(products, prices))
    return [asdict(product) for product in products]


def get_products_with_prices(category_id: str, city_id: str, min_goods: int):
    """
    This function sets up and triggers a Celery task chain to:
    1. Fetch products based on category and city.
    2. Fetch prices for the products.
    3. Combine the products with their prices.

    :param category_id: Category ID.
    :param city_id: City ID.
    :param min_goods: Minimum number of goods required.
    :return: The result of the task chain.
    """
    fetch_product_task = fetch_products_task.s(category_id, city_id, min_goods)

    task_chain = (
            fetch_product_task
            | fetch_prices_task.s()
            | combine_products_and_prices_task.s()
    )

    result = task_chain.apply_async()

    return result
