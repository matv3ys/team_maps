import os
import sys
from copy import deepcopy

import pygame
import requests
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget


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
        self.pushButton.clicked.connect(self.search)
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

    def search(self):
        global point_coord, flagNeeded, map_center_coord
        point_coord = get_pharmacy_coordinates(self.lineEdit.text(), map_center_coord)
        map_center_coord = deepcopy(point_coord)
        flagNeeded = True
        self.close()


def draw_map():
    global map_file, isChanged

    api_server = "http://static-maps.yandex.ru/1.x/"
    params = {'ll': ','.join(map(str, map_center_coord)),
              'z': z,
              'l': type}

    if flagNeeded:
        params['pt'] = f'{",".join(map(str, point_coord))},pm2bll'

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
    isChanged = False


def open_settings():
    global isChanged, type
    app = QApplication(sys.argv)
    ex = MyWidget(type)
    app.exec_()
    del ex
    isChanged = True


def get_adjacency_from_z():
    n = 0.001
    for _ in range(17 - z):
        n *= 1.7084507042253522
    return n


def get_pharmacy_coordinates(text, coodrs):
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "0e9e3c8a-0504-4663-ba95-2c1ebb146bd4"

    address_ll = ','.join(map(str, coodrs))

    search_params = {
        "apikey": api_key,
        "text": text,
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz"
    }

    response = requests.get(search_api_server, params=search_params)

    json_response = response.json()

    if 'features' not in json_response or not bool(json_response["features"]):
        return coodrs

    organization = json_response["features"][0]

    point = organization["geometry"]["coordinates"]
    return point


point_coord = [56.229420, 58.010577]
map_center_coord = [56.229420, 58.010577]
z = 10
type = 'sat'
pygame.init()
isChanged = True
flagNeeded = False
pygame.key.set_repeat(70, 70)
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
                isChanged = True
            if event.key == pygame.K_PAGEUP:
                z += 1
                if z > 17:
                    z = 17
                isChanged = True

            if event.key == 273:
                if map_center_coord[0] + get_adjacency_from_z() < 90:
                    map_center_coord[1] += get_adjacency_from_z()
                isChanged = True
            if event.key == 274:
                if map_center_coord[0] + get_adjacency_from_z() > 0:
                    map_center_coord[1] -= get_adjacency_from_z()
                isChanged = True
            if event.key == 275:
                if map_center_coord[0] + get_adjacency_from_z() < 180:
                    map_center_coord[0] += get_adjacency_from_z()
                isChanged = True
            if event.key == 276:
                if map_center_coord[0] - get_adjacency_from_z() > 0:
                    map_center_coord[0] -= get_adjacency_from_z()
                isChanged = True
            if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                open_settings()

    if isChanged:
        draw_map()
    pygame.display.flip()
