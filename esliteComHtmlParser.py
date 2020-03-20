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

        self.logger.info(bookInfo)


        # p_author = soup.find('p', string=self.__containsAuthor)
        # if p_author:
        #     bookInfo['作者']=str.strip(p_author.string.replace('作者 : ',''))


        # description=soup.find('meta', attrs={'name':'description'})['content']
        # self.__parseBookInfo(description, bookInfo)

        # divContents = soup.find_all('div', class_='content')
        # if divContents:
        #     divSummary=divContents[0] # summary

        #     bookInfo['內容簡介'] = self.__parseSummary(divSummary)
        #     bookInfo['本書特色'] = self.__parseFeature(divSummary)

        #     ageGroup, awards= self.__parseAwardAgeGroup(divSummary)
        #     bookInfo['適讀年齡']=ageGroup
        #     bookInfo['得獎記錄']='\n'.join(awards)

        #     divBio=divContents[0] if len(divContents) ==1 else divContents[1] 
        #     try:
        #         authorBio, illustrator, illustratorBio, translatorBio, translator = self.__parseBio(divBio)
        #         if not illustrator:
        #             try:
        #                 illustrator = self.__parseIllustrator(soup)
        #             except Exception as e:
        #                 self.logger.warn(f'Unable to parse illustrator', e)
        #                 # no-op
        #     except Exception as e:
        #         authorBio, illustrator, illustratorBio, translatorBio, translator = self.__parseBio2(divBio)

        #     bookInfo['作者簡介'] = '\n'.join(authorBio)
        #     bookInfo['繪者'] = illustrator
        #     bookInfo['繪者簡介'] = '\n'.join(illustratorBio)
        #     bookInfo['譯者簡介'] = '\n'.join(translatorBio)
        #     bookInfo['譯者'] = translator

        # bookInfo['定價'] = self.__parsePrice(soup)
        # bookInfo['規格'] = self.__parseFormFactor(soup)
        # bookInfo['叢書系列'] = self.__parseSeries(soup)
        # bookInfo['詳細分類'] = self.__parseDetailsCategory(soup)
        # bookInfo['出版地'] = self.__parsePubAt(soup)
        # bookInfo['導讀'] = self.__parseIntro(soup)
        return bookInfo

        # ok 書名			（已有）
        # ok ISBN			（有10個位或13個位，以13個位為準）
        # 網上書店連結	
        # ok 出版社		（已有）
        # ok 作者	
        # ok 繪者	
        # ok 譯者	
        # ok 出版日		（日期格式 2015/11/06 YYYY/MM/DD）
        # ok 簡｜繁 ｜ENG	
        # ok 定價			（原價 台幣單位 NT）
        # ok 內容簡介 		（1格內輸入，可跳行）
        # ok 本書特色		（如有才輸入，1格內輸入，可跳行）
        # ok 得獎記錄/榮耀	（如有才輸入，1格內輸入，可跳行）
        #  導讀			 （如有才輸入，1格內輸入，可跳行）	
        # ok 作者簡介		（如有才輸入，1格內輸入，可跳行）		
        # ok 繪者簡介   		（如有才輸入，1格內輸入，可跳行）		
        # ok 譯者簡介   		（如有才輸入，1格內輸入，可跳行）		
        # ok 叢書系列   		（如有才輸入，1格內輸入，可跳行）		
        # ok 規格（例：精裝 / 48頁 / 19 x 22 x 1 cm / 普通級 / 全彩印刷 / 初版）
        # ok 出版地		（透過閱讀分析內容簡介及作者簡介）
        # 原創地    （如有才輸入，1格內輸入，可跳行）	
        # ok適讀年齡 	    （如有才輸入，1格內輸入，可跳行）
        # ok 網上書店分類（例：童書/青少年文學> 圖畫書> 生活教育）
        # 公共圖書館索書號
        # ok 詳細分類

    # def __parseBookInfo(self, description, bookInfo:dict):
    #     lastKey=''
    #     for descBlock in description.split('，'):
    #         tuple=descBlock.split('：', 1)
    #         try:
    #             bookInfo[tuple[0]]=tuple[1]
    #             lastKey=tuple[0]
    #         except Exception:
    #             if lastKey:
    #                 bookInfo[lastKey] += ('，' + descBlock)
    #             # logger.exception(f'Error parsing metadata:{tuple}', e)

    # def __parseSummary(self, tag):
    #     endKeys = ['得獎記錄', '＊適讀年齡', '＊適讀對象：', '本書特色', '本書特點']
    #     summary=[]
    #     for sum in tag.stripped_strings:
    #         if any(x in sum for x in endKeys):
    #         # if '得獎記錄' in sum or '＊適讀年齡' in sum or '＊適讀對象：' in sum or '本書特色' in sum or '本書特點' in sum:
    #             return '\n'.join(summary)
    #         summary.append(sum)
    #     return '\n'.join(summary)

        
    # def __parseFeature(self, tag):
    #     feature=[]
    #     start=False
    #     startKeys =['本書特色', '本書特點', '書籍特色']
    #     endKeys =['＊適讀年齡：', '＊適讀對象：', '得獎記錄', '作者簡介']
    #     for txt in tag.stripped_strings:
    #         # if '本書特色' in txt or '本書特點' in txt:
    #         if any(x in txt for x in startKeys):
    #             start=True
    #             continue
    #         if any(x in txt for x in endKeys):
    #         # if '＊適讀年齡：' in txt or '＊適讀對象：' in txt or '得獎記錄' in txt or '作者簡介' in txt:
    #             return '\n'.join(feature) 
    #         if start:
    #             feature.append(txt)
    #     return '\n'.join(feature)

    # def __parseAwardAgeGroup(self, tag):
    #     awardStarted=False
    #     awards = []
    #     ageGroup = ''

    #     for txt in tag.stripped_strings:
    #         if '得獎記錄' in txt:
    #             awardStarted = True
    #             continue
    #         if '＊適讀年齡：' in txt:
    #             ageGroup = txt.replace('＊適讀年齡：','')
    #             continue
    #         if '＊適讀對象：' in txt:
    #             ageGroup = txt.replace('＊適讀對象：','')
    #             continue
    #         if awardStarted:
    #             awards.append(txt)
    #     return ageGroup, awards

    # def __parseBio(self, tag):
    #     authorKeys = ['作、繪者簡介', '作者、繪者簡介', '圖/文者簡介']

    #     authorBio=[]
    #     illustrator=''
    #     illustratorBio=[]
    #     translator=''
    #     translatorBio=[]

    #     txt = list(reversed(list(tag.stripped_strings)))
    #     t = ''
    #     while len(txt) > 0:
    #         t = txt.pop()
    #         # if '作、繪者簡介' in t or '作者、繪者簡介' in t or '圖/文者簡介' in t:
    #         if any(x in t for x in authorKeys):
    #             illustrator = txt.pop()
    #             t = txt.pop()
    #             while len(txt) > 0 and not '譯者簡介' in t:
    #                 authorBio.append(t)
    #                 illustratorBio.append(t)
    #                 t = txt.pop()

    #         if '作者簡介' in t:
    #             t = txt.pop() # skip the name
    #             t = txt.pop()
    #             while len(txt) > 0 and not '繪者簡介' in t and not '譯者簡介' in t :
    #                 authorBio.append(t)
    #                 t = txt.pop()
            
    #         if '繪者簡介' in t:
    #             illustrator = txt.pop()
    #             t = txt.pop()
    #             while len(txt) > 0 and not '譯者簡介' in t:
    #                 illustratorBio.append(t)
    #                 t = txt.pop()

    #         if '譯者簡介' in t:
    #             translator = txt.pop()
    #             while len(txt) > 0:
    #                 translatorBio.append(txt.pop())

    #     return authorBio, illustrator, illustratorBio, translatorBio, translator

    # def __parseBio2(self, tag):
    #     authorBio=[]
    #     illustrator=''
    #     illustratorBio=[]
    #     translator=''
    #     translatorBio=[]

    #     value = tag.find(string='作者簡介')
    #     if value:
    #         element = value.find_parent('p').find_next('p')
    #         # author = element.next_element.string
    #         element = element.find_next('p')
    #         authorBio = list(element.stripped_strings)
    #         translatorTitle = element.find_next(string='譯者簡介')
    #         if translatorTitle:
    #             translatorElement = translatorTitle.find_next('b')
    #             translator = translatorElement.string
    #             translatorBio = list(translatorElement.find_next('p').stripped_strings)

    #     authorBio = [s for s in authorBio if not s == '譯者簡介']
    #     return authorBio, illustrator, illustratorBio, translatorBio, translator

    # def __parseIllustrator(self, soup):
    #     element = soup.find(string=re.compile('.*繪者：.*'))
    #     if not element:
    #         return ''
    #     return element.next_sibling.string

    # def __parsePrice(self, soup):
    #     divPrice = soup.find('ul', class_='price')
    #     if not divPrice:
    #         return ''
    #     try:
    #         return divPrice.li.em.string
    #     except:
    #         return ''.join(list(divPrice.stripped_strings)).replace('定價：','').replace('元','')

    # def __parseFormFactor(self, soup):
    #     liFormFactor=soup.find('li', string=re.compile(".*規格：.*"))
    #     if not liFormFactor:
    #         return ''
    #     return ''.join(liFormFactor.stripped_strings).replace('規格：','').replace(' ','').replace('/',' / ')

    # def __parseSeries(self, soup):
    #     txt=soup.find(string=re.compile(".*叢書系列：.*"))

    #     if not txt:
    #         return ''

    #     return txt.parent.a.string

    # def __parseDetailsCategory(self, soup):
    #     # There maybe multiple group lists. E.g.
    #     # 1) 童書/青少年文學 > 圖畫書 > 知識繪本
    #     # 2) 專業/教科書/政府出版品 > 政府出版品 > 縣市采風 > 地方風情
    #     # See https://www.books.com.tw/products/0010753055?loc=M_0009_015

    #     items=soup.find_all(string=re.compile(".*本書分類：.*"))

    #     if not items:
    #         return ''

    #     values = []
    #     for txt in items:
    #         values.append(' '.join(list(txt.parent.stripped_strings)[1:]))
    #     return '\n'.join(values)

    # def __parsePubAt(self, soup):
    #     txt=soup.find('li', string=re.compile(".*出版地：.*"))

    #     if not txt:
    #         return ''

    #     return txt.string.replace('出版地：','').strip()

    # def __parseIntro(self, soup):
    #     intro = soup.find('strong', string='序')
    #     if intro:
    #         value= '\n'.join(list(intro.parent.stripped_strings))
    #         if value:
    #             return value

    #     intro = soup.find('h3', string='序')
    #     if intro:
    #         value = '\n'.join(list(intro.find_next('div', class_='content more_off').stripped_strings))
    #         if value:
    #             return value

    #     return ''

from pprint import pprint
import codecs
def readFile(path:str) -> str:
    with codecs.open(path, 'r', encoding='utf8') as f:
        html = f.read()
    return html

p=EsliteComHtmlParser()
html = readFile('eslite_sample_desktop.html')

bookInfo = {}
bookInfo = p.parse(html, bookInfo)
# logger.info(bookInfo)