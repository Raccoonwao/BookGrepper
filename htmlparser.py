from urllib import request as urlrequest
from urllib import response as urlresponse
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

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
    parsed_uri = urlsplit(uri) # remove uri query part
    uri = urlunsplit([parsed_uri.scheme, parsed_uri.netloc, parsed_uri.path, '', ''])

    bookInfo = { 'url' : uri, 'status' : None }

    if fromFile: 
        html = readFile(uri + '.html')
        bookInfo['status'] = f'Loaded from file:{uri}.html'
    else:
        if '.books.com.tw' in parsed_uri.netloc:
            html = readHtml(uri, proxy)
            bookInfo = bookComTwParser.parse(html, bookInfo)
            bookInfo['status']='Done'
            return bookInfo
        bookInfo['status'] = 'Unsupported website'
    
    return bookInfo

def xstr(s):
    if s is None:
        return ''
    return str(s)

def prepareValues(bookInfo: dict):
    keys = ['url', '出版社', '作者','繪者','譯者','出版日期','語言','定價','內容簡介','本書特色','得獎記錄','導讀','作者簡介','繪者簡介','譯者簡介','叢書系列','規格','出版地','原創地','適讀年齡','詳細分類','callNo','書名']

    firstValue = bookInfo.get('ISBN')
    if not firstValue:
        firstValue = bookInfo.get('status')

    row = [ firstValue ]
    for value in (xstr(bookInfo.get(key)) for key in keys):
        try:
            row.append(value)
        except:
            break
    
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

def parseBooks(googleSheetId:str):
    google_sheet = GoogleSheet(googleSheetId)
    items = loadGoogleSheet(google_sheet)

    proxy = None  
    i=0
    for book in items:
        cell = book[0]
        url = book[1]

        logger.info(f'Loading book:{url} , proxy:{proxy}')

        try:
            bookInfo = parseABook(url, proxy=proxy)
            bookInfo['callNo'] = search_call_number(bookInfo.get('ISBN'))
            values=prepareValues(bookInfo)
            google_sheet.writeSheet(cell, values)

            title = bookInfo.get("書名")
            logger.info(f'Book loaded:{title}')

            if not title == None:
                i+=1
                if i%2==0:
                    # long sleep after every 2 books to workaround avoid website reject
                    logger.info('Sleeping...')
                    time.sleep(10)
        except NotImplementedError as e:
            logger.exception(e)

bookComTwParser = BookComTwHtmlParser()
parseBooks('1se8bYdJOctG3hTN3_r21WZdpBUuh9yDJrKg7FJumwfc')

