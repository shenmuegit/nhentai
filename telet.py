from telethon import TelegramClient, events, sync

 
if __name__ == '__main__':
    # These example values won't work. You must get your own api_id and
    # api_hash from https://my.telegram.org, under API Development.
    api_id = 25066153
    api_hash = '1858222b25dbe9dbb87f88d1017fbb9b'

    client = TelegramClient('session_name', api_id, api_hash, proxy={
        'proxy_type': 'socks5',
        'addr': '127.0.0.1',
        'port': 1080
    })
    client.start()
    
    print(client.get_me().stringify())
    for dialog in client.iter_dialogs():
        print(dialog.name, dialog.id)
    client.delete_messages(-1002105586384,message_ids=[20,21,22,23,24,25,27,26,28])
    # client.parse_mode = None
    # client.send_file('meolordshen', 'D:/code/python/htai/app.py', thumb='C:/Users/Administrator/Desktop/appicon.png')
    # client.loop.run_until_complete(test(client))
    # client.send_message(-1002105586384, 'name: hello world \npage: 99\nlanguages: #chinese #english\nartists: #abc #cbe\ntags: #r3grf #fsgb #dbgfhnj #gtrjh', 
    #                               file='C:/Users/Administrator/Desktop/appicon.zip', thumb='C:/Users/Administrator/Desktop/appicon.png')
    # asyncio.run(test(client))
    # client.download_profile_photo('me')
    # messages = client.iter_messages(-1002105586384)
    # client.download_file()
    # for i in messages:
    #     print(i.stringify())
    #     # 下载
    #     client.download_media(i,"G:/hman/nhentai/book/")

        
    # str = messages[0].stringify()
    # msg = messages[0].download_media()