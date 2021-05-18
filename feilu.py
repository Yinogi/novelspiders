import requests
import bs4
import sys


class downloader:
    def __init__(self, target):
        self.target = target
        self.nums = 0
        self.names = []
        self.urls = []

    def get_download_url(self):
        req = requests.get(url=self.target)
        html = req.text
        tr_bf = bs4.BeautifulSoup(html, 'lxml')
        trs = tr_bf.find('div', class_='DivTable').find_all('a')
        # print(trs)
        for tr in trs:
            self.names.append(tr.get('title'))
            self.urls.append(tr.get('href'))
            self.nums += 1
        print('共有%f章需要下载'%(int(self.nums)))

    def get_contents(self, target):
        target = 'http:' + target
        req = requests.get(url=target)
        html = req.text
        bf = bs4.BeautifulSoup(html, 'lxml')
        bf = bf.find('div', class_='noveContent')
        # print(bf)
        texts = bf.find_all('p')
        texts = [txt.text for txt in texts]
        texts = "\n".join(texts)
        return texts

    def writer(self, name, path, text):
        with open(path,'a',encoding='utf-8')as f:
            f.write(name +'\n')
            f.writelines(text)
            f.write('\n\n')


if __name__ == "__main__":
    dl = downloader("https://b.faloo.com/942550.html")
    dl.get_download_url()
    print('已获取下载链接')
    print('开始下载')
    print(len(dl.names))
    for i in range(len(dl.urls)):
        content = dl.get_contents(dl.urls[i])
        # print(content)
        if content != None:
            dl.writer(dl.names[i], 'a.txt', content)
        sys.stdout.write("已下载:%.1f%%" % float((i/dl.nums)*100) + '\r')
        sys.stdout.flush()
        
    print('下载完成')

