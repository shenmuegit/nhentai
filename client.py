import psycopg2
import urllib.request
import time
import re
import threading
from pyquery import PyQuery as pq
from concurrent.futures import ThreadPoolExecutor, as_completed

semaphore = threading.Semaphore(1)
thread_poll = ThreadPoolExecutor(max_workers=1)
conn = psycopg2.connect(
    dbname="nhentai",
    user="postgres",
    password="shuyumeng2",
    host="localhost",
    port="5432",
)
path = "/Users/zhenzijun/Downloads/nhentai/"
# map
ipCookie = [
    # {"ip": "192.3.25.104", "cookie":"csrftoken=yUvus0YMmIrp3HixMx1vR5XbUmnlwIvLC7toMY2joCHQj6OHpb4rztSbdFeg5l5I; cf_clearance=KmD2FNJAV0Y.hzqp2QnZ8s05rTPYJqhsy1db2JnsM60-1714446289-1.0.1.1-_ZTmoiYY96Oa_uReasjy5s2m4GCCLDhLn2gjdQkNP3_6mVnjT7gaYJzySy_jmDAe_SuEeledJJAQk3v4hA3jsg"},
    # {"ip": "198.23.173.72", "cookie":"csrftoken=yUvus0YMmIrp3HixMx1vR5XbUmnlwIvLC7toMY2joCHQj6OHpb4rztSbdFeg5l5I; cf_clearance=dsI9BMLXR.FYje.ii41gygHvPdyUMd0Ci_efh98RCi8-1714384176-1.0.1.1-vg8p2lqF1xnJNnntIyC1UUePRbL5vV7xj9OnDuswXwZOTl0ZuavOkVDyCwcd4nzEdg9fa7UO4cdjkpOvPY3idw"},
    {"ip": "206.237.18.105", "cookie":"cf_clearance=ItXpHZCDRb0grSAOXkWQklPPy0dHxQix0lADXIOsSJ8-1714447237-1.0.1.1-U3FaNnP6l3I_9Qg8S8QoSaUayIVfeGSJJvKDsWECusqsYOPGp5QmeipFizCvNjJ53eJmmFfThEWhnz941kAXJA; csrftoken=KI69t26ByT4IHMcRmoXahpRrbhPLMTRbCQrtLUIA2Gs1o9L8TSrVT08eJGyfs1qH"}
]
ipIndex = -1
cookie = 'csrftoken=KI69t26ByT4IHMcRmoXahpRrbhPLMTRbCQrtLUIA2Gs1o9L8TSrVT08eJGyfs1qH; cf_clearance=iqji9oLep3W..nAzWVbJwo9CJnowEANASz5M3Hr1UAQ-1714447548-1.0.1.1-Y7QiQACjHk8nV6b986nCG_Rek.aq9X_eS0Gb85PgzaIIoXxtCWuY8GwEnY0F2kn3.pL344POlOW3zgZnP4HvWw'

def chooseIp():
    # 按顺序
    global ipIndex
    ipIndex += 1
    return ipCookie[ipIndex % 1]

def get(url, opener, max_retries=99):
    retries = 0
    while retries < max_retries:
        try:
            response = opener.open(url)
            return response.read().decode("utf-8")
        except Exception as e:
            print(f"Failed to get image: {e}")
            time.sleep(2)
            retries += 1
    print(f"get failed after {max_retries} retries")

def start(cookie):
    index = 0
    for pagenum in range(1, 392):
        httpproxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:1081','https': 'http://127.0.0.1:1081'})
        # httpproxy_handler = urllib.request.HTTPHandler()
        opener = urllib.request.build_opener(httpproxy_handler)
        request = urllib.request.Request("https://nhentai.net/search/?q=pages%3A%3E100+chinese&page=" + str(pagenum))

        header = [
            ("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"),
            ("accept-language", "en,zh-CN;q=0.9,zh;q=0.8"),
            ("cache-control", "max-age=0"),
            ("content-type", "application/x-www-form-urlencoded"),
            ("cookie", cookie),
            ("origin", "https://nhentai.net"),
            ("priority","u=0, i"),
            ("Referer", "https://nhentai.net/"),
            ("sec-ch-ua", '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'),
            ("sec-ch-ua-arch", '"arm"'),
            ("sec-ch-ua-bitness", '"64"'),
            ("sec-ch-ua-full-version", '"124.0.6367.91"'),
            ("sec-ch-ua-full-version-list", 'Chromium";v="124.0.6367.91", "Google Chrome";v="124.0.6367.91", "Not-A.Brand";v="99.0.0.0"'),
            ("sec-ch-ua-mobile", "?0"),
            ("sec-ch-ua-model", '""'),
            ("sec-ch-ua-platform", '"macOS"'),
            ("sec-ch-ua-platform-version", '"14.4.1"'),
            ("sec-fetch-dest", "document"),
            ("sec-fetch-mode", "navigate"),
            ("sec-fetch-site", "same-origin"),
            ("sec-fetch-user", "?1"),
            ("upgrade-insecure-requests", "1"),
            ("user-agent", 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        ]
        opener.addheaders = header
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
            if existByName(name):
                print(f"continue exist {name}")
                continue
            map = chooseIp()
            ip = map["ip"]
            cookie = map["cookie"]
            with semaphore:
                print(f'{ip},{href}')
                cookie = urllib.parse.quote(cookie)
                thread_poll.submit(access_shared_resource,ip,href,cookie,name,header)
    print("name exist")

def access_shared_resource(ip,href,cookie,name,header):
    with semaphore: 
        # 在临界区内，对共享资源进行操作
        while not download(ip,href,cookie):
            time.sleep(5)
        details(name,href,header)

def download(ip,key,cookie):
    httpproxy_handler = urllib.request.HTTPHandler()
    opener = urllib.request.build_opener(httpproxy_handler)
    request = urllib.request.Request(f'http://{ip}:8080/api/get_data?key={key}&cookie={cookie}')
    filename = key[key.find('/') + 1:key.rfind('/')]
    filename = filename[filename.find("/") + 1:]
    response = opener.open(request,timeout=3600)
    # 判断响应头Content-Type
    if response.getheader('Content-Type') == 'application/zip':
        # 保存文件到path
        with open(f'{path}{filename}.zip', 'wb') as f:
            f.write(response.read())
        print(f"Downloaded image to {path}{filename}.zip")
        return True
    # 如果不是文件则判断字符串是不是download
    elif response.read().decode("utf-8") == 'download':
        print(f"Downloaded image to {path}{filename}.zip")
    else:
        # 输出错误信息
        print(f"Failed to download image: {response.read().decode('utf-8')}")
    return False

def details(name,key,header):
    httpproxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:1081','https': 'http://127.0.0.1:1081'})
    opener = urllib.request.build_opener(httpproxy_handler)
    request = urllib.request.Request(f'https://nhentai.net{key}')
    opener.addheaders = header
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
            tagsHtml = i('.tags')('a').filter(lambda i, this: pq(this).attr('class') == 'name')
            # 遍历tagsHtml将所有text新增到tags
            for j in tagsHtml.items():
                tags.append(j.text())
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
    if tags:
        tags = queryTags(tags)
    # 如果artists不为空
    if artists:
        artists = queryArtists(artists)
    key = key[key.find('/') + 1:key.rfind('/')]
    key = key[key.find("/") + 1:]
    bookId = addBook(name,page,languages,f'https://nhentai.net{key}',f'/Users/shuyumeng/Documents/nhentai/{key}')
    addBookArtists(bookId,artists)
    addBookTags(bookId,tags)
    conn.commit()
    print(f"bookId:{bookId} name:{name} page:{page} languages:{languages} artists:{artists} tags:{tags}")

def addBookArtists(bookId,artists):
    cur = conn.cursor()
    for i in artists:
        cur.execute("INSERT INTO book_artist (book_id,artist_id) VALUES (%s,%s)", (bookId,i))

def addBookTags(bookId,tags):
    cur = conn.cursor()
    for i in tags:
        cur.execute("INSERT INTO book_tag (book_id,tag_id) VALUES (%s,%s)", (bookId,i))

def addBook(name,page,languages,url,path):
    cur = conn.cursor()
    cur.execute("INSERT INTO book (name,page,languages,url,path) VALUES (%s,%s,%s,%s,%s) RETURNING id", (name,page,languages,url,path))
    return cur.fetchone()[0]

def queryArtists(artists):
    cur = conn.cursor()
    cur.execute("SELECT id,name FROM artist WHERE name = %s", (artists,))
    dbArtists = cur.fetchall()
    # 对比 将artists中的每一个artist与dbArtists中的每一个name对比,不存在的插入数据库并获取id
    for i in artists:
        exist = False
        for j in dbArtists:
            if i == j[1]:
                exist = True
                break
        if not exist:
            cur.execute("INSERT INTO artist (name) VALUES (%s) RETURNING id", (i,))
            dbArtists.append((cur.fetchone(),i))
    # 返回id列表
    return [i[0] for i in dbArtists]

def queryTags(tags):
    cur = conn.cursor()
    cur.execute("SELECT id,name FROM tag WHERE tags = %s", (tags,))
    dbTags = cur.fetchall()
    # 对比 将tags中的每一个tag与dbTags中的每一个name对比,不存在的插入数据库并获取id
    for i in tags:
        exist = False
        for j in dbTags:
            if i == j[1]:
                exist = True
                break
        if not exist:
            cur.execute("INSERT INTO tag (name) VALUES (%s) RETURNING id", (i,))
            dbTags.append((cur.fetchone(),i))
    # 返回id列表
    return [i[0] for i in dbTags]


def existByName(name):
    cur = conn.cursor()
    cur.execute("SELECT * FROM book WHERE name = %s", (name,))
    return cur.fetchone() is not None

if __name__ == '__main__':
    start(cookie)
    conn.close()