import json, urllib2, requests

def main():
    host, token, proxy = readSettings()
    print("aria2 commands:")
    while not aria2Command:
        aria2Command = input().strip()
        url, header = parseCommand(aria2Command)
        sendJob(host, token, proxy, url, header)

def readSettings():
    with open('proxy.txt', 'rt') as f:
        proxy = f.read()

    host = input("host: ")
    if not host:
        host = 'localhost'

    token = input("token: ")

    return host, token, proxy

def parseCommand(aria2Command):
    argv = aria2Command.split()
    try:
        header = argv[argv.index('--header') + 1]
        url = filter(lambda arg: arg.startswith('\'http://'))[0]
    except (ValueError, IndexError):
        print("Invalid Command: " + aria2Command)
        return
    
    if len(header) == 0 or len(url) == 0:
        print("Invalid Command: " + aria2Command)
        return

    return url[1:-1], header[1:-1]

def sendJob(host, token, proxy, url, header):
    headers = dict(map(lambda s: s.split(': '), header.split(';')))
    r = requests.head(url, headers = headers, proxies = {'http':proxy})
    redirectedUrl = r.url

    jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'qwer',
                          'method':'aria2.addUri',
                          'params':['token:' + token, [redirectedUrl], {'header':header}]})
    c = urllib2.urlopen('http://%s:6800/jsonrpc' % host, jsonreq)
    c.read()
