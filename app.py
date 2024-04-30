from flask import Flask, request, Response, send_file
from zipfile import ZipFile
from pyquery import PyQuery as pq
import urllib.request
import shutil
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures

path = "/home/acg/"
# path = "/Users/zhenzijun/Downloads/a/"
thread_poll = ThreadPoolExecutor(max_workers=5)
app = Flask(__name__)

def responseDown(filename):
    # 流式读取
    def send_file():
        with open(filename, 'rb') as targetfile:
            while 1:
                data = targetfile.read(5 * 1024 * 1024)  # 每次读取20M
                if not data:
                    break
                yield data
    response = Response(send_file(), content_type='application/octet-stream')
    response.headers["Content-disposition"] = 'attachment; filename=%s' % filename  # 如果不加上这行代码，导致下图的问题
    return response


@app.route('/api/get_data', methods=['GET'])
def get_data():
    key = request.args.get('key')
    cookie = request.args.get('cookie')
    if key:
        filename = key[key.find('/') + 1:key.rfind('/')]
        # 第一个/开始到末尾
        filename = filename[filename.find("/") + 1:]
        file = f'{path}{filename}.zip'
        if not os.path.exists(file):
            # 删除目录
            shutil.rmtree(f'{path}{filename}', ignore_errors=True)
            download(key, cookie, path)
        # 通过 with 语句将临时文件发送给用户，并在下载完成后删除临时文件
        return send_file(file, as_attachment=True)
    else:
        return 'Please provide a key parameter.'


def get(url, opener, max_retries=99):
    retries = 0
    while retries < max_retries:
        try:
            response = opener.open(url)
            return response.read().decode("utf-8")
        except Exception as e:
            print(f"Failed to get image: {e}, url:{url}")
            time.sleep(2)
            retries += 1
    print(f"get failed after {max_retries} retries")

def down(url, opener, path, image, max_retries=20):
    retries = 0
    jpg = False
    png = False
    three = False
    five = False
    while retries < max_retries:
        try:
            response = opener.open(url, timeout=10)
            with open(path, "wb") as f:
                f.write(response.read())
            print(f"Downloaded image to {path}, PATH:{image}")
            return  # Download successful, exit the loop
        except Exception as e:
            time.sleep(1)
            url = urllib.request.Request(image)
            print(f"Failed to download image: {e} ,PATH:{image}")
            # 如果状态是404
            if hasattr(e, 'code') and e.code == 404:
                if not png and image.find(".jpg") != -1:
                    image = image.replace(".jpg", ".png")
                    png = True
                    print(f"Image not found, png trying {image}")
                elif not jpg and image.find(".png") != -1:
                    image = image.replace(".png", ".jpg")
                    jpg = True
                    print(f"Image not found, jpg trying {image}")
                # 如果image的第9位是3则修改为5，否则修改为3
                if not five and image[9] == '3':
                    image = image[:9] + '5' + image[10:]
                    five = True
                    print(f"Image not found, trying {image}")
                elif not three:
                    image = image[:9] + '3' + image[10:]
                    three = True
                    print(f"Image not found, trying {image}")
                if jpg and png and three and five:
                    print(f"Image not found, all tried, PATH:{image}")
                    break
            retries += 1
    print(f"Download failed after {max_retries} retries")

def download(key, cookie, path):
    # 链接本地代理1080
    # httpproxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:1081','https': 'http://127.0.0.1:1081'})
    httpproxy_handler = urllib.request.HTTPHandler()
    # 代理:method: POST
    opener = urllib.request.build_opener(httpproxy_handler)
    request = urllib.request.Request(f'https://nhentai.net{key}')
    opener.addheaders = [
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Language", "zh-CN,zh-Hans;q=0.9"),
        ("Connection", "keep-alive"),
        ("Cookie", cookie),
        ("Host", "nhentai.net"),
        ("Referer", "https://nhentai.net/"),
        ("Sec-Fetch-Dest", "document"),
        ("Sec-Fetch-Mode", "navigate"),
        ("Sec-Fetch-Site", "same-origin"),
        ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15")
    ]
    html = get(request, opener)
    d = pq(html)
    # 找到id = tags的section标签
    tags = d('#tags')
    # 遍历找到class=tag-container并且text中包含Pages字符串的节点
    pages = tags('.tag-container').filter(lambda i, this: pq(this).text().find('Pages') != -1)
    # 找到第一个class=tags内的第一个class=tag内的第一个span中的text
    pages = pages('.tags').eq(0)('.tag').eq(0)('span').eq(0).text()
    imageDomain = d(".lazyload").eq(0).attr('data-src')
    # 截取从第9到最后一个/为止
    imageDomain = "https://i" + imageDomain[9:imageDomain.rfind('/') + 1]
    downloadOpener = urllib.request.build_opener(httpproxy_handler)
    downloadOpener.addheaders = [
            ("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Sec-Fetch-Site", "none"),
            ("Cookie", cookie),
            ("Sec-Fetch-Mode", "navigate"),
            ("Host", "i3.nhentai.net"),
            ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"),
            ("Accept-Language", "zh-CN,zh-Hans;q=0.9"),
            ("Sec-Fetch-Dest", "document"),
            ("Connection", "keep-alive")
    ]
    all_task = []
    filename = key[key.find('/') + 1:key.rfind('/')]
    filename = filename[filename.find("/") + 1:]
    dir = path + filename
    # 创建目录
    os.makedirs(dir)
    # 遍历 pages, 从1到pages
    for i in range(1, int(pages) + 1):
        if i != 0 and i % 10 == 0:
            time.sleep(3)
        image = f"{imageDomain}{i}.jpg"
        all_task.append(thread_poll.submit(down, urllib.request.Request(image), downloadOpener, dir + "/" + str(i) + ".jpg",image, 20))
        print("download:" + image + ", path:" + dir + "/" + str(i) + ".jpg")
    concurrent.futures.wait(all_task,timeout=1800, return_when=concurrent.futures.ALL_COMPLETED)
    all_task.clear()
    print("download full " + str(len(all_task)))
    # 截取key的第一个/开始到最后一个/结束为止的字符串
    # 压缩目录path为filename.zip文件
    shutil.make_archive(dir, 'zip', dir)
    # 删除目录
    shutil.rmtree(dir, ignore_errors=True)

if __name__ == '__main__':
    app.run(debug=True,port=8080,host='0.0.0.0')
