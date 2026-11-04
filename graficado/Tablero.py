
import math

from Malla import Malla


class Tablero:
    def __init__(self, n=10, tam_celda=2.0, color=(45, 40, 110)):
        self.n = n
        self.tam = tam_celda
        self.mitad = n * tam_celda / 2        # del centro a una orilla

        # Rejilla de alambre: N+1 líneas en cada dirección -> N x N celdas
        self.malla = Malla.rejilla(self.mitad, self.tam, 0.0, color)

        # Celdas marcadas para verlas en pantalla: {(x, y): color}
        self.marcadas = {}

    # ------------------------------------------------------------------
    # Conversión celda <-> mundo
    # ------------------------------------------------------------------
    def celda_a_mundo(self, x, y):
        """Centro (X, Z) en el mundo de la celda (x, y)."""
        X = -self.mitad + (x + 0.5) * self.tam
        Z = self.mitad - (y + 0.5) * self.tam
        return X, Z

    def mundo_a_celda(self, X, Z):
        """Celda (x, y) en la que cae el punto (X, Z) del mundo, o None si está fuera."""
        x = math.floor((X + self.mitad) / self.tam)
        y = math.floor((self.mitad - Z) / self.tam)
        if self.dentro(x, y):
            return x, y
        return None

    def dentro(self, x, y):
        return 0 <= x < self.n and 0 <= y < self.n

    # ------------------------------------------------------------------
    # Marcar celdas (para probar la conexión con el modelo)
    # ------------------------------------------------------------------
    def marcar(self, x, y, color):
        self.marcadas[(x, y)] = color

    def desmarcar(self, x, y):
        self.marcadas.pop((x, y), None)

    def _malla_celda(self, x, y, color):
        """Cuadro de alambre un poco más chico que la celda (para que se distinga)."""
        cx, cz = self.celda_a_mundo(x, y)
        r = self.tam / 2 * 0.85
        return Malla(
            [[cx - r, 0, cz - r], [cx + r, 0, cz - r],
             [cx + r, 0, cz + r], [cx - r, 0, cz + r]],
            [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)],   # cuadro + una X
            color
        )

    # ------------------------------------------------------------------
    # Dibujo: alambre, se dibuja antes que las caras (siempre queda abajo)
    # ------------------------------------------------------------------
    def render(self, superficie, camara, opMat):
        self.malla.render(superficie, camara, opMat)
        for (x, y), color in self.marcadas.items():
            self._malla_celda(x, y, color).render(superficie, camara, opMat)