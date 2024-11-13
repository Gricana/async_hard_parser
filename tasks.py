import asyncio
from dataclasses import asdict
from typing import List, Dict, Any, Tuple

from celery_app import app
from importer import save_all
from parser import Product
from parser import fetch_products, fetch_prices, combine_product_and_prices


@app.task
def save_products(products: List[Dict], filename: str):
    """
    Celery task to save products into a file asynchronously.

    :param products: List of product dictionaries.
    :param filename: Name of the file to save products.
    """
    save_all(products, filename)


@app.task(bind=True)
def fetch_products_task(self, category_id: str, city_id: str,
                        min_goods: int) -> List[Dict]:
    """
    Celery task to fetch products based on category and city.

    :param category_id: Category ID used for filtering.
    :param city_id: City ID used for filtering.
    :param min_goods: Minimum number of goods required.
    :return: List of product dictionaries.
    """
    products = asyncio.run(fetch_products(category_id, city_id, min_goods))
    products = [product for product in products if
                isinstance(product, Product)]
    return [asdict(product) for product in products]


@app.task(bind=True)
def fetch_prices_task(self, products: List[Dict], city_id: str,
                      category_id: str) \
        -> Tuple[List[Dict], Dict[int, Dict[str, int]]]:
    """
    Celery task to fetch prices for a list of products.

    :param city_id: City ID used for filtering.
    :param category_id: Category ID used for filtering.
    :param products: List of Product objects.
    :return: Tuple with the original products and dict with prices for each product.
    """
    product_ids = [product.get('id') for product in products]
    prices = asyncio.run(fetch_prices(product_ids))
    return products, prices


@app.task(bind=True)
def combine_products_and_prices_task(self,
                                     data: Tuple[List[Dict], Dict[int, Dict[str, int]]],
                                     city_id: str, category_id: str) -> \
        List[Dict[str, Any]]:
    """
    Celery task to combine product information with prices.

    :param city_id: City ID used for filtering.
    :param category_id: Category ID used for filtering.
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
    fetch_product_task = fetch_products_task.s(
        category_id, city_id, min_goods
    ).set(routing_key=f'fetch.products.{city_id}.{category_id}')

    fetch_price_task = fetch_prices_task.s(city_id=city_id,
                                           category_id=category_id).set(
        routing_key=f'fetch.prices.{city_id}.{category_id}'
    )

    combine_products_task = combine_products_and_prices_task.s(
        city_id=city_id, category_id=category_id).set(
        routing_key=f'combine.products.{city_id}.{category_id}'
    )

    task_chain = fetch_product_task | fetch_price_task | combine_products_task
    result = task_chain.apply_async()
    return result
