from bs4 import BeautifulSoup
from htmlhelper import readHtml
import logging

# https://webcat.hkpl.gov.hk/search/query?match_1=PHRASE&field_1=isbn&term_1=9789867968722

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def search_call_number(isbn:str):
    if not isbn:
        return 'Missing ISBN'
    url = f'https://webcat.hkpl.gov.hk/search/query?match_1=PHRASE&field_1=isbn&term_1={isbn}&locale=en&theme=WEB'
    # logger.info(f'Searching Call Number. ISBN:{isbn}')
    try:
        html = readHtml(url)
        soup = BeautifulSoup(html, features="html.parser")
        callNoTitleTd = soup.find('td', string='Call Number')
        if callNoTitleTd:
            callNoSpan = callNoTitleTd.find_next('span', dir='ltr')
            return callNoSpan.string.strip()
        else:
            return 'Not Found'
    except:
        return 'Not Found'

# callNo = search_call_number('9789867968722')
# print(callNo)