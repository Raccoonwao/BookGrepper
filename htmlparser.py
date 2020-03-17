from urllib import request as urlrequest
from urllib import response as urlresponse
from urllib.parse import urlparse
from googlesheet import GoogleSheet
import urllib
import re
import codecs
import time
import logging

from htmlhelper import readHtml

from bs4 import BeautifulSoup
from pprint import pprint
from proxymanager import ProxyManager, Proxy
from HKLibrarySearcher import search_call_number
from bookComTwHtmlParser import BookComTwHtmlParser

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def readFile(path:str) -> str:
    with codecs.open(path, 'r', encoding='utf8') as f:
        html = f.read()
    return html

def parseABook(uri: str, fromFile: bool = False, proxy: Proxy = None) -> dict:
    if fromFile: 
        html = readFile(uri + '.html')
    else:
        html = readHtml(uri, proxy)

    bookInfo = { 'url' : uri }
    parsed_uri = urlparse(uri)
    if '.books.com.tw' in parsed_uri.netloc:
        return bookComTwParser.parse(html, bookInfo)
    raise NotImplementedError(f'Unsupported website:{uri}')

def xstr(s):
    if s is None:
        return ''
    return str(s)

def prepareValues(bookInfo: dict):
    keys = ['ISBN', 'url', '出版社', '作者','繪者','譯者','出版日期','語言','定價','內容簡介','本書特色','得獎記錄','導讀','作者簡介','繪者簡介','譯者簡介','叢書系列','規格','出版地','原創地','適讀年齡','詳細分類','callNo','書名']
     
    row = []
    for value in (xstr(bookInfo.get(key)) for key in keys):
        row.append(value)
    return [row]

def loadGoogleSheet(google_sheet:GoogleSheet, skipISBNFound: bool = True):
    """Return arrays of [ [Starting cell, url, isbn]. [...], ... ]"""
    data = google_sheet.readSheet('C2:D') # ISBN,Url
    items = []
    rowIndex = 1

    for row in data:
        rowIndex += 1
        if skipISBNFound and not row[0] == '': 
            continue
        items.append([ 'C' + str(rowIndex), row[1]] )
    return items

def fillCallNos(googleSheetId:str):
    google_sheet = GoogleSheet(googleSheetId)
    rows = loadGoogleSheet(google_sheet, False)
    for row in rows:
        isbn = row[2]
        if isbn:
            callNo = search_call_number(isbn)
            if not callNo:
                callNo = 'Not found' 
            google_sheet.writeSheet(row[0][1:]+ 'Y', [[callable]])

def parseBooks(googleSheetId:str) -> []:
    google_sheet = GoogleSheet(googleSheetId)
    items = loadGoogleSheet(google_sheet)

    # proxy_manager = ProxyManager()
    proxy = None  
    i=0
    for book in items:
        # proxy = proxy_manager.next()  

        cell = book[0]
        url = book[1]

        logger.info(f'Loading book:{url} , proxy:{proxy}')

        try:
            bookInfo = parseABook(url, proxy=proxy)
            bookInfo['callNo'] = search_call_number(bookInfo.get('ISBN'))
            values=prepareValues(bookInfo)
            google_sheet.writeSheet(cell, values)

            logger.info(f'Book loaded:{bookInfo["書名"]}')


            i+=1
            if i%2==0:
                # long sleep after every 2 books to workaround avoid website reject
                logger.info('Sleeping...')
                time.sleep(10)
        except NotImplementedError as e:
            logger.exception(e)

bookComTwParser = BookComTwHtmlParser()
parseBooks('1se8bYdJOctG3hTN3_r21WZdpBUuh9yDJrKg7FJumwfc')

