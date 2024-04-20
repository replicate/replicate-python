import os
import httpx

def get_proxy():

    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if http_proxy:
        return httpx.Proxy(url=http_proxy)

    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if https_proxy:
        return httpx.Proxy(url=https_proxy)

    return None
