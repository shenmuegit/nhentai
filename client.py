import psycopg2
import urllib.request
import time
import re
import threading
from pyquery import PyQuery as pq
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures

semaphore = threading.Semaphore(3)
thread_poll = ThreadPoolExecutor(max_workers=3)
conn = psycopg2.connect(
    dbname="nhentai",
    user="postgres",
    password="shuyumeng2",
    host="localhost",
    port="5432",
)
path = "/Users/shuyumeng/Documents/nhentai/"
# map
ipCookie = [
    # {"ip": "", "cookie":""},
    # {"ip": "", "cookie":""},
    {"ip": "206.237.18.105", "cookie":"cf_chl_3=;%20cf_chl_rc_m=;%20cf_clearance=n2dELdmwQV_qJBg3B2QRWv.Nv0Ejni_WdUAIIyqG.6Y-1714381691-1.0.1.1-NLKS1KBQvF2OUFQMQLRUf0dsD9t_OlhKqtjzVkV0ZdD_cSe7N3VKJJRlKLaCFDdcsgviwIbvxRPML0UHmLeHjA;%20csrftoken=HmP9TyESQtwpoXtuBDxeZWQp5M3xVEZ1gipg4Y3McS7ZStoBK58ACNka3hba9wXV;%20cf_chl_3=3d8d8b5c4bbd4bb;%20cf_chl_rc_m=2"}
]
cookie = 'csrftoken=HmP9TyESQtwpoXtuBDxeZWQp5M3xVEZ1gipg4Y3McS7ZStoBK58ACNka3hba9wXV; cf_chl_3=; cf_chl_rc_m=; cf_clearance=J7ynd5mlXXJ3oT7X0g07W.zdugvu4Hrptunc_hOpGqA-1714382511-1.0.1.1-utjFlzyhMSlrZtdyNS.iR0l3xJEG_z1.iedIPbZBXj42ydqsYNEasQNpxo1.SvYNa5IoQ39D_Rl6HoWA7iHtkw; cf_chl_3=3fe64c4ac310551; cf_chl_rc_m=2'

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
        opener.addheaders = [
            ("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
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
            ip = ipCookie[index]["ip"]
            cookie = ipCookie[index]["cookie"]
            with semaphore:
                print(f'{ip},{href}')
                # index += 1
                thread_poll.submit(access_shared_resource,ip,href,cookie,name)
    print("name exist")

def access_shared_resource(ip,href,cookie,name):
    with semaphore: 
        # 在临界区内，对共享资源进行操作
        while not download(ip,href,cookie):
            time.sleep(5)
        details(name,href,)

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
    return False

def details(name,key,header):
    httpproxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:1081','https': 'http://127.0.0.1:1081'})
    opener = urllib.request.build_opener(httpproxy_handler)
    request = urllib.request.Request(f'https://nhentai.net{key}')
    opener.addheaders = [header]
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