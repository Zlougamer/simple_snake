#!/usr/bin/python3
import collections
import dataclasses
import json
import pathlib
import pprint
import random
from typing import List
from typing import Tuple

import requests


GAME_CONFIG_PATH = pathlib.Path(__file__).parent / 'game_config.json'
SNAKE_START_SEP = 4
NEW_SNAKE_LEN = SNAKE_START_SEP - 1
NEIGHBOR_WINDOW = 3

@dataclasses.dataclass(frozen=True)
class Coord:
    x: int
    y: int


@dataclasses.dataclass(frozen=True)
class Neighborhood:
    up: str
    down: str
    left: str
    right: str


class Client:

    def __init__(self, address: str) -> None:
        self.address = address
        self.session = requests.Session()
    
    def make_step(
            self, apple_pos: Coord, head: Coord, neighbor: Neighborhood,
    ) -> Coord:
        head_x = head.x
        head_y = head.y

        params = {
            'head_x': head_x,
            'head_y': head_y,
            'apple_pos_x': apple_pos.x,
            'apple_pos_y': apple_pos.y,
            'up_head_val': neighbor.up,
            'down_head_val': neighbor.down,
            'left_head_val': neighbor.left,
            'right_head_val': neighbor.right,
        }
        result = self.session.get(self.address, params=params)
        result.raise_for_status()
        direction = result.json()['direction']
        print('^'*35)
        print('direction: ', direction)
        print('$'*35)
        if direction == 'up':
            new_coord = Coord(head_x + 1, head_y)
        elif direction == 'down':
            new_coord = Coord(head_x - 1, head_y)
        elif direction == 'left':
            new_coord = Coord(head_x, head_y - 1)
        elif direction == 'right':
            new_coord = Coord(head_x, head_y + 1)
        else:
            raise Exception('Wrong direction')
        return new_coord


class Snake:

    def __init__(
            self, _id: int, body_coords: collections.deque, client: Client,
    ) -> None:
        self.id = _id
        self.body_coords = body_coords
        self.client = client
    
    @property
    def head(self) -> Coord:
        return self.body_coords[-1]


@dataclasses.dataclass(frozen=True)
class GameConfig:
    field_height: int
    field_width: int
    players_number: int
    hostname: str
    start_port: int
    ticks: int


class Game:

    def __init__(
        self,
        ticks_remained: int,
        snakes: List[Snake],
        apple_pos: Coord,
        field_width: int,
        field_height: int,
    ) -> None:
        self.ticks_remained = ticks_remained
        self.snakes = snakes
        self.apple_pos = apple_pos
        self.field_width=field_width
        self.field_height=field_height

    
    def is_continues(self) -> bool:
        return self.ticks_remained > 0

    def show_field(self) -> None:
        print('Ticks remained: ', self.ticks_remained)
        width = self.field_width
        height = self.field_height
        field = [['_' for _ in range(width)] for _ in range(height)]
        field[self.apple_pos.x][self.apple_pos.y] = 'A'
        for snake in self.snakes:
            for coord in snake.body_coords:
                field[coord.x][coord.y] = str(snake.id)
            coord = snake.head
            field[coord.x][coord.y] = 'H'

        print('-' * 50)
        pprint.pprint(field[::-1][:])
        print('-' * 50)
    
    def make_step(self) -> None:
        # TODO: support several snakes handling
        assert len(self.snakes) == 1

        self.ticks_remained -= 1
        snake = self.snakes[0]
        head = snake.head
        
        neighborhood = self._get_point_neighborhood(head)
        new_coord = snake.client.make_step(self.apple_pos, head, neighborhood)

        if new_coord == self.apple_pos:
            self._find_new_apple_position()
        else:
            snake.body_coords.popleft()
        snake.body_coords.append(new_coord)
    
    def _get_point_neighborhood(self, head: Coord) -> Neighborhood:
        up_coord = Coord(x=head.x + 1, y=head.y)
        up = self._get_field_element_by_coord(up_coord)

        down_coord = Coord(x=head.x - 1, y=head.y)
        down = self._get_field_element_by_coord(down_coord)

        left_coord = Coord(x=head.x, y=head.y - 1)
        left = self._get_field_element_by_coord(left_coord)

        right_coord = Coord(x=head.x, y=head.y + 1)
        right = self._get_field_element_by_coord(right_coord)

        return Neighborhood(up=up, down=down, left=left, right=right)

    def _get_field_element_by_coord(self, coord: Coord) -> str:
        x = coord.x
        y = coord.y
        if (
            x < 0 or 
            x >= self.field_height or 
            y < 0 or 
            y >= self.field_width
        ):
            return 'X'
        for snake in self.snakes:
            for snake_coord in snake.body_coords:
                if coord == snake_coord:
                    return 'S'
        return '_'

    def _find_new_apple_position(self) -> None:
        while True:
            new_x = random.randint(0, self.field_height - 1)
            new_y = random.randint(0, self.field_width - 1)
            if self._get_field_element_by_coord(Coord(new_x, new_y)) != '_':
                continue
            self.apple_pos = Coord(new_x, new_y)
            break


def main() -> None:
    print('Welcome to Snake Game!')
    config = read_configuration()
    game = create_game(config)
    game.show_field()

    while game.is_continues():
        game.make_step()
        game.show_field()
    print('Snake Game is over!')


def read_configuration() -> GameConfig:
    config_json = json.loads(GAME_CONFIG_PATH.read_text())
    return GameConfig(
        field_height=config_json['field']['height'],
        field_width=config_json['field']['width'],
        players_number=config_json['players']['number'],
        hostname=config_json['players']['hostname'],
        start_port=config_json['players']['start_port'],
        ticks=config_json['ticks'],
    )


def create_game(config: GameConfig) -> Game:
    width = config.field_width
    height = config.field_height
    players_number = config.players_number

    bound = 2 * width + 2 * height - 4
    total_snakes_len = players_number * SNAKE_START_SEP
    if bound < total_snakes_len:
        raise Exception('Playing field is too small! Please, increase it')

    snakes = []
    for player_id, point in enumerate(range(0, bound, SNAKE_START_SEP)):
        if player_id >= players_number:
            break
        snake_coords = collections.deque()
        for i in range(NEW_SNAKE_LEN):
            snake_coords.append(
                _point_to_coord(point + i, width, height)
            )

        client_address = (
            'http://' + 
            config.hostname + 
            ':' + 
            str(config.start_port + player_id)
            )
        client = Client(client_address)
        snake = Snake(player_id, snake_coords, client)
        snakes.append(snake)

    apple_pos = Coord(height // 2, width // 2)

    return Game(
        ticks_remained=config.ticks,
        snakes=snakes,
        apple_pos=apple_pos,
        field_width=width,
        field_height=height,
    )

def _point_to_coord(point: int, width: int, height: int) -> Coord:
        if 0 <= point < width:
            first_coord = 0
            second_coord = point
        elif width <= point < width + height - 2:
            first_coord = point - width + 1
            second_coord = width - 1
        elif width + height - 2 <= point < 2 * width + height - 2:
            first_coord = height - 1
            second_coord = 2 * width + height - 3 - point
        else:
            first_coord = 2 * width + 2 * height - 4 - point
            second_coord = 0
        return Coord(first_coord, second_coord)



if __name__ == '__main__':
    main()