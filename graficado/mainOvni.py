
import pygame

from OpMat import OpMat3D
from Malla import Malla
from Ovni import Ovni
from Camara import Camara
from Pintor import dibujar_caras

# Configuración de la ventana
ANCHO, ALTO = 900, 600
FPS = 60

FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)       # bordes del ovni
COLOR_SUELO = (45, 40, 110)

LIMITE = 8.0                    # el campo va de -LIMITE a +LIMITE en X y Z

# Ovnis: (posición inicial (x, y, z), escala)
# Cada uno a una altura distinta para que no se atraviesen entre sí.
OVNIS = [
    ((-5.0, 6.5, -3.0), 0.8),
    (( 5.0, 7.5, -1.0), 0.7),
    (( 0.0, 8.5, -6.0), 0.6),
    ((-3.0, 9.5,  2.0), 0.5),
    (( 3.0, 10.5, 3.0), 0.5),
]
SEGMENTOS = 20                  # menos detalle por ovni = más FPS


def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ovnis")
    reloj = pygame.time.Clock()

    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 7.0, 20.0),
        objetivo=(0.0, 5.0, 0.0)
    )
    opMat = OpMat3D()

    suelo = Malla.rejilla(LIMITE + 2, 2.0, 0.0, COLOR_SUELO)
    ovnis = [
        Ovni(COLOR_OVNI, posicion=posicion, escala=escala,
             limite=LIMITE, segmentos=SEGMENTOS)
        for posicion, escala in OVNIS
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
                for ovni in ovnis:
                    ovni.alternar_luz()

        # --- 1. Actualizar ---
        for ovni in ovnis:
            ovni.update(delta_time)

        # --- 2. Fondo ---
        pantalla.fill(FONDO)

        # --- 3. Renderizar ---
        opMat.loadId()
        suelo.render(pantalla, camara, opMat)

        caras = []
        for ovni in ovnis:
            ovni.render(camara, opMat, caras)
        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(f"Ovnis  |  {reloj.get_fps():.0f} FPS")

        # --- 4. Mostrar frame ---
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()