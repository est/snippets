#!/usr/bin/python

from pyxmpp2.simple import send_message
from pyxmpp2.settings import XMPPSettings

argparser = XMPPSettings.get_arg_parser(add_help = True)
settings = XMPPSettings()
settings.load_arguments(argparser.parse_args())
from pyxmpp2.simple import send_message

# send_message("bob@example.org", "bob's password", "alice@example.org", "Hello Alice")

send_message(r'xyz\40gmail.com@weibo.com', 'pwd', 'WEIBOID@weibo.com', 'fuckoff')
