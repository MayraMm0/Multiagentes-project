"""
    Agente VACA (versión estática).
    Modelado:
      Cuerpo, cabeza, hocico, cuernos, cola, ubre y 4 patas, todo con cajas.
      La vaca mira hacia +X en coordenadas de modelo.
    Posición:
      Aparece en un punto aleatorio del campo, con una orientación aleatoria.
      No se mueve (update no hace nada).
"""
import random

from Malla import Malla


class Vaca:
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

        # --- Modelo ---------------------------------------------------
        self.partes = [
            Malla.caja(-1.1, 1.1, 0.95, 1.85, -0.5, 0.5, color),      # cuerpo
            Malla.caja(1.1, 1.75, 1.35, 2.05, -0.3, 0.3, color),      # cabeza
            Malla.caja(1.75, 1.95, 1.35, 1.7, -0.2, 0.2, color),      # hocico
            Malla.caja(1.2, 1.3, 2.05, 2.3, -0.28, -0.2, color),      # cuerno izq
            Malla.caja(1.2, 1.3, 2.05, 2.3, 0.2, 0.28, color),        # cuerno der
            Malla.caja(-1.35, -1.1, 1.4, 1.75, -0.04, 0.04, color),   # cola
            Malla.caja(-0.6, -0.2, 0.8, 0.95, -0.25, 0.25, color),    # ubre
        ]

        # Patas: cajas verticales que van del suelo (y=0) a la base del cuerpo.
        # Cada tupla es (x, z) de la pata en coordenadas del modelo.
        posiciones_patas = [(0.8, 0.32), (0.8, -0.32), (-0.8, 0.32), (-0.8, -0.32)]
        for cx, cz in posiciones_patas:
            self.partes.append(
                Malla.caja(cx - 0.12, cx + 0.12, 0.0, 0.95, cz - 0.12, cz + 0.12, color)
            )

    # ------------------------------------------------------------------
    # Movimiento: ninguno por ahora (se mantiene el método para que main.py
    # pueda seguir llamando vaca.update(dt) sin cambios).
    # ------------------------------------------------------------------
    def update(self, dt):
        pass

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def render(self, superficie, camara, opMat):
        opMat.loadId()
        opMat.translate(self.x, self.y, self.z)   # colocar en el campo
        opMat.rotate_y(self.rumbo)                # orientación aleatoria
        opMat.scale(self.escala, self.escala, self.escala)

        for parte in self.partes:
            parte.render(superficie, camara, opMat)