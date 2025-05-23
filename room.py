import json
import random
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

from ollama import Ollama, simple_ollama_query

class RoomType(Enum):
    START = "Start"
    EMPTY = "Empty"
    ENEMY = "Enemy"
    NPC = "NPC"
    TREASURE = "Treasure"
    BOSS = "Boss"
    EXIT = "Exit"

@dataclass
class NPC:
    name: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Enemy:
    name: str
    hp: int
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Loot:
    name: str
    amount: int = 1
    
    def to_dict(self):
        return asdict(self)

BOILERPLATE = "do not provide any additional text, comments or explanation, no quotemarks or any other indentation whatsoever"

class Room:
    def __init__(self, room_type: RoomType, floor_num: int):
        self.room_type = room_type
        self.name: Optional[str] = None
        self.connections: Dict[str, Room] = {}
        self.enemies: List[Enemy] = []
        self.npcs: List[NPC] = []
        self.loot: List[Loot] = []
        self.floor_num = floor_num
        
        self._initialize_content()

    def spawn_enemy(self, name = None, hp = 0):
        prompt = f"Generate an enemy name for an RPG, {BOILERPLATE}: "
        name = name or simple_ollama_query("llama3.2", prompt)
        hp = hp or int(re.findall(r'\d+', simple_ollama_query("llama3.2", f"On a scale from 10 to {100 + 100 * self.floor_num}, what do you think is the appropriate health of an enmy called '{name}' in an RPG, {BOILERPLATE}"))[0])
        self.enemies.append(Enemy(name, hp))
    
    def _initialize_content(self):
        if self.room_type == RoomType.ENEMY:
            num_enemies = random.randint(1, 3)
            for _ in range(num_enemies):
                self.spawn_enemy()
        elif self.room_type == RoomType.NPC:
            prompt = f"Generate a name for an NPC in an RPG, {BOILERPLATE}: "
            name = simple_ollama_query("llama3.2", prompt)
            self.npcs.append(NPC(name))
        elif self.room_type == RoomType.TREASURE or self.room_type == RoomType.START:
            max_loot = 5
            if self.room_type == RoomType.START:
                max_loot *= 2
            num_loot = random.randint(2, max_loot)
            for _ in range(num_loot):
                prompt = f"Generate a name for SINGULAR, RANDOM dungeon loot (e.g. {random.choice([
                    "weapon",
                    "spell tome",
                    "magic staff",
                    "scroll",
                    "potion",
                    "food",
                    "grenade",
                    "bomb",
                    "herbs",
                    "enchants"
                ])}) in an RPG, {BOILERPLATE}: "
                name = simple_ollama_query("llama3.2", prompt)
                self.loot.append(Loot(name, random.randint(1, 5)))
        
        content_desc = []
        if self.enemies:
            content_desc.append(f"enemies: {[e.name for e in self.enemies]}")
        if self.npcs:
            content_desc.append(f"npcs: {[n.name for n in self.npcs]}")
        if self.loot:
            content_desc.append(f"loot: {[l.name for l in self.loot]}")
        
        prompt = (f"Generate a creative name for a dungeon room containing "
                    f"{', '.join(content_desc)}, {BOILERPLATE}: ")
        self.name = "".join(Ollama("llama3.2").generate(prompt))
    
    def to_dict(self):
        return {
            "name": self.name,
            # "type": self.room_type.value,
            "connections": {dir: room.name for dir, room in self.connections.items()},
            "enemies": [enemy.to_dict() for enemy in self.enemies],
            "npcs": [npc.to_dict() for npc in self.npcs],
            "loot": [loot.to_dict() for loot in self.loot]
        }

    def json(self):
        return json.dumps(self.to_dict())
