#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import os.path

hostName = "localhost"
serverPort = 17293

def get_etag(path):
    """Return etag for a path"""
    if not os.path.isfile(path):
        return b""
    stat = os.stat(path)
    return "%.1f" % stat.st_mtime

def slurp(path):
    """Read all contents of a file as bytes"""
    if not os.path.isfile(path):
        return None
    etag = get_etag(path)
    with open(path, 'rb') as fh:
        return fh.read(), etag

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            return
        content, etag = slurp("current.html")
        if not content:
            content, etag = slurp("empty.html")
        self.send_response(200)
        self.send_header("Content-type", "text/html;charset=UTF-8")
        self.send_header("Content-Length", len(content))
        self.send_header("ETag", etag)
        self.end_headers()
        self.wfile.write(content)
    def do_HEAD(self):
        # TiddlyWiki uses ETag to check if a save was successful?
        etag = get_etag("current.html")
        self.send_response(200)
        self.send_header("Content-type", "text/html;charset=UTF-8")
        self.send_header("ETag", etag)
        self.end_headers()
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('allow', "GET,HEAD,POST,OPTIONS,CONNECT,PUT,DAV,dav")
        self.send_header('x-api-access-type', 'file')
        self.send_header('dav', 'tw5/put')
        self.send_header("Content-Length", "0")
        self.end_headers()
    def do_PUT(self):
        ifMatch = self.headers['If-Match']
        etag = get_etag("current.html")
        if ifMatch != etag:
            self.send_response(412) # Conflict
            self.send_header("ETag", etag)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)
        with open('current.html', 'w+b') as fh:
            fh.write(content)
        etag = get_etag("current.html")
        self.send_response(204)
        self.send_header("ETag", etag)
        self.send_header("Content-Length", "0")
        self.end_headers()

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
