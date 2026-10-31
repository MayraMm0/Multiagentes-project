import random
import pygame

from OpMat import OpMat3D
from Camara import Camara
from Malla import Malla
from Ovni import Ovni
from Vaca import Vaca
from Bresenham import rellenar_poligono, rellenar_poligono_alpha, dibujar_segmento_2d

# Configuración de la ventana
ANCHO, ALTO = 900, 600
FPS = 60

FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)       # Color de los bordes del ovni
COLOR_VACA = (60, 45, 60)       # Color de los bordes de las vacas
COLOR_SUELO = (45, 40, 110)

LIMITE = 8.0  # Límites del campo en X y Z


def dibujar_caras(superficie, caras):
    # Ordena las caras según su profundidad
    caras.sort(key=lambda cara: cara[0], reverse=True)

    superficie.lock()
    for _, puntos, relleno, borde in caras:
        if len(relleno) == 4:
            # Desbloquea la superficie para dibujar con transparencia
            superficie.unlock()
            rellenar_poligono_alpha(superficie, puntos, relleno)
            superficie.lock()
        else:
            rellenar_poligono(superficie, puntos, relleno)

        if borde is not None:
            n = len(puntos)
            for i in range(n):
                dibujar_segmento_2d(
                    superficie, puntos[i], puntos[(i + 1) % n], borde
                )
    superficie.unlock()


def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ovni y vaca - modelado 3D con Bresenham")
    reloj = pygame.time.Clock()

    # Configuración de la cámara
    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 5.5, 17.0),
        objetivo=(0.0, 3.0, 0.0)
    )

    opMat = OpMat3D()
    suelo = Malla.rejilla(LIMITE + 2, 2.0, 0.0, COLOR_SUELO)
    ovni = Ovni(COLOR_OVNI, posicion=(0.0, 6.5, 0.0), limite=LIMITE)
    vacas = [
        Vaca(
            COLOR_VACA,
            posicion=(random.uniform(-5, 5), 0.0, random.uniform(-5, 5)),
            limite=LIMITE
        )
        for _ in range(3)
    ]

    ejecutando = True
    while ejecutando:
        delta_time = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_l:
                ovni.alternar_luz()  # L: activar o desactivar el rayo

        # Actualiza el movimiento de los objetos
        ovni.update(delta_time)
        for vaca in vacas:
            vaca.update(delta_time)

        pantalla.fill(FONDO)
        opMat.loadId()

        # Dibuja primero el suelo
        suelo.render(pantalla, camara, opMat)

        # Reúne las caras para dibujarlas según su profundidad
        caras = []
        for vaca in vacas:
            vaca.render(camara, opMat, caras)
        ovni.render(camara, opMat, caras)

        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(
            f"Ovni y vaca - modelado 3D con Bresenham  |  {reloj.get_fps():.0f} FPS"
        )
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()