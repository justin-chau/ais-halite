import hlt
import logging
from hlt import constants
from hlt import Position
from hlt.positionals import Direction

""" <<<Game Begin>>> """

game = hlt.Game()
# Ready, starts 2 second timer per turn
game.ready("Justin-AIS-Halite")
logging.info("Initialized! ID = {}.".format(game.my_id))

""" <<<Game Loop>>> """

def find_best_move(ship):
    best_position = ship.position
    best_value = 0
    logging.info("finding best move...")
    for y in range(game_map.height):
        for x in range(game_map.width):
            cell = game_map[hlt.Position(x, y)]
            if not(cell.is_occupied) and (cell.position is not ship.position):
                cell_value = cell.halite_amount / game_map.calculate_distance(ship.position, cell.position)
                if cell_value > best_value:
                    best_value = cell_value
                    best_position = cell.position
            
    return best_position


while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map

    # Holds commands, submitted at the end of turn. 
    command_queue = []

    for ship in me.get_ships():
        if (ship.halite_amount > 500) and not game_map[me.shipyard.position].is_occupied:
            # if (me.halite_amount >= constants.DROPOFF_COST+5000) and (game_map.calculate_distance(ship.position, me.shipyard.position) > 30):
            #     command_queue.append(ship.make_dropoff())
            # else:
                command_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))
        else:
            max_halite_position = ship.position
            max_halite_value = game_map[ship.position].halite_amount

            for position in ship.position.get_surrounding_cardinals():
                if game_map[position].halite_amount * 0.125 > max_halite_value * 0.25:
                    max_halite_position = position
                    max_halite_value = game_map[position].halite_amount

            if max_halite_value is 0:
                max_halite_position = find_best_move(ship)

            if (max_halite_position is not ship.position):
                command_queue.append(ship.move(game_map.naive_navigate(ship, max_halite_position)))
            else:
                command_queue.append(ship.stay_still())

    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST+3000 and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # End turn.
    game.end_turn(command_queue)


