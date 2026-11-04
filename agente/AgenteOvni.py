import agentpy as ap
import random

"""
Qué hace
    - Se mueve random (arriba, abajo, izq, der)
    - Si una de sus 4 opciones tiene vaca, la recoge
    - Si lleva carga (vaca), va hacia esquina y la suelta
    - No choca con otros agentes. 1. Decide -> reserva 2. Ejecuta -> se mueve
        para que ninguno vaya a la celda ni vaca del otro
        
Cómo funciona con Modelo
    - tamaño de mapa
    - model.grid -> con campo vacas por celda
    - model.esquina -> celda para soltar vacas
    - model.agentes -> todos los ovnis
    - model.reservas -> dict {celda: id_agente}, se vacía al inicio de cada paso
"""

# Dirección (dx, dy) -> rumbo en grados (para que lo use la parte visual después)
RUMBOS = {(1, 0): 0.0, (0, 1): 90.0, (-1, 0): 180.0, (0, -1): 270.0}
DIRECCIONES = list(RUMBOS.keys())

# Tipos de celda por los que SÍ puede pasar
CAMINABLES = ("libre", "vaca", "deposito")

class AgenteOvni(ap.Agent):
    # Características de entorno
    def setup(self):
        self.carga = False  # lleva una vaca?
        self.estado = "explorando" # explorando | recogiendo | cargando | entregando | esperando
        self.accion = None # (mover | recoger | soltar, celda) o None
        self.rumbo = 0.0 # hacia donde mira en grados, para su giro
        
        # Para las métricas
        self.movimientos = 0 #entre celdas
        self.esperas = 0 
        self.vacas_entregadas = 0

        print(f"AgenteOvni{self.id} inicializado")

    # Helpers
    def posicion(self):
        return tuple(self.model.grid.positions[self])
    
    @staticmethod # no accede ni modifica atributos de self
    def _distancia(a, b):
        # Distancia Manhattan (no diagonales)
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    # celdas donde están los demás ovnis
    def _celdas_de_otros(self):
        grid = self.model.grid
        return {tuple(grid.positions[a]) for a in self.model.agentes if a is not self}
    
    
    # Sensores (4 celdas vecinas)
    # Devuelve {(dx, dy): (celda, tipo)}
        # tipo: pared | deposito | vaca | robot | libre
    def percibir(self):
        x, y = self.posicion()
        n = self.model.p.tamano
        otros = self._celdas_de_otros()
        vecinos = {}
        
        for dx, dy in DIRECCIONES:
            celda = (x + dx, y + dy)
            
            if not (0 <= celda[0] < n and 0 <= celda[1] < n):
                tipo = "pared"
            elif celda in otros or celda in self.model.reservas:
                tipo = "robot"
            elif celda == self.model.esquina:
                tipo = "deposito"
            elif self.model.grid.vacas[celda] > 0:
                tipo = "vaca"
            else:
                tipo = "libre"
                
            vecinos[(dx, dy)] = (celda, tipo)
            
        return vecinos
    
    
    # ==== 1. DECIDIR ====
    # reserva la celda a la que quiere ir
    def decidir(self):
        pos = self.posicion()
        vecinos = self.percibir()
        esquina = self.model.esquina
        self.accion = None
        
        if self.carga:
            # si ya está sobre la esquina suelta la vaca
            if pos == esquina:
                self.estado = "entregando"
                self.accion = ("soltar", esquina)
                return
            
            # si no, sigue avanzando a la esquina
            self.estado = "cargando"
            self.accion = self._elegir_paso(pos, vecinos, hacia_esquina=True)

        else:
            # Si ya está sobre una vaca (y no es depósito) -> recoge
            if pos != esquina and self.model.grid.vacas[pos] > 0:
                self.estado = "recogiendo"
                self.accion = ("recoger", pos)
                return
            
            # Busca vaca en vecinos -> se pone sobre ella
            # Si no encuentra vaca, se mueve al azar
            self.estado = "explorando"
            self.accion = self._elegir_paso(pos, vecinos, hacia_esquina = False)
            
        if self.accion is None:
            self.estado = "esperando"
            
    
    def _elegir_paso(self, pos, vecinos, hacia_esquina):
        libres = [celda for celda, tipo in vecinos.values() if tipo in CAMINABLES]
        if not libres: # no hay celdas libres no se mueve
            return None
        
        candidatas = libres
        if hacia_esquina:
            # elige celdas que lo acerca, si no hay elige random
            d_actual = self._distancia(pos, self.model.esquina)
            acercan = [c for c in libres
                        if self._distancia(c, self.model.esquina) < d_actual]
            candidatas = acercan or libres
        
        else:
            #elige celdas con vaca, si no hay elige random
            con_vaca = [celda for celda, tipo in vecinos.values() if tipo == "vaca"]
            candidatas = con_vaca or libres
                    
        celda = self.model.random.choice(candidatas)
        self.model.reservas[celda] = self.id # apartar destino
        return ("mover", celda)
    
    
    # ==== 2. EJECUTAR ====
    # sí cambia el mundo modelo y lo que hagan los demás
    def ejecutar(self):
        if self.accion is None:
            self.esperas += 1
            return
        
        tipo, celda = self.accion
        
        if tipo == "mover":
            x, y = self.posicion()
            self.rumbo = RUMBOS[(celda[0] - x, celda[1] - y)]
            self.model.grid.move_to(self, celda)
            self.movimientos += 1
            
        elif tipo == "recoger":
            self.model.grid.vacas[celda] -= 1
            self.carga = True
        
        elif tipo == "soltar":
            self.model.grid.vacas[celda] += 1
            self.carga = False
            self.vacas_entregadas += 1
    
    
    def step(self):
        print(f"Inicio del ciclo del AgenteOvni{self.id}")
        self.decidir()
        self.ejecutar()
        
    # Lo que usará la parte visual
    def estado_visual(self):
        return {
            "id": self.id,
            "celda": self.posicion(),
            "rumbo": self.rumbo,
            "carga": self.carga,
            "estado": self.estado,
        }
        