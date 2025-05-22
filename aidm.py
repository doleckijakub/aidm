import re
import requests
import json
import sys
import time
import traceback

from player import Player
from ollama import Ollama

def eprint(*args, **kwargs):
    # return
    print("\033[3m", end="", file=sys.stderr)
    print(*args, file=sys.stderr, **kwargs)
    print("\033[0m", end="", file=sys.stderr)

MAX_HISTORY_LENGTH = 10 # TODO

class AIDM:
    def __init__(self, party, dungeon):
        self.ollama = Ollama("dungeon-master")
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
                    r = self.handle_player_prompt(player_name, prompt)

    def reset(self):
        self.context = []

    def _append_context(self, line):
        self.context.append(line)
        return
        eprint("_append_context")
        for l in self.context:
            eprint("    ", l)
        eprint()

    def _build_prompt(self):
        return "\n".join(self.context)

    def _parse_args(self, args_str):
        if not args_str.strip():
            return []

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
        
        if not line.strip().startswith("AIDM:"):
            return

        # eprint("handle_line_fr", line)

        commands = re.findall(r'(\w+)\((.*?)\)', line)
        for cmd, args_str in commands:
            args = self._parse_args(args_str)
            handler = getattr(self, f'cmd_{cmd}', None)
            if handler:
                handler(*args)
            else:
                eprint(f"[AIDM] Unknown command: {cmd}({args})")

    def handle_player_prompt(self, player_name: str, prompt: str):
        self.reset()
        self._append_context(f"{player_name}: {prompt}")
        
        while True:
            prompt_data = self._build_prompt()
            self.server_intervened = False

            try:
                for line in self.ollama.generate(prompt_data):
                    self._append_context(line)
                    self.handle_line(line)

                    if re.search(r'(inventory|room)\(".*?"\)', line.strip()):
                        # eprint("!!! self.ollama.stop()")
                        self.ollama.stop()
                        self.server_intervened = True
                        break

                    if re.search(r'^(continue)\(".*?"\)', line.strip()):
                        return True

                    if line.strip().endswith("___"):
                        return False

            except Exception:
                eprint(f"[AIDM] Error: {traceback.format_exc()}")
                return False

            if not self.server_intervened:
                break

        return False


    # ---------------------
    # Command Implementations
    # ---------------------

    def print_sayer(self, name):
        h = hash(name)
        (h, r) = divmod(h, 128)
        (h, g) = divmod(h, 128)
        (h, b) = divmod(h, 128)
        print(f"\033[1m\033[38;2;{127+r};{127+g};{127+b}m{name}\033[0m: ", end = "")

    def cmd_say_as(self, name, text):
        self.print_sayer(name)
        print(text)

    def cmd_say(self, text):
        self.cmd_say_as("AIDM", text)

    def cmd_room(self, player_name):
        room_data = self.dungeon.get_room(self.players[player_name].position)
        eprint("room_data = ", room_data)
        response = room_data.json()
        self._append_context(f'Server: {response}')

    def cmd_inventory(self, player_name):
        inventory = self.players[player_name].inventory
        response = json.dumps(inventory)
        self._append_context(f'Server: {response}')

    def cmd_continue(self):
        return
        eprint("[Continue] No effect or invalid action.")

    def cmd_set_stat(self, entity, stat, value):
        print("TODO")
        eprint(f"[Stat Set] {entity}.{stat} = {value}")

    def cmd_modify_stat(self, entity, stat, diff):
        print("TODO")
        eprint(f"[Stat Modified] {entity}.{stat} += {diff} → {result}")

    def cmd_give(self, player_name, item, amount):
        player = self.players[player_name]
        player.inventory.setdefault(item, 0)
        player.inventory[item] += amount

    def cmd_take(self, player_name, item, amount):
        player = self.players[player_name]
        player.inventory.setdefault(item, 0)
        player.inventory[item] -= amount

    def cmd_equip(self, player_name, item):
        player = self.players[player_name]
        print("TODO")

    def cmd_pickup(self, player_name, item):
        player = self.players[player_name]
        player.inventory.setdefault(item, 0)
        player.inventory[item] += 1

        room = self.dungeon.get_room(player.position)
        room.loot.remove(item)

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


# class AIDM:
#     def __init__(self, party, dungeon):
#         self.ollama = Ollama("dungeon-master")
#         self.conversation = []
        
#         self.party = party
#         self.players = dict()
#         for player in party.players:
#             self.players[player.name] = player
#         self.dungeon = dungeon

#     def _parse_args(self, args_str):
#         if not args_str.strip():
#             return []
        
#         args = []
#         in_quotes = False
#         current_arg = []
#         quote_char = None
        
#         for char in args_str:
#             if char in ('"', "'") and not in_quotes:
#                 in_quotes = True
#                 quote_char = char
#                 current_arg.append(char)
#             elif char == quote_char and in_quotes:
#                 in_quotes = False
#                 current_arg.append(char)
#             elif char == ',' and not in_quotes:
#                 arg_str = ''.join(current_arg).strip()
#                 if arg_str:
#                     args.append(arg_str)
#                 current_arg = []
#             else:
#                 current_arg.append(char)
        
#         if current_arg:
#             arg_str = ''.join(current_arg).strip()
#             args.append(arg_str)
        
#         parsed_args = []
#         for arg in args:
#             if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
#                 parsed_args.append(arg[1:-1])
#             else:
#                 try:
#                     if '.' in arg:
#                         parsed_args.append(float(arg))
#                     else:
#                         parsed_args.append(int(arg))
#                 except ValueError:
#                     parsed_args.append(arg)
        
#         return parsed_args

#     def handle_line(self, line: str):
#         eprint("handle_line ", line)

#         commands = re.findall(r'(\w+)\((.*?)\)', line)

#         for cmd_name, args_str in commands:
#             cmd_name = cmd_name.lower()
#             handler = getattr(self, f"cmd_{cmd_name}", None)
#             if not handler:
#                 raise Exception(f"Unknown command: {cmd_name}")
#                 continue

#             args = self._parse_args(args_str)
#             try:
#                 eprint(f"Calling {cmd_name} with {args_str} = ", *args)
#                 handler(*args)
#             except Exception as e:
#                 eprint(f"Error in {cmd_name}: {e}")

#     def handle_player_prompt(self, player: Player, prompt: str):
#         self.to_be_continued = False
#         self.conversation = [f"{player.name}: {prompt}"]

#         while True:
#             lines = self.ollama.generate("\n".join(self.conversation))

#             should_restart = False

#             for line in lines:
#                 line = line.strip()
#                 if not line:
#                     continue

#                 if re.match(r'^(?!AIDM:)[^:]+:$', line):
#                     ollama.stop()
#                 else:
#                     if line.startswith("AIDM:"):
#                         line = line[5:]
#                     line = line.strip()

#                     self.conversation.append("AIDM: " + line)
#                     self.handle_line(line)

#                     if self.to_be_continued:
#                         return True

#                     should_restart = True
#                     break

#             if not should_restart:
#                 break
        
#         for line in self.conversation:
#             eprint(line)
        
#         return False

#     def run(self):
#         while True:
#             for player_name in self.players:
#                 # self.describe_location(player.position)

#                 r = True
#                 while r:
#                     self.print_sayer(player_name)
#                     prompt = input()
#                     r = self.handle_player_prompt(self.players.get(player_name), prompt)

#     # === Command implementations ===

#     def print_sayer(self, name):
#         h = hash(name)
#         (h, r) = divmod(h, 128)
#         (h, g) = divmod(h, 128)
#         (h, b) = divmod(h, 128)
#         print(f"\033[1m\033[38;2;{127+r};{127+g};{127+b}m{name}\033[0m: ", end = "")

#     def cmd_say_as(self, name, text):
#         self.print_sayer(name)
#         print(f"\033[38;2;{r};{g};{b}m{name}\033[0m: {text}")

#     def cmd_say(self, text):
#         self.cmd_say_as("AIDM", text)

#     def cmd_room(self, name):
#         pass

#     def cmd_give(self, player_name, item, amount):
#         p = self.players.get(player_name)
#         if not p:
#             raise Exception(f"Player {player_name} not found")
#         p.inventory.setdefault(item, 0)
#         p.inventory[item] += amount
#         eprint(f"{player_name} received {amount}x {item}")

#     def cmd_take(self, player_name, item, amount):
#         p = self.players.get(player_name)
#         if not p:
#             raise Exception(f"Player {player_name} not found")
#         inv = p.inventory.get("misc", {})
#         current_amount = inv.get(item, 0)
#         if current_amount >= amount:
#             inv[item] -= amount
#             eprint(f"{player_name} lost {amount}x {item}")
#         else:
#             eprint(f"{player_name} does not have enough {item}")

#     def cmd_inventory(self, player_name):
#         p = self.players.get(player_name)
#         if not p:
#             raise Exception(f"Player {player_name} not found")
#         inv_json = json.dumps(p.inventory)
#         self.conversation.append(f"{player_name}'s inventory: {inv_json}")

#     def cmd_damage(self, player_name, amount):
#         p = self.players.get(player_name)
#         if not p:
#             raise Exception(f"Player {player_name} not found")
#         p.hp -= amount
#         if p.hp <= 0:
#             p.die()
#         else:
#             eprint(f"{player_name} took {amount} damage. HP now {p.hp}")

#     def cmd_heal(self, player_name, amount):
#         p = self.players.get(player_name)
#         if not p:
#             raise Exception(f"Player {player_name} not found")
#         p.hp += amount
#         eprint(f"{player_name} healed {amount} HP. HP now {p.hp}")

#     def cmd_continue(self):
#         eprint("[continue]")
#         self.to_be_continued = True
