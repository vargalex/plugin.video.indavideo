# -*- coding: utf-8 -*-
import xbmc, xbmcgui, urllib, re, xbmcplugin, json
from resources.lib import client, control, history, cache


base_Url = 'https://indavideo.hu'
login_Url = 'https://daemon.indapass.hu/http/login'
user = control.setting('inda.user')
password = control.setting('inda.pass')
sysaddon = sys.argv[0]
sort_by = ['p_date', 'p_views', 'p_rate_num', 'p_comment_num']
msort = int(control.setting('msort'))
adult = '1' if (control.setting('adult') == 'true') else '0'

def get_login(params):
    try:
        if (user == '' or password == ''): raise Exception()    
        post = urllib.urlencode({'partner_id': 'indavideo', 'redirect_to': base_Url, 'username': user, 'password': password})
        cookie = client.request(login_Url, post=post, output='cookie')
        headers = {'Cookie': cookie}
        location = client.request(login_Url, post=post, headers=headers, output='geturl')        
        login = '1' if location == base_Url + '/' else '0'
        return login, cookie
    except:
        return '0', '0'

login, iv_cookie = cache.get(get_login, 12, 'cookie')

def folders():
    addDir('Keresés', '', 1, control.addonIcon(), control.addonFanart(), '', '', '')
    addDir('Ajánlott videók', base_Url + '/browse?', 3, control.addonIcon(), control.addonFanart(), '', '1', '')
    if adult == '1':
        addDir('Ajánlott videók (Erotika)', 'https://erotika.indavideo.hu/browse?', 3, control.addonIcon(), control.addonFanart(), '', '1', '')

    if login == '1':
        addDir('Videóim', base_Url + '/myprofile/myvideos?p_date=', 2, control.addonIcon(), control.addonFanart(), '', '1', '')
        addDir('Megnézendő', base_Url + '/myprofile/mywatchlater?p_date=', 2, control.addonIcon(), control.addonFanart(), '', '1', '')
        addDir('Feliratkozások', base_Url + '/myprofile/mysubscribes?p_date=', 2, control.addonIcon(), control.addonFanart(), '', '1', '')
    if not control.setting('savefolder') == 'Nincs megadva!':
        u=control.setting('savefolder')
        ok=True
        liz=xbmcgui.ListItem('Letöltések', iconImage=control.addonIcon(), thumbnailImage=control.addonIcon())
        cm = []
        liz.addContextMenuItems(cm, replaceItems=True)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    addFile('Beállítások', '', 10, control.addonIcon(), control.addonFanart(), '', '', '0')


def build_search_directory():
    addDir('[B]Új Keresés[/B]', '', 4, iconimage, fanart, '', '1', '')
    try:
        result = history.getHistory()
        for item in result:
            addDir(item[0], '', 4, iconimage, fanart, item[0], '', '-1')
    except:
        pass


def build_search_result():
    if description == None:
        search_text = open_search_panel()
        work_text = ''.join(search_text.split())
        if work_text != '':
            history.addHistory(search_text)
        else:
            return
    else: search_text = description
    
    post = urllib.urlencode({'p_uni': page, 'action': 'search', 'search': search_text, 'view': 'detailed', 'sort_mode': 'magic', 'adult': adult})
    result = client.request(base_Url + '/search?' + post)
    episodes = client.parseDOM(result, 'div', attrs={'class': 'item TYPE_.+?'})
    for item in episodes:
        try:
            title, link, img, plot, duration = getEpisode(item)
            addFile(title.encode('utf-8'), link, 7, img, fanart, plot.encode('utf-8'), duration, '1')
        except:
            pass
    control.content(int(sys.argv[1]), 'movies')
    try:
        next_page = client.parseDOM(result, 'div', attrs={'class': 'btn_next branded_pager_btn'})[0]
        if next_page == '': raise Exception()
        n_page = int(page) + 1
        addDir('[COLOR green]>> Következő oldal >>[/COLOR]', '', 4, iconimage, fanart, search_text, str(n_page), '')
    except:
        pass


def browse():
    post = urllib.urlencode({sort_by[msort]: page})
    result = client.request(url + post)
    episodes = client.parseDOM(result, 'div', attrs={'class': 'item TYPE_.+?'})
    for item in episodes:
        try:
            title, link, img, plot, duration = getEpisode(item)
            addFile(title.encode('utf-8'), link, 7, img, fanart, plot.encode('utf-8'), duration, '1')
        except:
            pass
    control.content(int(sys.argv[1]), 'movies')
    try:
        next_page = client.parseDOM(result, 'div', attrs={'class': 'btn_next branded_pager_btn'})[0]
        if next_page == '': raise Exception()
        n_page = int(page) + 1
        addDir('[COLOR green]>> Következő oldal >>[/COLOR]', url, 3, iconimage, fanart, '', str(n_page), '')
    except:
        pass


def getMyLists():
    result = client.request(url + page, cookie = iv_cookie)
    episodes = client.parseDOM(result, 'div', attrs={'class': 'item TYPE_.+?'})
    filter = []
    [filter.append(x) for x in episodes if x not in filter]
    episodes = filter
    if 'mywatchlater' in url: act = '2'
    elif 'mysubscribes' in url: act = '3'
    else: act = '1'
    for item in episodes:
        try:
            title, link, img, plot, duration = getEpisode(item)
            addFile(title.encode('utf-8'), link, 7, img, fanart, plot.encode('utf-8'), duration, act)
        except:
            pass
    control.content(int(sys.argv[1]), 'movies')
    try:
        next_page = client.parseDOM(result, 'div', attrs={'class': 'btn_next branded_pager_btn'})[0]
        if next_page == '': raise Exception()
        n_page = int(page) + 1
        addDir('[COLOR green]>> Következő oldal >>[/COLOR]', url, 2, iconimage, fanart, description, str(n_page), '')
    except:
        pass


def watchLater(url, action, silent = ''):
    try:
        title = url.split('/')[-1]
        post = urllib.urlencode({'op': 'watchlater', 'action': 'videoHandler', 'addOrRemove': action, 'url_title': title})
        result = client.request(base_Url + '/videohandler', cookie=iv_cookie, post=post)
        if '"success":1' in result and action == '1':
            control.infoDialog(u'Megn\u00E9zend\u0151kh\u00F6z hozz\u00E1adva', name)
        elif '"success":1' in result and action == '0' and silent == '':
            control.refresh()
            control.infoDialog(u'Megn\u00E9zend\u0151kb\u0151l elt\u00E1vol\u00EDtva', name)
    except:
        return


def subscribe():
    try:
        result = client.request(url, cookie=iv_cookie)
        user = client.parseDOM(result, 'div', attrs={'class': 'playlist_subscribe.+?'}, ret='data-user')[0]
        post = urllib.urlencode({'op': 'subscribe', 'addOrRemove': action, 'digest_frequency': '10', 'uid': 'null', 'CSRF': ''})
        result = client.request(base_Url + '/userhandler/' + user, cookie=iv_cookie, post=post)
        if '"success":1' in result and action == '1':
            control.infoDialog(u'Sikeres feliratkoz\u00E1s', user)
        elif '"success":1' in result and action == '0':
            control.refresh()
            control.infoDialog(u'Sikeres leiratkoz\u00E1s', user)
    except:
        pass


def getvideo(url, action, name, iconimage):
    result = client.request(url)

    emb_hash = client.parseDOM(result, 'input', attrs={'id': 'emb_hash'}, ret='value')[0]
    emb_hash = emb_hash.encode('utf-8')
    query = 'http://amfphp.indavideo.hu/SYm0json.php/player.playerHandler.getVideoData/' + emb_hash

    result = client.request(query)
    data = json.loads(result)['data']
  
    video_urls = []

    video_files = data.get('video_files')
    if isinstance(video_files, list):
        video_urls.extend(video_files)
    elif isinstance(video_files, dict):
        video_urls.extend(video_files.values())

    video_file = data.get('video_file')
    if video_file:
        video_urls.append(video_file)
    video_urls = list(set(video_urls))

    filesh = data.get('filesh')
        
    video_prefix = video_urls[0].rsplit('/', 1)[0]

    for flv_file in data.get('flv_files', []):
        flv_url = '{0}/{1}'.format(video_prefix, flv_file)
        if flv_url not in video_urls:
            video_urls.append(flv_url)

    filter = []
    
        
    sources = []
    for video_url in video_urls:
        try: video_url = video_url.encode('utf-8')
        except: pass
        height = client._search_regex(r'\.(\d{3,4})\.mp4(?:\?|$)', video_url)
        if filesh:
            if not height:
                continue
            token = filesh.get(height)
            if token is None:
                token = filesh.values()[-1]
            q = '&token={}'
            q = '?&channel=main-a&zone=hu' + q if video_url.endswith('.mp4') else q
            video_url = video_url + q.format(token)
        sources.append({
            'height': height,
            'url': video_url,
            })
        
    try: sources = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in sources)]
    except: pass
    sources = sorted(sources, key=lambda x: x['height'])[::-1]

    autopick = control.setting('autopick')

    if len(sources) == 1:
        direct_link = sources[0]['url']
    elif len(sources) > 1:
        if autopick == '1':
            direct_link = sources[0]['url']
        else:
            result = xbmcgui.Dialog().select((u'Min\u0151s\u00E9g'), [source['height'] + 'p' if source['height'] else 'Uknown' for source in sources])
            if result == -1:
                return
            else:
                direct_link = sources[result]['url']

    if direct_link:
        if action == '5':
            from resources.lib import downloader
            downloader.download(name, iconimage, direct_link)
        else:
            item = control.item(path=direct_link)
            item.setArt({'icon': iconimage, 'thumb': iconimage, 'poster': iconimage})
            #item.setInfo(type='Video', infoLabels = meta)
            control.resolve(int(sys.argv[1]), True, item)
            #from resources.lib.player import player
            #player().run(name, direct_link, iconimage, url)
                #if login == '1' and control.setting('watched') == 'true': watchLater(url, '0', '1')

def getEpisode(item):
    try:
        '''
        try: 
            title = client.parseDOM(item, 'a', attrs={'class': 'title'})[0]
            title = re.compile('\s*?(\S.+?)<').findall(title)[0]
        except:
        '''
        title = client.parseDOM(item, 'input', ret='value')[0].replace('_', ' ')
        title = client.replaceHTMLCodes(title)
        
        try:
            img = client.parseDOM(item, 'div', ret='style')[0]
            img = 'http:' + re.search('(//.*\.jpg)', img).group(1)
        except: img = control.addonIcon()

        link = client.parseDOM(item, 'a', ret='href')[0]
        
        try: plot = client.parseDOM(item, 'div', attrs={'class': 'description'})[0]
        except: plot = ''
        
        try:
            duration = client.parseDOM(item, 'div', attrs={'class': 'duration'})[0].split(':')
            if len(duration) == 2: duration = (int(duration[0]) * 60) + int(duration[1])
            elif len(duration) == 3: duration = (int(duration[0]) * 3600) + (int(duration[1]) * 60) + int(duration[2])
        except: duration = 0
        
        return title, link, img, plot, duration
    except:
        return


def open_search_panel():               
    search_text = ''
    keyb = xbmc.Keyboard('','Keresés')
    keyb.doModal()
 
    if (keyb.isConfirmed()):
        search_text = keyb.getText()

    return search_text


def addDir(name, url, mode, iconimage, fanart, description, page, action):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&fanart="+urllib.quote_plus(fanart)+"&description="+urllib.quote_plus(description)+"&page="+urllib.quote_plus(page)+"&action="+urllib.quote_plus(action)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description})
    liz.setProperty( "Fanart_Image", fanart )
    cm = []
    if action == '-1':
        cm.append((u'El\u0151zm\u00E9ny t\u00F6rl\u00E9se', 'RunPlugin(%s?mode=8&name=%s)' % (sysaddon, name)))
        cm.append((u'\u00D6sszes el\u0151zm\u00E9ny t\u00F6rl\u00E9se', 'RunPlugin(%s?mode=9)' % (sysaddon)))
    liz.addContextMenuItems(cm, replaceItems=True)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok


def addFile(name, url, mode, iconimage, fanart, description, duration, action):
    meta = {"Title": name, "Plot": description, "Duration": duration}
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&fanart="+urllib.quote_plus(fanart)+"&description="+urllib.quote_plus(description)+"&duration="+str(duration)+"&action="+urllib.quote_plus(action)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels=meta)
    liz.setProperty('IsPlayable', 'true')
    liz.setProperty( "Fanart_Image", fanart )
    cm = []
    if (action == '1' and login == '1'):
        cm.append((u'Hozz\u00E1ad\u00E1s a megn\u00E9zend\u0151kh\u00F6z', 'RunPlugin(%s?mode=5&url=%s&action=%s&name=%s)' % (sysaddon, url, '1', name.decode('utf-8'))))
        cm.append((u'Elt\u00E1vol\u00EDt\u00E1s a megn\u00E9zend\u0151kb\u0151l', 'RunPlugin(%s?mode=5&url=%s&action=%s&name=%s)' % (sysaddon, url, '0', name.decode('utf-8'))))
        cm.append((u'Feliratkoz\u00E1s', 'RunPlugin(%s?mode=6&url=%s&action=%s)' % (sysaddon, url, '1')))
    elif (action == '2' and login == '1'):
        cm.append((u'Elt\u00E1vol\u00EDt\u00E1s a megn\u00E9zend\u0151kb\u0151l', 'RunPlugin(%s?mode=5&url=%s&action=%s&name=%s)' % (sysaddon, url, '0', name.decode('utf-8'))))
        cm.append((u'Feliratkoz\u00E1s', 'RunPlugin(%s?mode=6&url=%s&action=%s)' % (sysaddon, url, '1')))
    elif (action == '3' and login == '1'):
        cm.append((u'Hozz\u00E1ad\u00E1s a megn\u00E9zend\u0151kh\u00F6z', 'RunPlugin(%s?mode=5&url=%s&action=%s&name=%s)' % (sysaddon, url, '1', name.decode('utf-8'))))
        cm.append((u'Elt\u00E1vol\u00EDt\u00E1s a megn\u00E9zend\u0151kb\u0151l', 'RunPlugin(%s?mode=5&url=%s&action=%s&name=%s)' % (sysaddon, url, '0', name.decode('utf-8'))))
        cm.append((u'Leiratkoz\u00E1s', 'RunPlugin(%s?mode=6&url=%s&action=%s)' % (sysaddon, url, '0')))
    if not action == '0':
        cm.append((u'Lej\u00E1tsz\u00E1si list\u00E1hoz ad', 'RunPlugin(%s?mode=11)' % sysaddon))
        cm.append((u'Lej\u00E1tsz\u00E1si lista', 'RunPlugin(%s?mode=12)' % sysaddon))
        if not control.setting('savefolder') == 'Nincs megadva!':
            cm.append((u'Let\u00F6lt\u00E9s', 'RunPlugin(%s?mode=7&url=%s&action=%s&name=%s&iconimage=%s)' % (sysaddon, url, '5', name.decode('utf-8'), iconimage)))
    liz.addContextMenuItems(cm, replaceItems=True)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    return ok

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

params = get_params()
url = None
name = None
mode = None
iconimage = None
fanart = None
description = None
page = '1'
duration = None
action = None
silent = ''

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage = urllib.unquote_plus(params["iconimage"])
except:
    pass
try:        
    mode = int(params["mode"])
except:
    pass
try:        
    fanart = urllib.unquote_plus(params["fanart"])
except:
    pass
try:        
    description = urllib.unquote_plus(params["description"])
except:
    pass
try:
    page = urllib.unquote_plus(params["page"])
except:
    pass
try:        
    duration = int(params["duration"])
except:
    pass
try:        
    action = urllib.unquote_plus(params["action"])
except:
    pass

if mode==None:
    folders()
elif mode==1:
    build_search_directory()
elif mode==2:
    getMyLists()
elif mode==3:
    browse()
elif mode==4:
    build_search_result()
elif mode==5:
    watchLater(url, action, silent)
elif mode==6:
    subscribe()
elif mode==7:
    getvideo(url, action, name, iconimage)
elif mode==8:
    history.deleteHistory(name)
elif mode==9:
    history.clear()
elif mode==10:
    control.openSettings()
elif mode==11:
    control.queueItem()
elif mode==12:
    control.openPlaylist()
elif mode==13:
    cache.clear()
    
xbmcplugin.endOfDirectory(int(sys.argv[1]))
