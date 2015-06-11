#!/usr/bin/python

import sys
import json
import urllib
from HTMLParser import HTMLParser

class MediumHtmlParser(HTMLParser):
    collect_data = False
    raw_json = ""

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.collect_data = True

    def handle_endtag(self, tag):
        if tag == "script" and self.collect_data:
            self.collect_data = False

    def handle_data(self, data):
        if self.collect_data:
            if "<![CDATA[" in data and "var GLOBALS" in data:
                data = data.replace("// <![CDATA[", "")
                data = data.replace("var GLOBALS = ", "")
                data = data.replace("// ]]>", "")

                print(data)

"""

def cleanText(text):
    patterns = ['s','m','d','ve','ll','t','re']
    for p in patterns:
        text = text.replace('.'+p, "'"+p)

    return text

raw_json = ''.join(open('medium-post.json', 'r').readlines())
json = json.loads(raw_json)

content = json['embedded']['value']['content']
paragraphs = content['bodyModel']['paragraphs']

for p in paragraphs:
    if p['text'] != "":
        text = cleanText(p['text'])

        if p['type'] == 3:
            text = "### " + text

        print(text + "\n")
"""

def usage():
    print("Usage: import-medium.py <url>")

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        usage()
        sys.exit(1)

    url = sys.argv[1]
    f = urllib.urlopen(url)

    parser = MediumHtmlParser()
    parser.feed(f.read())
