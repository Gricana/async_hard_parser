import asyncio
from dataclasses import dataclass
from typing import List, Dict

import aiohttp

from auth import get_token
from config import (API_URL, HEADERS, RETRIES, BATCH_SIZE,
                    MAX_CONCURRENT_REQUESTS)
from log_handler import logger
from utils import get_sign


@dataclass
class Product:
    """
    Represents a product in the pet store API.

    Attributes:
        id (int): Unique identifier for the product. Default is 0.
        name (str): Name of the product. Default is an empty string.
        link (str): URL link to the product's webpage. Default is an empty string.
        regular_price (int): Regular price of the product. Default is 0.
        promo_price (int): Promotional price of the product. Default is 0.
        brand (str): Brand name of the product. Default is 'Unknown'.
    """
    id: int = 0
    name: str = ''
    link: str = ''
    regular_price: int = 0
    promo_price: int = 0
    brand: str = 'Unknown'


async def fetch_data(url: str, params: dict, headers: dict,
                     data: dict = None, method: str = "GET") -> dict:
    """
    Makes an HTTP request and returns a response in JSON format.

    :param url: URL for the request.
    :param params: Request parameters.
    :param headers: Request headers.
    :param data: Data to send in the request (None by default).
    :param method: HTTP method (default GET).
    :return: Response in JSON format.
    """
    attempt = 0
    params = {k: v for k, v in params.items() if v is not None}

    while attempt < RETRIES:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url,
                                           headers=headers,
                                           params=params,
                                           data=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error {response.status}: "
                                     f"{response.reason}")
                        return {}
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {str(e)}")
            attempt += 1
            if attempt < RETRIES:
                logger.info(f"Retrying... ({attempt}/{RETRIES})")
                await asyncio.sleep(2)
            else:
                logger.error("Max retries reached. Giving up.")
                return {}


async def fetch_city_id(city_name: str) -> str | None:
    """
    Gets the city ID by its name.

    :param city_name: City name.
    :return: City ID or None if city not found.
    """
    url = f"{API_URL}/city_list_users/"
    params = {'token': await get_token()}
    params['sign'] = get_sign(params)
    data = await fetch_data(url, params, HEADERS)

    if 'data' in data:
        for city in data['data']['cities']:
            if city['title'].lower() == city_name.lower():
                return city['id']
    return None


def find_category_id(categories, category_name):
    """
    Recursive search for category ID by its name.

    :param categories: List of categories to search.
    :param category_name: Name of the category to search.
    :return: Category ID or None if category not found.
    """
    for category in categories:
        if category['title'].lower() == category_name.lower():
            return category['id']

        if category.get('has_child') and category.get('child'):
            result = find_category_id(category['child'], category_name)
            if result:
                return result

    return None


async def fetch_category_id(category_name: str, city_id: str) -> str | None:
    """
    Gets the category ID by its name and city ID.

    :param category_name: Category name.
    :param city_id: City ID.
    :return: Category ID or None if category not found.
    """
    url = f"{API_URL}/categories/"
    params = {'token': await get_token()}
    params['sign'] = get_sign(params)
    headers = {**HEADERS, 'Cookie': f"selected_city_code={city_id}"}

    data = await fetch_data(url, params, headers)

    if 'data' not in data or not isinstance(data['data'], dict):
        logger.error("Invalid response structure: "
                     "'data' key not found or is not a dict.")
        return None

    category_id = find_category_id(data['data']['categories'], category_name)

    if category_id:
        logger.info(f"Found category '{category_name}' "
                    f"with ID: {category_id}")
        return category_id
    else:
        logger.warning(f"Category '{category_name}' not found.")
        return None


async def fetch_products(category_id: str, city_id: str, min_goods: int) \
        -> List[Product]:
    """
    Retrieves a list of products by category ID and city ID.

    :param category_id: Category ID.
    :param city_id: City ID.
    :param min_goods: Minimum number of goods.
    :return: List of available products as Product objects.
    """
    url = f"{API_URL}/v2/catalog/product/list/"
    params = {
        'category_id': category_id,
        'count': min_goods,
        'page': 1,
        'token': await get_token()
    }
    params['sign'] = get_sign(params)
    headers = {**HEADERS, 'Cookie': f"selected_city_code={city_id}"}

    data = await fetch_data(url, params, headers)

    if 'data' not in data or 'goods' not in data['data']:
        logger.error("Invalid response structure. "
                     "'data' or 'goods' key not found.")
        return []

    total_pages = data['data'].get('total_pages', 1)
    logger.info(f"Total number of pages: {total_pages}")
    total_items = data['data'].get('total_items', 0)
    logger.info(f"Total number of products: {total_items}")

    if total_items <= min_goods:
        logger.info(f"There are less than {min_goods} products available")
        return []

    products = await fetch_and_add_products(url, params, headers, 1)

    # Create a list of async tasks to receive the remaining pages
    tasks = [fetch_and_add_products(url, params, headers, page)
             for page in range(2, total_pages + 1)]

    # Waiting for all tasks to be completed
    additional_products = await asyncio.gather(*tasks)

    products.extend(additional_products)

    logger.info(f"Total available products: {len(products)}")
    return products


async def fetch_and_add_products(url: str, params: dict, headers: dict,
                                 page: int) -> List[Product]:
    """
    Requests data for a given page and adds available products to the list.

    :param url: URL for the request.
    :param params: Request parameters.
    :param headers: Request headers.
    :param page: Page number.
    :return: List of available products.
    """
    logger.info(f"Fetching data from page {page}...")
    params['page'] = page
    del params['sign']
    params['sign'] = get_sign(params)

    data = await fetch_data(url, params, headers)

    products = []
    if 'data' in data and 'goods' in data['data']:
        products = add_products_from_data(data['data']['goods'])
        logger.info(f"Found {len(products)} products on page {page}.")
    else:
        logger.warning(f"No products found on page {page} "
                       f"or response format is incorrect.")

    return products


def add_products_from_data(goods: List[dict]) -> List[Product]:
    """
    Adds available products from the goods list to the products list.

    :param goods: List of products from the answer.
    :return: A list of available Product objects.
    """
    products = []
    for item in goods:
        if item.get('isAvailable'):
            product = Product(
                id=item['id'],
                name=item['title'],
                link=item['webpage'],
                brand=item.get('brand_name', 'Unknown')
            )
            products.append(product)
            logger.info(f"Added product: (ID: {product.id})")
    return products


async def fetch_prices(product_ids: List[int]) -> Dict[int, Dict[str, int]]:
    """
    Gets prices for a list of products by their ID.

    :param product_ids: List of product IDs.
    :return: Dictionary with prices for each product.
    """
    url = f"{API_URL}/v2/catalog/product/info-list/"

    unique_offers = list(set(product_ids))
    prices = {}

    # We divide unique offers into groups (packages)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def fetch_price_batch(batch_ids: List[int]):
        data = {f'offers[{j}]': offer for j, offer in enumerate(batch_ids)}
        data['token'] = await get_token()
        data['sign'] = get_sign(data)
        headers = {**HEADERS,
                   'Content-Type': 'application/x-www-form-urlencoded'}

        async with semaphore:
            try:
                response = await fetch_data(url, params={}, headers=headers,
                                            data=data, method='POST')
                if 'data' in response:
                    for product in response['data']['products']:
                        active_offer_id = product.get('active_offer_id')
                        if active_offer_id:
                            prices[active_offer_id] = dict(
                                regular_price=product['variants'][0]['price'][
                                    'old'],
                                promo_price=product['variants'][0]['price'][
                                    'actual']
                            )
                            logger.info(
                                f"Prices for product ID {active_offer_id}")
            except Exception as e:
                logger.warning(f"Error fetching prices "
                               f"for batch {batch_ids}: {str(e)}")
                await asyncio.sleep(1)

    # Run queries in parallel for each group
    tasks = []
    for i in range(0, len(unique_offers), BATCH_SIZE):
        batch_ids = unique_offers[i:i + BATCH_SIZE]
        tasks.append(fetch_price_batch(batch_ids))

    await asyncio.gather(*tasks)  # Wait for all requests to complete

    logger.info(f"Fetched prices for {len(prices)} products.")
    return prices


async def combine_product_and_prices(products: List[Product],
                                     prices: Dict[int, Dict[str, int]]) \
        -> List[Product]:
    """
    Updates a list of products with their corresponding price information.

    :param products: A list of Product objects.
    :param prices: A dictionary mapping product IDs to their price information.
                   Each entry should have the following structure:
                   {
                       product_id: {
                           'regular_price': <int>,   # The regular price
                           'promo_price': <int>      # The promotional price
                       }
                   }

    :return: A list of Product objects with updated price attributes.
    :raises: None
    """
    logger.info("Updating products with prices")

    for product in products:
        price_info = prices.get(product.id)
        if price_info:
            product.regular_price = price_info.get('regular_price', 0)
            product.promo_price = price_info.get('promo_price', 0)
        else:
            logger.warning(f"No price information found "
                           f"for product ID {product.id}")

    return products
