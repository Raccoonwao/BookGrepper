from iHtmlParser import IHtmlParser
from bs4 import BeautifulSoup
import re
import logging

class EsliteComHtmlParser(IHtmlParser):
    logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(message)s')
    logger = logging.getLogger(__name__)

    regex = {}

    def __init__(self):
        for item in [ '作者', '出版社' ]:
            self.regex[item] = re.compile(item + ' : .*')

    def __searchString(self, searchIn: str, searchRegex:str) -> str:
        if not searchIn:
            return None
        try:
            return re.search(searchRegex, searchIn).group(1)
        except AttributeError:
            return None

    def __lookupItem(self, itemRegex, bookInfo: dict, bookInfoKey:str, soup:BeautifulSoup):
        p=soup.find('p', string=itemRegex)
        if p:
            bookInfo[bookInfoKey] = str.strip(p.string.replace(bookInfoKey+' : ',''))
            return
        bookInfo[bookInfoKey]='Not found'

    def __parseMobile(self, soup: BeautifulSoup, bookInfo: dict):
        p_title = soup.find('h1', itemprop='name')
        if p_title:
            bookInfo['書名']=str.strip(p_title.string)

        for key, value in self.regex.items():
            self.__lookupItem(value, bookInfo, key, soup)

        p_price=soup.find('div', class_='price')
        if p_price:
            bookInfo['定價']=self.__searchString(''.join(p_price.stripped_strings), '([0-9]+)')

        p_price=soup.find('div', class_='price')
        if p_price:
            bookInfo['定價']=self.__searchString(''.join(p_price.stripped_strings), '([0-9]+)')

        element=soup.find('span',string='內容簡介')
        if element:
            bookInfo['內容簡介']=''.join(list(element.findNext('article').stripped_strings))

        element=soup.find('strong',string='■作者簡介')
        if element:
            bookInfo['作者簡介']=''.join(list(element.findNext('p').stripped_strings))

    def __parseDesktopKeywords(self, soup: BeautifulSoup, bookInfo:dict):
        defReplaceStr = ['／', '\xa0', '\n']
        keywords={
            '作者': None,
            '繪者': { 'replaceStr': ['攝影者', '/', '插畫'] },
            '出版社': None,
            '出版日期': None,
            '商品語言': { 'bookInfoKey': '語言' },
        }
        
        for ele in soup.findAll(class_='PI_item'):
            content=''.join(list(ele.stripped_strings))
            for key, value in keywords.items():
                if not key in content:
                    continue
                if not value:
                    bookInfo[key] = re.sub(r'|'.join(map(re.escape, defReplaceStr + [ key ])), '', content).strip()
                    continue

                bookInfoKey = value.get('bookInfoKey')
                if not bookInfoKey:
                    bookInfoKey = key

                replaceStr = value.get('replaceStr')
                if replaceStr:
                    effReplaceStr = defReplaceStr + replaceStr + [ key ]
                else:
                    effReplaceStr = defReplaceStr + [ key ]
                    
                bookInfo[bookInfoKey] = re.sub(r'|'.join(map(re.escape, effReplaceStr)), '', content).strip()

    def __parseDesktop(self, soup: BeautifulSoup, bookInfo:dict):
        element=soup.find('h1', itemprop='name')
        if element:
            bookInfo['書名']=''.join(list(element.stripped_strings))

        self.__parseDesktopKeywords(soup, bookInfo)

        h2_details = soup.find('h2', string='詳細資料')
        if h2_details:
            p = h2_details.findNext('p')
            details = ''.join(list(p.stripped_strings))
            bookInfo['ISBN13'] = self.__searchString(details, 'ISBN 13\D*(\d+)')
            bookInfo['ISBN'] = self.__searchString(details, 'ISBN 10\D*(\d+)')

        #規格 (精裝 / 40頁 / 23x31cm / 普通級 / 全彩印刷 / 初版) = 裝訂 + 頁數 + 尺寸 + 級別
        formFactor = soup.find('span', id='ctl00_ContentPlaceHolder1_Product_detail_book1_dlSpec_ctl02_lblDescription').string
        formFactor += ' / '
        formFactor += soup.find('span', id='ctl00_ContentPlaceHolder1_Product_detail_book1_dlSpec_ctl00_lblDescription').string
        formFactor += '頁 / '
        formFactor += soup.find('span', id='ctl00_ContentPlaceHolder1_Product_detail_book1_dlSpec_ctl01_lblDescription').string
        formFactor += ' / '
        formFactor += soup.find('span', id='ctl00_ContentPlaceHolder1_Product_detail_book1_dlSpec_ctl03_lblDescription').string
        bookInfo['規格'] = formFactor

        h2_description = soup.find('h2', string='內容簡介')
        if h2_description:
            bookInfo['內容簡介']='\n'.join(list(h2_description.parent.stripped_strings)).replace('內容簡介', '')
        h2_author = soup.find('h2', string='作者介紹')
        if h2_author:
            for p in h2_author.parent.findAll('p'):
                value = '\n'.join(list(p.stripped_strings))
                self.__parseAuthor(value, bookInfo, '作者', '作者簡介')
                self.__parseAuthor(value, bookInfo, '繪者', '繪者簡介')
                self.__parseAuthor(value, bookInfo, '譯者', '譯者簡介')

    def __parseAuthor(self, value, bookInfo, key, valueBookInfoKey):
        searchFor = bookInfo.get(key)
        if not searchFor:
            return
        for s in map(str.strip, searchFor.split('/')):
            if s in value:
                # Handle multiple authors
                existing = bookInfo.get(valueBookInfoKey)
                if not existing:
                    bookInfo[valueBookInfoKey]=value
                    return
                bookInfo[valueBookInfoKey] = existing + '\n' + value

    def parse(self, html, bookInfo:dict) -> dict:
        soup = BeautifulSoup(html, features="html.parser")

        try:
            self.__parseMobile(soup, bookInfo)
        except:
            self.__parseDesktop(soup, bookInfo)

        return bookInfo


      
# from pprint import pprint
# import codecs
# def readFile(path:str) -> str:
#     with codecs.open(path, 'r', encoding='utf8') as f:
#         html = f.read()
#     return html

# p=EsliteComHtmlParser()
# html = readFile('eslite_sample_desktop.html')

# bookInfo = {}
# bookInfo = p.parse(html, bookInfo)
# print(bookInfo)