# http://patternbuffer.wordpress.com/2008/03/15/play-mp3-from-python-on-mac/

import Foundation, AVFoundation
# from AppKit import NSSound
# sound = NSSound.alloc()
url = Foundation.NSURL.URLWithString_('http://est-win7:8000/05%20-%20Daft%20Punk%20-%20Armory.mp3') #"http://206.217.213.235:8050/")
# sound.initWithContentsOfURL_byReference_(url, True)
# sound.play()

err = Foundation.NSError

player = AVFoundation.AVAudioPlayer.alloc()
# http://www.mikeash.com/pyblog/friday-qa-2009-11-20-probing-cocoa-with-pyobjc.html
rtn = player.initWithContentsOfURL_error_(url, None)
# player.play()
