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

    current_targets = []
    for path in ship_paths.values():
        if len(path) > 0:
            current_targets.append(path[len(path)-1])

    for position in ship.position.get_surrounding_cardinals():
        if position not in current_targets:
            if game_map[position].halite_amount * 0.125 > max_halite_value * 0.25:
                optimal_position = position
                max_halite_value = game_map[position].halite_amount

    if max_halite_value == 0:
        max_halite_value = 0
        for y in range(game_map.height):
            for x in range(game_map.width):
                cell = game_map[hlt.Position(x, y)]
                if not cell.is_occupied and cell.position is not ship.position and cell.position not in current_targets:
                    cell_value = cell.halite_amount / game_map.calculate_distance(ship.position, cell.position)
                    if cell_value > max_halite_value:
                        max_halite_value = cell_value
                        optimal_position = cell.position
            
    return game_map.normalize(optimal_position)

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
        position_path.append(game_map.normalize(tuple_to_pos(position)))

    if len(position_path) < 0:
        position_path.append(game_map.normalize(target))

    return position_path

def pos_to_tuple(position):
    return (position.x, position.y)

def tuple_to_pos(tup):
    return game_map.normalize(Position(tup[0], tup[1]))

def can_move_off(ship):
    if ship.halite_amount >= 0.10*game_map[ship.position].halite_amount:
        return True
    else:
        return False

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []

    next_positions = {}

    players = game.players

    opposing_locations = []
    for player in players:
        if player != game.my_id:
            for ship in players[player].get_ships():
                opposing_locations.append(ship.position)

    logging.info("Current Paths (Turn Start): {}".format(ship_paths))

    for ship in me.get_ships():
        has_current_path = False
        for ship_id in ship_paths:
            if ship_id == ship.id and len(ship_paths[ship.id]) > 0:
                has_current_path = True

        if has_current_path == False:
            if ship.halite_amount > 750 and not game_map[me.shipyard.position].is_occupied:
                ship_paths[ship.id] = a_star(ship.position, me.shipyard.position)
            else:
                ship_paths[ship.id] = a_star(ship.position, find_best_position(ship))

    for ship_id in ship_paths:
        if me.has_ship(ship_id):
            if can_move_off(me.get_ship(ship_id)) and len(ship_paths[ship_id]) > 0:
                next_positions[ship_id] = ship_paths[ship_id][0]
            else:
                next_positions[ship_id] = me.get_ship(ship_id).position
    
    logging.info("Next Positions: {}".format(next_positions))

    next_adj_positions = {}

    for ship_id in next_positions:
        if next_positions[ship_id] == me.get_ship(ship_id).position:
            next_adj_positions[ship_id] = me.get_ship(ship_id).position

    for ship_id in next_positions:
        if ship_id not in next_adj_positions:
            if next_positions[ship_id] in next_adj_positions.values() or next_positions[ship_id] in opposing_locations:
                if me.get_ship(ship_id).position in next_adj_positions.values():
                    for position in me.get_ship(ship_id).position.get_surrounding_cardinals():
                        if position not in next_adj_positions.values():
                            ship_paths[ship_id].insert(0, me.get_ship(ship_id).position)
                            next_adj_positions[ship_id] = game_map.normalize(position)
                else:
                    next_adj_positions[ship_id] = me.get_ship(ship_id).position
            else:
                next_adj_positions[ship_id] = next_positions[ship_id]

    #     if next_positions[ship_id] == me.get_ship(ship_id).position:
    #         next_adj_positions[ship_id] = me.get_ship(ship_id).position
    #     elif next_positions[ship_id] not in next_adj_positions.values():
    #         next_adj_positions[ship_id] = next_positions[ship_id]
    #     else:
    #         next_adj_positions[ship_id] = me.get_ship(ship_id).position
            
    # positions = []
    # duplicate_positions = []
    # for ship_id in next_adj_positions:
    #     if pos_to_tuple(next_adj_positions[ship_id]) not in positions:
    #         positions.append(pos_to_tuple(next_adj_positions[ship_id]))
    #     else:
    #         duplicate_positions.append(next_adj_positions[ship_id])
    #         logging.info("Duplicate positions found: {}".format(duplicate_positions))

    # duplicate_ships = []
    # for duplicate in duplicate_positions:
    #     for ship_id, position in next_adj_positions.items():    # for name, age in dictionary.iteritems():  (for Python 2.x)
    #         if position == duplicate:
    #             if next_adj_positions[ship_id] != me.get_ship(ship_id).position:
    #                 next_adj_positions[ship_id] = me.get_ship(ship_id).position
    #                 logging.info("Duplicate Avoided!")

    # for ship in me.get_ships():
    #     if ship.id not in ship_paths:
    #         next_adj_positions[ship.id] = ship.position
    #     elif ship.position == next_positions[ship.id]:
    #         next_adj_positions[ship.id] = ship.position

    # for ship_id in next_positions:
    #     if next_positions[ship_id] not in next_adj_positions.values():
    #         next_adj_positions[ship_id] = next_positions[ship_id]
    #     else:
    #         next_adj_positions[ship_id] = me.get_ship(ship_id).position

    logging.info("Next Adjusted Positions: {}".format(next_adj_positions))

    for ship_id in next_adj_positions:
        choices = [Direction.North, Direction.South, Direction.West, Direction.East, Direction.Still]
        for choice in choices:
            if game_map.normalize(me.get_ship(ship_id).position.directional_offset(choice)) == game_map.normalize(next_adj_positions[ship_id]):
                command_queue.append(me.get_ship(ship_id).move(choice))
                if next_adj_positions[ship_id] == ship_paths[ship_id][0]:
                    ship_paths[ship_id].pop(0)

    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and not me.shipyard.position in next_adj_positions.values():
        command_queue.append(me.shipyard.spawn())
        
    logging.info("Current Paths (Turn End): {}".format(ship_paths))
    
    game.end_turn(command_queue)