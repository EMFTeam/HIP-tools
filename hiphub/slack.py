# -*- python-indent-offset: 4 -*-

import json
import http.client


def sendmsg(webhook, text, channel, username, icon_emoji=None):
    payload = {
        'channel': channel,
        'username': username,
        'text': text,
    }

    if icon_emoji:
        payload['icon_emoji'] = icon_emoji

    body = json.dumps(payload, indent=4)
    
    conn = http.client.HTTPSConnection('hooks.slack.com')
    conn.request('POST', webhook, body, {'Content-type': 'application/json'})
    response = conn.getresponse()
    response.read()
    conn.close()
    

def isis_sendmsg(text, channel='#hiphub', wink=False):
    icon_emoji = ':isis:' if not wink else ':isis-winking:'
    sendmsg('/services/T055NUPPW/B34JCEDBM/OVRrTApteiWLWPKsSqkvb21c', text, channel, 'isis', icon_emoji)
