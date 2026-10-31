import pygame

from OpMat import OpMat3D
from Malla import Malla
from Vaca import Vaca
from main import Camara, dibujar_caras, ANCHO, ALTO, FPS, FONDO, COLOR_VACA, COLOR_SUELO

# Posiciones iniciales de las vacas (x, y, z)
POSICIONES = [(-4.0, 0.0, 0.0), (0.0, 0.0, 2.5), (4.0, 0.0, -1.0)]


def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Vacas")
    reloj = pygame.time.Clock()

    # Configuración de la cámara
    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 4.0, 14.0),
        objetivo=(0.0, 2.5, 0.0)
    )
    opMat = OpMat3D()

    suelo = Malla.rejilla(8.0, 2.0, 0.0, COLOR_SUELO)
    vacas = [Vaca(COLOR_VACA, posicion=p) for p in POSICIONES]

    ejecutando = True
    while ejecutando:
        delta_time = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                ejecutando = False

        # Actualiza el movimiento de las vacas
        for vaca in vacas:
            vaca.update(delta_time)

        pantalla.fill(FONDO)

        # Dibuja el suelo y las vacas
        opMat.loadId()
        suelo.render(pantalla, camara, opMat)

        caras = []
        for vaca in vacas:
            vaca.render(camara, opMat, caras)
        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(f"Vacas  |  {reloj.get_fps():.0f} FPS")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()