import math
import random

from Malla import Malla
from OpMat import OpMat3D

# Colores de la vaca
BLANCO = (235, 232, 225)
ROSA = (240, 160, 185)
HUESO = (215, 200, 160)
GRIS = (110, 105, 105)


class Vaca:
    # Punto donde gira la cola
    PIVOTE_COLA = (-1.1, 1.75, 0.0)

    VEL_SUBIDA = 1.0       # Velocidad de subida
    VEL_GIRO = 120.0       # Velocidad de rotación
    ALTURA_MAX = 4.0       # Altura máxima

    def __init__(self, color, posicion=None, limite=8.0, escala=1.0):
        self.escala = escala
        self.limite = limite

        # Elige una posición aleatoria si no se proporciona una
        if posicion is None:
            margen = limite - 1.0
            posicion = (random.uniform(-margen, margen),
                        0.0,
                        random.uniform(-margen, margen))
        self.x, self.y, self.z = posicion

        # Asigna una orientación aleatoria
        self.rumbo = random.uniform(0, 360)

        # Define la altura y el giro inicial
        self.subida = random.uniform(0, self.ALTURA_MAX)
        self.giro = 0.0

        # Configura el movimiento de la cola
        self.tiempo = random.uniform(0, 10)
        self.vel_cola = random.uniform(3.0, 5.0)

        # Partes que forman el modelo de la vaca
        self.partes = [
            Malla.caja(-1.1, 1.1, 0.95, 1.85, -0.5, 0.5, color, BLANCO),     # cuerpo
            Malla.caja(1.1, 1.75, 1.35, 2.05, -0.3, 0.3, color, BLANCO),     # cabeza
            Malla.caja(1.75, 1.95, 1.35, 1.7, -0.2, 0.2, color, ROSA),       # hocico
            Malla.caja(1.2, 1.3, 2.05, 2.3, -0.28, -0.2, color, HUESO),      # cuerno izquierdo
            Malla.caja(1.2, 1.3, 2.05, 2.3, 0.2, 0.28, color, HUESO),        # cuerno derecho
            Malla.caja(-0.6, -0.2, 0.8, 0.95, -0.25, 0.25, color, ROSA),     # ubre
        ]

        # Agrega las cuatro patas
        posiciones_patas = [(0.8, 0.32), (0.8, -0.32), (-0.8, 0.32), (-0.8, -0.32)]
        for cx, cz in posiciones_patas:
            self.partes.append(
                Malla.caja(cx - 0.12, cx + 0.12, 0.0, 0.95, cz - 0.12, cz + 0.12,
                           color, GRIS)
            )

        # Separa la cola para poder animarla
        self.cola = Malla.caja(-1.35, -1.1, 1.4, 1.75, -0.04, 0.04, color, GRIS)

    # Actualiza el movimiento de la vaca
    def update(self, dt):
        self.tiempo += dt

        # Hace que la vaca suba y gire
        self.subida += self.VEL_SUBIDA * dt
        self.giro = (self.giro + self.VEL_GIRO * dt) % 360.0

        # Regresa la vaca al suelo al llegar a la altura máxima
        if self.subida >= self.ALTURA_MAX:
            self.subida = 0.0

    # Dibuja la vaca y sus partes
    def render(self, camara, opMat, caras):
        # Calcula la matriz de transformación de la vaca
        matriz = OpMat3D.matriz_trs(
            self.x, self.y + self.subida, self.z,
            ry=self.rumbo + self.giro,
            sx=self.escala, sy=self.escala, sz=self.escala
        )

        opMat.push()                          # Guarda la matriz actual
        opMat.multiplicar(matriz)             # Aplica la transformación de la vaca

        for parte in self.partes:
            parte.recolectar_caras(camara, opMat, caras)

        # Gira la cola alrededor de su punto de unión
        px, py, pz = self.PIVOTE_COLA
        opMat.push()
        opMat.translate(px, py, pz)
        opMat.rotate_y(25.0 * math.sin(self.tiempo * self.vel_cola))
        opMat.translate(-px, -py, -pz)
        self.cola.recolectar_caras(camara, opMat, caras)
        opMat.pop()                           # Recupera la matriz de la vaca

        opMat.pop()                           # Recupera la matriz de la escena