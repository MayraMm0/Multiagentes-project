import random
import pygame

from OpMat import OpMat3D
from Camara import Camara
from Malla import Malla
from Ovni import Ovni
from Vaca import Vaca
from Bresenham import rellenar_poligono, rellenar_poligono_alpha, dibujar_segmento_2d

ANCHO, ALTO = 900, 600
FPS = 60

FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)
COLOR_VACA = (60, 45, 60)
COLOR_SUELO = (45, 40, 110)

LIMITE = 8.0  # el campo va de -LIMITE a +LIMITE en X y Z


def dibujar_caras(superficie, caras):
    """
    Algoritmo del pintor:
    1. Ordena TODAS las caras de la escena de la más lejana a la más cercana.
    2. Rellena cada cara (scanline) y dibuja su borde justo después,
       para que las caras de enfrente tapen también los bordes de atrás.
    """
    caras.sort(key=lambda cara: cara[0], reverse=True)

    # Bloquear la superficie una vez: set_at ya no la bloquea en cada píxel
    superficie.lock()
    for _, puntos, relleno, borde in caras:
        if len(relleno) == 4:
            # Cara translúcida (r, g, b, alpha): blit necesita la superficie
            # desbloqueada. Se mezcla con lo que ya está dibujado detrás.
            superficie.unlock()
            rellenar_poligono_alpha(superficie, puntos, relleno)
            superficie.lock()
        else:
            rellenar_poligono(superficie, puntos, relleno)

        if borde is not None:
            n = len(puntos)
            for i in range(n):
                dibujar_segmento_2d(superficie, puntos[i], puntos[(i + 1) % n], borde)
    superficie.unlock()


def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ovni y vaca - modelado 3D con Bresenham")
    reloj = pygame.time.Clock()

    # Objetos principales
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
        Vaca(COLOR_VACA, posicion=(random.uniform(-5, 5), 0.0, random.uniform(-5, 5)),
             limite=LIMITE)
        for _ in range(3)
    ]

    ejecutando = True
    while ejecutando:
        # Tiempo transcurrido desde el frame anterior, en segundos
        delta_time = reloj.tick(FPS) / 1000.0

        # procesar eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_l:
                ovni.alternar_luz()  # L: prender / apagar el rayo

        # --- 1. Actualizar agentes ---
        ovni.update(delta_time)
        for vaca in vacas:
            vaca.update(delta_time)

        # --- 2. Fondo ---
        pantalla.fill(FONDO)

        # --- 3. Renderizar ---
        opMat.loadId()  # matriz de la escena (identidad)

        # El suelo es de alambre y siempre queda abajo: se dibuja primero
        suelo.render(pantalla, camara, opMat)

        # Cada objeto hace push -> sus transformaciones -> recolecta -> pop
        caras = []
        for vaca in vacas:
            vaca.render(camara, opMat, caras)
        ovni.render(camara, opMat, caras)

        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(
            f"Ovni y vaca - modelado 3D con Bresenham  |  {reloj.get_fps():.0f} FPS"
        )

        # --- 4. Mostrar frame ---
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()