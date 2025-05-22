import json

from ollama import Ollama

ollama = Ollama("dungeon-generator")

def parse_first_valid_json(text):
    text = "".join(text)
    print("parse_first_valid_json", text)
    depth = 0
    result = []
    for i, char in enumerate(text):
        result.append(char)
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(''.join(result))
                except json.JSONDecodeError:
                    break
    raise ValueError("No valid JSON object found")

class Room:
    def __init__(self, x, y, z, name):
        self.position = (x, y, z)
        self.name = name
        self.connections = {
            "north": None,
            "east": None,
            "south": None,
            "west": None,
            "up": None,
            "down": None
        }
        self.enemies = []
        self.npcs = []
        self.loot = []
        self.visited = False

    def get_data(self):
        while True:
            res = ollama.generate(f"\"{self.name}\"")
            try:
                data = parse_first_valid_json(res)
                if data is None:
                    raise ValueError("data is None")
                return data
            except:
                print("Retrying room generation")
                continue

    def visit(self):
        if self.visited:
            return

        self.visited = True
        
        data = self.get_data()

        print("Room.get_data() = ", data)

        if data:
            if data["connections"]:
                for direction in data["connections"]:
                    self.connections[direction] = data["connections"][direction] or None
            if data["enemies"]:
                self.enemies = data["enemies"] or []
            if data["npcs"]:
                self.npcs = data["npcs"] or []
            if data["loot"]:
                self.loot = data["loot"] or []

    def json(self):
        connections = {}
        for direction in self.connections:
            if self.connections[direction]:
                connections[direction] = self.connections[direction]

        return json.dumps({
            "name": self.name,
            "connections": connections,
            "enemies": self.enemies,
            "npcs": self.npcs,
            "loot": self.loot
        })