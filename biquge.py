# -*- coding: utf-8 -*-
import requests
import bs4
import sys
import time
import argparse


class Biquge(object):
    def __init__(self):
        self.search_ = "https://www.biquge5200.com/modules/article/search.php?searchkey=%s"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
        }

    def __get_bookinfo(self, info):
        """
        :param info: dict
        :return:
        """
        try:
            res = requests.get(url=info["链接"], headers=self.headers)
            html = res.text
        except Exception as err:
            print("请求页面异常，请检查网络: %s" % str(err))
            return None, None, None

        try:
            bf = bs4.BeautifulSoup(html, features="html.parser")
        except:
            print("页面解析出错: %s" % info["链接"])
            return None, None, None

        try:
            info.pop("最新章节")
            info.pop("链接")
        except:
            pass
        intro = "\n".join(["%s: %s" % (k, v) for k, v in info.items()])

        try:
            intro_ = bf.find("div", id="intro")
            if intro_ is not None:
                intro_ = intro_.text
            else:
                intro_ = ""
            intro = intro + "\n\n" + intro_
            chaps = bf.find("div", id="list").find_all("a")
            chaps_list = sorted([chap.get("href") for chap in list(set(chaps))])
        except:
            return None, None, None
        else:
            try:
                chaps_name = {chap.get("href"): chap.text for chap in chaps}
            except:
                chaps_name = None
        return intro, chaps_list, chaps_name

    def search(self, keyword, log=True):
        """
        书籍搜索
        :param keyword:
        :param log: 默认下载选项不打印书籍信息，查询选项打印
        :return: [{}, {}, ...]
        """
        url = self.search_ % keyword
        try:
            res = requests.get(url=url, headers=self.headers)
            html = res.text
        except Exception as err:
            print("请求页面异常，请检查网络: %s" % str(err))
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
            if log is True:
                print("\n".join(["%s:%s" % (k, v) for k, v in bookinfo.items()]) + "\n")
            ret.append(bookinfo)
        if len(ret) == 0:
            print("未找到书籍")
        return ret

    def chapters(self, name, num):
        """
        根据书名和章节号返回章节名和章节url
        :param name:
        :param num:
        :return:
        """
        infos = self.search(name, log=False)
        tgt = None
        for info in infos:
            if name == info["文章名称"]:
                tgt = info
                break
        if tgt is None:
            print("未找到，请输入正确的书名")
            return

        _, _, chaps_name = self.__get_bookinfo(tgt)
        if chaps_name is None:
            print("获取章节列表失败")
            return
        chap_list = sorted(chaps_name.keys())
        try:
            chap = chap_list[int(num) - 1]
        except:
            print('请输入正确的章节数：%d - %d' % (1, len(chap_list)))
            return
        else:
            chap_name = chaps_name[chap]
            print("%s\n%s" % (chap_name, chap))
            print("\n因目录包含上架感言、请假条等单章，故实际查询结果可能与输入章节号有偏差，请自行调整章节号\n")

    def download(self, name, start=None):
        """
        书籍下载
        :param name:
        :param start: 起始章节的链接，用于增量下载，也可以直接传入书籍章节目录url，此时将全本下载，用于下载搜索框搜不出来的书
        :return:
        """
        infos = self.search(name, log=False)
        tgt = None
        for info in infos:
            if name == info["文章名称"]:
                tgt = info
                break
        if tgt is None:
            if start is None:
                print("未找到，请输入正确的书名")
                return
            else:
                tgt = {"链接": start}

        intro, chaps, _ = self.__get_bookinfo(tgt)
        if intro is None or chaps is None:
            print("内容解析异常，请稍后重试")
            return
        if start is None:
            with open("%s.txt" % name, "a", encoding='utf-8') as f:
                f.write(intro)
                f.write("\n\n\n")

        p = 0
        if start is not None:
            try:
                p = chaps.index(start)
            except ValueError:
                print("指定url章节未找到，将从头开始下载...")
                p = 0
            chaps = chaps[p:]
        total = len(chaps)

        count = 0
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
                print("请求页面%s异常，请检查网络: %s" % (chap, str(err)))
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
                f.write("\n")
                f.write(title)
                f.write("\n")
                f.write(content)
                f.write("\n\n")

            sys.stdout.write("已下载:%.1f%%" % float((count / total) * 100) + '\r')
            sys.stdout.flush()

        if success:
            print("下载完成: %s" % name)
            print("追加模式下载可能存在内容乱码问题，请移走原文件重新下载并将下载内容手动添加至原文件")
        else:
            print("下载失败")

    def main(self):
        parser = argparse.ArgumentParser(description='单线程模式从www.biquge5200.com下载小说')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-s', type=str, dest="search", help="关键字搜索，后跟书名或作者关键字")
        group.add_argument('-d', type=str, dest="download", help="下载，后跟完整书名")
        group.add_argument('-c', type=str, nargs=2, dest="args", help="返回指定书籍指定章节的标题和url")
        parser.add_argument('-u', type=str, dest="url", help="下载起始位置，若此参数存在则从指定url开始下载，不存在则从头下载")
        arguments = parser.parse_args()

        if arguments.search:
            return self.search(arguments.search.strip())
        elif arguments.download:
            if arguments.url:
                self.download(arguments.download.strip(), arguments.url.strip())
            else:
                self.download(arguments.download.strip())
        elif arguments.args:
            return self.chapters(arguments.args[0], arguments.args[1])
        else:
            parser.print_usage()
            sys.exit(0)


if __name__ == "__main__":
    bqg = Biquge()
    try:
        bqg.main()
    except KeyboardInterrupt:
        print("退出")
