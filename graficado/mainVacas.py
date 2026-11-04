"""
    Escena de prueba: solo las VACAS.
    Tres vacas en puntos fijos que suben mientras rotan sobre el eje Y.
    Reutiliza la cámara y el algoritmo del pintor de main.py.
"""
import pygame
import math
from OpMat import OpMat3D
from Malla import Malla
from Vaca import Vaca
from main import Camara, dibujar_caras, ANCHO, ALTO, FPS, FONDO, COLOR_VACA, COLOR_SUELO

# Vacas en puntos fijos (x, y, z)
POSICIONES = [(-4.0, 0.0, 0.0), (0.0, 0.0, 2.5), (4.0, 0.0, -1.0)]

CORRAL = (5.0, -4.0)       # centro (x, z)
RADIO_CORRAL = 1.5         # medio ancho del cuadro
COLOR_CORRAL = (255, 0, 0)
ALTO_POSTE = 8.0

cx, cz = CORRAL
r = RADIO_CORRAL
corral = Malla(
    [[cx - r, 0, cz - r], [cx + r, 0, cz - r],      # 0, 1
     [cx + r, 0, cz + r], [cx - r, 0, cz + r],      # 2, 3  (las esquinas)
     [cx, 0, cz], [cx, ALTO_POSTE, cz]],            # 4, 5  (el poste)
    [(0, 1), (1, 2), (2, 3), (3, 0),                # el cuadro
     (4, 5)],                                       # la línea del centro
    COLOR_CORRAL
)

def main():
    pygame.init()

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Vacas")
    reloj = pygame.time.Clock()

    # Cámara más cerca y más baja que en la escena completa
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
    vaca_control = vacas[0]

    pila = []

    indice = 0  # antes del while
    vaca_control = vacas[indice]

    while ejecutando:
        delta_time = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_w:
                vaca_control.subir()
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_s:
                vaca_control.bajar()
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_e:
                vaca_control.quieta()
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                distancia = math.hypot(vaca_control.x - cx, vaca_control.z - cz)
                print("distancia al corral:", round(distancia, 2))
                if distancia < RADIO_CORRAL:
                    vaca_control.x, vaca_control.z = cx, cz
                    vaca_control.quieta()
                    vaca_control.bajar()

                    if vaca_control not in pila:
                        piso = len(pila) * Vaca.ALTO_LOMO * vaca_control.escala
                        if vaca_control.y + vaca_control.subida < piso:
                            print("mas arriba")
                        else:
                            vaca.cambiar_piso(piso)
                            vaca.quieta()
                            vaca.bajar()
                            pila.append(vaca_control)
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_TAB:
                indice = (indice + 1) % len(vacas)
                vaca_control = vacas[indice]








        # --- 1. Actualizar ---
        teclas = pygame.key.get_pressed()

        dx = dz = 0.0
        if teclas[pygame.K_RIGHT]:
            dx += 1
        if teclas[pygame.K_LEFT]:
            dx -= 1
        if teclas[pygame.K_UP]:
            dz -= 1
        if teclas[pygame.K_DOWN]:
            dz += 1


        paso = Vaca.VEL_CAMINAR * delta_time
        vaca_control.mover(dx * paso, dz * paso)

        for vaca in vacas:
            vaca.update(delta_time)

        # --- 2. Fondo ---
        pantalla.fill(FONDO)

        # --- 3. Renderizar ---
        opMat.loadId()
        suelo.render(pantalla, camara, opMat)
        corral.render(pantalla, camara, opMat)

        caras = []
        for vaca in vacas:
            vaca.render(camara, opMat, caras)



        dibujar_caras(pantalla, caras)

        pygame.display.set_caption(f"Vacas  |  {reloj.get_fps():.0f} FPS")

        # --- 4. Mostrar frame ---
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
