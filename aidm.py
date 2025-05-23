import re
import requests
import json
import sys
import time
import traceback
import ast

from player import Player
from ollama import Ollama

def eprint(*args, **kwargs):
    # return
    print("\033[3m", end="", file=sys.stderr)
    print(*args, file=sys.stderr, **kwargs)
    print("\033[0m", end="", file=sys.stderr)

class SafeExecutor:
    def __init__(self, context):
        self.context = context

    def is_safe_ast(self, code: str):
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError:
            return False

        allowed_nodes = (
            ast.Module, ast.Expr, ast.Call, ast.Name, ast.Load,
            ast.Constant, ast.Attribute, ast.arguments, ast.arg,
            ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
            ast.UnaryOp, ast.USub, ast.UAdd, ast.Compare, ast.Eq,
            ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Subscript, ast.Attribute,
        )

        for node in ast.walk(tree):
            if not isinstance(node, allowed_nodes):
                return node
        return True

    def safe_exec(self, code: str):
        r = self.is_safe_ast(code)
        if r is not True:
            raise ValueError(f"Unsafe or unsupported code: {ast.dump(r, indent = 4)}")
        exec(code, {"__builtins__": {}}, self.context)

LOGFILE = time.strftime("logs/%Y-%m-%d_%H_%M_%S.log")

class AIDM:
    def __init__(self, party, dungeon):
        self.ollama = Ollama("dungeon-master")
        self.conversation = []
        self.context = []
        
        self.party = party
        self.players = dict()
        for player in party.players:
            self.players[player.name] = player
        self.dungeon = dungeon

    def run(self):
        while True:
            for player_name in self.players:
                r = True
                while r:
                    self.print_sayer(player_name)
                    prompt = input()
                    if prompt[0] == "!":
                        SafeExecutor(context = { "self": self }).safe_exec(prompt[1:])
                    else:
                        r = self.handle_player_prompt(player_name, prompt)
                    
                    for some_player_name in self.players:
                        if self.players[some_player_name].hp <= 0:
                            self.cmd_say(f"{some_player_name} died")
                            self.players.remove(some_player_name)

                    self.conversation.extend(self.context)
                    self.conversation.append("___")

                    with open(LOGFILE, "w") as f:
                        f.write("\n".join(self.conversation))
            else:
                self.cmd_say("Everyone died. GG")
                return

    def reset(self):
        self.context = []

    def _append_context(self, line):
        self.context.append(line)
        return
        eprint("context:")
        for l in self.context:
            eprint("    ", l)
        eprint()

    def _build_prompt(self):
        # return "\n".join(self.context)
        return "\n".join(self.conversation[-15:]) + "\n" + "\n".join(self.context)

    def _parse_args(self, args_str):
        if not args_str.strip():
            return []

        for player_name in self.players:
            f = f"{player_name}, "
            if args_str.startswith(f):
                # eprint(f"Skipping '{f}' in args_str")
                args_str = args_str[len(f):]

        args = []
        in_quotes = False
        current_arg = []
        quote_char = None

        for char in args_str:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current_arg.append(char)
            elif char == quote_char and in_quotes:
                in_quotes = False
                current_arg.append(char)
            elif char == ',' and not in_quotes:
                arg_str = ''.join(current_arg).strip()
                if arg_str:
                    args.append(arg_str)
                current_arg = []
            else:
                current_arg.append(char)

        if current_arg:
            arg_str = ''.join(current_arg).strip()
            args.append(arg_str)

        parsed_args = []
        for arg in args:
            if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                parsed_args.append(arg[1:-1])
            else:
                try:
                    if '.' in arg:
                        parsed_args.append(float(arg))
                    else:
                        parsed_args.append(int(arg))
                except ValueError:
                    parsed_args.append(arg)

        return parsed_args

    def handle_line(self, line: str):
        # eprint("handle_line", line)
        
        # if not line.strip().startswith("AIDM:"):
        #     return

        # eprint("handle_line_fr", line)

        commands = re.findall(r'(\w+)\((.*?)\)', line)
        for cmd, args_str in commands:
            args = self._parse_args(args_str)
            handler = getattr(self, f'cmd_{cmd}', None)
            if handler:
                handler(*args)
                self.got_a_response = True
            else:
                eprint(f"[AIDM] Unknown command: {cmd}({args})")

    def handle_player_prompt(self, player_name: str, prompt: str):
        self.last_player_prompted = player_name
        self.got_a_response = False

        self.reset()
        self._append_context(f"{player_name}: {prompt}")
        
        while True:
            prompt_data = self._build_prompt()
            self.server_intervened = False

            try:
                for line in self.ollama.generate(prompt_data):
                    self._append_context(line)
                    self.handle_line(line)

                    if re.search(r'(inventory|room|modify_stat)\(".*?"\)', line.strip()):
                        self.ollama.stop()
                        self.server_intervened = True
                        break

                    if re.search(r'^(continue)\(".*?"\)', line.strip()):
                        return True

                if not self.got_a_response:
                    eprint("no response from AI - probably failed to parse it, retrying...")
                    return self.handle_player_prompt(player_name, prompt)

            except Exception:
                eprint(f"[AIDM] Error: {traceback.format_exc()}")
                eprint("retrying...")
                return self.handle_player_prompt(player_name, prompt)

            if not self.server_intervened:
                break

        return False

    def print_sayer(self, name):
        h = hash(name)
        (h, r) = divmod(h, 128)
        (h, g) = divmod(h, 128)
        (h, b) = divmod(h, 128)
        print(f"\033[1m\033[38;2;{127+r};{127+g};{127+b}m{name}\033[0m: ", end = "")

    # ---------------------
    # Command Implementations
    # ---------------------

    def cmd_say_as(self, name, text):
        self.print_sayer(name)
        print(text)

    def cmd_say(self, text):
        self.cmd_say_as("AIDM", text)

    def cmd_room(self, player_name):
        room = self.dungeon.get_room(self.players[player_name].position)
        response = f"{player_name} is currently in a room called '{room.name}'. "

        if room.connections:
            exits = [f"'{destination.name}' to the {direction}" for direction, destination in room.connections.items()]
            response += "Exits are: " + ", ".join(exits) + ". "
        else:
            response += "There are no visible exits. "

        if room.enemies:
            enemies = ', '.join(f"{e.name} at {e.hp}HP" for e in room.enemies)
            response += f"Enemies in the room: {enemies}. "
        else:
            response += "There are no enemies here. "

        if room.npcs:
            npcs = ', '.join(n.name for n in room.npcs)
            response += f"NPCs present: {npcs}. "
        else:
            response += "You see no NPCs around. "

        if room.loot:
            loot = ', '.join(f"{item.amount}x '{item.name}'" for item in room.loot)
            response += f"Loot on the ground: {loot}."
        else:
            response += "There is no loot here."

        self._append_context(f'Server: {response}')

    def cmd_inventory(self, player_name):
        inventory = self.players[player_name].inventory
        response = f"{player_name} has {", ".join([f"{inventory[item]}x '{item}'" for item in inventory]) or "nothing on them"}"
        self._append_context(f'Server: {response}')

    def cmd_continue(self):
        return
        eprint("[Continue] No effect or invalid action.")

    def cmd_set_stat(self, entity_name, stat, value):
        entity = None
        if entity_name in self.players:
            entity = self.players[entity_name]
        else:
            room = self.dungeon.get_room(self.players[self.last_player_prompted].position)
            if entity_name in room.npcs:
                entity = room.npcs[entity_name]
            elif entity_name in room.enemies:
                entity = room.enemies[entity_name]
            else:
                print("Skibidi toilet :c")
        setattr(entity, stat, value)

    def cmd_modify_stat(self, entity_name, stat, diff):
        entity = None
        if entity_name in self.players:
            entity = self.players[entity_name]
        else:
            room = self.dungeon.get_room(self.players[self.last_player_prompted].position)
            if entity_name in room.npcs:
                entity = room.npcs[entity_name]
            elif entity_name in room.enemies:
                entity = room.enemies[entity_name]
            else:
                print("Skibidi toilet :c")
        setattr(entity, stat, getattr(entity, stat) + diff)
        self._append_context(f'Server: {entity_name}.{stat} = {getattr(entity, stat)}')

    def cmd_give(self, player_name, item, amount):
        player = self.players[player_name]
        player.inventory.setdefault(item, 0)
        player.inventory[item] += amount

    def cmd_take(self, player_name, item, amount):
        player = self.players[player_name]
        player.inventory.setdefault(item, 0)
        player.inventory[item] -= amount

    def cmd_pickup(self, player_name, item, amount = 1):
        player = self.players[player_name]

        room = self.dungeon.get_room(player.position)
        for l in room.loot:
            if l.name == item:
                l.amount -= amount
                if l.amount == 0:
                    room.loot.remove(l)
                    break
                elif l.amount < 0:
                    raise ValueError(f"Picked up {amount} of {item} and there is now {l.amount} of it")

        player.inventory.setdefault(item, 0)
        player.inventory[item] += amount

    def cmd_move(self, player_name, direction):
        player = self.players[player_name]
        
        dirs = dict()
        dirs["north"] = (0, 0,  1)
        dirs["south"] = (0, 0, -1)
        dirs["east"] =  ( 1, 0, 0)
        dirs["west"] =  (-1, 0, 0)
        dirs["up"] =    ( 1, 0, 0)
        dirs["down"] =  (-1, 0, 0)

        (dx, dy, dz) = dirs[direction]

        player.position = (
            player.position[0] + dx,
            player.position[1] + dy,
            player.position[2] + dz
        )