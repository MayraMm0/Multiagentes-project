"""
    Malla de alambre (wireframe): vértices + aristas.
    - Guarda los vértices como matriz homogénea de 4 x N (igual que Piramide).
    - Sabe dibujarse: transforma, proyecta con la Cámara y une con Bresenham.
    - Incluye constructores: caja, superficie de revolución y rejilla.
"""
import math
import numpy as np
 
from Bresenham import dibujar_segmento_2d
 
 
class Malla:
    def __init__(self, puntos, aristas, color):
        # puntos: lista de [x, y, z] -> matriz 4 x N homogénea
        arr = np.array(puntos, dtype=float).T
        self.points = np.vstack([arr, np.ones((1, arr.shape[1]))]) # añade fila de 1s
        self.edges = list(aristas)
        self.color = color
 
    def render(self, superficie, camara, opMat):
        """Dibuja la malla usando la matriz de modelado que tenga opMat ahora."""
        transformados = opMat.transform_points(self.points)
        xs, ys, validos = camara.proyectar_lote(transformados[:3, :])
 
        # redondea al entero más cercano, y lo pasa a lista de python (más rápido que escalares numpy)
        xs = np.rint(xs).astype(int).tolist()
        ys = np.rint(ys).astype(int).tolist()
        validos = validos.tolist()
 
        for i, j in self.edges:
            if validos[i] and validos[j]: # solo dibuja si ambos extremos se pueden proyectar
                dibujar_segmento_2d(
                    superficie,
                    (xs[i], ys[i]),
                    (xs[j], ys[j]),
                    self.color
                )
 
    # ------------------------------------------------------------------
    # Constructores
    # ------------------------------------------------------------------
    @staticmethod # Función que no usa self
    def caja(x0, x1, y0, y1, z0, z1, color):
        """Paralelepípedo alineado a los ejes (8 vértices, 12 aristas)."""
        puntos = [
            [x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1],
            [x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1],
        ]
        aristas = [
            (0, 1), (1, 2), (2, 3), (3, 0),   # base
            (4, 5), (5, 6), (6, 7), (7, 4),   # tapa
            (0, 4), (1, 5), (2, 6), (3, 7),   # verticales
        ]
        return Malla(puntos, aristas, color)
 
    # Base del ovni
    @staticmethod
    def revolucion(perfil, segmentos, color):
        """
        Superficie de revolución se obtiene girando una curva 2D alrededor del eje Y.
        perfil: lista de (radio, y) de abajo hacia arriba.
        Un punto con radio ~0 es un polo (un solo vértice).
        Aristas: un anillo por cada nivel + un meridiano entre niveles.
        """
        puntos = []
        aristas = []
        niveles = []   # índices de los vértices de cada nivel
 
        for radio, y in perfil:
            if radio < 1e-9:
                puntos.append([0.0, y, 0.0])
                niveles.append([len(puntos) - 1])
            else:
                indices = []
                for k in range(segmentos):
                    ang = 2 * math.pi * k / segmentos
                    puntos.append([radio * math.cos(ang), y, radio * math.sin(ang)])
                    indices.append(len(puntos) - 1)
                niveles.append(indices) # niveles[n] = índices de los vértices del anillo n
 
        # Anillos horizontales
        for indices in niveles:
            if len(indices) > 1:
                for k in range(segmentos):
                    aristas.append((indices[k], indices[(k + 1) % segmentos]))
 
        # Meridianos (líneas verticales entre niveles consecutivos)
        for abajo, arriba in zip(niveles[:-1], niveles[1:]):
            for k in range(segmentos):
                a = abajo[k] if len(abajo) > 1 else abajo[0]
                b = arriba[k] if len(arriba) > 1 else arriba[0]
                aristas.append((a, b))
 
        return Malla(puntos, aristas, color)
 
    # Líneas del suelo
    @staticmethod
    def rejilla(tamano, paso, y, color):
        """Rejilla cuadrada en el plano XZ a la altura y (el 'suelo')."""
        puntos = []
        aristas = []
        n = int(tamano / paso)
        for i in range(-n, n + 1):
            c = i * paso
            # línea paralela a Z (x = c)
            puntos.append([c, y, -tamano])
            puntos.append([c, y, tamano])
            aristas.append((len(puntos) - 2, len(puntos) - 1))
            # línea paralela a X (z = c)
            puntos.append([-tamano, y, c])
            puntos.append([tamano, y, c])
            aristas.append((len(puntos) - 2, len(puntos) - 1))
        return Malla(puntos, aristas, color)
 
