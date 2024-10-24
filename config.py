import os

from utils import basic_auth


SALT = os.getenv('SIGN_SALT', 'ABCDEF00G')

USERNAME = os.getenv('NAME', '4lapymobile')
PASSWORD = os.getenv('PASSWORD', 'xJ9w1Q3(r')

API_URL = "https://4lapy.ru/api"

HEADERS = {
    "Version-Build": "3.3.9",
    "X-Apps-Screen": "1792x828",
    "X-Apps-OS": "18.1",
    "X-Apps-Additionally": "404",
    "User-Agent": "lapy/3.3.9 (iPhone; iOS 18.1; Scale/2.00)",
    "Accept-Language": "en-RU;q=1, ru-RU;q=0.9",
    "X-Apps-Build": "3.3.9(1)",
    "Connection": "keep-alive",
    "X-Apps-Location": "lat:0.0,lon:0.0",
    "Host": "4lapy.ru",
    "X-Apps-Device": "iPhone12,1",
    "Authorization": f"Basic {basic_auth(USERNAME, PASSWORD)}",
    "Accept-Encoding": "gzip, deflate, br"
}
RETRIES = 3
BATCH_SIZE = 200  # Number of items to process at one time
MAX_CONCURRENT_REQUESTS = 5
