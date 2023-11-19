import httpx, time\

from collections import Counter

__doc__ == '''
Read vps info from panels like SolusVM
'''

url = 'https://my.hosteons.com/cart.php?a=add&pid=%d'
UA = 'Mozilla/5.0 (Macintosh; Windows NT 98; X11; Linux) AppleWebKit/666.66(KHTML, like Gecko) Chrome/199.9.9999.99 Safari/666.66 Edg/199.9.9999.99'

pages = {}
pages_len = {}

for i in range(1, 200):
    with httpx.Client() as client:
        try:
            r = client.get(url % i, headers={'user-agent': UA}, follow_redirects=True, timeout=10)
            c = r.read()
        except Exception as ex:
            print(ex.reason)
            c = ex.read()  # ex.headers
            continue
    pages[i] = c
    pages_len[i] = len(c)
    print('pid=%d data=%s' % (i, len(c)))
    time.sleep(1)

bad_page = Counter(pages_len.values()).most_common(1)[0][0]
for k, v in pages.items():
    with open('%d.html' % k, 'wb') as f:
        if len(v) == bad_page:
            continue
        f.write(v)

