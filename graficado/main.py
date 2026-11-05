"""
    Simulación multiagente: 5 OVNIS buscan 3 vacas y las apilan en el depósito.

    AgentPy (carpeta agente) decide todo: posiciones, estados y tiempos.
    Pygame solo dibuja lo que dice la lógica, interpolando entre pasos:

      - Cada INTERVALO_PASO segundos se llama a modelo.step().
      - `fraccion` (0 -> 1) es cuánto ha pasado del intervalo actual.
      - Un OVNI se dibuja entre su celda anterior y su celda actual según
        `fraccion`: llega justo cuando la lógica da el siguiente paso, así el
        movimiento es continuo y nunca se adelanta ni se atrasa.
      - Las vacas usan `inicio` y `fin` (en pasos) que pone la lógica, así la
        subida y la bajada terminan exactamente cuando el OVNI sigue su camino.

    Teclas:  L -> mostrar siempre todos los rayos   ESC -> salir
"""
import os
import sys
from pathlib import Path

# Permite importar la carpeta agente al ejecutar este archivo desde graficado.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")   # sin mensaje de pygame en la terminal
import pygame

from OpMat import OpMat3D
from Ovni import Ovni
from Vaca import Vaca
from Camara import Camara
from Pintor import dibujar_caras
from Tablero import Tablero
from agente.MundoModelo import MundoModelo


ANCHO, ALTO = 900, 600
FPS = 60
FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)
COLOR_VACA = (60, 45, 60)
COLOR_SUELO = (45, 40, 110)
COLOR_DEPOSITO = (80, 220, 120)

N_CELDAS = 10
TAM_CELDA = 2.0
CANTIDAD_OVNIS = 5
CANTIDAD_VACAS = 3

INTERVALO_PASO = 0.65      # segundos entre pasos de AgentPy

# Cada OVNI a una altura distinta (la panza del más bajo queda arriba de
# una pila de 3 vacas, que mide 2·1.85 + 2.3 = 6 unidades).
ALTURAS_OVNIS = [7.5, 8.5, 9.5, 10.5, 11.5]
ESCALAS_OVNIS = [0.8, 0.7, 0.6, 0.5, 0.5]

ALTO_VACA = 2.3            # de las patas a la punta de los cuernos
ESCALA_COLGADA = 0.45      # tamaño de la vaca mientras va en el rayo
MARGEN_PANZA = 0.15        # espacio entre los cuernos y la panza del OVNI

# Estados en los que el rayo del OVNI está encendido
ESTADOS_CON_RAYO = ("abduciendo", "transportando", "entregando")


def crear_modelo():
    modelo = MundoModelo({
        "tamano": N_CELDAS,
        "cantidad_agentes": CANTIDAD_OVNIS,
        "cantidad_vacas": CANTIDAD_VACAS,
    })
    modelo.setup()
    return modelo


def interpolar(a, b, t):
    return a + (b - a) * t


def suave(t):
    """Arranca y frena suave (para subir y bajar a las vacas)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def progreso(info, tiempo):
    """Avance (0 -> 1) de la animación de una vaca entre `inicio` y `fin`."""
    duracion = info["fin"] - info["inicio"]
    return max(0.0, min(1.0, (tiempo - info["inicio"]) / duracion))


def altura_colgada(ovni):
    """Altura de las patas de una vaca colgada debajo de ese OVNI."""
    return ovni.altura_panza() - ALTO_VACA * ESCALA_COLGADA - MARGEN_PANZA


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    reloj = pygame.time.Clock()

    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 19.0, 24.0),
        objetivo=(0.0, 3.0, 0.0)
    )
    opMat = OpMat3D()

    tablero = Tablero(N_CELDAS, TAM_CELDA, COLOR_SUELO)
    modelo = crear_modelo()
    tablero.marcar(*modelo.deposito, COLOR_DEPOSITO)

    # Un modelo 3D por agente, vinculados por id.
    ovnis = {}
    for i, agente in enumerate(modelo.agentes):
        X, Z = tablero.celda_a_mundo(*agente.posicion())
        ovnis[agente.id] = Ovni(
            COLOR_OVNI,
            posicion=(X, ALTURAS_OVNIS[i], Z),
            escala=ESCALAS_OVNIS[i],
            segmentos=20,
            segmentos_cupula=32,
            controlado=True
        )

    vacas = {}
    for info in modelo.estados_vacas():
        X, Z = tablero.celda_a_mundo(*info["posicion"])
        vacas[info["id"]] = Vaca(COLOR_VACA, posicion=(X, 0.0, Z))

    rayos_siempre = False
    tiempo_paso = 0.0
    ejecutando = True

    while ejecutando:
        delta_time = reloj.tick(FPS) / 1000.0

        # --- Eventos ---
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif evento.key == pygame.K_l:
                    rayos_siempre = not rayos_siempre

        # --- 1. Lógica: un paso de AgentPy cada INTERVALO_PASO segundos ---
        tiempo_paso += delta_time
        if modelo.terminado:
            # Ya no hay más pasos: solo se termina de animar el último.
            tiempo_paso = min(tiempo_paso, INTERVALO_PASO)
        elif tiempo_paso >= INTERVALO_PASO:
            tiempo_paso = min(tiempo_paso - INTERVALO_PASO, INTERVALO_PASO)
            modelo.step()
        fraccion = tiempo_paso / INTERVALO_PASO
        tiempo = modelo.pasos + fraccion          # tiempo en "pasos", continuo

        # --- 2. OVNIS: entre su celda anterior y la actual ---
        estados = {e["id"]: e for e in modelo.estados_agentes()}
        for id_agente, ovni in ovnis.items():
            e = estados[id_agente]
            X0, Z0 = tablero.celda_a_mundo(*e["celda_anterior"])
            X1, Z1 = tablero.celda_a_mundo(*e["celda"])
            ovni.colocar(interpolar(X0, X1, fraccion), interpolar(Z0, Z1, fraccion))
            ovni.luz_encendida = rayos_siempre or e["estado"] in ESTADOS_CON_RAYO
            ovni.update(delta_time)

        # --- 3. Vacas: según su estado en la lógica ---
        for info in modelo.estados_vacas():
            vaca = vacas[info["id"]]
            ovni = ovnis.get(info["agente"])
            estado = info["estado"]

            if estado == "suelo":
                if vaca.estado != "quieta":
                    vaca.quieta()

            elif estado == "subiendo":
                # Sube girando y se encoge hasta quedar colgada del OVNI.
                t = suave(progreso(info, tiempo))
                vaca.pose(ovni.x, ovni.z,
                          altura=interpolar(0.0, altura_colgada(ovni), t),
                          giro=360.0 * t,
                          escala=interpolar(vaca.escala, ESCALA_COLGADA, t))

            elif estado == "transportada":
                vaca.pose(ovni.x, ovni.z, altura_colgada(ovni), escala=ESCALA_COLGADA)

            elif estado == "bajando":
                # Baja del OVNI a su nivel de la pila y recupera su tamaño.
                t = suave(progreso(info, tiempo))
                X, Z = tablero.celda_a_mundo(*modelo.deposito)
                vaca.pose(X, Z,
                          altura=interpolar(altura_colgada(ovni), info["nivel"], t),
                          escala=interpolar(ESCALA_COLGADA, vaca.escala, t))

            else:   # depositada
                X, Z = tablero.celda_a_mundo(*modelo.deposito)
                vaca.pose(X, Z, info["nivel"])

            vaca.update(delta_time)          # la cola

        # --- 4. Dibujar ---
        pantalla.fill(FONDO)
        opMat.loadId()
        tablero.render(pantalla, camara, opMat)

        caras = []
        for vaca in vacas.values():
            vaca.render(camara, opMat, caras)
        for ovni in ovnis.values():
            ovni.render(camara, opMat, caras)
        dibujar_caras(pantalla, caras)

        if modelo.terminado:
            titulo = (f"OVNIS y vacas | Terminado: {modelo.total_entregadas}/"
                      f"{CANTIDAD_VACAS} vacas en {modelo.pasos} pasos")
        else:
            titulo = (f"OVNIS y vacas | Paso {modelo.pasos} | Entregadas "
                      f"{modelo.total_entregadas}/{CANTIDAD_VACAS}")
        pygame.display.set_caption(f"{titulo} | {reloj.get_fps():.0f} FPS")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
