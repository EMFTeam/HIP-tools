#!/usr/bin/python3

import slack
import datetime

slack.isis_sendmsg('Hey, mortals, this test message was sent using `slack.isis_sendmsg` at {} here in Toronto. Yes, Toronto is unfortunately where @ziji is keeping me for now.'.format(datetime.datetime.today()))
