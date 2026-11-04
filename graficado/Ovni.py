import math
import random

from Malla import Malla
from OpMat import OpMat3D

# Colores de relleno por zona
CASCO = (85, 90, 110)        # mitad de abajo del cuerpo
FILO = (60, 62, 78)          # franjas del ecuador (el borde del platillo)
CUBIERTA = (150, 155, 175)   # mitad de arriba del cuerpo
CUPULA = (90, 200, 230)
ALIEN_VERDE = (100, 235, 140)
ALIEN_NEGRO = (15, 15, 20)
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
    N_ESFERA = 20          # franjas de la semiesfera (finas, para el dibujo)
    SEGMENTOS_ESFERA = 64  # gajos de la semiesfera
    THETA_ALIEN = 90.0     # lado donde va el dibujo (θ = 90° es +Z del modelo)
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
        y_centro = self._altura_superficie(r)
        semiesfera = Malla.esfera(
            r, None, relleno=CUPULA,       # sin bordes: no tapan el dibujo
            segmentos=self.SEGMENTOS_ESFERA, anillos=self.N_ESFERA,
            lat_min=0.0, lat_max=90.0,
            centro=(0.0, y_centro, 0.0)
        )
        self._pintar_alien(semiesfera, y_centro, r)
        return semiesfera

    @staticmethod
    def _color_alien(u, v):
        """
        El dibujo, en coordenadas del lado de la cúpula visto de frente:
          u: horizontal, de -1 (izquierda) a 1 (derecha)
          v: vertical, de 0 (base de la cúpula) a 1 (polo)
        Devuelve el color de ese punto, o None si ahí no hay dibujo.
        """
        def elipse(cu, cv, ru, rv):
            return ((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2 <= 1.0

        # Ojos y boca (negro), encima de
        if elipse(-0.16, 0.62, 0.11, 0.085) or elipse(0.16, 0.62, 0.11, 0.085):
            return ALIEN_NEGRO
        if 0.41 <= v <= 0.47 and -0.18 <= u <= 0.14:
            return ALIEN_NEGRO

        # Silueta: cabeza + cuello + cuerpo
        def silueta(m):
            return (elipse(0.0, 0.57, 0.33 + m, 0.30 + m)        # cabeza
                    or (abs(u) <= 0.22 + m and v <= 0.36)         # cuello
                    or elipse(0.0, 0.0, 0.52 + m, 0.33 + m))      # cuerpo

        if silueta(0.0):
            return ALIEN_VERDE
        if silueta(0.07):               # contorno negro
            return ALIEN_NEGRO
        return None

    def _pintar_alien(self, semiesfera, y_centro, r):
        """
        Colorea las caras de la semiesfera que caen dentro del dibujo.
        Del centro de cada cara se recuperan sus coordenadas de la ecuación
        paramétrica de la esfera:
            θ = atan2(z, x)          φ = asin((y - y_centro) / r)
        y el dibujo se proyecta de frente sobre el lado θ = THETA_ALIEN:
            u = -cos(φ) · sin(θ - THETA_ALIEN)        v = sin(φ)
        """
        pts = semiesfera.points
        for i, cara in enumerate(semiesfera.caras):
            n = len(cara)
            cx = sum(pts[0, j] for j in cara) / n
            cy = sum(pts[1, j] for j in cara) / n
            cz = sum(pts[2, j] for j in cara) / n

            theta = math.atan2(cz, cx)
            phi = math.asin(max(-1.0, min(1.0, (cy - y_centro) / r)))

            dtheta = theta - math.radians(self.THETA_ALIEN)
            if math.cos(dtheta) <= 0:          # el otro lado: sin dibujo
                continue
            u = -math.cos(phi) * math.sin(dtheta)
            v = math.sin(phi)

            color = self._color_alien(u, v)
            if color is not None:
                semiesfera.rellenos[i] = color

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
    def altura_panza(self):
        """Altura (en el mundo) del polo de abajo del cuerpo, sin contar el flote."""
        return self.y_base - self.C * self.escala

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
        cuerpo, arriba = self.mallas

        # Cuerpo: sin flote ni inclinación, solo posición y escala -> T · S
        opMat.push()
        opMat.multiplicar(OpMat3D.matriz_trs(
            self.x, self.y_base, self.z,
            sx=self.escala, sy=self.escala, sz=self.escala
        ))
        cuerpo.recolectar_caras(camara, opMat, caras)

        # Parte de arriba: hereda la matriz del cuerpo y además gira sobre Y
        opMat.push()
        opMat.multiplicar(OpMat3D.matriz_trs(0.0, 0.0, 0.0, ry=self.giro))
        arriba.recolectar_caras(camara, opMat, caras)
        opMat.pop()                       # regresa a la matriz del cuerpo

        opMat.pop()                       # regresa a la matriz de la escena

        if self.luz_encendida:
            # Punta del rayo = polo de abajo del cuerpo
            px, py, pz = self.x, self.altura_panza(), self.z

            # La pirámide unitaria va de y=0 (punta) a y=-1 (base):
            # escalar sy = py hace que la base quede justo en el suelo (y = 0).
            # Gira sobre Y junto con la parte de arriba: T · Ry · S
            opMat.push()
            opMat.multiplicar(OpMat3D.matriz_trs(
                px, py, pz,
                ry=self.giro,
                sx=self.radio_rayo, sy=py, sz=self.radio_rayo
            ))
            self.rayo.recolectar_caras(camara, opMat, caras)
            opMat.pop()