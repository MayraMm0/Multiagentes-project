"""
    Agente VACA.
    Modelado:
      Cuerpo, cabeza, hocico, cuernos, cola, ubre y 4 patas, todo con cajas
      rellenas. La vaca mira hacia +X en coordenadas de modelo.
    Posición:
      Aparece en un punto aleatorio del campo, con una orientación aleatoria.
    Movimiento:
      Se traslada hacia arriba mientras rota sobre el eje Y. Al llegar a
      ALTURA_MAX vuelve al suelo y empieza otra vez. También mueve la cola
      (ejemplo de push/pop).
    Matrices (colapsadas con OpMat3D.matriz_trs):
      T(x, y + subida, z) · Ry(rumbo + giro) · S se calcula cada frame en una
      sola fórmula. No necesita pivote: el eje Y del modelo ya pasa por el
      centro de la vaca.
"""
import math
import random

from Malla import Malla
from OpMat import OpMat3D

# Colores de relleno
BLANCO = (235, 232, 225)
ROSA = (240, 160, 185)
HUESO = (215, 200, 160)
GRIS = (110, 105, 105)


class Vaca:
    # Punto donde la cola se une al cuerpo (pivote de su giro)
    PIVOTE_COLA = (-1.1, 1.75, 0.0)

    VEL_SUBIDA = 1.0       # unidades por segundo
    VEL_GIRO = 120.0       # grados por segundo (sobre el eje Y)
    ALTURA_MAX = 4.0       # al subir esto, regresa al suelo

    def __init__(self, color, posicion=None, limite=8.0, escala=1.0):
        self.escala = escala
        self.limite = limite

        # Si no se da posición, se elige una al azar dentro del campo
        # (con un margen de 1 unidad para que no quede en el borde).
        if posicion is None:
            margen = limite - 1.0
            posicion = (random.uniform(-margen, margen),
                        0.0,
                        random.uniform(-margen, margen))
        self.x, self.y, self.z = posicion

        # Orientación aleatoria: giro sobre el eje Y, en grados.
        self.rumbo = random.uniform(0, 360)

        # Subida y giro actuales (cada vaca empieza en un punto distinto
        # de la animación para que no vayan sincronizadas)
        self.subida = random.uniform(0, self.ALTURA_MAX)
        self.giro = 0.0

        # Animación de la cola (cada vaca con su propio desfase)
        self.tiempo = random.uniform(0, 10)
        self.vel_cola = random.uniform(3.0, 5.0)

        # --- Modelo (color = bordes, último argumento = relleno) ------
        self.partes = [
            Malla.caja(-1.1, 1.1, 0.95, 1.85, -0.5, 0.5, color, BLANCO),     # cuerpo
            Malla.caja(1.1, 1.75, 1.35, 2.05, -0.3, 0.3, color, BLANCO),     # cabeza
            Malla.caja(1.75, 1.95, 1.35, 1.7, -0.2, 0.2, color, ROSA),       # hocico
            Malla.caja(1.2, 1.3, 2.05, 2.3, -0.28, -0.2, color, HUESO),      # cuerno izq
            Malla.caja(1.2, 1.3, 2.05, 2.3, 0.2, 0.28, color, HUESO),        # cuerno der
            Malla.caja(-0.6, -0.2, 0.8, 0.95, -0.25, 0.25, color, ROSA),     # ubre
        ]

        # Patas: cajas verticales que van del suelo (y=0) a la base del cuerpo.
        # Cada tupla es (x, z) de la pata en coordenadas del modelo.
        posiciones_patas = [(0.8, 0.32), (0.8, -0.32), (-0.8, 0.32), (-0.8, -0.32)]
        for cx, cz in posiciones_patas:
            self.partes.append(
                Malla.caja(cx - 0.12, cx + 0.12, 0.0, 0.95, cz - 0.12, cz + 0.12,
                           color, GRIS)
            )

        # La cola va aparte porque tiene su propio movimiento
        self.cola = Malla.caja(-1.35, -1.1, 1.4, 1.75, -0.04, 0.04, color, GRIS)

    # ------------------------------------------------------------------
    # Movimiento
    # ------------------------------------------------------------------
    def update(self, dt):
        self.tiempo += dt

        # Trasladar hacia arriba y rotar sobre Y
        self.subida += self.VEL_SUBIDA * dt
        self.giro = (self.giro + self.VEL_GIRO * dt) % 360.0

        # Al llegar arriba, vuelve al suelo
        if self.subida >= self.ALTURA_MAX:
            self.subida = 0.0

    # ------------------------------------------------------------------
    # Dibujo (recolecta caras; main.py las ordena y dibuja)
    # ------------------------------------------------------------------
    def render(self, camara, opMat, caras):
        # T(x, y + subida, z) · Ry(rumbo + giro) · S, en una sola fórmula
        matriz = OpMat3D.matriz_trs(
            self.x, self.y + self.subida, self.z,
            ry=self.rumbo + self.giro,
            sx=self.escala, sy=self.escala, sz=self.escala
        )

        opMat.push()                          # guarda la matriz de la escena
        opMat.multiplicar(matriz)             # colocar la vaca

        for parte in self.partes:
            parte.recolectar_caras(camara, opMat, caras)

        # Cola: giro alrededor de su pivote, solo afecta a la cola
        px, py, pz = self.PIVOTE_COLA
        opMat.push()
        opMat.translate(px, py, pz)
        opMat.rotate_y(25.0 * math.sin(self.tiempo * self.vel_cola))
        opMat.translate(-px, -py, -pz)
        self.cola.recolectar_caras(camara, opMat, caras)
        opMat.pop()                           # regresa a la matriz de la vaca

        opMat.pop()                           # regresa a la matriz de la escena