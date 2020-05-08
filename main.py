import os
import sys

import pygame
import requests


def draw_map():
    global map_file, change

    api_server = "http://static-maps.yandex.ru/1.x/"
    params = {'ll': ','.join(map(str, coord)),
              'z': z,
              'l': 'map'}

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


coord = [56.229420, 58.010577]
z = 10
pygame.init()
change = True
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            os.remove(map_file)
            sys.exit(0)
    if change:
        draw_map()
    pygame.display.flip()