import pygame

from OpMat import OpMat3D
from Malla import Malla
from Ovni import Ovni
from Vaca import Vaca
from Camara import Camara
from Pintor import dibujar_caras
from Tablero import Tablero

# Configuración de la ventana
ANCHO, ALTO = 900, 600
FPS = 60

FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)       # bordes del ovni
COLOR_VACA = (60, 45, 60)       # bordes de las vacas
COLOR_SUELO = (45, 40, 110)

# Tablero: igual a la matriz del modelo de los agentes (N x N celdas)
N_CELDAS = 10
TAM_CELDA = 2.0       # unidades del mundo por celda -> tablero de 20 x 20

# Vacas en celdas (x = columna, y = fila) del tablero
CELDAS_VACAS = [(1, 2), (5, 5), (8, 1)]

# Ovnis: (posición inicial (x, y, z), escala)
# Cada uno a una altura distinta para que no se atraviesen entre sí.
OVNIS = [
    ((-4.0, 6.5, -2.0), 1.0),
    (( 4.0, 8.5,  1.0), 0.7),
    (( 0.0, 10.5, -5.0), 0.5),
]


# ======================================================================
# Programa principal
# ======================================================================
def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ovnis y vacas - modelado 3D con Bresenham")
    reloj = pygame.time.Clock()

    # Objetos principales
    # Más alta para que se vea
    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 16.0, 22.0),
        objetivo=(0.0, 2.0, 0.0)
    )

    opMat = OpMat3D()

    tablero = Tablero(N_CELDAS, TAM_CELDA, COLOR_SUELO)
    tablero.marcar(0, 0, (255, 80, 80))        # celda (0, 0): esquina de adelante a la izquierda
    tablero.marcar(N_CELDAS - 1, N_CELDAS - 1, (80, 220, 120))   # (9, 9): atrás a la derecha

    # El ovni patrulla dentro del tablero (un poco antes de la orilla)
    limite = tablero.mitad - TAM_CELDA / 2

    # Varias instancias de la clase Ovni
    ovnis = [
        Ovni(COLOR_OVNI, posicion=posicion, escala=escala, limite=limite)
        for posicion, escala in OVNIS
    ]

    # Cada vaca en el centro de su celda
    vacas = []
    for x, y in CELDAS_VACAS:
        X, Z = tablero.celda_a_mundo(x, y)
        vacas.append(Vaca(COLOR_VACA, posicion=(X, 0.0, Z)))

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
                for ovni in ovnis:
                    ovni.alternar_luz()    # L: prender / apagar los rayos

        # --- 1. Actualizar agentes ---
        for ovni in ovnis:
            ovni.update(delta_time)
        for vaca in vacas:
            vaca.update(delta_time)

        # --- 2. Fondo ---
        pantalla.fill(FONDO)

        # --- 3. Renderizar ---
        opMat.loadId()                 # matriz de la escena (identidad)

        # El tablero es de alambre y siempre queda abajo: se dibuja primero
        tablero.render(pantalla, camara, opMat)

        # Cada objeto hace push -> sus transformaciones -> recolecta -> pop.
        # Todas las caras van a la misma lista, así el pintor ordena juntas
        # las de todos los ovnis y vacas.
        caras = []
        for vaca in vacas:
            vaca.render(camara, opMat, caras)
        for ovni in ovnis:
            ovni.render(camara, opMat, caras)

        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(
            f"Ovnis y vacas - modelado 3D con Bresenham  |  {reloj.get_fps():.0f} FPS"
        )

        # --- 4. Mostrar frame ---
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()