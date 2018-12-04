import jwt
import socketserver
from http.server import SimpleHTTPRequestHandler
from json import dumps, loads

PORT = 80

public_key = b"""-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDdlatRjRjogo3WojgGHFHYLugd
UWAY9iR3fy4arWNA1KoS8kVw33cJibXr8bvwUAUparCwlvdbH6dvEOfou0/gCFQs
HUfQrSDv+MuSUMAe8jzKE4qW+jK+xQU9a03GUnKHkkle+Q0pX/g6jXZ7r1/xAK5D
o2kQ+X5xK9cipRgEKwIDAQAB
-----END PUBLIC KEY-----
"""


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        headers = self.headers
        payload = loads(self.rfile.read(int(self.headers['Content-Length'])).decode("UTF-8"))["payload"]
        try:
            payload = jwt.decode(payload.encode("utf-8"), public_key, algorithms='RS256')
        except Exception:
            pass
        print("\nHeaders:\n", headers, "\nPayload\n", dumps(payload, indent=4))


httpd = socketserver.TCPServer(("", PORT), Handler)
httpd.serve_forever()
