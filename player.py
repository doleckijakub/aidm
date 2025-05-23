import json
import random

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
        self.name = random.choice([
            "Zilun",
            "Rehlu"
            "Rhusan",
            "Neiho",
            "Brirver",
            "Havengloom",
            "Mangark",
            "Longkiller",
            "Midren",
            "Butsk",
            "Fir",
            "Valursk",
            "Gognon",
            "Stillmark",
            "Mar",
            "Peacetrack",
            "Lezuezath",
            "Vizeltuek",
            "Kem",
            "Zah",
            "Sunkhim",
            "Zilmolder",
            "Tradzatrentu",
            "Mauzac",
            "Vemoro",
            "Tim",
            "Kiam",
            "Zuw",
            "Pu",
            "Crieleres",
            "Rildocis",
            "Vorfer",
            "Dedristu",
        ])

        self.race = "Elf"
        self.class_ = "Mage"

        # self.name = input("Name > ")
        
        # print("Races: " + ", ".join(RACES))
        # self.race = None
        # while not self.race in RACES:
        #     self.race = input("Race > ")

        # print("Classes: " + ", ".join(CLASSES))
        # self.class_ = None
        # while not self.class_ in CLASSES:
        #     self.class_ = input("Class > ")
        
        self.position = (0, 0, 0)
        self.hp = 100
        self.inventory = dict()

    def desc(self):
        return f"{self.name}, a {self.race} {self.class_}"