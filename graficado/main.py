import math
import random

import numpy as np
import pygame

from OpMat import OpMat3D
from Malla import Malla
from Ovni import Ovni
from Vaca import Vaca

ANCHO, ALTO = 900, 600
import math
import random

import numpy as np
import pygame

from OpMat import OpMat3D
from Malla import Malla
from Ovni import Ovni
from Vaca import Vaca
from Bresenham import rellenar_poligono, rellenar_poligono_alpha, dibujar_segmento_2d

# Configuración de la ventana
ANCHO, ALTO = 900, 600
FPS = 60

FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)       # bordes del ovni
COLOR_VACA = (60, 45, 60)       # bordes de las vacas
COLOR_SUELO = (45, 40, 110)

LIMITE = 8.0          # el campo va de -LIMITE a +LIMITE en X y Z


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


def restar(a,b):
    return np.array(a, dtype=float) - np.array(b, dtype=float)

def producto_punto(a,b):
    return np.dot(a, b)

def producto_cruz(a,b):
    return np.cross(a, b)

def normalizar(v):
    magnitud = np.linalg.norm(v)

    if magnitud == 0:
        raise ValueError("No se puede normalizar un vector de magnitud cero")

    return v / magnitud

class Camara:
    def __init__(
        self,
        screen_width = 900,
        screen_height = 600,
        posicion = (10.0, 10.0, 10.0),
        objetivo = (0.0, 0.0, 0.0),
        arriba = (0.0, 1.0, 0.0)
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.posicion = np.array(posicion, dtype=float)
        self.objetivo = np.array(objetivo, dtype=float)
        self.arriba = np.array(arriba, dtype=float)

        self.fov_y = 60.0
        self.znear = 1.0
        self.zfar = 500.0

        # Sistema de coordenadas de la cámara (orientación), equivalente en intención a gluLookAt.
        self.frente = normalizar(
            restar(self.objetivo, self.posicion)
        )
        self.derecha = normalizar(
            producto_cruz(self.frente, self.arriba)
        )
        self.arriba_camara = producto_cruz(
            self.derecha,
            self.frente
        )

        # Distancia focal en píxeles
        # en universo 3D (Aplicar Perspectiva: cuánto "encoger" según distancia)
        # aplica distancia focal por semejanza de triángulos
        self.focal = (
            (self.screen_height / 2)
            / math.tan(math.radians(self.fov_y) / 2)
        )

        # Matriz de vista 3x3 precalculada: sus filas son derecha, arriba y frente.
        # Así un solo producto V @ relativo da (x_cam, y_cam, profundidad)
        # en lugar de tres productos punto separados.
        self.vista = np.vstack([self.derecha, self.arriba_camara, self.frente])
        self.posicion_col = self.posicion.reshape(3, 1)

    def proyectar(self, punto):
        # relativo -> saber si el objeto está atrás de cámara o en el área visual
        # vector que apunta directo desde cam -> punto/obj. Pos punto respecto a cámara
        relativo = restar(punto, self.posicion)

        # Con respecto a cámara, en un espacio 2D (pixel) donde cae
        x_cam = producto_punto(relativo, self.derecha)
        y_cam = producto_punto(relativo, self.arriba_camara)
        profundidad = producto_punto(relativo, self.frente)

        # No proyectar puntos fuera de profundidad válida
        if profundidad <= self.znear or profundidad > self.zfar:
            return None

        # Convertir al sistema de pixeles
        # Hace la proyección FINAL, con el (0,0) como centro de la pantalla, +y abajo
        x_pantalla = (
            self.screen_width / 2
            + x_cam * self.focal / profundidad
        )
        y_pantalla = (
            self.screen_height / 2
            - y_cam * self.focal / profundidad
        )

        return (x_pantalla, y_pantalla)

    """
        Misma matemática que proyectar(), pero para muchos puntos a la vez (que corra más rápido)
        puntos: arreglo 3 x N (columnas = puntos)
        Devuelve (xs, ys, validos, profundidad): arreglos de largo N.
          validos[i] es False si el punto i está detrás de la cámara o fuera de perspectiva.
          profundidad[i] se usa para ordenar caras (algoritmo del pintor).
        Sirve para no llamar a proyectar() muchas veces por frame
    """
    def proyectar_lote(self, puntos):
        # Un solo producto matricial: filas = x_cam, y_cam, profundidad
        x_cam, y_cam, profundidad = self.vista @ (puntos - self.posicion_col)

        # validos -> es False si el punto i está detrás de la cámara o fuera de perspectiva.
        validos = (profundidad > self.znear) & (profundidad <= self.zfar)

        # Evitar dividir entre cero en los puntos inválidos
        escala = self.focal / np.where(validos, profundidad, 1.0)

        xs = self.screen_width / 2 + x_cam * escala
        ys = self.screen_height / 2 - y_cam * escala

        return xs, ys, validos, profundidad


# ======================================================================
# Programa principal
# ======================================================================
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
                ovni.alternar_luz()        # L: prender / apagar el rayo

        # --- 1. Actualizar agentes ---
        ovni.update(delta_time)
        for vaca in vacas:
            vaca.update(delta_time)

        # --- 2. Fondo ---
        pantalla.fill(FONDO)

        # --- 3. Renderizar ---
        opMat.loadId()                 # matriz de la escena (identidad)

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
FPS = 60

FONDO = (13, 10, 45)
COLOR_OVNI = (30, 30, 45)  # bordes del ovnifrom Bresenham import rellenar_poligono, rellenar_poligono_alpha, dibujar_segmento_2d

COLOR_VACA = (60, 45, 60)  # bordes de las vacas
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


def restar(a, b):
    return np.array(a, dtype=float) - np.array(b, dtype=float)


def producto_punto(a, b):
    return np.dot(a, b)


def producto_cruz(a, b):
    return np.cross(a, b)


def normalizar(v):
    magnitud = np.linalg.norm(v)

    if magnitud == 0:
        raise ValueError("No se puede normalizar un vector de magnitud cero")

    return v / magnitud


class Camara:
    def __init__(
            self,
            screen_width=900,
            screen_height=600,
            posicion=(10.0, 10.0, 10.0),
            objetivo=(0.0, 0.0, 0.0),
            arriba=(0.0, 1.0, 0.0)
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.posicion = np.array(posicion, dtype=float)
        self.objetivo = np.array(objetivo, dtype=float)
        self.arriba = np.array(arriba, dtype=float)

        self.fov_y = 60.0
        self.znear = 1.0
        self.zfar = 500.0

        self.frente = normalizar(
            restar(self.objetivo, self.posicion)
        )
        self.derecha = normalizar(
            producto_cruz(self.frente, self.arriba)
        )
        self.arriba_camara = producto_cruz(
            self.derecha,
            self.frente
        )

        # Distancia focal en píxeles
        # en universo 3D (Aplicar Perspectiva: cuánto "encoger" según distancia)
        # aplica distancia focal por semejanza de triángulos
        self.focal = (
                (self.screen_height / 2)
                / math.tan(math.radians(self.fov_y) / 2)
        )

        # Matriz de vista 3x3 precalculada: sus filas son derecha, arriba y frente.
        # Así un solo producto V @ relativo da (x_cam, y_cam, profundidad)
        # en lugar de tres productos punto separados.

        self.vista = np.vstack([self.derecha, self.arriba_camara, self.frente])
        self.posicion_col = self.posicion.reshape(3, 1)

    def proyectar(self, punto):
        # relativo -> saber si el objeto está atrás de cámara o en el área visual
        # vector que apunta directo desde cam -> punto/obj. Pos punto respecto a cámara
        relativo = restar(punto, self.posicion)

        # Con respecto a cámara, en un espacio 2D (pixel) donde cae
        x_cam = producto_punto(relativo, self.derecha)
        y_cam = producto_punto(relativo, self.arriba_camara)
        profundidad = producto_punto(relativo, self.frente)

        # No proyectar puntos fuera de profundidad válida
        if profundidad <= self.znear or profundidad > self.zfar:
            return None

        # Convertir al sistema de pixeles
        # Hace la proyección FINAL, con el (0,0) como centro de la pantalla, +y abajo
        x_pantalla = (
                self.screen_width / 2
                + x_cam * self.focal / profundidad
        )
        y_pantalla = (
                self.screen_height / 2
                - y_cam * self.focal / profundidad
        )

        return (x_pantalla, y_pantalla)

    """
        Misma matemática que proyectar(), pero para muchos puntos a la vez (que corra más rápido)
        puntos: arreglo 3 x N (columnas = puntos)
        Devuelve (xs, ys, validos, profundidad): arreglos de largo N.
          validos[i] es False si el punto i está detrás de la cámara o fuera de perspectiva.
          profundidad[i] se usa para ordenar caras (algoritmo del pintor).
        Sirve para no llamar a proyectar() muchas veces por frame
    """

    def proyectar_lote(self, puntos):
        # Un solo producto matricial: filas = x_cam, y_cam, profundidad
        x_cam, y_cam, profundidad = self.vista @ (puntos - self.posicion_col)

        # validos -> es False si el punto i está detrás de la cámara o fuera de perspectiva.
        validos = (profundidad > self.znear) & (profundidad <= self.zfar)

        # Evitar dividir entre cero en los puntos inválidos
        escala = self.focal / np.where(validos, profundidad, 1.0)

        xs = self.screen_width / 2 + x_cam * escala
        ys = self.screen_height / 2 - y_cam * escala

        return xs, ys, validos, profundidad


# ======================================================================
# Programa principal
# ======================================================================
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

        ovni.update(delta_time)
        for vaca in vacas:
            vaca.update(delta_time)

        pantalla.fill(FONDO)

        opMat.loadId()

        suelo.render(pantalla, camara, opMat)

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