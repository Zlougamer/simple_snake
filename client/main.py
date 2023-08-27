#!/usr/bin/python3
import argparse
from http import server as http_server
from typing import List
import urllib.parse

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'


class HttpGetHandler(http_server.BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        res = urllib.parse.urlparse(self.path)
        query = dict(urllib.parse.parse_qsl(res.query))
        direction = make_decision(query)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        result_response_str = '{"direction": "%s"}' % direction
        self.wfile.write(result_response_str.encode())


def run_server(port: int) -> None:
  server_address = ('', port)
  httpd = http_server.HTTPServer(server_address, HttpGetHandler)
  try:
      httpd.serve_forever()
  except KeyboardInterrupt:
      httpd.server_close()


def make_decision(query) -> str:
    apple_pos_x = query['apple_pos_x']
    apple_pos_y = query['apple_pos_y']
    coord_x = query['coord_x']
    coord_y = query['coord_y']
    
    delta_x = int(coord_x) - int(apple_pos_x)
    delta_y = int(coord_y) - int(apple_pos_y)

    if abs(delta_x) < abs(delta_y):
        if delta_y > 0:
            return LEFT
        else:
            return RIGHT
    else:
        if delta_x > 0:
            return DOWN
        else:
            return UP


if __name__ == '__main__':
    print('I am a client to Snake Game!')
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    run_server(args.port)
