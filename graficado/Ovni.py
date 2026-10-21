"""
    Agente OVNI.
    Modelado:
      Superficie de revolución con el perfil:
      casco inferior curvo -> borde (filo) del disco -> cubierta superior que
      sube suavemente -> collar -> cúpula semiesférica con meridianos
      que convergen en el polo.
    Movimiento:
      - Patrulla entre puntos de paso aleatorios sobre el campo.
      - Flota (sube y baja) y gira sobre su eje.
      - Se inclina un poco hacia donde avanza.
"""
import math
import random
 
from Malla import Malla
 
 
class Ovni:
    # Medidas del modelo (en unidades de modelo, antes de escalar)
    RADIO = 5.0          # radio del disco
    PROFUNDIDAD = 1.35   # qué tan hondo es el casco inferior
    RADIO_COLLAR = 2.5   # donde termina el disco y empieza la cúpula
    ALTO_CUBIERTA = 0.5  # altura de la cubierta en el collar
    RADIO_CUPULA = 2.3
    ALTO_CUPULA = 1.9
 
    def __init__(self, color, posicion=(0.0, 6.0, 0.0), escala=0.6,
                 limite=8.0, segmentos=32):
        self.malla = Malla.revolucion(self._perfil(), segmentos, color)
 
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
        n_casco = 11
        for k in range(n_casco + 1):
            t = (math.pi / 2) * k / n_casco
            perfil.append((R * math.sin(t), -self.PROFUNDIDAD * math.cos(t)))
 
        # 2. Cubierta superior: del borde hacia el collar, subiendo suave
        n_cubierta = 7
        ancho = R - self.RADIO_COLLAR
        for k in range(1, n_cubierta + 1):
            r = R - ancho * k / n_cubierta
            u = (r - self.RADIO_COLLAR) / ancho          # 1 en el borde, 0 en el collar
            perfil.append((r, self.ALTO_CUBIERTA * (1 - u * u)))
 
        # 3. Collar: un pequeño escalón entre el disco y la cúpula
        perfil.append((self.RADIO_CUPULA, self.ALTO_CUBIERTA + 0.12))
 
        # 4. Cúpula semiesférica (el último punto es el polo, radio 0)
        n_cupula = 10
        y0 = self.ALTO_CUBIERTA + 0.12
        for k in range(1, n_cupula + 1):
            a = (math.pi / 2) * k / n_cupula
            perfil.append((self.RADIO_CUPULA * math.cos(a),
                           y0 + self.ALTO_CUPULA * math.sin(a)))
 
        return perfil
 
    # ------------------------------------------------------------------
    # Movimiento
    # ------------------------------------------------------------------
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
    # Dibujo
    # ------------------------------------------------------------------
    def render(self, superficie, camara, opMat):
        flote = 0.35 * math.sin(self.tiempo * 2.0)
 
        # Inclinación hacia donde avanza (mover en +x -> cabecea sobre z negativo)
        inclina_z = -self.vx * 2.5
        inclina_x = self.vz * 2.5
 
        # Orden: se escribe T, tilt, giro, escala (la escala se aplica primero al modelo)
        opMat.loadId()
        opMat.translate(self.x, self.y_base + flote, self.z)
        opMat.rotate_z(inclina_z)
        opMat.rotate_x(inclina_x)
        opMat.rotate_y(self.giro)
        opMat.scale(self.escala, self.escala, self.escala)
 
        self.malla.render(superficie, camara, opMat)
