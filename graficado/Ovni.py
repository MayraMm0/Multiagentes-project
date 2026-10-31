"""
    Agente OVNI.
    Modelado (dos mallas):
      1. Cuerpo: un ELIPSOIDE completo dado por la ecuación

             x²/9 + y²/9 + z²/1 = 1      (semiejes a = 3, b = 3, c = 1)

         En la ecuación el eje delgado es z (convención matemática: z hacia
         arriba). En este motor el eje vertical es Y, así que al pasarla al
         motor se intercambian y <-> z: el semieje delgado (1) queda vertical
         y el elipsoide queda acostado, como platillo.
      2. Parte de arriba, según FORMA_ARRIBA:
         - "esfera": semiesfera   x² + y² + z² = r²   sentada sobre el cuerpo.
         - "cubo":   un cubo sentado sobre el cuerpo.
      Cada franja tiene su color de relleno.
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
CASCO = (85, 90, 110)        # mitad de abajo del cuerpo
FILO = (60, 62, 78)          # franjas del ecuador (el borde del platillo)
CUBIERTA = (150, 155, 175)   # mitad de arriba del cuerpo
CUPULA = (90, 200, 230)
CUBO_CLARO = (150, 230, 250)
CUBO_MEDIO = (60, 160, 200)
CUBO_OSCURO = (40, 110, 150)

# Rayo de luz: colores con alfa (r, g, b, transparencia 0-255)
LUZ_LADOS = (255, 245, 150, 55)
LUZ_BASE = (255, 245, 150, 95)    # cuadro de luz en el suelo, más intenso


class Ovni:
    # --- Cuerpo: semiejes de la ecuación x²/A² + y²/B² + z²/C² = 1 ---
    A = 3.0     # semieje en x  (A² = 9)
    B = 3.0     # semieje en y  (B² = 9)
    C = 1.0     # semieje en z  (C² = 1), el delgado -> vertical en el motor
    N_CUERPO = 16          # franjas del cuerpo (de polo a polo)

    # --- Parte de arriba: "esfera" o "cubo" ---
    FORMA_ARRIBA = "esfera"
    RADIO_ESFERA = 1.3     # r de la ecuación x² + y² + z² = r²
    N_ESFERA = 10          # franjas de la semiesfera
    LADO_CUBO = 1.6

    def __init__(self, color, posicion=(0.0, 6.0, 0.0), escala=1.0,
                 limite=8.0, segmentos=32):
        # 1. Cuerpo. Malla.elipsoide recibe los semiejes en el orden del
        #    motor (x, y vertical, z):  x <- A,  y (vertical) <- C,  z <- B.
        mitad = self.N_CUERPO // 2
        colores_cuerpo = ([CASCO] * (mitad - 1) + [FILO]          # abajo
                          + [FILO] + [CUBIERTA] * (mitad - 1))     # arriba
        cuerpo = Malla.elipsoide(
            self.A, self.C, self.B, color,
            relleno=colores_cuerpo,
            segmentos=segmentos, anillos=self.N_CUERPO,
            lat_min=-90.0, lat_max=90.0
        )

        # 2. Parte de arriba
        if self.FORMA_ARRIBA == "cubo":
            arriba = self._cubo(color)
        else:
            arriba = self._semiesfera(color, segmentos)

        self.mallas = [cuerpo, arriba]

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
    def _altura_superficie(self, r):
        """
        Altura del cuerpo a una distancia r del eje vertical. De la ecuación
        del cuerpo (en el motor):  (r/A)² + (y/C)² = 1  ->  y = C·sqrt(1 - (r/A)²)
        """
        return self.C * math.sqrt(1.0 - (r / self.A) ** 2)

    def _semiesfera(self, color, segmentos):
        """
        Semiesfera x² + y² + z² = r² (latitud de 0° a 90°).
        Su base, un círculo de radio r, se apoya justo donde el cuerpo
        tiene ese mismo radio.
        """
        r = self.RADIO_ESFERA
        return Malla.esfera(
            r, color, relleno=CUPULA,
            segmentos=segmentos, anillos=self.N_ESFERA,
            lat_min=0.0, lat_max=90.0,
            centro=(0.0, self._altura_superficie(r), 0.0)
        )

    def _cubo(self, color):
        """
        Cubo centrado en el eje vertical. Su base se pone a la altura en la
        que sus esquinas (a distancia mitad·√2 del eje) tocan el cuerpo,
        para que no flote ni se hunda de más.
        """
        mitad = self.LADO_CUBO / 2
        y0 = self._altura_superficie(mitad * math.sqrt(2))
        # Un tono por cara (orden de Malla.caja: abajo, arriba, z0, z1, x0, x1)
        # para que se note el volumen y el giro.
        tonos = [CUBO_OSCURO, CUBO_CLARO, CUPULA, CUBO_MEDIO, CUBO_MEDIO, CUPULA]
        return Malla.caja(-mitad, mitad, y0, y0 + self.LADO_CUBO, -mitad, mitad,
                          color, tonos)

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
        for malla in self.mallas:
            malla.recolectar_caras(camara, opMat, caras)
        opMat.pop()

        if self.luz_encendida:
            # Punta del rayo = punto más bajo del casco, ya transformado
            # (así sigue pegada al casco aunque el ovni se incline).
            px, py, pz, _ = matriz_ovni @ (0.0, -self.C, 0.0, 1.0)   # polo de abajo del cuerpo

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