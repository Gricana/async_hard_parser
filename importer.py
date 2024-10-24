import asyncio
import json
from typing import List, Dict

import pandas as pd


async def save_to_json(products: List[Dict], filename: str):
    """
    Async saves a list of products to a file in JSON format.

    :param products: List of product dictionaries to save.
    :param filename: The name of the file to save the data.
    """
    await asyncio.to_thread(_save_json, products, filename)


def _save_json(products: List[Dict], filename: str):
    """
    Saves a list of products to a file in JSON format.

    :param products: List of product dictionaries to save.
    :param filename: The name of the file to save the data.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)


async def save_to_csv(products: List[Dict], filename: str):
    """
    Async saves a list of products to a CSV file.

    :param products: List of product dictionaries to save.
    :param filename: The name of the file to save the data.
    """
    await asyncio.to_thread(_save_csv, products, filename)


def _save_csv(products: List[Dict], filename: str):
    """
    Saves a list of products to a file in CSV format.

    :param products: List of product dictionaries to save.
    :param filename: The name of the file to save the data.
    """
    df = pd.DataFrame(products)  # Directly use the list of dictionaries
    df.to_csv(filename, index=False)


async def save_to_xlsx(products: List[Dict], filename: str):
    """
    Async saves a list of products to a file in XLSX format.

    :param products: List of product dictionaries to save.
    :param filename: The name of the file to save the data.
    """
    await asyncio.to_thread(_save_xlsx, products, filename)


def _save_xlsx(products: List[Dict], filename: str):
    """
    Saves a list of products to a file in XLSX format.

    :param products: List of product dictionaries to save.
    :param filename: The name of the file to save the data.
    """
    df = pd.DataFrame(products)  # Directly use the list of dictionaries
    df.to_excel(filename, index=False)


async def save_all(products: List[Dict], filename: str):
    """
    Saves a list of products to a file of the specified format.

    Determines the file format by extension and calls the corresponding
    async save function.

    :param products: List of product dictionaries.
    :param filename: The file name to save the data, including ext.
    :raises ValueError: If the specified file format is not supported.
    """
    file_extension = filename.split('.')[-1].lower()
    save_function = {
        'json': save_to_json,
        'csv': save_to_csv,
        'xlsx': save_to_xlsx,
    }.get(file_extension)

    if save_function:
        await save_function(products, filename)
    else:
        raise ValueError("Unsupported file format. Use json, csv, or xlsx.")
