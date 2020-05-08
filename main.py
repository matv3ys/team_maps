import os
import sys

import pygame
import requests

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget

from PyQt5 import QtCore, QtGui, QtWidgets


class MyWidget(QWidget):
    def __init__(self, type):
        super().__init__()
        uic.loadUi('widget.ui', self)
        self.types = ['схема', "спутник", "гибрид"]
        if type == 'map':
            i = 0
        elif type == 'sat':
            i = 1
        else:
            i = 2
        self.comboBox.setCurrentIndex(i)
        self.comboBox.activated[str].connect(self.choice)
        self.show()

    def choice(self, text):
        global type
        index = self.types.index(text)
        if index == 0:
            self.comboBox.setCurrentIndex(0)
            type = 'map'
        if index == 1:
            self.comboBox.setCurrentIndex(1)
            type = 'sat'
        if index == 2:
            self.comboBox.setCurrentIndex(2)
            type = 'sat,skl'
        self.close()


def draw_map():
    global map_file, change

    api_server = "http://static-maps.yandex.ru/1.x/"
    params = {'ll': ','.join(map(str, coord)),
              'z': z,
              'l': type}

    response = requests.get(api_server, params=params)

    if not response:
        print("Ошибка выполнения запроса:")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)

    map_file = "map.png"
    with open(map_file, "wb") as file:
        file.write(response.content)
    screen = pygame.display.set_mode((600, 450))
    screen.blit(pygame.image.load(map_file), (0, 0))
    change = False


def open_settings():
    global change, type
    app = QApplication(sys.argv)
    ex = MyWidget(type)
    app.exec_()
    del ex
    change = True


coord = [56.229420, 58.010577]
z = 10
type = 'sat'
pygame.init()
change = True
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            os.remove(map_file)
            sys.exit(0)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PAGEDOWN:
                z -= 1
                if z < 0:
                    z = 1
                change = True
            if event.key == pygame.K_PAGEUP:
                z += 1
                if z > 17:
                    z = 17
                change = True
            if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                open_settings()
    if change:
        draw_map()
    pygame.display.flip()
