import json, os, shlex, sys, requests

CONF_PATH = 'proxy.txt'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'
REMOTE_TIMEOUT = (10, 10)
LOCAL_TIMEOUT = (5, 5)
REDIRECT_BLACKLIST = ['http://www.kankan.com']

def main():
    host, token, proxy = readSettings()
    print("aria2 commands (enter empty line to exit):")

    count = 0
    while True:
        aria2Command = input().strip()
        if not aria2Command:
            break

        url, header = parseCommand(aria2Command)
        sendJob(host, token, proxy, url, header, str(count))
        count += 1

def readSettings():
    if os.path.isfile(CONF_PATH):
        with open(CONF_PATH, 'rt') as f:
            proxy = f.readline().strip()
    else:
        proxy = input("proxy: ")
        with open(CONF_PATH, 'wt') as f:
            f.write(proxy + '\n')

    host = input("host (empty means localhost): ")
    if not host:
        host = 'localhost'

    token = input("token: ")

    return host, token, proxy

def parseCommand(aria2Command):
    argv = shlex.split(aria2Command)
    try:
        headers = [ argv[i + 1] for i, s in enumerate(argv) if s == '--header' ]
        url = next(filter(lambda arg: arg.startswith('http://'), argv))
    except (IndexError, StopIteration):
        print("[FAILED] invalid Command: " + aria2Command)
        sys.exit(1)

    if len(headers) == 0 or len(url) == 0:
        print("[FAILED] invalid Command: " + aria2Command)
        sys.exit(1)

    return url, headers

def sendJob(host, token, proxy, url, header, id):
    headers = dict([ s.split(': ') for s in header if s ])
    headers['User-Agent'] = USER_AGENT
    
    try:
        r = requests.get(url, headers = headers, proxies = {'http':proxy},
                         allow_redirects = False, timeout = REMOTE_TIMEOUT)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("[FAILED] Connection with Thunder Lixian failed.")
        print("-------> %s" % e)
        sys.exit(1)

    # for now, redirection for both downloads and geoblocking seem to be implemented
    # with HTTP 302; HTTP 301 is supported should there be any change
    if r.status_code == requests.codes.moved or r.status_code == requests.codes.found:
        redirectedUrl = r.headers['location']
        if any([redirectedUrl.startswith(wanted) for wanted in REDIRECT_BLACKLIST]):
            print("[FAILED] Geoblocked and redirected to: %s . Maybe proxy isn't working." % redirectedUrl)
            sys.exit(1)
    else:
        print("[FAILED] No redirection captured. HTTP status code: %d." % r.status_code)
        sys.exit(1)

    payload = json.dumps({'jsonrpc':'2.0', 'id':id,
                          'method':'aria2.addUri',
                          'params':['token:' + token, [redirectedUrl], {'header':header}]})

    try:
        r = requests.post('http://%s:6800/jsonrpc' % host, data = payload, timeout = LOCAL_TIMEOUT)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("[FAILED] Connection with aria2 @ %s failed. Check hostname and token." % host)
        print("-------> %s" % e)
        sys.exit(1)

    response = r.json()
    if 'code' in response:
        print("[FAILED] Failed to create task on aria2: %s ." % response['message'])
        sys.exit(1)
    else:
        print("[Success] Created task on aria2.")


if __name__ == '__main__':
    main()
