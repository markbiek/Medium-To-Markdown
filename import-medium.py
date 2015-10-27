#!/usr/bin/python
#v0.4

import sys
import os
import json
import urllib2
import datetime
import re
from HTMLParser import HTMLParser

##############################################################################
# Config

PAR_TYPES = {
        'QUOTE': 6,
        'H2':    3,
        'H3':    13,
        'IMG':   4
        }

##############################################################################

class MediumHtmlParser(HTMLParser):
    collect_data = False
    raw_json = ''
    images = {}

    def __get_img_src(self, attrs):
        for attr in attrs:
            if attr[0] == 'src':
                img_url = attr[1]
                img = img_url.split('/')[-1]
                return (img, img_url)

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.collect_data = True
        if tag == 'img':
            img, img_url = self.__get_img_src(attrs)
            self.images[img] = img_url

    def handle_endtag(self, tag):
        if tag == 'script' and self.collect_data:
            self.collect_data = False

    def handle_data(self, data):
        if self.collect_data:
            if '<![CDATA[' in data and 'window["obvInit"]' in data:
                data = data.replace('// <![CDATA[', '')
                data = data.replace('window["obvInit"]', '')
                data = data.replace('// ]]>', '')

                self.raw_json = clean_json(os.linesep.join([s for s in data.splitlines() if s]))
                self.raw_json = self.raw_json[1:-1]

def clean_json(raw_json):
    # Medium encodes some chars as \x<ascii hex> which is invalid json
    # We turn those encodings back into plain ascii chars
    m = re.findall(ur'\\x[aA-zZ0-9]{2}', raw_json, re.UNICODE)
    for x in m:
        raw_json = raw_json.replace(x, chr(int('0x' + x[2:], 16)))

    return raw_json

def clean_text(text):
    return re.sub(r'(\w+)\.(\w+)', r"\1'\2", text)

def usage():
    print('Usage: import-medium.py [OPTIONS] <url>')
    print('    --pelican\tOutput in a format suitable for use with the Pelican blog engine')

"""
TODO:
    We'll redo this to use a proper arg parser when we have more than one argument
"""
def parse_args():
    config = { 'pelican': False, 'url': '' }

    if sys.argv[1] == '--pelican':
        config['pelican'] = True
        config['url'] = sys.argv[2]
    else:
        config['url'] = sys.argv[1]

    return config

def insert_link(text, markup):
    text = text.encode('ascii', 'ignore')

    start = markup['start']
    end = markup['end']
    
    return '{0}[{1}]({2}){3}'.format(text[:start], text[start:end], markup['href'], text[end:])

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        usage()
        sys.exit(1)

    config = parse_args()

    url = config['url']
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    f = opener.open(url)

    encoding = f.headers.getparam('charset')
    parser = MediumHtmlParser()
    html = f.read()

    parser.feed(html.decode(encoding))

    json = json.loads(parser.raw_json)

    # Other fields we need to grab for pelican
    ut_first_published = int(str(json['embedded']['value']['firstPublishedAt'])[0:-3])
    first_published = datetime.datetime.fromtimestamp(ut_first_published).strftime('%Y-%m-%d %H:%M')
    post_title = json['embedded']['value']['title']
    slug = json['embedded']['value']['slug']
    outfile_name = first_published + '-' + slug + '.md'
    author = json['embedded']['value']['creator']['username']

    if config['pelican']:
        sys.stdout = open(outfile_name, 'w')

        print('Title: ' + post_title.encode('ascii', 'ignore'))
        print('Date: ' + first_published)
        print('Author: ' + author)
        print('Category: ')
        print('Tags: ')
        print('Slug: ' + slug)
        print('')

    # Grab the paragraph data for the post
    content = json['embedded']['value']['content']
    paragraphs = content['bodyModel']['paragraphs']

    for p in paragraphs:
        text = clean_text(p['text'])

        if p['type'] == PAR_TYPES['QUOTE']:
            text = '> ' + text

        if p['type'] == PAR_TYPES['H2']:
            # If we're in pelican mode, the first H2 is a duplicate 
            # of the title so we just skip that line entirely
            if config['pelican'] and text == post_title:
                text = ''
            else:
                text = '### ' + text

        if p['type'] == PAR_TYPES['H3']:
            text = '#### ' + text

        if p['type'] == PAR_TYPES['IMG']:
            img = p['metadata']['id']
            if img in parser.images.keys():
                w = p['metadata']['originalWidth']
                h = p['metadata']['originalHeight']
                img_url = parser.images[img]

                text = '<img src="{0}" width="{1}" height="{2}" />'.format(img_url, w, h)
            else:
                print("UNKNOWN IMAGE " + img)

        # Text has markups 
        if len(p['markups']) > 0:
            for m in p['markups']:
                # Link markup 
                if 'href' in m.keys() and p['type'] != PAR_TYPES['IMG']:
                    text = insert_link(text, m)

        if text != '':
            print(text.encode('utf-8', 'ignore') + '\n')
