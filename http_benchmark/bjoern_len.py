import bjoern, json
from pprint import pformat

import readline, rlcompleter; readline.parse_and_bind("tab: complete")


def home_app(environ, start_response):
  # s = json.dumps({'name': 'A Royal Baby', 'body':'A slow news week'})
  s = pformat(environ)
  start_response('200 OK', [('Content-Length', str(len(s))), ('Content-Type', 'text/plain')])
  import pdb; pdb.set_trace()
  yield s


bjoern.run(home_app, '0.0.0.0', 8086)

