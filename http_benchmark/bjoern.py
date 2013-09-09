import bjoern, json


def home_app(environ, start_response):
  s = json.dumps({'name': 'A Royal Baby', 'body':'A slow news week'})
  start_response('200 OK', [('Content-Length', str(len(s))), ('Content-Type', 'text/plain')])
  yield s


bjoern.run(home_app, '127.0.0.1', 8086)
