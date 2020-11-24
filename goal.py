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
Misha Schwartz, and Jaisie Sin

=== Module Description ===

This file contains the hierarchy of Goal classes.
"""
from __future__ import annotations
import random
from typing import List, Tuple, Any
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> List[Goal]:
    """Return a randomly generated list of goals with length num_goals.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Precondition:
        - num_goals <= len(COLOUR_LIST)
    """
    n = random.randint(0, 1)
    goals = []
    goaldict = {}
    while len(goaldict) < num_goals:
        col = random.choice(COLOUR_LIST)
        if n == 0:
            goaldict[col] = BlobGoal(col)
        else:
            goaldict[col] = PerimeterGoal(col)
    for key in goaldict:
        goals.append(goaldict[key])
    return goals


def _nested_list_maker(side: int) -> List[List[Any]]:
    lst = []
    for _ in range(side):
        lst.append([])
    for sublist in lst:
        for _ in range(side):
            sublist.append([])
    return lst


def _flatten(block: Block) -> List[List[Tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j]

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    side = pow(2, block.max_depth - block.level)
    lst = _nested_list_maker(side)
    _flatten_helper(block, lst, 0, 0)
    return lst


def _flatten_helper(block: Block, lst: List, x: int, y: int) \
        -> None:
    s = len(lst) // pow(2, block.level)
    if len(block.children) == 0:
        for i in range(x, x+s):
            for j in range(y, y+s):
                lst[i][j] = block.colour
    else:
        k = s//2
        _flatten_helper(block.children[0], lst, x+k, y)
        _flatten_helper(block.children[1], lst, x, y)
        _flatten_helper(block.children[2], lst, x, y+k)
        _flatten_helper(block.children[3], lst, x+k, y+k)


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def __init__(self, target_colour: Tuple[int, int, int]) -> None:
        """Initialize this goal to have the given target colour.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A perimeter goal in the game of Blocky.

        Player tries to have as much of the outer edge of the puzzle
        occupied by blocks of the correct color.

        === Attributes ===
        colour:
            The target colour for this goal, that is the colour to which
            this goal applies.
        """
    def score(self, board: Block) -> int:
        flat = _flatten(board)
        k = len(flat[0])
        count = 0
        for i in range(k):
            if flat[i][0] == self.colour:
                count += 1
            if flat[i][k-1] == self.colour:
                count += 1
        for j in range(k):
            if flat[0][j] == self.colour:
                count += 1
            if flat[k-1][j] == self.colour:
                count += 1
        return count

    def description(self) -> str:
        return 'Have the maximum number of ' + colour_name(self.colour) \
               + " around the perimeter of the game"


class BlobGoal(Goal):
    """A player blob goal in the game of Blocky.

        Player tries to make the largest blob of the target color.
        A blob is defined when blocks of the same color share an edge.

        === Attributes ===
        colour:
            The target colour for this goal, that is the colour to which
            this goal applies.
        """
    def score(self, board: Block) -> int:
        score = 0
        flat = _flatten(board)
        visited = _nested_list_maker(len(flat))
        for r in visited:
            for j in range(len(visited)):
                r[j] = -1
        for i in range(len(visited)):
            for j in range(len(visited)):
                if visited[i][j] == -1:
                    score = max(score, self._undiscovered_blob_size(
                        (i, j), flat, visited))
        return score

    def _undiscovered_blob_size(self, pos: Tuple[int, int],
                                board: List[List[Tuple[int, int, int]]],
                                visited: List[List[int]]) -> int:
        """Return the size of the largest connected blob that (a) is of this
        Goal's target colour, (b) includes the cell at <pos>, and (c) involves
        only cells that have never been visited.

        If <pos> is out of bounds for <board>, return 0.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure that, in each cell, contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.
        """
        blob_size = 0
        if not 0 <= pos[0] < len(board) or not 0 <= pos[1] < len(board[0]):
            return blob_size  # return 0 if out of bounds
        x, y = pos
        if visited[x][y] == 1 or visited[x][y] == 0:
            # cell is already visited, do not count
            return blob_size
        elif board[x][y] != self.colour:
            # not visited but color not matching
            visited[x][y] = 0
            return blob_size
        # accounts for position out of bounds,
        # previously visited cells, and the wrong color
        blob_size += 1
        visited[x][y] = 1
        blob_size += self._undiscovered_blob_size((x-1, y), board, visited)
        blob_size += self._undiscovered_blob_size((x+1, y), board, visited)
        blob_size += self._undiscovered_blob_size((x, y+1), board, visited)
        blob_size += self._undiscovered_blob_size((x, y-1), board, visited)
        return blob_size

    def description(self) -> str:
        return 'Make the largest blob (blocks with edges touching) in ' \
               + colour_name(self.colour)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
