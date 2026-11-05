"""
    Modelo del mundo (AgentPy).

    Tablero de N x N celdas. Celda (x, y): x = columna (0 izquierda),
    y = fila (0 arriba). El depósito está en la esquina inferior derecha.

    Información compartida por el equipo de OVNIS:
      revisiones[x, y] -> cuántas veces alguien pasó por la celda o junto a
                          ella. Sirve para explorar primero lo menos revisado.
      reclamos         -> {id_vaca: id_agente}. Una vaca reclamada solo la
                          recoge su OVNI; así dos no van por la misma.
      objetivos        -> {id_agente: celda} a dónde va a explorar cada uno;
                          sirve para que se repartan el tablero.

    Tiempo: la abducción y la entrega duran un número fijo de pasos. La parte
    gráfica usa `inicio` y `fin` de cada vaca para que su animación termine
    justo cuando la lógica pasa al siguiente estado.
"""
import numpy as np
import agentpy as ap

from agente.AgenteOvni import AgenteOvni

PASOS_ABDUCCION = 3      # pasos que tarda la vaca en subir hasta el OVNI
PASOS_ENTREGA = 2        # pasos que tarda en bajar a la pila
ALTO_PILA = 1.85         # altura del lomo de una vaca (cada nivel de la pila)


class MundoModelo(ap.Model):

    def setup(self):
        n = self.p.tamano
        cantidad_agentes = self.p.cantidad_agentes
        cantidad_vacas = self.p.cantidad_vacas

        if cantidad_agentes + cantidad_vacas > n * n - 1:
            raise ValueError("No hay suficientes celdas para los OVNIS y las vacas")

        # Semilla opcional para repetir exactamente una corrida. AgentPy solo
        # la aplica con model.run(); aquí se llama a step() a mano.
        if "seed" in self.p:
            self.random.seed(self.p.seed)

        self.n = n
        self.deposito = (n - 1, n - 1)
        self.grid = ap.Grid(self, (n, n))
        self.grid.add_field("vacas", np.zeros((n, n), dtype=int))

        self.pasos = 0
        self.total_entregadas = 0
        self.terminado = False

        self.revisiones = np.zeros((n, n), dtype=int)
        self.reclamos = {}
        self.objetivos = {}

        # Posiciones iniciales aleatorias y distintas (sin usar el depósito).
        celdas = [(x, y) for x in range(n) for y in range(n) if (x, y) != self.deposito]
        self.random.shuffle(celdas)
        posiciones_vacas = celdas[:cantidad_vacas]
        posiciones_ovnis = celdas[cantidad_vacas:cantidad_vacas + cantidad_agentes]

        # Estado de cada vaca, vinculado por id con su modelo gráfico.
        self.vacas_estado = {}
        for id_vaca, posicion in enumerate(posiciones_vacas, start=1):
            self.grid.vacas[posicion] = id_vaca
            self.vacas_estado[id_vaca] = {
                "id": id_vaca,
                "posicion": posicion,
                "estado": "suelo",     # suelo, subiendo, transportada, bajando, depositada
                "agente": None,
                "inicio": 0,           # paso en que empezó la animación actual
                "fin": 0,              # paso en que termina
                "nivel": 0.0,          # altura en la pila
            }

        self.agentes = ap.AgentList(self, cantidad_agentes, AgenteOvni)
        self.grid.add_agents(self.agentes, posiciones_ovnis)
        for agente in self.agentes:
            agente.direccion = self.random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
            agente.marcar_revisadas()

    # ------------------------------------------------------------------
    # Paso de la simulación
    # ------------------------------------------------------------------
    def step(self):
        if self.terminado:
            return

        # Cada OVNI percibe, decide y actúa en orden aleatorio. Al ser uno
        # tras otro, un reclamo hecho por uno ya lo ve el siguiente.
        for agente in self.agentes.shuffle():
            agente.step()

        self.pasos += 1
        if self.vacas_estado and self.total_entregadas == len(self.vacas_estado):
            self.terminado = True

    # ------------------------------------------------------------------
    # Utilidades del tablero
    # ------------------------------------------------------------------
    def dentro(self, celda):
        return 0 <= celda[0] < self.n and 0 <= celda[1] < self.n

    def vaca_en(self, celda):
        """Id de la vaca en el suelo de esa celda, o 0 si no hay."""
        return int(self.grid.vacas[celda]) if self.dentro(celda) else 0

    def libre_para(self, id_vaca, id_agente):
        """La vaca no está reclamada, o la reclamó este mismo agente."""
        return self.reclamos.get(id_vaca, id_agente) == id_agente

    # ------------------------------------------------------------------
    # Ciclo de vida de una vaca
    # ------------------------------------------------------------------
    def iniciar_abduccion(self, id_vaca, id_agente):
        info = self.vacas_estado[id_vaca]
        self.grid.vacas[info["posicion"]] = 0          # ya no está en el suelo
        self.reclamos.pop(id_vaca, None)
        info.update(estado="subiendo", agente=id_agente,
                    inicio=self.pasos + 1, fin=self.pasos + 1 + PASOS_ABDUCCION)
        return info["fin"]

    def terminar_abduccion(self, id_vaca):
        self.vacas_estado[id_vaca]["estado"] = "transportada"

    def iniciar_entrega(self, id_vaca):
        info = self.vacas_estado[id_vaca]
        # Nivel en la pila: cuántas vacas ya están (o van) en el depósito.
        en_pila = sum(1 for v in self.vacas_estado.values()
                      if v["estado"] in ("bajando", "depositada"))
        info.update(estado="bajando", posicion=self.deposito,
                    inicio=self.pasos + 1, fin=self.pasos + 1 + PASOS_ENTREGA,
                    nivel=en_pila * ALTO_PILA)
        return info["fin"]

    def terminar_entrega(self, id_vaca):
        info = self.vacas_estado[id_vaca]
        info.update(estado="depositada", agente=None)
        self.total_entregadas += 1

    # ------------------------------------------------------------------
    # Consultas para la parte gráfica
    # ------------------------------------------------------------------
    def estados_vacas(self):
        return [dict(info) for info in self.vacas_estado.values()]

    def estados_agentes(self):
        return [agente.estado_visual() for agente in self.agentes]
