import pygame as pg
import os
import json
import random
import time
import numpy as np
import shutil
import sys
import configparser as inicp
import ctypes
from tkinter import messagebox
import pgmore as pgm

class Main:
    def __init__(self):
        self.system = pgm.System()
        self.system.GetAdmin()
        pg.init()
        self.load_data()
        self.screen = pg.display.set_mode((self.bg_config['screen'][0], self.bg_config['screen'][1]))
        self.clock = pg.time.Clock()
        self.running = True

    def load_data(self):
        self.bg_config = json.load(open("config/bg.json", "r"))
    
    def quit(self):
        pg.quit()
        sys.exit()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

    def update(self):
        # Update game logic here
        pass

    def lang(self, key):
        return self.lang_data[key]

    def draw(self):
        self.screen.fill((0, 0, 0))  # Clear the screen with black
        # Draw game elements here
        pg.display.flip()  # Update the display

if __name__ == '__main__':
    main = Main()