"""
    Escena de prueba: solo el OVNI.
    El ovni patrulla, flota, gira sobre su eje y se inclina hacia donde avanza.
    Tecla L: prender / apagar el rayo.
    Reutiliza la cámara y el algoritmo del pintor de main.py.
"""
import pygame

from OpMat import OpMat3D
from Malla import Malla
from Ovni import Ovni
from main import Camara, dibujar_caras, ANCHO, ALTO, FPS, FONDO, COLOR_OVNI, COLOR_SUELO

LIMITE_OVNI = 5.0      # el ovni patrulla en [-LIMITE_OVNI, LIMITE_OVNI]


def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ovni")
    reloj = pygame.time.Clock()

    # Cámara apuntando a la altura del ovni
    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 8.0, 16.0),
        objetivo=(0.0, 4.5, 0.0)
    )
    opMat = OpMat3D()

    suelo = Malla.rejilla(8.0, 2.0, 0.0, COLOR_SUELO)
    ovni = Ovni(COLOR_OVNI, posicion=(0.0, 6.5, 0.0), limite=LIMITE_OVNI)

    ejecutando = True
    while ejecutando:
        delta_time = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_l:
                ovni.alternar_luz()        # L: prender / apagar el rayo

        # --- 1. Actualizar ---
        ovni.update(delta_time)

        # --- 2. Fondo ---
        pantalla.fill(FONDO)

        # --- 3. Renderizar ---
        opMat.loadId()
        suelo.render(pantalla, camara, opMat)

        caras = []
        ovni.render(camara, opMat, caras)
        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(f"Ovni  |  {reloj.get_fps():.0f} FPS")

        # --- 4. Mostrar frame ---
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
