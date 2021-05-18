# -*- coding: utf-8 -*-
import re
import requests
import traceback
from bs4 import BeautifulSoup


class GaoH:
    def __init__(self):
        self.base_url = "http://www.gaohbook.net/"

        self.title_pattern = r'<span class="title">(.*)</span>'
        self.author_pattern = r'<a href="/author/.+">(.+)</a>'
        self.description_pattern = r'(?s)<div class="description">(.*?)</div>'

        self.ul_pattern = r'(?s)<ul class="nav chapter-list">(.*?)</ul>'
        self.href_pattern = r'<li><a href="(.*)">.*</a></li>'

    def catch_chapter(self, book_id):
        print("获取章节列表...")
        url = self.base_url + "book/%s.html"
        try:
            res = requests.get(url % str(book_id))
            text = res.text
        except:
            print("小说页面获取失败: %s" % traceback.format_exc())
            return None, None, None

        book_name = re.search(self.title_pattern, text).group(1)
        book_name = book_name.lstrip('《')
        book_name = book_name.rstrip('》')
        author = re.search(self.author_pattern, text).group(1)
        des = re.search(self.description_pattern, text).group(1).split('<br />')
        des = [data.strip() for data in des]
        des = '\n'.join(des)
        title = "%s\n\n作者：%s\n\n%s\n\n\n\n" % (book_name, author, des)

        chap_ul = re.search(self.ul_pattern, text)
        if chap_ul:
            print("获取章节列表成功！")
            chap_str = chap_ul.group(1)
        else:
            print("获取章节列表失败！")
            return None, None, None
        chap_list = chap_str.split("\n")

        chap_id_list = list()
        for chap in chap_list:
            if chap == "":
                continue
            res = re.match(self.href_pattern, chap)
            if res:
                url = res.group(1)
                chap_id_list.append(url)
        if len(chap_id_list) == 0:
            print("获取章节id列表失败！")
            return None, None, None
        return book_name, title, chap_id_list

    def catch_content(self, addr):
        print("获取%s正文内容..." % addr)
        url = self.base_url + addr
        try:
            res = requests.get(url)
            html = res.text
        except:
            print("小说页面%s获取失败: %s" % (addr, traceback.format_exc()))
            return None, None
        pattern = r'(?s)<div class="content">(.*?)</div>'
        res = re.search(pattern, html)
        if res:
            text_str = res.group(1)
        else:
            print("获取正文内容失败！")
            return None, None
        text_list = text_str.split("<br />")
        text_list = [text.strip('&nbsp;&nbsp;&nbsp;&nbsp;') for text in [text.strip() for text in text_list]]
        text_list = ["    %s" % text for text in text_list if text != '']
        chap_name = text_list[0].strip()
        return chap_name, '\n'.join(text_list[1:])

    def run(self, book_id):
        print("开始...")
        try:
            book_name, title, chap_list = self.catch_chapter(book_id)
        except:
            print("章节获取失败：%s" % traceback.format_exc())
            return
        with open(('%s.txt' % book_name), 'w') as txt:
            txt.write(title)
            for chap in chap_list:
                count = chap_list.index(chap)
                name, data = self.catch_content(chap)
                if data is '':
                    print('%s章节获取内容为空，已停止。')
                    break
                name = "第%d章：%s\n" % (count + 1, name)
                txt.write(name)
                txt.write(data)
                txt.write('\r\n\r\n')
            print("下载完毕！")


class YuBook:
    def __init__(self):
        self.base_url = 'https://m.yubook.la'
        self.headers = {
            'Host': 'm.yubook.la',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    def run(self, addr):
        print("开始...")
        url = "%s%s" % (self.base_url, addr)
        try:
            res = requests.get(url, headers=self.headers)
            res.encoding = res.apparent_encoding
            html = res.text
        except:
            print("章节列表%s获取失败: %s" % (addr, traceback.format_exc()))
            return

        soup = BeautifulSoup(html, "lxml")
        book_name = soup.find_all("div", class_="nav_name", limit=1)[0].text
        author = soup.find_all("p", class_="p1", limit=1)[0].text
        des = soup.find_all("p", class_="p2")[1].text.strip()
        start_page = soup.find_all("div", class_="nav_p2")[0].a['href']

        tt = "%s\n\n%s\n\n%s\n\n\n\n" % (book_name, author, des)
        with open(('%s.txt' % book_name), 'w') as txt:
            txt.write(tt)
            print("获取%s正文内容..." % addr)
            url = "%s%s" % (self.base_url, start_page)
            while True:
                try:
                    res = requests.get(url, headers=self.headers)
                    res.encoding = res.apparent_encoding
                    html = res.text
                except:
                    print("章节%s获取失败: %s" % (addr, traceback.format_exc()))
                    return
                ch_name, novel_ctt, next_page = self.catch_content(html)
                txt.write(ch_name)
                txt.write('\r\n')
                txt.write(novel_ctt)
                txt.write('\r\n\r\n')
                if next_page is None:
                    print("下载完毕！")
                    break
                url = "%s%s" % (self.base_url, next_page)
                print("获取%s正文内容..." % next_page)

    @staticmethod
    def catch_content(html):
        soup = BeautifulSoup(html, "lxml")
        ch_name = soup.find_all('h1')[1].text
        ch = re.search(r'(\d+)[:：](.+)', ch_name)
        count = ch.group(1)
        name = ch.group(2)
        ch_name = "第%s章：%s" % (count, name)
        ctt = soup.find_all("div", id="novelcontent", class_="novelcontent")[0].text.strip()
        ctt = '\n'.join(["    %s" % text for text in ctt.split("    ")])
        ad = soup.find_all("a", class_="p4")[0].attrs['href']
        if ad[-4:] != 'html':
            return ch_name, ctt, None
        else:
            return ch_name, ctt, ad


if __name__ == "__main__":
    gh = GaoH()
    bid = input("请输入整型小说id：")
    gh.run(bid)

    # yb = YuBook()
    # pg = input("请输入整型小说id：")
    # yb.run(pg)


