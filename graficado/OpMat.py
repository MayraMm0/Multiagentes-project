import numpy as np


class OpMat3D:
    """
    Matriz de modelado 4x4 con pila (push/pop).

    Optimización: en lugar de construir una matriz 4x4 completa y hacer
    M @ T (64 multiplicaciones), cada operación modifica SOLO las columnas
    de M que cambian. El resultado es idéntico a multiplicar por la derecha.
    """

    def __init__(self):
        # Matriz de modelado actual, inicializada como identidad
        self.matriz_modelado = np.identity(4)
        # Pila de matrices guardadas con push()
        self.pila = []

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    def loadId(self):
        """Restablece todas las transformaciones acumuladas."""
        self.matriz_modelado = np.identity(4)

    def push(self):
        """Guarda una COPIA de la matriz actual (como glPushMatrix)."""
        self.pila.append(self.matriz_modelado.copy())

    def pop(self):
        """Recupera la última matriz guardada (como glPopMatrix)."""
        if not self.pila:
            raise IndexError("pop() sin push(): la pila de matrices está vacía")
        self.matriz_modelado = self.pila.pop()

    def multiplicar(self, matriz):
        """M = M @ matriz. Sirve para aplicar matrices ya precalculadas."""
        self.matriz_modelado = self.matriz_modelado @ matriz

    # ------------------------------------------------------------------
    # Transformaciones (equivalen a M = M @ T, M @ S, M @ R)
    # ------------------------------------------------------------------
    def translate(self, tx, ty, tz):
        # M @ T solo cambia la última columna: col3 += M[:, :3] @ t
        M = self.matriz_modelado
        M[:, 3] += M[:, :3] @ np.array((tx, ty, tz), dtype=float)

    def scale(self, sx, sy, sz):
        # M @ S escala cada columna por su factor
        M = self.matriz_modelado
        M[:, 0] *= sx
        M[:, 1] *= sy
        M[:, 2] *= sz

    def rotate_x(self, deg):
        # M @ Rx solo mezcla las columnas 1 y 2
        rad = np.deg2rad(deg)
        c, s = np.cos(rad), np.sin(rad)
        M = self.matriz_modelado
        c1, c2 = M[:, 1].copy(), M[:, 2].copy()
        M[:, 1] = c * c1 + s * c2
        M[:, 2] = -s * c1 + c * c2

    def rotate_y(self, deg):
        # M @ Ry solo mezcla las columnas 0 y 2
        rad = np.deg2rad(deg)
        c, s = np.cos(rad), np.sin(rad)
        M = self.matriz_modelado
        c0, c2 = M[:, 0].copy(), M[:, 2].copy()
        M[:, 0] = c * c0 - s * c2
        M[:, 2] = s * c0 + c * c2

    def rotate_z(self, deg):
        # M @ Rz solo mezcla las columnas 0 y 1
        rad = np.deg2rad(deg)
        c, s = np.cos(rad), np.sin(rad)
        M = self.matriz_modelado
        c0, c1 = M[:, 0].copy(), M[:, 1].copy()
        M[:, 0] = c * c0 + s * c1
        M[:, 1] = -s * c0 + c * c1

    # ------------------------------------------------------------------
    # Matriz colapsada: T · Rz · Rx · Ry · S en un solo paso
    # ------------------------------------------------------------------
    @staticmethod
    def matriz_trs(tx, ty, tz, rx=0.0, ry=0.0, rz=0.0, sx=1.0, sy=1.0, sz=1.0):
        """
        Devuelve directamente el producto T · Rz · Rx · Ry · S, calculado a
        mano (fórmula cerrada) en vez de multiplicar 5 matrices 4x4.

        Rx·Ry =
            [ cy      0    sy    ]
            [ sx·sy   cx  -sx·cy ]
            [-cx·sy   sx   cx·cy ]
        Rz·(Rx·Ry) da la parte de rotación de abajo; S escala cada columna
        y T se coloca en la última columna.
        (Con rx = rz = 0 queda simplemente T · Ry · S.)
        """
        ax, ay, az = np.deg2rad((rx, ry, rz))
        cx, snx = np.cos(ax), np.sin(ax)
        cy, sny = np.cos(ay), np.sin(ay)
        cz, snz = np.cos(az), np.sin(az)

        return np.array([
            [(cz * cy - snz * snx * sny) * sx, -snz * cx * sy, (cz * sny + snz * snx * cy) * sz, tx],
            [(snz * cy + cz * snx * sny) * sx,  cz * cx * sy,  (snz * sny - cz * snx * cy) * sz, ty],
            [(-cx * sny) * sx,                  snx * sy,      (cx * cy) * sz,                   tz],
            [0.0,                               0.0,           0.0,                              1.0],
        ])

    # Espera que points ya esté en coordenadas homogéneas (4 x N)
    def transform_points(self, points):
        return self.matriz_modelado @ points