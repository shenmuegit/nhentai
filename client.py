import urllib.request
import time
import re
import os
from pyquery import PyQuery as pq
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import shutil
from telethon import TelegramClient, events, sync
import oss2
import sys
import hashlib


endpoint = 'http://oss-cn-beijing.aliyuncs.com'
auth = oss2.Auth('1', '1')
bucket = oss2.Bucket(auth, endpoint, 'nhentai')
thread_poll = ThreadPoolExecutor(max_workers=5)
blocking_queue = queue.Queue(maxsize=20)
api_id = 3

api_hash = '2'
# client = TelegramClient('session_name', api_id, api_hash,proxy={
#         'proxy_type': 'socks5',
#         'addr': '127.0.0.1',
#         'port': 1080
#     })
client = TelegramClient('session_name', api_id, api_hash)
client.start()
print(client.get_me().stringify())
# conn = psycopg2.connect(
#     dbname="nhentai",
#     user="postgres",
#     password="shuyumeng2",
#     host="localhost",
#     port="5432",
# )
# proxy = 'http://127.0.0.1:1081'
path = "/home/"
cookie = "cf_chl_3=25bea0854b45673; cf_clearance=i0fqNQTsepQT6MTCOBxhGzfDlULY5SXrb5Xmgy5gGmM-1714810118-1.0.1.1-taC7s437.2Afc_vlcl4PlIhzFnBM_tm1HHPrTDnDdsIFiSuE6HPwI0u3HJL5BkBtWqAVh6yHz8cWYGT0V.Ra1w; csrftoken=Bv6SCDJDfJ2qDb8Wf37iV3wqkatqMBhDXsJktEDXKlwawUwzd2n9Y0d652n8EgUE"
# httpproxy_handler = urllib.request.build_opener()
opener = urllib.request.build_opener()       
# download_proxy_handler = urllib.request.ProxyHandler({'http': proxy,'https': proxy})
download_opener = urllib.request.build_opener()

def get(url, opener, max_retries=99):
    retries = 0
    while retries < max_retries:
        try:
            response = opener.open(url)
            return response.read().decode("utf-8")
        except Exception as e:
            print(f"Failed to get image page: {e}")
            time.sleep(2)
            retries += 1
    print(f"get failed after {max_retries} retries")

def start(startIndex):
    print("cookie:" + cookie)
    access_shared_resource()
    for pagenum in range(startIndex, 530):
        request = urllib.request.Request("https://nhentai.net/search/?q=pages%3A%3E100+chinese&page=" + str(pagenum))
        html = get(request, opener)
        d = pq(html)
        d = d(".index-container").eq(0)
        lis = d('a').items()
        print("pagenum:" + str(pagenum))
        for i in lis:
            href = i.attr("href")
            name = i(".caption").text()
            # 删除name中每一对[]中的内容,包括[]本身
            name = re.sub(r'\[[^\]]*\]', '', name)
            # 删除两边的空格
            name = name.strip()
            # md5 name
            key = hashlib.md5(name.encode()).hexdigest()
            if existByName(key):
                print(f"continue exist {name}")
                continue
            addBookTmp(key)
            download(href,path,name,key)
    print("name exist")

def access_shared_resource():
    def downloadAndDetails():
        while True:
            data = blocking_queue.get(block=True)
            down(data['path'],data['url'],20)
            blocking_queue.task_done() 
    thread_poll.submit(downloadAndDetails)
    thread_poll.submit(downloadAndDetails)
    thread_poll.submit(downloadAndDetails)
    

def down(path, image, max_retries=20):
    retries = 0
    # 截取 从第一个.开始最后一个.结尾
    suffix = image[image.find("."):image.rfind(".")]
    domain = [3,5,7]
    type = [".png",".jpg"]
    urls = []
    for i in domain:
        for t in type:
            urls.append(image[:9] + str(i) + suffix + t)
    # print(urls)
    index = 0
    while retries < max_retries:
        try:
            response = download_opener.open(urllib.request.Request(image), timeout=10)
            print(f"Downloaded image to {path}, PATH:{image}")
            with open(path, "wb") as f:
                f.write(response.read())
            return  # Download successful, exit the loop
        except urllib.error.URLError as e:
            print(f"HTTPError download: {e} ,PATH:{image}")
            # 如果状态是404
            if e.code == 404:
                image = urls[index]
                index += 1
                if index == 6:
                    print(f"Image not found, all tried, PATH:{image}")
                    break
            retries += 1  
            # 超时重试
        except Exception as e:
            time.sleep(1)
            print(f"Exception download: {e} ,PATH:{image}")
            return
    print(f"Download failed after {max_retries} retries")

def download(key, path, name, hash):
    print(f'key:{key},path:{path}')
    request = urllib.request.Request(f'https://nhentai.net{key}')
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
    filename = key[key.find('/') + 1:key.rfind('/')]
    filename = filename[filename.find("/") + 1:]
    dir = path + filename
    # 创建目录
    os.makedirs(dir,exist_ok=True)
    # 遍历 pages, 从1到pages
    for i in range(1, int(pages) + 1):
        image = f"{imageDomain}{i}.jpg"
        # i = 最后一个
        blocking_queue.put({
                "path":dir + "/" + str(i) + ".jpg",
                "url":image
        })
        while i == int(pages):
            if blocking_queue.empty():
                details(name,key,dir,hash)
                break
    print(f"download full {key}")

def details(name,key,dir,hash):
    request = urllib.request.Request(f'https://nhentai.net{key}')
    html = get(request, opener)
    d = pq(html)
    # 找到class=tag-container的div
    divs = d('.tag-container')
    tags = []
    page = 0
    languages = ''
    artists = []
    # 遍历divs
    for i in divs.items():
        # 如果text包含Tags
        if i.text().find('Tags') != -1:
            # 找到class=tags下的a标签中的class=name的span标签
            tagsHtml = i('a')
            # 遍历tagsHtml将所有text新增到tags
            for j in tagsHtml.items():
                tags.append(j('.name').text())
        # 如果text包含Pages
        elif i.text().find('Pages') != -1:
            page = i('.tags').eq(0)('.tag').eq(0)('span').eq(0).text()
        # 如果包含Languages
        elif i.text().find('Languages') != -1:
            languagesHtml = i('.tags')('a')
            # 遍历languagesHtml
            for j in languagesHtml.items():
                # 找到其中每一个class=name的span标签的text
                languages += j('.name').text() + ','
            # 删除最后一个逗号
            languages = languages[:-1]
         # 如果text包含Artists   
        elif i.text().find('Artists') != -1:
            artistsHtml = i('.tags')('a')
            # 遍历artistsHtml找到其中每一个span的class=name的text放到artists
            for j in artistsHtml.items():
                artists.append(j('.name').text())
    # 如果tags不为空
    tagStr = ''
    if tags:
        # tags = queryTags(cur,tags)
        for i in tags:
            tagStr += f"#{i} "
    # 如果artists不为空
    artistsStr = ''
    if artists:
        # artists = queryArtists(cur,artists)
        for i in artists:
            artistsStr += f"#{i} "
    languagesStr = ''
    if languages:
        # 遍历languages，给每个languages[i]前加一个#
        for i in languages.split(','):
            languagesStr += f"#{i} "
    # 删除第一个/
    key = key[1:]
    # addBook(cur,name,page,languages,f'https://nhentai.net/{key}',f'{path}{key}')
    # addBookArtists(cur,bookId,artists)
    # addBookTags(cur,bookId,tags)
    # 截取key的第一个/开始到最后一个/结束为止的字符串
    # 压缩目录path为filename.zip文件
    # jpg 或者 png 哪个存在用哪个
    thumb = dir + "/1.jpg"
    if not os.path.exists(thumb):
        thumb = dir + "/1.png"
    # 开始zip 记录时间 格式化
    print(f"start zip {dir} " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    shutil.make_archive(dir, 'zip', dir)
    print(f"end zip {dir} " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    client.send_message(-1002105586384, f'name: {name} \npage: {page}\nlanguages: {languagesStr}\nartists: {artistsStr}\ntags: {tagStr}', 
                        file = dir + ".zip", 
                        thumb = thumb)
    print(f"send message {name} " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    # 删除目录
    shutil.rmtree(dir, ignore_errors=True)
    # 删除文件
    os.remove(dir + ".zip")
    bucket.put_object(hash, "")
    bucket.delete_object("tmp_" + hash)
    print(f"name:{name} page:{page} languages:{languages} artists:{artists} tags:{tags}")

def addBookArtists(cur,bookId,artists):
    for i in artists:
        cur.execute("INSERT INTO book_artist (book_id,artist_id) VALUES (%s,%s)", (bookId,i))

def addBookTags(cur,bookId,tags):
    for i in tags:
        cur.execute("INSERT INTO book_tag (book_id,tag_id) VALUES (%s,%s)", (bookId,i))

def addBookTmp(key):
   bucket.put_object("tmp_" + key, "")

def addBook(cur,name,page,languages,url,path):
    cur.execute("INSERT INTO book (name,page,language,url,path) VALUES (%s,%s,%s,%s,%s) RETURNING id", (name,page,languages,url,path))
    return cur.fetchone()[0]

def queryArtists(cur,artists):
    # artists是列表
    cur.execute("SELECT id,name FROM artist WHERE name in %s", (tuple(artists),))
    dbArtists = cur.fetchall()
    # 对比 将artists中的每一个artist与dbArtists中的每一个name对比,不存在的插入数据库并获取id
    for i in artists:
        exist = False
        for j in dbArtists:
            if i == j[1]:
                exist = True
                break
        if not exist:
            cur.execute("INSERT INTO artist (name) VALUES (%s) RETURNING id", (str(i),))
            dbArtists.append((cur.fetchone(),i))
    # 返回id列表
    return [i[0] for i in dbArtists]

def queryTags(cur,tags):
    cur.execute("SELECT id,name FROM tag WHERE name in %s", (tuple(tags),))
    dbTags = cur.fetchall()
    # 对比 将tags中的每一个tag与dbTags中的每一个name对比,不存在的插入数据库并获取id
    for i in tags:
        exist = False
        for j in dbTags:
            if i == j[1]:
                exist = True
                break
        if not exist:
            cur.execute("INSERT INTO tag (name) VALUES (%s) RETURNING id", (str(i),))
            dbTags.append((cur.fetchone(),i))
    # 返回id列表
    return [i[0] for i in dbTags]


def existByName(key):
    return bucket.object_exists(key) or bucket.object_exists("tmp_" + key)

if __name__ == '__main__':
    # 参数 命令行获取
    startIndex = int(str(sys.argv[1]))
    cookie = str(sys.argv[2])
    opener.addheaders = [
            ("accept",'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'),
            ("accept-language",'en,zh-CN;q=0.9,zh;q=0.8'),
            ("cookie",cookie),
            ("priority",'u=0, i'),
            ("sec-ch-ua",'"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'),
            ("sec-ch-ua-arch",'"x86"'),
            ("sec-ch-ua-bitness",'"64"'),
            ("sec-ch-ua-full-version",'"124.0.6367.91"'),
            ("sec-ch-ua-full-version-list",'"Chromium";v="124.0.6367.91", "Google Chrome";v="124.0.6367.91", "Not-A.Brand";v="99.0.0.0"'),
            ("sec-ch-ua-mobile",'?0'),
            ("sec-ch-ua-model",'""'),
            ("sec-ch-ua-platform",'"Windows"'),
            ("sec-ch-ua-platform-version",'"10.0.0"'),
            ("sec-fetch-dest",'document'), 
            ("sec-fetch-mode",'navigate'),
            ("sec-fetch-site",'same-origin'),
            ("sec-fetch-user",'?1'),
            ("upgrade-insecure-requests",'1'),
            ("user-agent",'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    ] 
    download_opener.addheaders = [
            ("accept",'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'),
            ("accept-language",'en,zh-CN;q=0.9,zh;q=0.8'),
            ("cookie",cookie),
            ("priority",'u=0, i'),
            ("sec-ch-ua",'"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'),
            ("sec-ch-ua-mobile",'?0'),
            ("sec-ch-ua-platform",'"Windows"'),
            ("sec-fetch-dest",'document'),
            ("sec-fetch-mode",'navigate'),
            ("sec-fetch-site",'none'),
            ("sec-fetch-user",'?1'),
            ("upgrade-insecure-requests",'1'),
            ("user-agent",'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    ]
    print(f'page:{startIndex},cookie:{cookie}')
    start(startIndex)
    # conn.close()