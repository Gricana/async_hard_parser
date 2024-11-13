import argparse
import asyncio
import logging

from tasks import get_products_with_prices, save_products


def create_parser() -> argparse.ArgumentParser:
    """
    Creates and configures a command-line argument parser.

    :return: An instance of argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(description="Pet store API parser")
    parser.add_argument("category",
                        help="Enter the name of the product category. "
                             "No case matching.")
    parser.add_argument("city",
                        help="Enter the name of the city. No case matching.")
    parser.add_argument("min_goods", type=int,
                        help="Enter the minimum available number of products "
                             "in the category.")
    parser.add_argument("filename",
                        help="Output filename (json, csv, or xlsx format)")
    return parser


async def main():
    logging.basicConfig(level=logging.INFO)

    parser = create_parser()
    args = parser.parse_args()

    category = args.category
    city = args.city
    min_goods = args.min_goods
    filename = args.filename

    logging.info(
        f"Fetching products for category '{category}', city '{city}' "
        f"and minimum goods {min_goods}...")

    result = get_products_with_prices(category, city, min_goods)

    try:
        products = result.get(timeout=300)

        if products:
            logging.info(f"Fetched {len(products)} products.")
            save_result = save_products.apply_async(args=[products, filename])
            save_result.get(timeout=300)

            logging.info(f"Products saved successfully in '{filename}'.")
        else:
            logging.warning("No products were found or processed.")

    except Exception as e:
        logging.error(
            f"An error occurred while fetching or saving products: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
