import math
import numpy as np

from Bresenham import dibujar_segmento_2d


class Malla:
    def __init__(self, puntos, aristas, color, caras=None, relleno=None):
        # Convierte los puntos a una matriz homogénea de 4 x N
        arr = np.array(puntos, dtype=float).T
        self.points = np.vstack([arr, np.ones((1, arr.shape[1]))])
        self.edges = list(aristas)
        self.color = color

        # Permite ocultar las caras que están de espaldas a la cámara
        self.culling = True

        self.caras = [tuple(c) for c in (caras or [])]
        if relleno is None:
            relleno = color
        if isinstance(relleno, list):
            self.rellenos = list(relleno)
        else:
            self.rellenos = [relleno] * len(self.caras)

    def _proyectar(self, camara, opMat):
        transformados = opMat.transform_points(self.points)
        xs, ys, validos, prof = camara.proyectar_lote(transformados[:3, :])

        # Redondea las coordenadas y las convierte a listas
        return (np.rint(xs).astype(int).tolist(),
                np.rint(ys).astype(int).tolist(),
                validos.tolist(),
                prof.tolist())

    def render(self, superficie, camara, opMat):
        xs, ys, validos, _ = self._proyectar(camara, opMat)

        for i, j in self.edges:
            if validos[i] and validos[j]:
                dibujar_segmento_2d(
                    superficie,
                    (xs[i], ys[i]),
                    (xs[j], ys[j]),
                    self.color
                )

    def recolectar_caras(self, camara, opMat, lista, culling=None):
        # Agrega las caras visibles para dibujarlas después de ordenarlas
        if culling is None:
            culling = self.culling
        xs, ys, validos, prof = self._proyectar(camara, opMat)

        for cara, relleno in zip(self.caras, self.rellenos):
            # Descarta la cara si algún vértice no se puede proyectar
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
                if area >= 0:
                    continue

            profundidad = sum(prof[i] for i in cara) / len(cara)
            lista.append((profundidad, puntos_2d, relleno, self.color))

    # Constructores
    @staticmethod
    def caja(x0, x1, y0, y1, z0, z1, color, relleno=None):
        puntos = [
            [x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1],
            [x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1],
        ]
        aristas = [
            (0, 1), (1, 2), (2, 3), (3, 0),   # Base
            (4, 5), (5, 6), (6, 7), (7, 4),   # Tapa
            (0, 4), (1, 5), (2, 6), (3, 7),   # Verticales
        ]
        caras = [
            (0, 1, 2, 3),   # Abajo
            (4, 7, 6, 5),   # Arriba
            (0, 4, 5, 1),
            (3, 2, 6, 7),
            (0, 3, 7, 4),
            (1, 5, 6, 2),
        ]
        return Malla(puntos, aristas, color, caras, relleno)

    @staticmethod
    def piramide(color, relleno=None):
        puntos = [
            [-1.0, -1.0, -1.0], [1.0, -1.0, -1.0],
            [1.0, -1.0, 1.0], [-1.0, -1.0, 1.0],
            [0.0, 0.0, 0.0],                      # Punta
        ]
        aristas = [
            (0, 1), (1, 2), (2, 3), (3, 0),   # Base
            (0, 4), (1, 4), (2, 4), (3, 4),   # Lados
        ]
        caras = [
            (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4),
            (0, 3, 2, 1),                                 # Base
        ]
        return Malla(puntos, aristas, color, caras, relleno)

    # Construcción de superficies a partir de anillos
    @staticmethod
    def _desde_anillos(puntos, niveles, segmentos, color, relleno):
        aristas = []

        # Conecta los vértices de cada anillo
        for indices in niveles:
            if len(indices) > 1:
                for k in range(segmentos):
                    aristas.append((indices[k], indices[(k + 1) % segmentos]))

        # Conecta los anillos entre sí
        for abajo, arriba in zip(niveles[:-1], niveles[1:]):
            for k in range(segmentos):
                a = abajo[k] if len(abajo) > 1 else abajo[0]
                b = arriba[k] if len(arriba) > 1 else arriba[0]
                aristas.append((a, b))

        # Crea las caras entre cada par de anillos
        if relleno is None:
            relleno = color
        caras = []
        rellenos = []
        for franja, (abajo, arriba) in enumerate(zip(niveles[:-1], niveles[1:])):
            color_franja = relleno[franja] if isinstance(relleno, list) else relleno
            for k in range(segmentos):
                k2 = (k + 1) % segmentos
                if len(abajo) == 1:                     # Triángulo en la parte inferior
                    cara = (abajo[0], arriba[k], arriba[k2])
                elif len(arriba) == 1:                  # Triángulo en la parte superior
                    cara = (abajo[k], arriba[0], abajo[k2])
                else:                                   # Cuadrilátero
                    cara = (abajo[k], arriba[k], arriba[k2], abajo[k2])
                caras.append(cara)
                rellenos.append(color_franja)

        return Malla(puntos, aristas, color, caras, rellenos)

    @staticmethod
    def revolucion(perfil, segmentos, color, relleno=None):
        puntos = []
        niveles = []

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
                niveles.append(indices)

        return Malla._desde_anillos(puntos, niveles, segmentos, color, relleno)

    @staticmethod
    def elipsoide(a, b, c, color, relleno=None, segmentos=32, anillos=12,
                  lat_min=-90.0, lat_max=90.0, centro=(0.0, 0.0, 0.0)):
        cx, cy, cz = centro
        puntos = []
        niveles = []

        for i in range(anillos + 1):
            phi = math.radians(lat_min + (lat_max - lat_min) * i / anillos)
            y = cy + b * math.sin(phi)

            if abs(math.cos(phi)) < 1e-9:
                puntos.append([cx, y, cz])
                niveles.append([len(puntos) - 1])
                continue

            indices = []
            for k in range(segmentos):
                theta = 2 * math.pi * k / segmentos
                puntos.append([cx + a * math.cos(phi) * math.cos(theta),
                               y,
                               cz + c * math.cos(phi) * math.sin(theta)])
                indices.append(len(puntos) - 1)
            niveles.append(indices)

        return Malla._desde_anillos(puntos, niveles, segmentos, color, relleno)

    @staticmethod
    def esfera(r, color, relleno=None, segmentos=32, anillos=12,
               lat_min=-90.0, lat_max=90.0, centro=(0.0, 0.0, 0.0)):
        cx, cy, cz = centro
        puntos = []
        niveles = []

        for i in range(anillos + 1):
            phi = math.radians(lat_min + (lat_max - lat_min) * i / anillos)
            y = cy + r * math.sin(phi)

            if abs(math.cos(phi)) < 1e-9:
                puntos.append([cx, y, cz])
                niveles.append([len(puntos) - 1])
                continue

            indices = []
            for k in range(segmentos):
                theta = 2 * math.pi * k / segmentos
                puntos.append([cx + r * math.cos(phi) * math.cos(theta),
                               y,
                               cz + r * math.cos(phi) * math.sin(theta)])
                indices.append(len(puntos) - 1)
            niveles.append(indices)

        return Malla._desde_anillos(puntos, niveles, segmentos, color, relleno)

    # Dibuja la rejilla del suelo
    @staticmethod
    def rejilla(tamano, paso, y, color):
        puntos = []
        aristas = []
        n = int(tamano / paso)
        for i in range(-n, n + 1):
            c = i * paso
            # Línea paralela al eje Z
            puntos.append([c, y, -tamano])
            puntos.append([c, y, tamano])
            aristas.append((len(puntos) - 2, len(puntos) - 1))
            # Línea paralela al eje X
            puntos.append([-tamano, y, c])
            puntos.append([tamano, y, c])
            aristas.append((len(puntos) - 2, len(puntos) - 1))
        return Malla(puntos, aristas, color)