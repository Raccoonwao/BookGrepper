from urllib import request as urlrequest
from urllib import response as urlresponse
from proxymanager import ProxyManager, Proxy

def readHtml(url: str, proxy: Proxy= None) -> str:
    # url = baseUrl + id
    # logger.info(f'Reading html:{url}, proxy: {proxy}...')
    
    req = urlrequest.Request(url)
    if not proxy == None:
        req.set_proxy(f'http://{str(proxy)}', 'http')

    # with urllib.request.urlopen(url) as response:
    with urlrequest.urlopen(req) as response:
        mybytes = response.read()
        # response.release_conn()

    html = mybytes.decode("utf8")
    return html
    
    # proxies = None if proxy == None else {'http': f'http://{proxy.host}:{proxy.port}/'}
    # # try:
    # opener = urllib.request.FancyURLopener(proxies)
    # with opener.open(url) as f:
    #     response = f.read()
    # return response.decode('utf-8')
    # except Exception as e:
    #     logger.error(f'bad:{proxy}')