"""
    Agente OVNI (AgentPy).

    Ciclo de cada paso:  percibir -> decidir y actuar -> marcar lo revisado.

    Estados:
      explorando    -> recorre el tablero hacia su objetivo de exploración.
      yendo_a_vaca  -> detectó una vaca en una celda vecina y la reclamó.
      abduciendo    -> está sobre la vaca; la vaca sube (PASOS_ABDUCCION).
      transportando -> lleva la vaca al depósito por la ruta más corta.
      entregando    -> está en el depósito; la vaca baja a la pila (PASOS_ENTREGA).

    Reglas de movimiento:
      - Solo en las cuatro direcciones cardinales, una celda por paso.
      - Si el siguiente paso sigue acercando a su destino, conserva la
        dirección: así cada trayecto es una "L" con a lo más un giro.
      - Explorando, sigue derecho mientras eso le muestre celdas que nadie
        ha revisado. Si no, va hacia la celda MENOS REVISADA por el equipo,
        cerca de él, sin girar de más y lejos de los demás OVNIS.
      - Detecta vacas solo en su celda y en sus cuatro celdas vecinas.
"""
import agentpy as ap

DIRECCIONES = [(1, 0), (0, 1), (-1, 0), (0, -1)]   # derecha, abajo, izquierda, arriba


def distancia(a, b):
    """Distancia Manhattan: número de pasos cardinales entre dos celdas."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class AgenteOvni(ap.Agent):
    # Pesos para elegir a dónde explorar (ver elegir_objetivo)
    PESO_GIRO = 3.0          # castigo por tener que girar para llegar
    PESO_SEPARACION = 0.6    # premio por alejarse de los demás OVNIS

    def setup(self):
        self.direccion = (1, 0)
        self.estado = "explorando"
        self.carga = None              # id de la vaca que lleva
        self.vaca_reclamada = None     # id de la vaca a la que va
        self.objetivo = None           # celda a la que va a explorar
        self.revisiones_objetivo = 0   # revisiones del objetivo cuando lo eligió
        self.fin_espera = 0            # paso en que termina la abducción o la entrega
        self.celda_anterior = None
        self.movimientos = 0
        self.vacas_entregadas = 0

        # Lo que percibe en el paso actual
        self.kb = {
            "celda": None,
            "vaca_aqui": 0,            # vaca en su celda que puede recoger
            "vacas_vecinas": [],       # [(direccion, celda, id_vaca)] que puede recoger
            "en_deposito": False,
        }

    # ------------------------------------------------------------------
    # Percepción
    # ------------------------------------------------------------------
    def posicion(self):
        return tuple(self.model.grid.positions[self])

    def percibir(self):
        modelo = self.model
        x, y = self.posicion()

        aqui = modelo.vaca_en((x, y))
        vecinas = []
        for d in DIRECCIONES:
            celda = (x + d[0], y + d[1])
            id_vaca = modelo.vaca_en(celda)
            if id_vaca and modelo.libre_para(id_vaca, self.id):
                vecinas.append((d, celda, id_vaca))

        self.kb.update(
            celda=(x, y),
            vaca_aqui=aqui,
            vacas_vecinas=vecinas,
            en_deposito=(x, y) == modelo.deposito,
        )

    def marcar_revisadas(self):
        """Suma una revisión a su celda y a sus vecinas.
        Una celda con una vaca sin reclamar NO se marca: así sigue atrayendo
        a los OVNIS libres hasta que alguien la recoja."""
        modelo = self.model
        x, y = self.posicion()
        for dx, dy in [(0, 0)] + DIRECCIONES:
            celda = (x + dx, y + dy)
            if not modelo.dentro(celda):
                continue
            id_vaca = modelo.vaca_en(celda)
            if id_vaca and id_vaca not in modelo.reclamos:
                continue
            modelo.revisiones[celda] += 1

    # ------------------------------------------------------------------
    # Movimiento
    # ------------------------------------------------------------------
    def direcciones_hacia(self, destino):
        """Direcciones cardinales que acercan al destino."""
        x, y = self.posicion()
        opciones = []
        if destino[0] > x:
            opciones.append((1, 0))
        elif destino[0] < x:
            opciones.append((-1, 0))
        if destino[1] > y:
            opciones.append((0, 1))
        elif destino[1] < y:
            opciones.append((0, -1))
        return opciones

    def paso_hacia(self, destino):
        """Elige la dirección del siguiente paso hacia el destino."""
        opciones = self.direcciones_hacia(destino)
        if not opciones:
            return None
        if self.direccion in opciones:          # seguir derecho si sirve
            return self.direccion
        if len(opciones) == 1:
            return opciones[0]
        # Hay que girar: hacia la celda menos revisada; si empatan,
        # por el eje que falta recorrer más.
        x, y = self.posicion()
        rev = self.model.revisiones

        def clave(d):
            siguiente = (x + d[0], y + d[1])
            restante = abs(destino[0] - x) if d[0] else abs(destino[1] - y)
            return (rev[siguiente], -restante)

        return min(opciones, key=clave)

    def mover(self, direccion):
        x, y = self.posicion()
        self.model.grid.move_to(self, (x + direccion[0], y + direccion[1]))
        self.direccion = direccion
        self.movimientos += 1

    def avanzar_hacia(self, destino):
        direccion = self.paso_hacia(destino)
        if direccion is not None:
            self.mover(direccion)

    # ------------------------------------------------------------------
    # Exploración
    # ------------------------------------------------------------------
    def costo_giro(self, celda):
        """0 si puede empezar a ir hacia la celda sin girar,
        1 si tiene que girar a un lado, 2 si tiene que dar media vuelta."""
        opciones = self.direcciones_hacia(celda)
        if self.direccion in opciones:
            return 0
        atras = (-self.direccion[0], -self.direccion[1])
        if opciones == [atras]:
            return 2
        return 1

    def elegir_objetivo(self):
        modelo = self.model
        rev = modelo.revisiones
        posicion = self.posicion()

        # Celdas y objetivos de los demás OVNIS, para repartirse el tablero.
        otros = []
        for agente in modelo.agentes:
            if agente is not self:
                otros.append(agente.posicion())
                if agente.objetivo is not None:
                    otros.append(agente.objetivo)

        # Solo las celdas menos revisadas del tablero.
        minimo = rev.min()
        candidatas = [(x, y) for x in range(modelo.n) for y in range(modelo.n)
                      if rev[x, y] == minimo and (x, y) != posicion]
        if not candidatas:
            candidatas = [(x, y) for x in range(modelo.n) for y in range(modelo.n)
                          if (x, y) != posicion]

        def costo(celda):
            lejos_de_otros = min((distancia(celda, o) for o in otros), default=0)
            return (distancia(posicion, celda)         # cerca de él
                    + self.PESO_GIRO * self.costo_giro(celda)     # sin girar de más
                    - self.PESO_SEPARACION * lejos_de_otros   # lejos de los demás
                    + 0.01 * modelo.random.random())   # desempate

        self.objetivo = min(candidatas, key=costo)
        self.revisiones_objetivo = rev[self.objetivo]

    def celdas_nuevas_al_avanzar(self, direccion):
        """Cuántas celdas sin revisar vería si da un paso en esa dirección
        (la de enfrente y las dos de los lados de la celda a la que llega)."""
        modelo = self.model
        x, y = self.posicion()
        dx, dy = direccion
        llegada = (x + dx, y + dy)
        if not modelo.dentro(llegada):
            return 0
        vistas = [(llegada[0] + dx, llegada[1] + dy),      # enfrente
                  (llegada[0] + dy, llegada[1] + dx),      # un lado
                  (llegada[0] - dy, llegada[1] - dx)]      # el otro lado
        minimo = modelo.revisiones.min()
        return sum(1 for c in vistas
                   if modelo.dentro(c) and modelo.revisiones[c] == minimo)

    def explorar(self):
        self.estado = "explorando"
        rev = self.model.revisiones

        # Mientras seguir derecho le muestre celdas sin revisar, sigue derecho:
        # trayectorias largas y continuas, sin giros de más.
        if self.celdas_nuevas_al_avanzar(self.direccion) > 0:
            self.objetivo = None
            self.mover(self.direccion)
            return

        # Si no, va hacia la celda menos revisada que le convenga. Elige una
        # nueva si no tiene, si ya llegó, o si otro OVNI ya la revisó.
        if (self.objetivo is None
                or self.objetivo == self.posicion()
                or rev[self.objetivo] > self.revisiones_objetivo):
            self.elegir_objetivo()
        self.avanzar_hacia(self.objetivo)

    # ------------------------------------------------------------------
    # Decisión
    # ------------------------------------------------------------------
    def reclamar(self, id_vaca):
        reclamos = self.model.reclamos
        if self.vaca_reclamada is not None and reclamos.get(self.vaca_reclamada) == self.id:
            del reclamos[self.vaca_reclamada]
        reclamos[id_vaca] = self.id
        self.vaca_reclamada = id_vaca

    def buscar_vaca(self):
        """Decide qué hacer si está libre. Devuelve True si ya actuó."""
        modelo = self.model
        kb = self.kb

        # 1. Está encima de una vaca: la recoge. Si otro la había reclamado
        #    pero todavía no llega, se la queda (no tiene caso pasarle encima).
        if kb["vaca_aqui"]:
            self.reclamar(kb["vaca_aqui"])
            self.carga = kb["vaca_aqui"]
            self.vaca_reclamada = None
            self.fin_espera = modelo.iniciar_abduccion(self.carga, self.id)
            self.estado = "abduciendo"
            return True

        # 2. Ya iba hacia una vaca que sigue siendo suya.
        if self.vaca_reclamada is not None:
            info = modelo.vacas_estado[self.vaca_reclamada]
            if (modelo.reclamos.get(self.vaca_reclamada) == self.id
                    and info["estado"] == "suelo"):
                self.estado = "yendo_a_vaca"
                self.avanzar_hacia(info["posicion"])
                return True
            self.vaca_reclamada = None          # otro se la quedó

        # 3. Ve una vaca libre en una celda vecina: la reclama y va por ella
        #    (primero la que está de frente, para no girar).
        if kb["vacas_vecinas"]:
            vecinas = sorted(kb["vacas_vecinas"], key=lambda v: v[0] != self.direccion)
            direccion, _, id_vaca = vecinas[0]
            self.reclamar(id_vaca)
            self.estado = "yendo_a_vaca"
            self.mover(direccion)
            return True

        return False

    def step(self):
        modelo = self.model
        self.celda_anterior = self.posicion()
        self.percibir()

        # La vaca está subiendo: espera a que llegue al OVNI.
        if self.estado == "abduciendo":
            if modelo.pasos < self.fin_espera:
                return
            modelo.terminar_abduccion(self.carga)
            self.estado = "transportando"

        # La vaca está bajando a la pila: espera a que llegue.
        if self.estado == "entregando":
            if modelo.pasos < self.fin_espera:
                return
            modelo.terminar_entrega(self.carga)
            self.carga = None
            self.vacas_entregadas += 1
            self.objetivo = None
            self.estado = "explorando"

        if self.estado == "transportando":
            if self.kb["en_deposito"]:
                self.fin_espera = modelo.iniciar_entrega(self.carga)
                self.estado = "entregando"
            else:
                self.avanzar_hacia(modelo.deposito)
        elif not self.buscar_vaca():
            self.explorar()

        self.marcar_revisadas()

    # ------------------------------------------------------------------
    # Para la parte gráfica
    # ------------------------------------------------------------------
    def estado_visual(self):
        return {
            "id": self.id,
            "celda": self.posicion(),
            "celda_anterior": self.celda_anterior or self.posicion(),
            "direccion": self.direccion,
            "carga": self.carga,
            "estado": self.estado,
        }
