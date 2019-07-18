#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import zlib
import base64
import json
import sys
from datetime import datetime
try:
    from bs4 import BeautifulSoup
    import requests
except ModuleNotFoundError as nfe:
    print(f'Fehler: Ein benötigtes Modul ist nicht installiert: {nfe}', file=sys.stderr)
    sys.exit(1)
try:
    import config
except ModuleNotFoundError as nfe:
    print(f'Fehler: Konfigurationsdatei "config.py" nicht gefunden', file=sys.stderr)
    sys.exit(1)

version = sys.version_info
if version < (3, 7):
    print(f'Die installierte python Version {version.major}.{version.minor}.{version.micro} wird nicht unterstützt. Bitte installieren 3.7.0 oder höher', file=sys.stderr)
    sys.exit(1)

strike_char = '\u0336'

def strike_adjusted_len(text):
    return len(text) - text.count(strike_char)

def strike_adjusted_ljust(text, length):
    length += text.count(strike_char)
    return text.ljust(length)

def strike(text):
    # Windows can't seem to handle the other one
    if 'win' in sys.platform:
        return '-' + text + '-'
    result = ''
    for c in text:
        result += c + strike_char
    return result

def ascii_table(iterable, header):
    header_lens = [len(x) for x in header]
    num_cols = len(header)
    widths = header_lens
    for row in iterable:
        if len(row) != num_cols:
            raise Exception("Number of columns not consistent")
        for idx, col in enumerate(row):
            header_lens[idx] = max(strike_adjusted_len(str(col)), header_lens[idx])
    col_delim = ' | '
    first_col_delim = '| '
    last_col_delim = ' |'
    table_width = sum((x+len(col_delim) for x in header_lens))
    table_width += len(first_col_delim)
    table_width -= abs(len(col_delim) - len(last_col_delim))

    horizontal_decorator = ' ' + ('-' * (table_width-2)) + ' \n'
    out = horizontal_decorator

    out += first_col_delim
    for idx, h in enumerate(header):
        out += h.ljust(header_lens[idx]) + (col_delim if idx != num_cols else last_col_delim)
    out += '\n' + horizontal_decorator

    for row in iterable:
        out += first_col_delim
        for idx, col in enumerate(row):
            out += strike_adjusted_ljust(col, header_lens[idx]) + (col_delim if idx != num_cols else last_col_delim)
        out += '\n'
    out += horizontal_decorator
    return out

base_url = 'https://www.dsbmobile.de/'
user_agent = 'Mozilla/5.0'
s = requests.Session()
headers = {'User-Agent': user_agent}

# Login
s.headers.update(headers)
r = s.get(base_url+'/Login.aspx')
if r.status_code != 200:
    print('Serverfehler von DSB. Versuch es später nochmal!', file=sys.stderr)
    sys.exit(1)
event_validation = re.search(r'id=\"__EVENTVALIDATION\"\ value=\"([^\"]+)\"', r.text).group(1)
viewstate = re.search(r'id=\"__VIEWSTATE\"\ value=\"([^\"]+)\"', r.text).group(1)
r = s.post(base_url+'/Login.aspx', data= {
    'txtUser' : config.DSB['login'],
    'txtPass' : config.DSB['password'],
    '__VIEWSTATE' : viewstate,
    '__EVENTVALIDATION' : event_validation,
    'ctl03': config.DSB['loginbutton']
    })
s.get(base_url+'/Default.aspx')

# get data
req_time = datetime.isoformat(datetime.utcnow(), timespec='milliseconds')+'Z'
dsb_data = '{"UserId":"","UserPw":"","Abos":[],"AppVersion":"2.3","Language":"de","OsVersion":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0","AppId":"","Device":"WebApp","PushId":"","BundleId":"de.heinekingmedia.inhouse.dsbmobile.web","Date":"'+req_time+'","LastUpdate":"'+req_time+'"}'
gzip = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
compressed = gzip.compress(dsb_data.encode('utf-8')) + gzip.flush()
compressed_string = base64.b64encode(compressed).decode('utf-8')
s.headers.update({'Referer': 'https://www.dsbmobile.de/'})
s.headers.update({'Bundle_ID': 'de.heinekingmedia.inhouse.dsbmobile.web'})
r = s.post(base_url+'/JsonHandlerWeb.ashx/GetData', json={
    'req':
        {'Data' : compressed_string, 'DataType': 1}
    },)

# parse data
decoded = base64.b64decode(json.loads(r.text)['d'])
decompressed = zlib.decompress(decoded, zlib.MAX_WBITS | 16)
parsed = json.loads(decompressed.decode('utf-8'))

plan_urls = []
notice = config.DSB.get('notice', None)
for plan in parsed['ResultMenuItems'][0]['Childs'][1]['Root']['Childs']:
    if notice and not notice in plan['Title']:
        continue
    plan_urls.append(plan['Childs'][0]['Detail'])

class_re = re.compile(config.DSB['class'])

sub_plan = {}
strike_regex = re.compile(r'<strike>\w+?<\/strike>', re.IGNORECASE)
for plan_url in plan_urls:
    r = requests.get(plan_url)
    soup = BeautifulSoup(re.sub(r'&nbsp;', '', r.text, 0, re.MULTILINE), 'html.parser')
    for day in soup.find_all('center'):
        day_title = day.find('div')
        if not day_title:
            continue
        date = day_title.text
        subs = day.find('table')
        details = []
        for sub in subs.find_all('td', text=class_re):
            class_details = []
            for detail in sub.parent.find_all('td'):
                txt = f'{strike(detail.strike.text)}' if detail.strike else detail.text
                class_details.append(txt)
            details.append(class_details)
        if date in sub_plan:
            sub_plan[date].extend(details)
        else:
            sub_plan[date] = details
for day in sub_plan:
    print(day)
    if len(sub_plan[day]):
        print(ascii_table(sub_plan[day], ['Klasse', 'Stunde', 'Art', 'Fach', 'Vertretung', 'Raum', 'Info']))
    else:
        print('Keine Vertretungen')
    print()
