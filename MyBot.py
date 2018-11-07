import hlt
import logging
from queue import *
from hlt import constants
from hlt import Position
from hlt.positionals import Direction

game = hlt.Game()
game.ready("Justin-Bot")
logging.info("Initialized! ID = {}.".format(game.my_id))

# Dictionary with ship_id as key and ship path.
ship_paths = {}

def find_best_position(ship):
    # Returns the optimal position to set the target to per ship.
    optimal_position = ship.position
    max_halite_value = game_map[ship.position].halite_amount #* 1.35

    # Finds all current long term targets from paths.
    current_targets = []
    for path in ship_paths.values():
        if len(path) > 0:
            current_targets.append(path[len(path)-1])

    for position in ship.position.get_surrounding_cardinals():
        if game_map.normalize(position) not in current_targets:
            if game_map[position].halite_amount * 0.125 > max_halite_value * 0.25:
                optimal_position = position
                max_halite_value = game_map[position].halite_amount

    if max_halite_value == 0:
        max_halite_value = 0
        for y in range(game_map.height):
            for x in range(game_map.width):
                cell = game_map[hlt.Position(x, y)]
                if not cell.is_occupied and cell.position is not ship.position and game_map.normalize(cell.position) not in current_targets:
                    cell_value = cell.halite_amount / game_map.calculate_distance(ship.position, cell.position)
                    if cell_value > max_halite_value:
                        max_halite_value = cell_value
                        optimal_position = cell.position

    logging.info("Ship {} has found position {}".format(ship.id, optimal_position))      
    return game_map.normalize(optimal_position)

def a_star(start, target):
    target_tuple = pos_to_tuple(game_map.normalize(target))
    frontier = Queue()
    frontier.put(pos_to_tuple(game_map.normalize(start)))
    came_from = {}
    came_from[pos_to_tuple(game_map.normalize(start))] = None

    while not frontier.empty():
        current = frontier.get()

        if current == target_tuple:
            break

        for next in Position(current[0], current[1]).get_surrounding_cardinals():
            if pos_to_tuple(game_map.normalize(next)) not in came_from:
                frontier.put(pos_to_tuple(game_map.normalize(next)))
                came_from[pos_to_tuple(game_map.normalize(next))] = current

    current = pos_to_tuple(game_map.normalize(target))
    path = []

    while current != pos_to_tuple(game_map.normalize(start)):
        path.append(current)
        current = came_from[current]
    
    path.append(pos_to_tuple(game_map.normalize(start)))
    path.reverse()

    position_path = []

    for position in path:
        position_path.append(game_map.normalize(tuple_to_pos(position)))

    del position_path[0] #Important: Prevents ships from staying in place during path change.

    if len(position_path) < 1:
        position_path.append(game_map.normalize(target))
        logging.info("Staying in place.")

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

def find_nearest_drop(ship):
    optimal_position = me.shipyard.position
    min_distance = game_map.calculate_distance(ship.position, me.shipyard.position)
    for drop in me.get_dropoffs():
        if game_map.calculate_distance(ship.position, drop.position) < min_distance:
            optimal_position = drop.position
            min_distance = game_map.calculate_distance(ship.position, drop.position)

    return optimal_position

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    next_positions = {}
    players = game.players
    turn_halite = me.halite_amount

    collided_ships = []
    for ship_id in ship_paths:
        if not me.has_ship(ship_id):
            collided_ships.append(ship_id)

    for ship_id in collided_ships:
        ship_paths.pop(ship_id)
        logging.info("Removing collided ship paths for ship: {}".format(ship_id))

    opposing_locations = []
    for player in players:
        if player != game.my_id:
            for ship in players[player].get_ships():
                opposing_locations.append(game_map.normalize(ship.position))

    logging.info("Current Paths (Turn Start): {}".format(ship_paths))

    for ship in me.get_ships():
        has_current_path = False
        for ship_id in ship_paths:
            if ship_id == ship.id and len(ship_paths[ship.id]) > 0:
                has_current_path = True

        if has_current_path == False:
            if ship.halite_amount > 750:
                nearest_drop = find_nearest_drop(ship)
                ship_paths[ship.id] = a_star(ship.position, nearest_drop)
            else:
                ship_paths[ship.id] = a_star(ship.position, find_best_position(ship))

    for ship_id in ship_paths:
        if me.has_ship(ship_id):
            if can_move_off(me.get_ship(ship_id)) and len(ship_paths[ship_id]) > 0:
                next_positions[ship_id] = game_map.normalize(ship_paths[ship_id][0])
            else:
                next_positions[ship_id] = game_map.normalize(me.get_ship(ship_id).position)
    
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

    logging.info("Next Adjusted Positions: {}".format(next_adj_positions))

    for ship_id in next_adj_positions:
        choices = [Direction.North, Direction.South, Direction.West, Direction.East, Direction.Still]
        for choice in choices:
            if game_map.normalize(me.get_ship(ship_id).position.directional_offset(choice)) == game_map.normalize(next_adj_positions[ship_id]):
                command_queue.append(me.get_ship(ship_id).move(choice))
                if next_adj_positions[ship_id] == ship_paths[ship_id][0]:
                    ship_paths[ship_id].pop(0)

    if game.turn_number <= 200 and turn_halite >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and not me.shipyard.position in next_adj_positions.values():
        command_queue.append(me.shipyard.spawn())
        
    logging.info("Current Paths (Turn End): {}".format(ship_paths))
    
    game.end_turn(command_queue)