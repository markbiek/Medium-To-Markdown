#!/usr/bin/python

import sys
import os
import json
import urllib
import datetime
import re
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

                self.raw_json = os.linesep.join([s for s in data.splitlines() if s])

def cleanText(text):
    patterns = ['s','m','d','ve','ll','t','re']
    for p in patterns:
        text = text.replace('.'+p, "'"+p)

    return text


def usage():
    print("Usage: import-medium.py [OPTIONS] <url>")
    print("    --pelican\tOutput in a format suitable for use with the Pelican blog engine")

"""
TODO:
    We'll redo this to use a proper arg parser when we have more than one argument
"""
def parseArgs():
    config = { 'pelican': False, 'url': '' }

    if sys.argv[1] == '--pelican':
        config['pelican'] = True
        config['url'] = sys.argv[2]
    else:
        config['url'] = sys.argv[1]

    return config

def insertLink(text, markup):
    text = text.encode("ascii", "ignore")

    start = markup['start']
    end = markup['end']
    
    return "{0}[{1}]({2}){3}".format(text[:start], text[start:end], markup['href'], text[end:])

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        usage()
        sys.exit(1)

    config = parseArgs()

    url = config['url']
    f = urllib.urlopen(url)

    parser = MediumHtmlParser()
    parser.feed(f.read())

    json = json.loads(parser.raw_json)

    """Other fields we need to grab for pelican"""
    ut_first_published = int(str(json['embedded']['value']['firstPublishedAt'])[0:-3])
    first_published = datetime.datetime.fromtimestamp(ut_first_published).strftime('%Y-%m-%d %H:%M')
    post_title = json['embedded']['value']['title']
    slug = json['embedded']['value']['slug']
    outfile_name = first_published + "-" + slug + ".md"
    author = json['embedded']['value']['creator']['username']

    if config['pelican']:
        sys.stdout = open(outfile_name, 'w')

        print("Title: " + post_title.encode("ascii", "ignore"))
        print("Date: " + first_published)
        print("Author: " + author)
        print("Category: ")
        print("Tags: ")
        print("Slug: " + slug)
        print("")

    """Grab the paragraph data for the post"""
    content = json['embedded']['value']['content']
    paragraphs = content['bodyModel']['paragraphs']

    for p in paragraphs:
        if p['text'] != "":
            text = cleanText(p['text'])

            """ Quote """
            if p['type'] == 6:
                text = "> " + text

            """ Subhead """
            if p['type'] == 3:
                text = "### " + text

            """ Text has markups """
            if len(p['markups']) > 0:
                for m in p['markups']:
                    """ Link markup """
                    if 'href' in m.keys():
                        text = insertLink(text, m)

            print(text.encode("ascii", "ignore") + "\n")
