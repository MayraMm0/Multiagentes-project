import numpy as np
from OpMat import OpMat3D
from Bresenham import dibujar_segmento_2d

class Piramide:
    def __init__(self):
        # Vértices de la pirámide
        self.points = np.array([
            [-5.0,  5.0,  5.0, -5.0,  0.0],
            [-2.5, -2.5, -2.5, -2.5,  7.0],
            [-5.0, -5.0,  5.0,  5.0,  0.0],
            [ 1.0,  1.0,  1.0,  1.0,  1.0]
        ], dtype = float)

        # Aristas que conectan los vértices
        self.edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            (0, 4),
            (1, 4),
            (2, 4),
            (3, 4)
        ]

        # Matriz para aplicar transformaciones 3D
        self.opMat = OpMat3D()

        # Ángulo de rotación
        self.deg = 0.0

        # Color de las aristas
        self.color = (232, 139, 221)

    # Actualiza la rotación
    def update(self, delta_deg):
        self.deg += delta_deg

    # Dibuja la pirámide en pantalla
    def render(self, superficie, camara):
        # Reinicia las transformaciones
        self.opMat.loadId()

        # Aplica la rotación sobre el eje Y
        self.opMat.rotate_y(self.deg)

        # Transforma los vértices
        transformed_points = self.opMat.transform_points(self.points)

        # Recorre las aristas de la pirámide
        for inicio, fin in self.edges:
            # Obtiene los extremos de cada arista
            punto_a = transformed_points[:3, inicio]
            punto_b = transformed_points[:3, fin]

            # Proyecta los puntos en la pantalla
            extremo_a = camara.proyectar(punto_a)
            extremo_b = camara.proyectar(punto_b)

            # Dibuja la arista si ambos puntos son visibles
            if extremo_a is not None and extremo_b is not None:
                dibujar_segmento_2d(
                    superficie,
                    extremo_a,
                    extremo_b,
                    self.color
                )