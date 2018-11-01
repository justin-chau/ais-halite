import hlt

from hlt import constants
from hlt.positionals import Direction
import random
import logging

""" <<<Game Begin>>> """

game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("Respawn-Halite")
logging.info("Initialized! ID = {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the end of the turn.
    command_queue = []

    for ship in me.get_ships():
        if (ship.halite_amount > 500) or ((ship.position is me.shipyard.position) and ship.halite_amount > 30):
            command_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))
        else:
            max_halite_position = ship.position
            max_halite_value = game_map[ship.position].halite_amount

            for position in ship.position.get_surrounding_cardinals():
                if game_map[position].halite_amount * 0.125 > max_halite_value * 0.25:
                    max_halite_position = position
                    max_halite_value = game_map[position].halite_amount

            if (max_halite_position is not ship.position):
                command_queue.append(ship.move(game_map.naive_navigate(ship, max_halite_position)))
            else:
                command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST+3000 and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

