from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class Serv(BaseHTTPRequestHandler):
    def do_GET(self):
        print("hello", self.path)
        parsed = urlparse(self.path)
        code = parse_qs(parsed.query)["code"][0]

        # You may see a "Google hasn't verified this app" screen during the authorization process, which appears if the sdm.service scope is not configured on your OAuth consent screen in Google Cloud. This screen can be bypassed by clicking the Advanced option and then clicking Go to Project Name (unsafe).

        print(code)


redirect_url = "http://localhost:3000"
client_address = redirect_url.rsplit(":", maxsplit=1)
client_address[0] = client_address[0].split("://", maxsplit=1)[1]
client_address[1] = int(client_address[1])

print(client_address)

server = HTTPServer(tuple(client_address), Serv)

server.handle_request()
server.server_close()
