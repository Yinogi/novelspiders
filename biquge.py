# -*- coding: utf-8 -*-
import requests
import bs4
import sys
import time
import argparse


class Biquge:
    def __init__(self):
        self.search_ = "https://www.biquge5200.com/modules/article/search.php?searchkey=%s"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
        }

    def search(self, keyword):
        url = self.search_ % keyword
        try:
            res = requests.get(url=url, headers=self.headers)
            html = res.text
        except Exception as err:
            print("请求页面异常: %s" % str(err))
            return

        try:
            bf = bs4.BeautifulSoup(html, features="html.parser")
            tbs = bf.table
            trs = tbs.find_all('tr')
        except:
            print("页面解析出错")
            return

        ret = list()
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) == 0:
                continue
            bookinfo = [td.text for td in tds]
            bookinfo = dict(zip(["文章名称", "最新章节", "作者", "字数", "更新", "状态"], bookinfo))
            bookurl = tr.find("a").get("href")
            bookinfo["链接"] = bookurl
            print("\n".join(["%s:%s" % (k, v) for k, v in bookinfo.items()]) + "\n")
            ret.append(bookinfo)
        if len(ret) == 0:
            print("未找到")
        return ret

    def download(self, name, start=None):
        infos = self.search(name)
        tgt = None
        for info in infos:
            if name == info["文章名称"]:
                tgt = info
                break

        try:
            res = requests.get(url=tgt["链接"], headers=self.headers)
            html = res.text
        except Exception as err:
            print("请求页面异常: %s" % str(err))
            return

        try:
            bf = bs4.BeautifulSoup(html, features="html.parser")
        except:
            print("页面解析出错: %s" % tgt["链接"])
            return

        tgt.pop("最新章节")
        tgt.pop("链接")
        intro = "\n".join(["%s: %s" % (k, v) for k, v in tgt.items()])

        try:
            intro_ = bf.find("div", id="intro")
            if intro_ is not None:
                intro_ = intro_.text
            else:
                intro_ = ""
            intro = intro + "\n\n" + intro_
            chaps = bf.find("div", id="list").find_all("a")
            chaps = sorted([chap.get("href") for chap in list(set(chaps))])
        except:
            print("内容解析异常，请稍后重试")
            return

        with open("%s.txt" % name, "a", encoding='utf-8') as f:
            f.write(intro)
            f.write("\n\n\n")

        p = 0
        total = len(chaps)
        if start is not None:
            p = chaps.index(start)
            if p is not None:
                chaps = chaps[p:]
            else:
                print("请输入正确的起始章节地址")
                return
        count = p

        success = True
        for chap in chaps:
            count += 1
            if count % 5 == 0:
                time.sleep(1)
            if count % 20 == 0:
                time.sleep(2)

            try:
                res = requests.get(url=chap, headers=self.headers)
                html = res.text
            except Exception as err:
                print("请求页面%s异常: %s" % (chap, str(err)))
                return

            try:
                bf = bs4.BeautifulSoup(html, features="html.parser")
                title = bf.find("h1")
                if title is not None:
                    title = title.text
                    if title == "Bad GateWay":
                        print("访问网站频率过高，请稍后再试")
                        print("当前进度：%.1f%%，下一章节：%s" % (float((count / total) * 100), chap))
                        success = False
                        break
                else:
                    print("找不到title: %s" % chap)
                    success = False
                    break
                title = "第%d章%s" % (count, title)

                content = bf.find("div", id="content")
                if content is not None:
                    content = content.text
                else:
                    print("找不到content: %s" % chap)
                    success = False
                    break
                content = content.replace("　　", "\n")
            except:
                print("内容解析异常，请稍后重试")
                success = False
                break

            with open("%s.txt" % name, "a", encoding='utf-8') as f:
                f.write(title)
                f.write("\n")
                f.write(content)
                f.write("\n\n")

            sys.stdout.write("已下载:%.1f%%" % float((count / total) * 100) + '\r')
            sys.stdout.flush()

        if success:
            print("下载完成: %s" % name)
        else:
            print("下载失败")

    def main(self):
        parser = argparse.ArgumentParser(description='单线程模式从www.biquge5200.com下载小说')
        parser.add_argument('-s', metavar="search", dest='search', type=str, help="关键字搜索，后跟书名或作者关键字")
        parser.add_argument('-d', metavar="download", dest='download', type=str, help="下载，后跟完整书名")
        parser.add_argument('-u', metavar="url", dest='url', type=str, help="下载起始位置，若此参数存在则从指定url开始下载，不存在则从头下载")
        arguments = parser.parse_args()

        if arguments.search and arguments.download:
            print("参数错误：不能同时-s和-d")
            parser.print_usage()
            sys.exit(0)
        if arguments.search:
            if arguments.url:
                print("参数错误：-s不支持子参数-u")
                parser.print_usage()
                sys.exit(0)
            else:
                return self.search(arguments.search.strip())
        elif arguments.download:
            if arguments.url:
                self.download(arguments.download.strip(), arguments.url.strip())
            else:
                self.download(arguments.download.strip())
        else:
            parser.print_usage()
            sys.exit(0)


if __name__ == "__main__":
    bqg = Biquge()
    try:
        bqg.main()
    except KeyboardInterrupt:
        print("退出")
