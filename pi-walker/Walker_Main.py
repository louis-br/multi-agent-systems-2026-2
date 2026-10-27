import sys
from threading import Thread

from maspy import *

from Map_Env import Map
from Walker_Ag import Walker
from Equipe_Ag import Coordenador, Memoria, Juiz

PADRAO = ((10, 10), 0.2, 4, (10, 50))


def criar_sistema(map_size, walls_perc, num_walkers, valores):
    map = Map(map_size, walls_perc, valores)
    Memoria("Memoria")
    Juiz("Juiz", map)
    coordenador = Coordenador("Coordenador", map)
    for _ in range(num_walkers):
        Walker("Walker", map)
    coordenador.add(Goal("iniciar"))
    return map


if __name__ == '__main__':
    Admin(listener_log=True)
    Channel().show_exec = True

    if "--sem-gui" in sys.argv:
        criar_sistema(*PADRAO)
        Admin().slow_cycle_by(0.02)
        Admin().start_system()
    else:
        from Pygame_Screens import MapVisualizer, MenuScreen
        settings = MenuScreen().loop()
        if settings:
            map = criar_sistema(*settings)
            Admin().slow_cycle_by(0.2)
            Thread(target=Admin().start_system, daemon=True).start()
            MapVisualizer(map).loop()
