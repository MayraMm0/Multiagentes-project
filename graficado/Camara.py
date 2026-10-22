"""
    Este archivo debe:
    - Definir posición de la cámara
    - Calcular vectores de orientación
    - Proyectar un punto 3D en perspectiva
    - Devolver None si el punto está detrás
"""
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