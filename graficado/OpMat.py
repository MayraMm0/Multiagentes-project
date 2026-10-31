import numpy as np


class OpMat3D:
    # Matriz de modelado 4x4 con pila de matrices
    def __init__(self):
        # Matriz de modelado inicial
        self.matriz_modelado = np.identity(4)
        self.pila = []

    # Estado de la matriz
    def loadId(self):
        # Restablece la matriz a la identidad
        self.matriz_modelado = np.identity(4)

    def push(self):
        # Guarda una copia de la matriz actual
        self.pila.append(self.matriz_modelado.copy())

    def pop(self):
        # Recupera la última matriz guardada
        if not self.pila:
            raise IndexError("pop() sin push(): la pila de matrices está vacía")
        self.matriz_modelado = self.pila.pop()

    def multiplicar(self, matriz):
        # Multiplica la matriz actual por otra matriz
        self.matriz_modelado = self.matriz_modelado @ matriz

    # Transformaciones
    def translate(self, tx, ty, tz):
        # Aplica el desplazamiento
        M = self.matriz_modelado
        M[:, 3] += M[:, :3] @ np.array((tx, ty, tz), dtype=float)

    def scale(self, sx, sy, sz):
        # Aplica el escalado en cada eje
        M = self.matriz_modelado
        M[:, 0] *= sx
        M[:, 1] *= sy
        M[:, 2] *= sz

    def rotate_x(self, deg):
        # Aplica la rotación sobre el eje X
        rad = np.deg2rad(deg)
        c, s = np.cos(rad), np.sin(rad)
        M = self.matriz_modelado
        c1, c2 = M[:, 1].copy(), M[:, 2].copy()
        M[:, 1] = c * c1 + s * c2
        M[:, 2] = -s * c1 + c * c2

    def rotate_y(self, deg):
        # Aplica la rotación sobre el eje Y
        rad = np.deg2rad(deg)
        c, s = np.cos(rad), np.sin(rad)
        M = self.matriz_modelado
        c0, c2 = M[:, 0].copy(), M[:, 2].copy()
        M[:, 0] = c * c0 - s * c2
        M[:, 2] = s * c0 + c * c2

    def rotate_z(self, deg):
        # Aplica la rotación sobre el eje Z
        rad = np.deg2rad(deg)
        c, s = np.cos(rad), np.sin(rad)
        M = self.matriz_modelado
        c0, c1 = M[:, 0].copy(), M[:, 1].copy()
        M[:, 0] = c * c0 + s * c1
        M[:, 1] = -s * c0 + c * c1

    # Combina traslación, rotación y escalado en una matriz
    @staticmethod
    def matriz_trs(tx, ty, tz, rx=0.0, ry=0.0, rz=0.0, sx=1.0, sy=1.0, sz=1.0):
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

    # Aplica la matriz de modelado a los puntos
    def transform_points(self, points):
        return self.matriz_modelado @ points