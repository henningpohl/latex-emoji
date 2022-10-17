from bs4 import BeautifulSoup
from mako.template import Template
import base64
import os
import json
import requests
import requests_cache

# http://www.unicode.org/emoji/charts/index.html
# http://www.unicode.org/emoji/charts/full-emoji-list.html
PAGE_URL = 'http://www.unicode.org/emoji/charts/full-emoji-list.html'

template = Template(filename='emoji.sty.TEMPLATE', output_encoding='utf8')

def get_header_names(header):
    cols = header.find_all('th')
    cols = [c.get_text() for c in cols]
    cols = [c.replace('*','') for c in cols]
    cols = [c.lower() for c in cols]
    return cols

def extract_image(column):
    if 'miss' in column['class']:
        return None

    if 'miss7' in column['class']:
        return None

    data = column.img['src']
    data_start = data.find("base64,")
    if data_start == -1:
        return None
    
    data = base64.b64decode(data[data_start + len("base64,"):])
    return data

def save_image(folder, imgSrc, filename):
    if os.path.exists(folder) is False:
        os.mkdir(folder)

    filename = os.path.join(folder, filename)
    if os.path.exists(filename):
        return

    img = extract_image(imgSrc)
    if img is not None:
        with open(filename, 'wb') as out:
            out.write(img)

def scrape():
    soup = BeautifulSoup(requests.get(PAGE_URL).text, "html5lib")
    table = soup('table')[0]

    header = table.select_one('tr > th[class=cchars]').find_parent('tr')
    keys = get_header_names(header)

    with open('emoji.sty', 'wb') as out:
        out_codes = []
        for row in table.find_all('tr'):          
            fields = {k:c for k, c in zip(keys, row.find_all('td')) }          
            if len(fields) != len(keys):
                continue

            codes = fields['code'].text.replace('U+', '').split(' ')
            filename = "-".join(codes) + ".png"

            save_image('ios', fields['appl'], filename)
            save_image('android', fields['goog'], filename)
            save_image('twitter', fields['twtr'], filename)
            save_image('windows', fields['wind'], filename)
            save_image('one', fields['joy'], filename)
            save_image('facebook', fields['fb'], filename)

            if len(codes) == 1:
                out_codes.append("".join(codes))

        print(len(out_codes))

        out.write(template.render(emojis = out_codes))

if __name__ == '__main__':
    requests_cache.install_cache('scrape_cache')
    scrape()
