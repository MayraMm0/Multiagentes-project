"""
    Agente OVNI.
    Modelado:
      Superficie de revolución con el perfil:
      casco inferior curvo -> borde (filo) del disco -> cubierta superior que
      sube suavemente -> collar -> cúpula semiesférica con meridianos
      que convergen en el polo. Cada franja tiene su color de relleno.
      Rayo de luz: pirámide translúcida de la panza del ovni al suelo
      (se prende y apaga con alternar_luz()).
    Movimiento:
      - Patrulla entre puntos de paso aleatorios sobre el campo.
      - Flota (sube y baja) y gira sobre su eje.
      - Se inclina un poco hacia donde avanza.
    Optimización:
      T · Rz · Rx · Ry · S se calcula con una sola fórmula cerrada
      (OpMat3D.matriz_trs) en vez de 5 multiplicaciones de matrices 4x4.
"""
import math
import random

from Malla import Malla
from OpMat import OpMat3D

# Colores de relleno por zona
CASCO = (85, 90, 110)
FILO = (60, 62, 78)
CUBIERTA = (150, 155, 175)
COLLAR = (55, 55, 70)
CUPULA = (90, 200, 230)

# Rayo de luz: colores con alfa (r, g, b, transparencia 0-255)
LUZ_LADOS = (255, 245, 150, 55)
LUZ_BASE = (255, 245, 150, 95)    # cuadro de luz en el suelo, más intenso


class Ovni:
    # Medidas del modelo (en unidades de modelo, antes de escalar)
    RADIO = 5.0          # radio del disco
    PROFUNDIDAD = 1.35   # qué tan hondo es el casco inferior
    RADIO_COLLAR = 2.5   # donde termina el disco y empieza la cúpula
    ALTO_CUBIERTA = 0.5  # altura de la cubierta en el collar
    RADIO_CUPULA = 2.3
    ALTO_CUPULA = 1.9

    N_CASCO = 11
    N_CUBIERTA = 7
    N_CUPULA = 10

    def __init__(self, color, posicion=(0.0, 6.0, 0.0), escala=0.6,
                 limite=8.0, segmentos=32):
        self.malla = Malla.revolucion(self._perfil(), segmentos, color,
                                      self._colores_franjas())

        # Rayo de luz: pirámide translúcida sin bordes (color de borde None).
        # Sin culling: al ser translúcida, también se ven sus caras de atrás.
        self.rayo = Malla.piramide(None, [LUZ_LADOS] * 4 + [LUZ_BASE])
        self.rayo.culling = False
        self.radio_rayo = 1.8           # medio ancho de la base, en el suelo
        self.luz_encendida = True

        self.escala = escala
        self.limite = limite            # el ovni se mueve en [-limite, limite]

        self.x, self.y_base, self.z = posicion
        self.vx = 0.0
        self.vz = 0.0
        self.velocidad = 3.5            # unidades por segundo
        self.destino = self._nuevo_destino()

        self.giro = 0.0                 # grados de giro sobre su eje
        self.vel_giro = 60.0            # grados por segundo
        self.tiempo = 0.0               # para el flote

    # ------------------------------------------------------------------
    # Modelado
    # ------------------------------------------------------------------
    def _perfil(self):
        """Lista de (radio, y) de abajo (centro del casco) hasta el polo de la cúpula."""
        R = self.RADIO
        perfil = []

        # 1. Casco inferior: cuarto de elipse, del centro de abajo hasta el borde
        for k in range(self.N_CASCO + 1):
            t = (math.pi / 2) * k / self.N_CASCO
            perfil.append((R * math.sin(t), -self.PROFUNDIDAD * math.cos(t)))

        # 2. Cubierta superior: del borde hacia el collar, subiendo suave
        ancho = R - self.RADIO_COLLAR
        for k in range(1, self.N_CUBIERTA + 1):
            r = R - ancho * k / self.N_CUBIERTA
            u = (r - self.RADIO_COLLAR) / ancho          # 1 en el borde, 0 en el collar
            perfil.append((r, self.ALTO_CUBIERTA * (1 - u * u)))

        # 3. Collar: un pequeño escalón entre el disco y la cúpula
        perfil.append((self.RADIO_CUPULA, self.ALTO_CUBIERTA + 0.12))

        # 4. Cúpula semiesférica (el último punto es el polo, radio 0)
        y0 = self.ALTO_CUBIERTA + 0.12
        for k in range(1, self.N_CUPULA + 1):
            a = (math.pi / 2) * k / self.N_CUPULA
            perfil.append((self.RADIO_CUPULA * math.cos(a),
                           y0 + self.ALTO_CUPULA * math.sin(a)))

        return perfil

    def _colores_franjas(self):
        """Un color por franja (entre niveles consecutivos del perfil)."""
        return ([CASCO] * (self.N_CASCO - 1) + [FILO]   # casco, la última franja es el filo
                + [CUBIERTA] * self.N_CUBIERTA
                + [COLLAR]
                + [CUPULA] * self.N_CUPULA)

    # ------------------------------------------------------------------
    # Movimiento
    # ------------------------------------------------------------------
    def alternar_luz(self):
        self.luz_encendida = not self.luz_encendida

    def _nuevo_destino(self):
        l = self.limite
        return (random.uniform(-l, l), random.uniform(-l, l))

    def update(self, delta_time):
        self.tiempo += delta_time
        self.giro = (self.giro + self.vel_giro * delta_time) % 360.0

        # Avanzar hacia el destino actual
        dx = self.destino[0] - self.x
        dz = self.destino[1] - self.z
        distancia = math.hypot(dx, dz)

        if distancia < 0.5:
            self.destino = self._nuevo_destino()
            dx = self.destino[0] - self.x
            dz = self.destino[1] - self.z
            distancia = math.hypot(dx, dz)

        # Velocidad deseada y suavizado (para que no gire en seco)
        vx_deseada = dx / distancia * self.velocidad
        vz_deseada = dz / distancia * self.velocidad
        suavizado = min(1.0, 2.5 * delta_time)
        self.vx += (vx_deseada - self.vx) * suavizado
        self.vz += (vz_deseada - self.vz) * suavizado

        self.x += self.vx * delta_time
        self.z += self.vz * delta_time

    # ------------------------------------------------------------------
    # Dibujo (recolecta caras; main.py las ordena y dibuja)
    # ------------------------------------------------------------------
    def render(self, camara, opMat, caras):
        flote = 0.35 * math.sin(self.tiempo * 2.0)

        # Inclinación hacia donde avanza (mover en +x -> cabecea sobre z negativo)
        inclina_z = -self.vx * 2.5
        inclina_x = self.vz * 2.5

        # Equivale a: translate -> rotate_z -> rotate_x -> rotate_y -> scale,
        # pero en una sola matriz calculada con la fórmula cerrada.
        matriz_ovni = OpMat3D.matriz_trs(
            self.x, self.y_base + flote, self.z,
            rx=inclina_x, ry=self.giro, rz=inclina_z,
            sx=self.escala, sy=self.escala, sz=self.escala
        )
        opMat.push()
        opMat.multiplicar(matriz_ovni)
        self.malla.recolectar_caras(camara, opMat, caras)
        opMat.pop()

        if self.luz_encendida:
            # Punta del rayo = punto más bajo del casco, ya transformado
            # (así sigue pegada al casco aunque el ovni se incline).
            px, py, pz, _ = matriz_ovni @ (0.0, -self.PROFUNDIDAD, 0.0, 1.0)

            # La pirámide unitaria va de y=0 (punta) a y=-1 (base):
            # escalar sy = py hace que la base quede justo en el suelo (y = 0).
            # Gira junto con el ovni, pero sin inclinarse.
            opMat.push()
            opMat.multiplicar(OpMat3D.matriz_trs(
                px, py, pz,
                ry=self.giro,
                sx=self.radio_rayo, sy=py, sz=self.radio_rayo
            ))
            self.rayo.recolectar_caras(camara, opMat, caras)
            opMat.pop()