#!/usr/bin/python3
import dataclasses
import json
import pathlib
import pprint
import random
from typing import List
from typing import Tuple

import requests


GAME_CONFIG_PATH = pathlib.Path(__file__).parent / 'game_config.json'

@dataclasses.dataclass(frozen=True)
class Coord:
    x: int
    y: int


class Client:

    def __init__(self, _id: int, address: str, coord: Coord) -> None:
        self.id = _id
        self.address = address
        self.coord = coord
        self.session = requests.Session()
    
    def make_step(self, apple_pos: Coord, field: List[List[str]]) -> None:
        coord_x = self.coord.x
        coord_y = self.coord.y

        # if coord_y - 1 >= 0:
        #     up_cell = field[coord_x][coord_y - 1]
        # else:
        #     up_cell = 'X'

        # if coord_y + 1 >= 0:
        #     down_cell = field[coord_x][coord_y + 1]
        # else:
        #     down_cell = 'X'

        # if coord_x - 1 >= 0:
        #     left_cell = field[coord_x - 1][coord_y]
        # else:
        #     left_cell = 'X'

        # if coord_x + 1 >= 0:
        #     right_cell = field[coord_x + 1][coord_y]
        # else:
        #     right_cell = 'X'

        params = {
            'coord_x': coord_x,
            'coord_y': coord_y,
            'apple_pos_x': apple_pos.x,
            'apple_pos_y': apple_pos.y,
            # 'up_cell': up_cell,
            # 'down_cell': down_cell
            # 'left_cell': left_cell,
            # 'right_cell': right_cell,
        }
        result = self.session.get(self.address, params=params)
        result.raise_for_status()
        direction = result.json()['direction']
        if direction == 'up':
            new_coord = Coord(coord_x + 1, coord_y)
        elif direction == 'down':
            new_coord = Coord(coord_x - 1, coord_y)
        elif direction == 'left':
            new_coord = Coord(coord_x, coord_y - 1)
        elif direction == 'right':
            new_coord = Coord(coord_x, coord_y + 1)
        else:
            raise Exception('Wrong direction')
        return new_coord


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
        field: List[List[str]],
        ticks_remained: int,
        clients: List[Client],
        apple_pos: Coord,
    ) -> None:
        self.field = field
        self.ticks_remained = ticks_remained
        self.clients = clients
        self.apple_pos = apple_pos
    
    def is_continues(self) -> bool:
        return self.ticks_remained > 0

    def show_field(self) -> None:
        print('Ticks remained: ', self.ticks_remained)
        print('-' * 50)
        pprint.pprint(self.field[::-1][:])
        print('-' * 50)
    
    def make_step(self) -> None:
        # TODO: support several clients handling
        assert len(self.clients) == 1

        self.ticks_remained -= 1
        client = self.clients[0]

        new_coord = client.make_step(self.apple_pos, self.field)

        self.field[client.coord.x][client.coord.y] = '_'
        client.coord = new_coord
        self.field[client.coord.x][client.coord.y] = str(client.id)

        if new_coord == self.apple_pos:
            self._find_new_apple_position()
    
    def _find_new_apple_position(self) -> None:
        while True:
            new_x = random.randint(0, len(self.field) - 1)
            new_y = random.randint(0, len(self.field[0]) - 1)
            if self.field[new_x][new_y] != '_':
                continue
            self.field[new_x][new_y] = 'A'
            break
        self.apple_pos = Coord(new_x, new_y)




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

    field = [['_' for _ in range(width)] for _ in range(height)]

    bound = 2 * width + 2 * height - 4
    if bound < players_number:
        raise Exception('players_number is higher than number of starting positions!')

    step = bound // players_number
    clients = []
    for player_id, player in enumerate(range(0, bound, step)):
        if player_id >= players_number:
            break
        if 0 <= player < width:
            first_coord = 0
            second_coord = player
        elif width <= player < width + height - 2:
            first_coord = player - width + 1
            second_coord = -1
        elif width + height - 2 <= player < 2 * width + height - 2:
            first_coord = -1
            second_coord = 2 * width + height - 3 - player
        else:
            first_coord = 2 * width + 2 * height - 4 - player
            second_coord = 0
        client_coord = Coord(first_coord, second_coord)
        field[client_coord.x][client_coord.y] = str(player_id)

        client_address = 'http://' + config.hostname + ':' + str(config.start_port + player_id)
        client = Client(player_id, client_address, client_coord)
        clients.append(client)

    apple_pos = Coord(height // 2, width // 2)
    field[apple_pos.x][apple_pos.y] = 'A'

    return Game(
        field=field,
        ticks_remained=config.ticks,
        clients=clients,
        apple_pos=apple_pos,
    )


if __name__ == '__main__':
    main()