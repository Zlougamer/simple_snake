#!/usr/bin/python3
import argparse
from http import server as http_server
import random
import time
from typing import List
import urllib.parse

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

SERVER_ERRORS = [500, 502, 503, 504, 507, 510, 429]
SERVER_ERR_PROBS = [10, 8, 8, 5, 3 ,1, 1]
SLEEP_TIME = 2

class HttpGetHandler(http_server.BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        if random.randrange(10) == 0:  # Generate non-200 response
            random_error = random.choices(
                SERVER_ERRORS, SERVER_ERR_PROBS, k=1,
            )[0]
            self.send_response(random_error)
            return 
            
        if random.randrange(10) == 0:  # Provide a request timeout
            time.sleep(SLEEP_TIME)
            return 
            
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
    head_x = query['head_x']
    head_y = query['head_y']

    up_head_val = query['up_head_val']
    down_head_val = query['down_head_val']
    left_head_val = query['left_head_val']
    right_head_val = query['right_head_val']
    
    delta_x = int(head_x) - int(apple_pos_x)
    delta_y = int(head_y) - int(apple_pos_y)

    # First, try to shorten distance between head and apple
    if abs(delta_x) < abs(delta_y):
        if delta_y > 0 and left_head_val == '_':
            return LEFT
        if delta_y < 0 and right_head_val == '_':
            return RIGHT
        if delta_x > 0 and down_head_val == '_':
            return DOWN
        if delta_x < 0 and up_head_val == '_':
            return UP
    else:
        if delta_x > 0 and down_head_val == '_':
            return DOWN
        if delta_x < 0 and up_head_val == '_':
            return UP
        if delta_y > 0 and left_head_val == '_':
            return LEFT
        if delta_y < 0 and right_head_val == '_':
            return RIGHT
    
    # Otherwise, try to go to empty place
    if down_head_val == '_':
        return DOWN
    if up_head_val == '_':
        return UP
    if left_head_val == '_':
        return LEFT
    if right_head_val == '_':
        return RIGHT

    # Finally, go somewhere
    return random.choice([UP, DOWN, LEFT, RIGHT])

if __name__ == '__main__':
    print('I am a client to Snake Game!')
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    run_server(args.port)
