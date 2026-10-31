import math
import random

from Malla import Malla
from OpMat import OpMat3D

# Colores del cuerpo y la parte superior
CASCO = (85, 90, 110)        # Parte inferior
FILO = (60, 62, 78)          # Borde del platillo
CUBIERTA = (150, 155, 175)   # Parte superior
CUPULA = (90, 200, 230)
CUBO_CLARO = (150, 230, 250)
CUBO_MEDIO = (60, 160, 200)
CUBO_OSCURO = (40, 110, 150)

# Colores del rayo de luz con transparencia
LUZ_LADOS = (255, 245, 150, 55)
LUZ_BASE = (255, 245, 150, 95)    # Luz en el suelo


class Ovni:
    # Dimensiones del cuerpo
    A = 3.0     # Semieje en X
    B = 3.0     # Semieje en Y
    C = 1.0     # Semieje vertical
    N_CUERPO = 16

    # Forma de la parte superior
    FORMA_ARRIBA = "esfera"
    RADIO_ESFERA = 1.3
    N_ESFERA = 10
    LADO_CUBO = 1.6

    def __init__(self, color, posicion=(0.0, 6.0, 0.0), escala=1.0,
                 limite=8.0, segmentos=32):
        # Construye el cuerpo del ovni
        mitad = self.N_CUERPO // 2
        colores_cuerpo = ([CASCO] * (mitad - 1) + [FILO]
                          + [FILO] + [CUBIERTA] * (mitad - 1))
        cuerpo = Malla.elipsoide(
            self.A, self.C, self.B, color,
            relleno=colores_cuerpo,
            segmentos=segmentos, anillos=self.N_CUERPO,
            lat_min=-90.0, lat_max=90.0
        )

        # Construye la parte superior
        if self.FORMA_ARRIBA == "cubo":
            arriba = self._cubo(color)
        else:
            arriba = self._semiesfera(color, segmentos)

        self.mallas = [cuerpo, arriba]

        # Crea el rayo de luz sin bordes
        self.rayo = Malla.piramide(None, [LUZ_LADOS] * 4 + [LUZ_BASE])
        self.rayo.culling = False
        self.radio_rayo = 1.8
        self.luz_encendida = True

        self.escala = escala
        self.limite = limite

        self.x, self.y_base, self.z = posicion
        self.vx = 0.0
        self.vz = 0.0
        self.velocidad = 3.5
        self.destino = self._nuevo_destino()

        self.giro = 0.0
        self.vel_giro = 60.0
        self.tiempo = 0.0

    # Modelado
    def _altura_superficie(self, r):
        # Calcula la altura del cuerpo según la distancia al centro
        return self.C * math.sqrt(1.0 - (r / self.A) ** 2)

    def _semiesfera(self, color, segmentos):
        # Coloca la semiesfera sobre el cuerpo
        r = self.RADIO_ESFERA
        return Malla.esfera(
            r, color, relleno=CUPULA,
            segmentos=segmentos, anillos=self.N_ESFERA,
            lat_min=0.0, lat_max=90.0,
            centro=(0.0, self._altura_superficie(r), 0.0)
        )

    def _cubo(self, color):
        # Coloca el cubo sobre el cuerpo
        mitad = self.LADO_CUBO / 2
        y0 = self._altura_superficie(mitad * math.sqrt(2))
        # Asigna un color a cada cara
        tonos = [CUBO_OSCURO, CUBO_CLARO, CUPULA, CUBO_MEDIO, CUBO_MEDIO, CUPULA]
        return Malla.caja(-mitad, mitad, y0, y0 + self.LADO_CUBO, -mitad, mitad,
                          color, tonos)

    # Movimiento
    def alternar_luz(self):
        self.luz_encendida = not self.luz_encendida

    def _nuevo_destino(self):
        l = self.limite
        return (random.uniform(-l, l), random.uniform(-l, l))

    def update(self, delta_time):
        self.tiempo += delta_time
        self.giro = (self.giro + self.vel_giro * delta_time) % 360.0

        # Calcula la distancia hasta el destino
        dx = self.destino[0] - self.x
        dz = self.destino[1] - self.z
        distancia = math.hypot(dx, dz)

        if distancia < 0.5:
            self.destino = self._nuevo_destino()
            dx = self.destino[0] - self.x
            dz = self.destino[1] - self.z
            distancia = math.hypot(dx, dz)

        # Ajusta la velocidad para cambiar de dirección suavemente
        vx_deseada = dx / distancia * self.velocidad
        vz_deseada = dz / distancia * self.velocidad
        suavizado = min(1.0, 2.5 * delta_time)
        self.vx += (vx_deseada - self.vx) * suavizado
        self.vz += (vz_deseada - self.vz) * suavizado

        self.x += self.vx * delta_time
        self.z += self.vz * delta_time

    # Dibujo
    def render(self, camara, opMat, caras):
        flote = 0.35 * math.sin(self.tiempo * 2.0)

        # Inclina el ovni según la dirección del movimiento
        inclina_z = -self.vx * 2.5
        inclina_x = self.vz * 2.5

        # Calcula las transformaciones en una sola matriz
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
            # Calcula la posición de la punta del rayo
            px, py, pz, _ = matriz_ovni @ (0.0, -self.C, 0.0, 1.0)

            # Ajusta el rayo para que llegue hasta el suelo
            opMat.push()
            opMat.multiplicar(OpMat3D.matriz_trs(
                px, py, pz,
                ry=self.giro,
                sx=self.radio_rayo, sy=py, sz=self.radio_rayo
            ))
            self.rayo.recolectar_caras(camara, opMat, caras)
            opMat.pop()