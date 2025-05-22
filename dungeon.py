from room import Room

class Dungeon:
    def __init__(self):
        starting_room = Room(0, 0, 0, "Starting room")
        starting_room.visit()

        self.rooms = {
            (0, 0, 0): starting_room
        }

    def get_room(self, pos):
        return self.rooms[pos]