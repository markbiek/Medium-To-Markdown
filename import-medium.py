#!/usr/bin/python

import json

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
