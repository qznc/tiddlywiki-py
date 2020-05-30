#!/usr/bin/env python3
import logging
logging.basicConfig(level=logging.INFO)

from http.server import BaseHTTPRequestHandler, HTTPServer
import os.path
import sys
import datetime

hostName = "localhost"
serverPort = 17293
storage = None

def get_etag(path):
    """Return etag for a path"""
    if not os.path.isfile(path):
        return b""
    stat = os.stat(path)
    return "mtime_microseconds:%.0f" % (stat.st_mtime / 1000)

def slurp(path):
    """Read all contents of a file as bytes"""
    if not os.path.isfile(path):
        return None, None
    etag = get_etag(path)
    with open(path, 'rb') as fh:
        return fh.read(), etag

def backup_path(storage):
    path, ext = os.path.splitext(storage)
    first_of_current_month = datetime.datetime.utcnow().replace(day=1)
    lastMonth = first_of_current_month - datetime.timedelta(days=1)
    date = lastMonth.strftime("%Y-%m")
    return f"{path}-{date}{ext}"

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            return self.respond(404)
        content, etag = slurp(storage)
        if not content:
            content, etag = slurp("empty.html")
        self.respond(200, etag, content)
    def do_HEAD(self):
        # TiddlyWiki uses ETag to check if a save was successful
        etag = get_etag(storage)
        self.respond(200, etag)
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('allow', "GET,HEAD,POST,OPTIONS,CONNECT,PUT,DAV,dav")
        self.send_header('x-api-access-type', 'file')
        self.send_header('dav', 'tw5/put')
        self.send_header("Content-Length", "0")
        self.end_headers()
    def do_PUT(self):
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)
        ifMatch = self.headers['If-Match']
        etag = get_etag(storage)
        if ifMatch != etag:
            logging.warning(f"etag mismatch: {ifMatch} != {etag}")
            with open("etag_mismatch.html", 'w+b') as fh:
                fh.write(content)
            return self.respond(412, etag)
        with open(storage, 'w+b') as fh:
            fh.write(content)
        logging.info(f"Stored: {storage}")
        backup = backup_path(storage)
        if not os.path.isfile(backup):
            with open(backup, 'w+b') as fh:
                fh.write(content)
            logging.info(f"Stored backup: {backup}")
        etag = get_etag(storage)
        self.respond(204, etag)
    def respond(self, status, etag=None, content=None):
        self.send_response(status)
        self.send_header("Content-type", "text/html;charset=UTF-8")
        if etag:
            self.send_header("ETag", etag)
        if content:
            self.send_header("Content-Length", len(content))
        self.end_headers()
        if content:
            self.wfile.write(content)

if __name__ == "__main__":        
    if len(sys.argv) > 1:
        storage_folder = sys.argv[1]
        storage = os.path.join(storage_folder, "tiddlywiki.html")
    else:
        storage = "current.html"
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
