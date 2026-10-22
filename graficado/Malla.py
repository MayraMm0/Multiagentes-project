"""
    Malla 3D: vértices + aristas (+ caras opcionales).
    - Guarda los vértices como matriz homogénea de 4 x N.
    - render(): dibujo de alambre (wireframe) directo con Bresenham.
    - recolectar_caras(): proyecta las caras y las agrega a una lista común
      para que main.py las ordene con el algoritmo del pintor.
    - Incluye constructores: caja, superficie de revolución y rejilla.
"""
import math
import numpy as np

from Bresenham import dibujar_segmento_2d


class Malla:
    def __init__(self, puntos, aristas, color, caras=None, relleno=None):
        """
        color:   color de las aristas / bordes.
        caras:   lista de tuplas de índices (polígonos convexos, 3+ vértices).
        relleno: un color para todas las caras, o una lista con un color por cara.
        """
        # puntos: lista de [x, y, z] -> matriz 4 x N homogénea
        arr = np.array(puntos, dtype=float).T
        self.points = np.vstack([arr, np.ones((1, arr.shape[1]))]) # añade fila de 1s
        self.edges = list(aristas)
        self.color = color

        # Backface culling activado por defecto. En mallas translúcidas se
        # apaga (malla.culling = False) porque las caras de atrás se ven a través.
        self.culling = True

        self.caras = [tuple(c) for c in (caras or [])]
        if relleno is None:
            relleno = color
        if isinstance(relleno, list):
            self.rellenos = list(relleno)
        else:
            self.rellenos = [relleno] * len(self.caras)

    def _proyectar(self, camara, opMat):
        """Transforma con la matriz actual y proyecta todos los vértices."""
        transformados = opMat.transform_points(self.points)
        xs, ys, validos, prof = camara.proyectar_lote(transformados[:3, :])
        # redondea al entero más cercano, y lo pasa a lista de python (más rápido que escalares numpy)
        return (np.rint(xs).astype(int).tolist(),
                np.rint(ys).astype(int).tolist(),
                validos.tolist(),
                prof.tolist())

    def render(self, superficie, camara, opMat):
        """Dibujo de alambre con la matriz de modelado que tenga opMat ahora."""
        xs, ys, validos, _ = self._proyectar(camara, opMat)

        for i, j in self.edges:
            if validos[i] and validos[j]: # solo dibuja si ambos extremos se pueden proyectar
                dibujar_segmento_2d(
                    superficie,
                    (xs[i], ys[i]),
                    (xs[j], ys[j]),
                    self.color
                )

    def recolectar_caras(self, camara, opMat, lista, culling=None):
        """
        Agrega a `lista` una tupla por cara visible:
            (profundidad_promedio, puntos_2d, color_relleno, color_borde)
        No dibuja nada: el dibujo se hace después de ordenar TODAS las caras
        de la escena (así el ovni y las vacas se tapan bien entre sí).

        culling (backface culling): todas las caras tienen sus vértices en el
        mismo sentido vistos desde afuera. Ya proyectadas, si el área con signo
        del polígono (fórmula de shoelace) es >= 0, la cara le da la espalda
        a la cámara y se descarta. Así se dibuja casi la mitad de caras.
        """
        if culling is None:
            culling = self.culling
        xs, ys, validos, prof = self._proyectar(camara, opMat)

        for cara, relleno in zip(self.caras, self.rellenos):
            # Si algún vértice queda detrás de la cámara, se descarta la cara
            if not all(validos[i] for i in cara):
                continue
            puntos_2d = [(xs[i], ys[i]) for i in cara]

            if culling:
                area = 0
                n = len(puntos_2d)
                for k in range(n):
                    x0, y0 = puntos_2d[k]
                    x1, y1 = puntos_2d[(k + 1) % n]
                    area += x0 * y1 - x1 * y0
                if area >= 0:      # de espaldas (o de canto): no se dibuja
                    continue

            profundidad = sum(prof[i] for i in cara) / len(cara)
            lista.append((profundidad, puntos_2d, relleno, self.color))

    # ------------------------------------------------------------------
    # Constructores
    # ------------------------------------------------------------------
    @staticmethod # Función que no usa self
    def caja(x0, x1, y0, y1, z0, z1, color, relleno=None):
        """Paralelepípedo alineado a los ejes (8 vértices, 12 aristas, 6 caras)."""
        puntos = [
            [x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1],
            [x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1],
        ]
        aristas = [
            (0, 1), (1, 2), (2, 3), (3, 0),   # base
            (4, 5), (5, 6), (6, 7), (7, 4),   # tapa
            (0, 4), (1, 5), (2, 6), (3, 7),   # verticales
        ]
        # Vértices en el mismo sentido vistos desde afuera
        # (no hace falta para el pintor, pero sí para un backface culling futuro)
        caras = [
            (0, 1, 2, 3),   # abajo   (y0)
            (4, 7, 6, 5),   # arriba  (y1)
            (0, 4, 5, 1),   # z0
            (3, 2, 6, 7),   # z1
            (0, 3, 7, 4),   # x0
            (1, 5, 6, 2),   # x1
        ]
        return Malla(puntos, aristas, color, caras, relleno)

    @staticmethod
    def piramide(color, relleno=None):
        """
        Pirámide de base cuadrada, de cabeza: la punta en el origen (0, 0, 0)
        y la base en y = -1, de -1 a 1 en X y Z. Se acomoda con escalado:
        sy = altura y sx, sz = medio ancho de la base.
        (5 vértices, 8 aristas, 4 caras laterales + la base)
        """
        puntos = [
            [-1.0, -1.0, -1.0], [1.0, -1.0, -1.0],
            [1.0, -1.0, 1.0], [-1.0, -1.0, 1.0],
            [0.0, 0.0, 0.0],                      # punta
        ]
        aristas = [
            (0, 1), (1, 2), (2, 3), (3, 0),   # base
            (0, 4), (1, 4), (2, 4), (3, 4),   # hacia la punta
        ]
        caras = [
            (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4),   # lados
            (0, 3, 2, 1),                                 # base
        ]
        return Malla(puntos, aristas, color, caras, relleno)

    # Base del ovni
    @staticmethod
    def revolucion(perfil, segmentos, color, relleno=None):
        """
        Superficie de revolución se obtiene girando una curva 2D alrededor del eje Y.
        perfil: lista de (radio, y) de abajo hacia arriba.
        Un punto con radio ~0 es un polo (un solo vértice).
        Aristas: un anillo por cada nivel + un meridiano entre niveles.
        Caras: un cuadrilátero por segmento entre dos niveles
               (triángulo si uno de los niveles es un polo).
        relleno: un color, o una lista con un color por FRANJA
                 (len(perfil) - 1 colores, de abajo hacia arriba).
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

        # Caras entre niveles consecutivos (una franja por par de niveles)
        if relleno is None:
            relleno = color
        caras = []
        rellenos = []
        for franja, (abajo, arriba) in enumerate(zip(niveles[:-1], niveles[1:])):
            color_franja = relleno[franja] if isinstance(relleno, list) else relleno
            for k in range(segmentos):
                k2 = (k + 1) % segmentos
                # Mismo sentido de giro que las caras de la caja (vistas desde afuera)
                if len(abajo) == 1:                     # polo abajo -> triángulo
                    cara = (abajo[0], arriba[k], arriba[k2])
                elif len(arriba) == 1:                  # polo arriba -> triángulo
                    cara = (abajo[k], arriba[0], abajo[k2])
                else:                                   # cuadrilátero
                    cara = (abajo[k], arriba[k], arriba[k2], abajo[k2])
                caras.append(cara)
                rellenos.append(color_franja)

        return Malla(puntos, aristas, color, caras, rellenos)

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