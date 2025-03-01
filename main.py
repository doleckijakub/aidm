#!/usr/bin/env python3

import requests
import json

# ollama

OLLAMA_HOST = "127.0.0.1:11434"

def ollama_request(model, prompt, stream):
    return requests.post(
        f"http://{OLLAMA_HOST}/api/generate",
        headers = { "Content-Type": "application/json" },
        json = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        },
        stream = stream
    )

def ollama_request_text(model, prompt):
    return ollama_request(model, prompt, False).json()["response"]

def ollama_request_stream(model, prompt):
    for chunk in ollama_request(model, prompt, True).iter_lines():
        if chunk:
            yield json.loads(chunk.decode("utf-8"))["response"]

# room

def parse_first_valid_json(text):
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

    def visit(self):
        if self.visited:
            return

        self.visited = True
        
        data = None
        while True:
            res = ollama_request_text("dungeon-generator", f"\"{self.name}\"")
            try:
                data = parse_first_valid_json(res)
            except:
                continue
            finally:
                break

        print(data)

        if data:
            if data["connections"]:
                for direction in data["connections"]:
                    self.connections[direction] = data["connections"][direction]
            if data["enemies"]:
                self.enemies = data["enemies"]
            if data["npcs"]:
                self.npcs = data["npcs"]
            if data["loot"]:
                self.loot = data["loot"]

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

# aidm

MAX_HISTORY_LENGTH = 10

class AIDM:
    def __init__(self):
        self.history = []

    def remember(self, text):
        self.history.append(text)
        if len(self.history) >= MAX_HISTORY_LENGTH:
            self.history = self.history[0:MAX_HISTORY_LENGTH]

    def handle_player_prompt(self, player, prompt):
        pass

    def describe_location(self, room):
        text = ""
        room_json = room.json()
        print(f"room_json = {room_json}")
        for chunk in ollama_request_stream("llama3.2:1b", f"Given the following JSON describing a room in a tabletop RPG setting: {room_json} Describe the room as if you are a Dungeon Master narrating the scene to the players. Include: A description of the room's notable features; any items or loot that can be found; possible exits and where they lead, described in a way that encourages exploration. Keep the tone consistent with a fantasy setting. Be as concise as possible, limit youself to 5 sentences."):
            print(chunk, end="", flush=True)
            text += chunk
        self.remember(text)

# player

RACES = [
    "Human",
    "Elf",
    "Magicborn",
    "Dwarf",
    "Ogre",
    "Fairy",
    "Gnome",
    "Jew",
    "Dragonborn",
    "Demon",
    "Goblin",
    "Minotaur"
]

CLASSES = [
    "Healer",
    "Warrior",
    "Mage",
    "Herbalist",
    "Archer",
    "Rouge",
    "Paladin",
    "Bard",
    "Monk",
    "Bum",
    "Midget",
    "Druid",
    "Necromancer"
]

class Player:
    def __init__(self):
        self.name = input("Name > ")
        
        print("Races: " + ", ".join(RACES))
        self.race = None
        while not self.race in RACES:
            self.race = input("Race > ")

        print("Classes: " + ", ".join(CLASSES))
        self.class_ = None
        while not self.class_ in CLASSES:
            self.class_ = input("Class > ")

        # self.backstory = ollama_request_text("llama3.2:1b", f"Generate a single sentence backstory for a RPG player called {self.name} who is a {self.race} {self.class_}")
        # print(self.backstory)

    def desc(self):
        return f"{self.name}, a {self.race} {self.class_}"

# party

class Party:
    def __init__(self):
        self.players = []
        size = 0 # int(input("Party size > "))
        for i in range(size):
            print(f"Player {i + 1}")
            self.players.append(Player())

        self.position = (0, 0, 0)

# dungeon

class Dungeon:
    def __init__(self):
        starting_room = Room(0, 0, 0, "Starting room")
        starting_room.visit()

        self.rooms = {
            (0, 0, 0): starting_room
        }

    def get_room(self, pos):
        return self.rooms[pos]


# main

if __name__ == "__main__":
    dm = AIDM()
    dungeon = Dungeon()
    party = Party()

    # for text in ollama_request_stream("llama3.2", f"Generate a brief ({3 + len(party.players)} sentence) story that describes a party of {", ".join(player.desc() for player in party.players)} and starts their dungeon scavenging adventure"):
    #     print(text, end="", flush=True)
    print()

    while True:
        dm.describe_location(dungeon.get_room(party.position))
        break
