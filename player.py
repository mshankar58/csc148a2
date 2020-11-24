"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE

MOVES = [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,
         SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PAINT, COMBINE]


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    goals = generate_goals(num_human + num_random + len(smart_players))
    players = []
    for i in range(num_human):
        players.append(HumanPlayer(i, goals[i]))
    for i in range(num_random):
        players.append(RandomPlayer(num_human + i, goals[num_human + i]))
    for i in range(len(smart_players)):
        players.append(SmartPlayer(num_human + num_random + i,
                                   goals[num_human + num_random + i]
                                   , smart_players[i]))
    return players


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth
    """
    x1, y1 = block.position
    x2, y2 = location
    if not (x1 <= x2 < x1 + block.size and y1 <= y2 < y1 + block.size):
        return None
    if not block.children:
        return block
    elif block.level == level:
        return block
    else:
        for child in block.children:
            k = _get_block(child, location, level)
            if k is not None:
                return k
        return None


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    return action[0], action[1], block


def _validate_move(action: Tuple[str, int], block: Block, direction: int,
                   col: Tuple[int, int, int]) -> bool:

    move_successful = False
    if action in [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE]:
        move_successful = block.rotate(direction)
    elif action in [SWAP_HORIZONTAL, SWAP_VERTICAL]:
        move_successful = block.swap(direction)
    elif action == SMASH:
        move_successful = block.smash()
    elif action == PAINT:
        move_successful = block.paint(col)
    elif action == COMBINE:
        move_successful = block.combine()
    elif action == PASS:
        move_successful = False
    return move_successful


class HumanPlayer(Player):
    """A human player.
    """
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


class RandomPlayer(Player):
    """A random computer player in the Blocky game.

        === Public Attributes ===
        id:
            This player's number.
        goal:
            This player's assigned goal for the game.

        === Private Attributes ===
        _proceed:
          True when the player should make a move, False when the player should
          wait.
    """
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        valid = False
        x, y = 0, 0
        action = MOVES[0]

        while not valid:
            x, y = random.randint(0, board.size), random.randint(0, board.size)
            copy_board = board.create_copy()
            block = _get_block(copy_board, (x, y), copy_board.max_depth)
            action = MOVES[random.randint(0, len(MOVES)-1)]
            valid = _validate_move(action, block, 1, self.goal.colour)

        b_real = _get_block(board, (x, y), board.max_depth)
        # get the block from the real board
        move = _create_move(action, b_real)
        # make a move using that real block; do not execute
        self._proceed = False
        # Must set to False before returning!
        return move


class SmartPlayer(Player):
    """A random computer player in the Blocky game.

            === Public Attributes ===
            id:
                This player's number.
            goal:
                This player's assigned goal for the game.

            === Private Attributes ===
            _proceed:
              True when the player should make a move, False when the
              player should wait.
            _difficulty:
            How many possible moves the player should consider.
        """
    _proceed: bool
    _difficulty: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        Player.__init__(self, player_id, goal)
        self._proceed = False
        self._difficulty = difficulty
        # contingency for zero or negative? - check a2 site

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def _evaluate(self, move: Tuple[str, Optional[int], Block], board: Block) \
            -> int:
        copy_board = board.create_copy()
        x, y = board.position
        fake_block = _get_block(copy_board, (x, y), copy_board.max_depth)
        action = move[0], move[1]
        initial = self.goal.score(copy_board)
        if action == ROTATE_CLOCKWISE:
            fake_block.rotate(1)
        elif action == ROTATE_COUNTER_CLOCKWISE:
            fake_block.rotate(3)
        elif action == SWAP_VERTICAL:
            fake_block.swap(1)
        elif action == SWAP_HORIZONTAL:
            fake_block.swap(0)
        elif action == SMASH:
            fake_block.smash()
        elif action == PAINT:
            fake_block.paint(self.goal.colour)
        elif action == COMBINE:
            fake_block.combine()
        elif action == PASS:
            return 0
        final = self.goal.score(copy_board)
        return final-initial

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """

        if not self._proceed:
            return None  # Do not remove
        finals = []

        while len(finals) < self._difficulty:
            x, y = random.randint(0, board.size), random.randint(0, board.size)
            copy_board = board.create_copy()
            fake_block = _get_block(copy_board, (x, y), copy_board.max_depth)
            action = MOVES[random.randint(0, len(MOVES) - 1)]
            valid = _validate_move(action, fake_block, 1, self.goal.colour)
            if valid:
                b_real = _get_block(board, (x, y), board.max_depth)
                # get the block from the real board
                move = _create_move(action, b_real)
                # make a move using that real block; do not execute
                finals.append(move)

        the_move = _create_move(PASS, board)
        score_increase = 0
        for possible_move in finals:
            if self._evaluate(possible_move, board) > score_increase:
                the_move = possible_move
        self._proceed = False
        # Must set to False before returning!
        return the_move


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
