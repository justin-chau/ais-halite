import hlt
import logging
from queue import *
from hlt import constants
from hlt import Position
from hlt.positionals import Direction

game = hlt.Game()
game.ready("Justin-Halite-Bot")
logging.info("Initialized! ID = {}.".format(game.my_id))

ship_paths = {} #Dict with paths for each ship.

def find_best_position(ship):
    optimal_position = ship.position
    max_halite_value = game_map[ship.position].halite_amount

    for position in ship.position.get_surrounding_cardinals():
        if game_map[position].halite_amount * 0.125 > max_halite_value * 0.25:
            optimal_position = position
            max_halite_value = game_map[position].halite_amount

    if max_halite_value is 0:
        for y in range(game_map.height):
            for x in range(game_map.width):
                cell = game_map[hlt.Position(x, y)]
                if not cell.is_occupied and cell.position is not ship.position:
                    cell_value = cell.halite_amount / game_map.calculate_distance(ship.position, cell.position)
                    if cell_value > max_halite_value:
                        max_halite_value = cell_value
                        optimal_position = cell.position
            
    return optimal_position

def a_star(start, target):
    target_tuple = pos_to_tuple(target)
    frontier = Queue()
    frontier.put(pos_to_tuple(start))
    came_from = {}
    came_from[pos_to_tuple(start)] = None

    while not frontier.empty():
        current = frontier.get()

        if current == target_tuple:
            break

        for next in Position(current[0], current[1]).get_surrounding_cardinals():
            if pos_to_tuple(next) not in came_from:
                frontier.put(pos_to_tuple(next))
                came_from[pos_to_tuple(next)] = current

    current = pos_to_tuple(target)
    path = []

    while current != pos_to_tuple(start):
        path.append(current)
        current = came_from[current]
    
    path.append(pos_to_tuple(start))
    path.reverse()

    position_path = []

    for position in path:
        position_path.append(tuple_to_pos(position))

    return position_path

def pos_to_tuple(position):
    return (position.x, position.y)

def tuple_to_pos(tup):
    return Position(tup[0], tup[1])

def navigate(ship, target):
    command_queue.append(ship.move(game_map.naive_navigate(ship, target)))

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []

    logging.info("Current Paths: {}".format(ship_paths))

    for ship in me.get_ships():
        if ship.halite_amount > 750 and not game_map[me.shipyard.position].is_occupied:
            ship_paths[ship.id] = a_star(ship.position, me.shipyard.position)
            navigate(ship, me.shipyard.position)
        else:
            if ship.halite_amount >= 0.10*game_map[ship.position].halite_amount:
                ship_paths[ship.id] = a_star(ship.position, find_best_position(ship))
                navigate(ship, find_best_position(ship))
            else:
                command_queue.append(ship.stay_still())

    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)