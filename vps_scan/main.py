import httpx, time, re, os

from collections import Counter

__doc__ == '''
Read vps info from panels like SolusVM
'''

url = 'https://my.hosteons.com/cart.php?a=add&pid=%d'
UA = 'Mozilla/5.0 (Macintosh; Windows NT 98; X11; Linux) AppleWebKit/666.66(KHTML, like Gecko) Chrome/199.9.9999.99 Safari/666.66 Edg/199.9.9999.99'

pages = {}

def scan():
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

def store():
    # filter bad pid
    bad_pages = [k for k, _ in Counter(len(c) for c in pages.values()).most_common(1)]
    for k, v in pages.items():
        with open('%d.html' % k, 'wb') as f:
            if len(v) in bad_pages:
                continue
            f.write(v)


def re_search(ptn, s):
    m = re.search(ptn, s, re.S | re.I)
    if m:
        return m.group(1)
    return ''

def parse(i, c):
    core = re_search(r'product-title.+?Core[^:]*?: +(\d+)', c) or ''
    if not core:
        return
        cpu = re_search(r'product-title.+?CPU: +([^\r\n]+)<', c) or '?'
        core = f'"{cpu}"'
    ram = re_search(r'product-title.+?RAM: +([\d+\.]+\s?\w)', c).replace(' ', '')
    disk = re_search(r'product-title.+?(?:Disk Space|Drive): +([\d\.]+\s?\w+)\W', c).replace(' ', '')
    bw = re_search(r'product-title.+?BANDWIDTH:\D+?([\d\.]+\s?[TMG])', c).replace(' ', '')
    price = re_search(r'"annually".*?(\$[\d\.]+)', c)
    print(f'| {i} | {core}C{ram} | {disk} | {bw}bps | {price} |')

targets = [int(x[:-5]) for x in os.listdir('.') if x.endswith('.html')]
targets.sort()
for i in targets:
    with open(f'{i}.html') as f:
        c = f.read()
        if 's a problem' in c:
            continue
        parse(i, c)
    # break
    
