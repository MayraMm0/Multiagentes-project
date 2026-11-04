
import math
import pygame

from OpMat import OpMat3D
from Malla import Malla
from Vaca import Vaca
from Ovni import Ovni
from Camara import Camara
from Pintor import dibujar_caras

# Configuración de la ventana
ANCHO, ALTO = 900, 600
FPS = 60

FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)       # bordes del ovni
COLOR_VACA = (60, 45, 60)       # bordes de las vacas
COLOR_SUELO = (45, 40, 110)

LIMITE = 8.0                    # el campo va de -LIMITE a +LIMITE en X y Z

# Vacas en puntos fijos (x, y, z)
POSICIONES = [(-4.0, 0.0, 0.0), (0.0, 0.0, 2.5), (4.0, 0.0, -1.0)]

# Corral: donde se apilan las vacas
CORRAL = (5.0, -4.0)            # centro (x, z)
RADIO_CORRAL = 1.5              # medio ancho del cuadro
COLOR_CORRAL = (255, 0, 0)
ALTO_POSTE = 8.0


def crear_corral():
    """Cuadro de alambre en el suelo + un poste en el centro."""
    cx, cz = CORRAL
    r = RADIO_CORRAL
    return Malla(
        [[cx - r, 0, cz - r], [cx + r, 0, cz - r],      # 0, 1
         [cx + r, 0, cz + r], [cx - r, 0, cz + r],      # 2, 3  (las esquinas)
         [cx, 0, cz], [cx, ALTO_POSTE, cz]],            # 4, 5  (el poste)
        [(0, 1), (1, 2), (2, 3), (3, 0),                # el cuadro
         (4, 5)],                                       # la línea del centro
        COLOR_CORRAL
    )


def soltar_en_corral(vaca, pila):
    """Si la vaca está en el corral y va por encima de la pila, la apila."""
    cx, cz = CORRAL
    if vaca in pila:
        print("esta vaca ya está en la pila")
        return

    distancia = math.hypot(vaca.x - cx, vaca.z - cz)
    print("distancia al corral:", round(distancia, 2))
    if distancia >= RADIO_CORRAL:
        print("no está dentro del corral (tiene que ser menor que", RADIO_CORRAL, ")")
        return

    piso = len(pila) * Vaca.ALTO_LOMO * vaca.escala
    if vaca.y + vaca.subida < piso:
        print("súbela más: tiene que ir por encima de la pila")
        return

    vaca.x, vaca.z = cx, cz
    vaca.cambiar_piso(piso)
    vaca.quieta()        # recalcula su matriz con la nueva posición
    vaca.bajar()         # baja hasta su piso (si ya está ahí, no hace nada)
    pila.append(vaca)


def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Vacas")
    reloj = pygame.time.Clock()

    # Cámara un poco más alta y atrás para que quepa el ovni
    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 7.0, 18.0),
        objetivo=(0.0, 3.5, 0.0)
    )
    opMat = OpMat3D()

    suelo = Malla.rejilla(LIMITE, 2.0, 0.0, COLOR_SUELO)
    corral = crear_corral()

    vacas = [Vaca(COLOR_VACA, posicion=p) for p in POSICIONES]
    ovni = Ovni(COLOR_OVNI, posicion=(0.0, 7.5, 0.0), limite=LIMITE)

    pila = []                    # vacas en el corral, de abajo hacia arriba
    indice = 0
    vaca_control = vacas[indice]

    ejecutando = True
    while ejecutando:
        delta_time = reloj.tick(FPS) / 1000.0

        # --- Eventos: acciones de una sola vez ---
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type != pygame.KEYDOWN:
                continue
            elif evento.key == pygame.K_ESCAPE:
                ejecutando = False
            elif evento.key == pygame.K_TAB:
                indice = (indice + 1) % len(vacas)
                vaca_control = vacas[indice]
            elif evento.key == pygame.K_l:
                ovni.alternar_luz()
            elif vaca_control in pila:
                continue                 # las vacas de la pila ya no se mueven
            elif evento.key == pygame.K_w:
                vaca_control.subir()
            elif evento.key == pygame.K_s:
                vaca_control.bajar()
            elif evento.key == pygame.K_e:
                vaca_control.quieta()
            elif evento.key == pygame.K_SPACE:
                soltar_en_corral(vaca_control, pila)

        # --- 1. Actualizar ---
        # Caminar: mientras la tecla esté presionada (cada frame)
        if vaca_control not in pila:
            teclas = pygame.key.get_pressed()
            dx = dz = 0.0
            if teclas[pygame.K_RIGHT]:
                dx += 1
            if teclas[pygame.K_LEFT]:
                dx -= 1
            if teclas[pygame.K_UP]:
                dz -= 1          # se aleja de la cámara
            if teclas[pygame.K_DOWN]:
                dz += 1          # se acerca
            paso = Vaca.VEL_CAMINAR * delta_time
            vaca_control.mover(dx * paso, dz * paso)

        for vaca in vacas:
            vaca.update(delta_time)
        ovni.update(delta_time)

        # --- 2. Fondo ---
        pantalla.fill(FONDO)

        # --- 3. Renderizar ---
        opMat.loadId()
        suelo.render(pantalla, camara, opMat)      # alambre: siempre abajo
        corral.render(pantalla, camara, opMat)

        caras = []
        for vaca in vacas:
            vaca.render(camara, opMat, caras)
        ovni.render(camara, opMat, caras)
        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(
            f"Vacas  |  vaca {indice + 1} de {len(vacas)}  |  "
            f"pila: {len(pila)}  |  {reloj.get_fps():.0f} FPS"
        )

        # --- 4. Mostrar frame ---
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()