import bjoern, json, mimetypes, subprocess
from pprint import pformat
from wsgiref.simple_server import make_server

import readline, rlcompleter; readline.parse_and_bind("tab: complete")


cmd = 'convert "1.jpg" -filter Lanczos -thumbnail 200x150 -'



def home_app(environ, start_response):
  # s = json.dumps({'name': 'A Royal Baby', 'body':'A slow news week'})
  s = pformat(environ)
  start_response('200 OK', [('Content-Length', str(len(s))), ('Content-Type', 'text/plain')])
  # import pdb; pdb.set_trace()
  yield s

def image_app(environ, start_response):
	start_response('200 OK', [('Content-Type', 'image/jpeg'), ('Content-Length', '23146'), ('Connection', 'Close')])
	proc = subprocess.Popen([
		'convert',
		'1.jpg',
		'-filter', 'Lanczos',
		'-thumbnail', '200x150',
		'-',
	], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	# return environ['wsgi.file_wrapper'](proc.stdout)
	return proc.stdout

def image_app2(environ, start_response):
	start_response('200 OK', [('Content-Type', 'image/jpeg'), ('Content-Length', '23146'), ('Connection', 'Close')])
	stdout, stderr = subprocess.Popen([
		'convert',
		'1.jpg',
		'-filter', 'Lanczos',
		'-thumbnail', '200x150',
		'-',
	], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
	return stdout

def hello_app(environ, start_response):
	start_response('200 OK', [('Content-Type', 'text/plain')])
	proc = subprocess.Popen("echo hello world", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return proc.stdout


# bjoern.run(image_app2, '0.0.0.0', 8087)
# make_server('', 8086, hello_app).serve_forever()
# uwsgi --http 0:8087 --wsgi  bj:image_app2 --master --workers 16 -L --cpu-affinity=1


"""
import subprocess
def f():
  proc = subprocess.Popen("echo hello world", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  yield from proc.stdout



http://interfacelift.com/wallpaper/7yz4ma1/03339_badlandsintheafternoonsun_1920x1080.jpg


"""