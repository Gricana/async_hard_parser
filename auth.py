import aiohttp

from utils import get_sign


async def get_token() -> str | None:
    """
    Async obtains an access token from the API.

    :return: Access token (string) if the request is successful,
             else None if the token was not found or an error occurred.
    """
    from config import API_URL, HEADERS

    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}/start/"
        params = {'sign': get_sign({})}
        async with session.get(url, headers=HEADERS,
                               params=params) as response:
            data = await response.json()
            token = data['data']['token'] if 'data' in data else None
            return token
