import hlt
from hlt import constants, Position
from hlt.positionals import Direction
import random
import logging

""" <<<Game Begin>>> """
game = hlt.Game()
game.ready("MyPythonBot")
logging.info("Initialized Bot. Player ID is {}.".format(game.my_id))

long_targets = {}
k_distance_multiplier = 100

def has_long_target(ship):
    for ship_id in long_targets:
        if ship_id is ship.id and long_targets[ship_id]['target'] is not ship.position:
            return True
    return False

def has_arrival_conflict(ship, position):
    update_long_targets_collisions()
    ship_distance = game_map.calculate_distance(ship.position, position)
    for ship_id in long_targets:
        if long_targets[ship_id]['target'] is position:
            conflict_ship = me.get_ship(ship_id)
            conflict_ship_distance = game_map.calculate_distance(conflict_ship.position, position)
            if conflict_ship_distance is ship_distance:
                return True
    return False

def is_in_short_targets(target):
    for ship_id in short_targets:
        logging.info("Checking conflict for position {}".format(target))
        logging.info("Against {}".format(short_targets[ship_id]['target']))
        if target == short_targets[ship_id]['target']:
            logging.info("Found another short target!")
            return True
    return False

def is_in_long_targets(target):
    for ship_id in short_targets:
        logging.info("Checking conflict for position {}".format(target))
        logging.info("Against {}".format(long_targets[ship_id]['target']))
        if target == long_targets[ship_id]['target']:
            logging.info("Found another long target!")
            return True
    return False

def set_short_target(ship, target):
    directions = [Direction.North, Direction.South, Direction.West, Direction.East]
    min_distance = game_map.calculate_distance(ship.position, target)
    optimal_direction = Direction.Still
    for direction in directions:
        prospect_position = ship.position.directional_offset(direction)
        prospect_distance = game_map.calculate_distance(prospect_position, target)
        if prospect_distance < min_distance and is_in_short_targets(prospect_position) is False:
            min_distance = prospect_distance
            optimal_direction = direction

    optimal_position = ship.position.directional_offset(optimal_direction)
    if ship.id in short_targets:
        short_targets[ship.id]['target'] = optimal_position
    else:
        short_targets[ship.id] = {}
        short_targets[ship.id]['target'] = optimal_position
    command_queue.append(ship.move(optimal_direction))

def set_long_target(ship):
    max_value = 0
    optimal_position = ship.position
    for y in range(game_map.height):
        for x in range(game_map.width):
            cell = game_map[Position(x, y)]
            if (cell.position != ship.position) and not (is_in_long_targets(cell.position)):
                if has_arrival_conflict(ship, cell.position) is False:
                    cell_distance = game_map.calculate_distance(ship.position, cell.position)
                    cell_halite = cell.halite_amount
                    prospect_value = cell_halite/cell_distance
                    if prospect_value > max_value:
                        max_value = prospect_value
                        optimal_position = cell.position
    
    long_targets[ship.id] = {}
    long_targets[ship.id]['target'] = optimal_position
    set_short_target(ship, long_targets[ship.id]['target'])

def update_long_targets_collisions():
    ship_ids = []
    for ship_id in long_targets:
        ship_ids.append(ship_id)
    for ship_id in ship_ids:
        if me.has_ship(ship_id) is False:
            logging.info("Popping")
            long_targets.pop(ship_id)

""" <<<Game Loop>>> """

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    drops = []
    drops.append(me.shipyard.position)
    for dropoff in me.get_dropoffs():
        drops.append(dropoff.position)
    short_targets = {}
    command_queue = []

    for ship in me.get_ships():
        if has_long_target(ship):
            set_short_target(ship, long_targets[ship.id]['target'])
            logging.info("Ship already has long range.")
        else:
            set_long_target(ship)

    logging.info("Current Short Targets: {}".format(short_targets))
    logging.info("Current Long Targets: {}".format(long_targets))

    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)