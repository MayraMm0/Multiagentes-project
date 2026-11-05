"""
    Agente VACA (modelo gráfico).
    Modelado: cuerpo, cabeza, hocico, cuernos, ubre, 4 patas y cola, con cajas
    rellenas. La vaca mira hacia +X y tiene las patas en y = 0.

    Dos formas de moverla:
      - Animaciones propias (mainVacas.py): quieta(), subir(), bajar(),
        mover(), cambiar_piso(). Cada una con su matriz colapsada.
      - Pose directa (main.py, conectado con AgentPy): pose() la coloca
        exactamente donde diga la lógica, frame por frame.
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

    ALTO_LOMO = 1.85       # altura del lomo: ahí se para la vaca de arriba en la pila

    # Subiendo
    VEL_SUBIDA = 1.0       # unidades por segundo
    VEL_GIRO = 120.0       # grados por segundo (sobre el eje Y)
    ALTURA_MAX = 4.0       # hasta dónde sube
    # Bajando
    VEL_BAJADA = 1.5       # unidades por segundo

    ESCALA_MIN = 0.4
    VEL_CAMINAR = 3.0

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

        # Animación de la cola (cada vaca con su propio desfase)
        self.tiempo = random.uniform(0, 10)
        self.vel_cola = random.uniform(3.0, 5.0)

        # Empieza quieta en el suelo
        self.subida = 0.0          # cuánto está sobre el suelo
        self.giro = 0.0            # grados extra sobre Y mientras sube
        self.quieta()

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

    def _escala_actual(self):
        t = self.subida / self.ALTURA_MAX  # 0 en el suelo, 1 arriba
        return self.escala * (1 - t) + self.escala * self.ESCALA_MIN * t

    # Cambios de fase
    def quieta(self):
        """Detiene a la vaca donde esté. Su matriz se calcula una sola vez aquí."""
        self.estado = 'quieta'
        self.rumbo = (self.rumbo + self.giro) % 360.0  # conservar hacia dónde quedó viendo
        self.giro = 0.0
        self.matriz_quieta = OpMat3D.matriz_trs(
            self.x, self.y + self.subida, self.z,  # ojo: + subida
            ry=self.rumbo,
            sx=self._escala_actual(), sy=self._escala_actual(), sz=self._escala_actual()

        )


    def subir(self):
        if self.estado == 'subiendo' or self.subida >= self.ALTURA_MAX:
            return                      # ya va subiendo, o ya está arriba
        self.estado = 'subiendo'
        self.rumbo = (self.rumbo + self.giro) % 360.0
        self.giro = 0.0

    def bajar(self):
        # Se queda con la orientación que tenía al terminar de subir,
        # así no "salta" al cambiar de fase.
        if self.subida <= 0.0:
            return
        self.estado = 'bajando'
        self.rumbo = (self.rumbo + self.giro) % 360.0
        self.giro = 0.0

    def pose(self, x, z, altura, giro=0.0, escala=None):
        """Coloca la vaca directamente: patas a la altura `altura`, girada
        `giro` grados extra sobre Y y con la escala indicada.
        Matriz colapsada: T(x, altura, z) · Ry(rumbo + giro) · S."""
        e = self.escala if escala is None else escala
        self.x, self.z = x, z
        self.estado = 'pose'
        self.matriz_pose = OpMat3D.matriz_trs(
            x, altura, z,
            ry=self.rumbo + giro,
            sx=e, sy=e, sz=e
        )

    def cambiar_piso(self, nuevo_y):
        """Cambia sobre qué está parada, sin moverla en el mundo."""
        altura = self.y + self.subida       # dónde está ahora
        self.y = nuevo_y
        self.subida = altura - nuevo_y      # lo que le falta por bajar hasta su nuevo piso

    def mover(self, dx, dz):
        self.x += dx
        self.z += dz
        if self.estado == 'quieta':
            self.quieta()


    # Movimiento
    def update(self, dt):
        self.tiempo += dt

        if self.estado == 'subiendo':
            # Trasladar hacia arriba y rotar sobre Y
            self.subida += self.VEL_SUBIDA * dt
            self.giro = (self.giro + self.VEL_GIRO * dt) % 360.0
            if self.subida >= self.ALTURA_MAX:
                self.subida = self.ALTURA_MAX
                self.quieta()

        elif self.estado == 'bajando':
            # Descender sin girar
            self.subida -= self.VEL_BAJADA * dt
            if self.subida <= 0.0:
                self.subida = 0.0
                self.quieta()

    def _matriz(self):
        """La matriz colapsada de la fase actual."""

        if self.estado == 'quieta':
            return self.matriz_quieta          # precalculada al entrar a la fase

        if self.estado == 'pose':
            return self.matriz_pose            # la puso main.py con pose()

        if self.estado == 'subiendo':
            # T(x, y + subida, z) · Ry(rumbo + giro) · S
            return OpMat3D.matriz_trs(
                self.x, self.y + self.subida, self.z,
                ry=self.rumbo + self.giro,
                sx=self._escala_actual(), sy=self._escala_actual(), sz=self._escala_actual()
            )

        # 'bajando': T(x, y + subida, z) · Ry(rumbo) · S
        return OpMat3D.matriz_trs(
            self.x, self.y + self.subida, self.z,
            ry=self.rumbo,
            sx=self._escala_actual(), sy=self._escala_actual(), sz=self._escala_actual()
        )


    # Dibujo (recolecta caras; main.py las ordena y dibuja)
    def render(self, camara, opMat, caras):
        opMat.push()                          # guarda la matriz de la escena
        opMat.multiplicar(self._matriz())     # colocar la vaca según su fase

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