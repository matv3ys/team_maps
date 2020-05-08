import os
import sys
from copy import deepcopy

import pygame
import requests
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget


class MyWidget(QWidget):
    def __init__(self, type):
        global toponym_index

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
        self.pushButton_search.clicked.connect(self.search)
        self.pushButton_reset.clicked.connect(self.reset)
        if toponym_index:
            self.radioButton_index.setChecked(True)
        self.radioButton_index.toggled.connect(self.index)
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
        get_coordinates(self.lineEdit.text())
        map_center_coord = deepcopy(point_coord)
        flagNeeded = True
        self.close()

    def reset(self):
        global flagNeeded, toponym

        flagNeeded = False
        toponym = None
        self.close()

    def index(self):
        global toponym_index

        if self.radioButton_index.isChecked():
            toponym_index = True
        else:
            toponym_index = False


def draw_map():
    global map_file, isChanged, flagNeeded, toponym_index, toponym

    api_server = "http://static-maps.yandex.ru/1.x/"

    coords = ','.join(map(str, map_center_coord))

    params = {'ll': coords,
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
    if toponym:
        address = toponym['metaDataProperty']['GeocoderMetaData']['text']
        if toponym_index:

            try:
                index = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
            except KeyError:
                index = 'отсутствует'

            address += f'   Индекс: {index}'

        screen.fill(pygame.Color('red'), pygame.Rect(0, 0, 600, 50))
        font = pygame.font.Font(None, 20)
        text = font.render(address, 1, (255, 255, 255))
        screen.blit(text, (15, 10))
    isChanged = False


def search_toponym(position):
    global z, point_coord, map_center_coord, flagNeeded

    step_y = 181.65 / 2 ** (z - 1)
    step_x = 416.26 / 2 ** (z - 1)

    x, y = position
    xt, yt = point_coord[0] - (300 - x) * step_x / 600, point_coord[1] + (225 - y) * step_y / 450

    text = ','.join(list(map(str, [xt, yt])))

    get_coordinates(text)
    map_center_coord = deepcopy(point_coord)
    flagNeeded = True
    isChanged = True


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


def get_ll_spn(toponym):
    lclon, lclat = toponym['boundedBy']['Envelope']['lowerCorner'].split()
    uclon, uclat = toponym['boundedBy']['Envelope']['upperCorner'].split()
    lclon, lclat = float(lclon), float(lclat)
    uclon, uclat = float(uclon), float(uclat)
    d_lon = uclon - lclon
    d_lat = uclat - lclat
    if d_lon > d_lat:
        spn = f'{d_lon},{d_lon}'
    else:
        spn = f'{d_lat},{d_lat}'
    ll = ','.join(toponym['Point']['pos'].split())
    return ll, spn


def get_coordinates(text):
    global point_coord, isChanged, toponym

    geocoder_url = "http://geocode-maps.yandex.ru/1.x/"
    response = requests.get(geocoder_url, params={
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": text
    })

    if not response:
        return

    if response.json()['response']["GeoObjectCollection"][
        'metaDataProperty']['GeocoderResponseMetaData'][
        'found'] == '0':
        return

    toponym = response.json()["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]

    ll, spn = get_ll_spn(toponym)
    point_coord = list(map(float, ll.split(',')))


point_coord = [56.229420, 58.010577]
map_center_coord = [56.229420, 58.010577]
z = 10
type = 'sat'
pygame.init()
isChanged = True
flagNeeded = False
toponym = None
toponym_index = False
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

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                search_toponym(event.pos)
                isChanged = True

    if isChanged:
        draw_map()
    pygame.display.flip()
