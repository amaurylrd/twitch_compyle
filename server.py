from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class Serv(BaseHTTPRequestHandler):
    def do_GET(self):
        print("hello get", self.get_autorization_code(self.path))

    def do_POST(self):
        print("hello post", self.get_autorization_code(self.path))

    def get_autorization_code(self, path: str) -> str:
        return parse_qs(urlparse(path).query)["code"][0]


redirect_url = "http://localhost:3000"
client_address = redirect_url.rsplit(":", maxsplit=1)
client_address[0] = client_address[0].split("://", maxsplit=1)[1]
client_address[1] = int(client_address[1])

print(client_address)

server = HTTPServer(tuple(client_address), Serv)

server.handle_request()
server.server_close()
