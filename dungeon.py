import random
from typing import Tuple, Dict, List, Optional, Set
from collections import deque
from room import Room, RoomType

class Dungeon:
    def __init__(self):
        self.floors: Dict[int, Dict[Tuple[int, int], Room]] = {}
        self._generated_floors: Set[int] = set()
        self.generate_floor(0)

    def print_floor(self, floor_num: int):
        if floor_num not in self._generated_floors:
            return

        floor = self.floors[floor_num]

        xs = []
        zs = []

        for (x, z) in floor.keys():
            print((x, z))
            xs.append(x)
            zs.append(z)
        
        min_x = min(xs)
        max_x = max(xs)

        min_z = min(zs)
        max_z = max(zs)

        for z in range(min_z, max_z + 1):
            for x in range(min_x, max_x + 1):
                if (x, z) in floor.keys():
                    print("[ ]", end = "")
                else:
                    print("   ", end = "")
                    
            print()
    
    def generate_floor(self, floor_num: int):
        if floor_num in self._generated_floors:
            return
        
        self._generated_floors.add(floor_num)
        floor_rooms = {}
        
        start_room = Room(RoomType.START, floor_num)
        floor_rooms[(0, 0)] = start_room
        
        expansion_queue = deque([(0, 0)])
        directions = [(0, 1, 'north'), (0, -1, 'south'), 
                     (1, 0, 'east'), (-1, 0, 'west')]
        
        num_rooms = random.randint(6 + floor_num, 15 + floor_num * 2)
        rooms_created = 1
        
        while expansion_queue and rooms_created < num_rooms:
            x, z = expansion_queue.popleft()
            
            random.shuffle(directions)
            
            for dx, dz, direction in directions:
                if rooms_created >= num_rooms:
                    break
                
                new_pos = (x + dx, z + dz)
                
                if new_pos not in floor_rooms:
                    room_type = random.choices(
                        [RoomType.EMPTY, RoomType.ENEMY, RoomType.NPC, RoomType.TREASURE],
                        weights=[0 + floor_num*0.02,
                                0.4 + floor_num*0.03,
                                0.2 - floor_num*0.01,
                                1 - floor_num*0.05]
                    )[0]
                    
                    new_room = Room(room_type, floor_num)
                    floor_rooms[new_pos] = new_room
                    rooms_created += 1
                    
                    floor_rooms[(x, z)].connections[direction] = new_room
                    opposite_dir = self._get_opposite_direction(direction)
                    new_room.connections[opposite_dir] = floor_rooms[(x, z)]
                    
                    expansion_queue.append(new_pos)
        
        exit_room_type = RoomType.BOSS if floor_num > 0 else RoomType.EXIT
        exit_room = Room(exit_room_type, floor_num)
        
        last_room_pos = expansion_queue[-1] if expansion_queue else (0, 0)
        placed_exit = False
        
        for dx, dz, direction in directions:
            exit_pos = (last_room_pos[0] + dx, last_room_pos[1] + dz)
            if exit_pos not in floor_rooms:
                floor_rooms[exit_pos] = exit_room
                floor_rooms[last_room_pos].connections[direction] = exit_room
                opposite_dir = self._get_opposite_direction(direction)
                exit_room.connections[opposite_dir] = floor_rooms[last_room_pos]
                placed_exit = True
                break
        
        if not placed_exit:
            for dx, dz, direction in directions:
                exit_pos = (last_room_pos[0] + dx, last_room_pos[1] + dz)
                if exit_pos in floor_rooms and floor_rooms[exit_pos].room_type != RoomType.START:
                    floor_rooms[exit_pos] = exit_room
                    for ndx, ndz, ndir in directions:
                        neighbor_pos = (exit_pos[0] + ndx, exit_pos[1] + ndz)
                        if neighbor_pos in floor_rooms:
                            floor_rooms[neighbor_pos].connections[self._get_opposite_direction(ndir)] = exit_room
                            exit_room.connections[ndir] = floor_rooms[neighbor_pos]
                    break
        
        self.floors[floor_num] = floor_rooms
    
    def get_room(self, position: Tuple[int, int, int]) -> Optional[Room]:
        x, y, z = position
        if y not in self.floors:
            raise ValueError(f"Floor {y} not generated yet")
        return self.floors[y].get((x, z))
    
    def _get_opposite_direction(self, direction: str) -> str:
        opposites = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east"
        }
        return opposites.get(direction, direction)
    
    def to_dict(self):
        return {
            "floors": {
                floor_num: {
                    f"{x},{y}": room.to_dict() for (x, y), room in floor_rooms.items()
                }
                for floor_num, floor_rooms in self.floors.items()
            }
        }