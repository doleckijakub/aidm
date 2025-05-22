#!/usr/bin/env python3

from aidm import AIDM
from party import Party
from dungeon import Dungeon

if __name__ == "__main__":
    party = Party()
    dungeon = Dungeon()

    AIDM(party, dungeon).run()
