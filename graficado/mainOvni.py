import pygame

from OpMat import OpMat3D
from Malla import Malla
from Ovni import Ovni
from main import Camara, dibujar_caras, ANCHO, ALTO, FPS, FONDO, COLOR_OVNI, COLOR_SUELO

LIMITE_OVNI = 5.0  # Límite del recorrido del ovni


def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ovni")
    reloj = pygame.time.Clock()

    # Configuración de la cámara
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
                ovni.alternar_luz()  # L: activar o desactivar el rayo

        # Actualiza el movimiento del ovni
        ovni.update(delta_time)

        pantalla.fill(FONDO)

        # Dibuja el suelo y el ovni
        opMat.loadId()
        suelo.render(pantalla, camara, opMat)

        caras = []
        ovni.render(camara, opMat, caras)
        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(f"Ovni  |  {reloj.get_fps():.0f} FPS")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()