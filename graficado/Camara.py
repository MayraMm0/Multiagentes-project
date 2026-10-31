import numpy as np
import math

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

        # Calcula la orientación de la cámara
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

        # Calcula la distancia focal en píxeles
        self.focal = (
            (self.screen_height / 2)
            / math.tan(math.radians(self.fov_y) / 2)
        )

        # Guarda la matriz de vista para proyectar los puntos más rápido
        self.vista = np.vstack([self.derecha, self.arriba_camara, self.frente])
        self.posicion_col = self.posicion.reshape(3, 1)

    def proyectar(self, punto):
        # Calcula la posición del punto respecto a la cámara
        relativo = restar(punto, self.posicion)

        x_cam = producto_punto(relativo, self.derecha)
        y_cam = producto_punto(relativo, self.arriba_camara)
        profundidad = producto_punto(relativo, self.frente)

        # Ignora los puntos fuera del rango de visión
        if profundidad <= self.znear or profundidad > self.zfar:
            return None

        # Convierte las coordenadas 3D a píxeles
        x_pantalla = (
            self.screen_width / 2
            + x_cam * self.focal / profundidad
        )
        y_pantalla = (
            self.screen_height / 2
            - y_cam * self.focal / profundidad
        )

        return (x_pantalla, y_pantalla)

    # Proyecta varios puntos al mismo tiempo
    def proyectar_lote(self, puntos):
        # Calcula las coordenadas de todos los puntos usando la matriz de vista
        x_cam, y_cam, profundidad = self.vista @ (puntos - self.posicion_col)

        # Identifica los puntos que están dentro del rango de visión
        validos = (profundidad > self.znear) & (profundidad <= self.zfar)

        # Evita dividir entre cero en los puntos inválidos
        escala = self.focal / np.where(validos, profundidad, 1.0)

        xs = self.screen_width / 2 + x_cam * escala
        ys = self.screen_height / 2 - y_cam * escala

        return xs, ys, validos, profundidad