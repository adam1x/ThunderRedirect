import json, os, shlex, requests

CONF_PATH = 'proxy.txt'

def main():
    host, token, proxy = readSettings()
    print("aria2 commands:")

    count = 0
    while True:
        aria2Command = input().strip()
        url, header = parseCommand(aria2Command)
        sendJob(host, token, proxy, url, header, str(count))
        count += 1
        if not aria2Command:
            break

def readSettings():
    if os.path.isfile(CONF_PATH):
        with open(CONF_PATH, 'rt') as f:
            proxy = f.readline().strip()
    else:
        proxy = input("proxy: ")
        with open(CONF_PATH, 'wt') as f:
            f.write(proxy + '\n')

    host = input("host: ")
    if not host:
        host = 'localhost'

    token = input("token: ")

    return host, token, proxy

def parseCommand(aria2Command):
    argv = shlex.split(aria2Command)
    try:
        headers = [ argv[i + 1] for i, s in enumerate(argv) if s == '--header' ]
        url = next(filter(lambda arg: arg.startswith('http://'), argv))
    except (ValueError, IndexError, StopIteration):
        print("Invalid Command: " + aria2Command)
        sys.exit()

    if len(headers) == 0 or len(url) == 0:
        print("Invalid Command: " + aria2Command)
        sys.exit()

    return url, headers

def sendJob(host, token, proxy, url, header, id):
    headers = dict([ s.split(': ') for s in header if s ])
    headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'
    thunderRequests = requests.get(url, headers = headers, proxies = {'http':proxy}, allow_redirects = False)
    redirectedUrl = thunderRequests.headers['location']

    jsonreq = json.dumps({'jsonrpc':'2.0', 'id':id,
                          'method':'aria2.addUri',
                          'params':['token:' + token, [redirectedUrl], {'header':header}]})

    try:
        aria2Requests = requests.post('http://%s:6800/jsonrpc' % host, data = jsonreq)
    except ConnectionRefusedError:
        print("Unable to connect to aria2 @ %s" % host)
        sys.exit()

    print(aria2Requests.json())


if __name__ == '__main__':
    main()
