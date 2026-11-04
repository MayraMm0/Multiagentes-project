"""
Qué hace
    - Mapa de NxN, coordenadas enteras
    - K vacas en cerdas aleatorias y ovnis en celdas aleatorias
    - esquina (N-1, N-1) es el deposito
    - En cada paso: se vacían las reservas, los ovnis deciden y luego ejecutan
    - Termina: cuando todas las vacas se hayan recogido
    - Guarda historial paso a paso para la parte visual
"""

import numpy as np
import agentpy as ap

from AgenteOvni import AgenteOvni

class MundoModelo(ap.Model):
    def setup(self):
        n = self.p.tamano
        k = self.p.cantidad_vacas
        m = self.p.cantidad_agentes
        
        # espacio mínimo
        if k + m + 1 > n*n:
            raise ValueError("No hay suficiente espacio")
        
        self.esquina = (n-1, n-1)
        self.reservas = {} # {celda: id_agente}, se vacía en cada paso
        self.paso_final = None # paso en que terminó
        
        
        # 1. Cuadricula (mapa) y capa de vacas
        self.grid = ap.Grid(self, (n, n))
        self.grid.add_field('vacas', np.zeros((n, n), dtype=int))
        
        # 2. Celdas disponibles (todas menos depósito)
        celdas = [(x, y) for x in range(n) for y in range(n) if (x, y) != self.esquina]
        
        self.random.shuffle(celdas)
        
        # 3. K vacas en las primeras K celdas (ya en aleatorio)
        for celda in celdas[:k]:
            self.grid.vacas[celda] = 1
            
        # 4. Los ovnis empiezan en celdas sin vaca
        posiciones = celdas[k:k + m]
        self.agentes = ap.AgentList(self, m, AgenteOvni)
        self.grid.add_agents(self.agentes, posiciones)
        
        # 5. Historial para la parte visual (se llena en update)
        self.historial = []
        
    # Un paso de la simulación
    def step(self):
        self.reservas = {} # empieza vacío
        
        # 1. cada ovni decide y reserva
        for agente in self.agentes.shuffle():
            agente.decidir()
            
        # 2. Todos ejecutan
        self.agentes.ejecutar()
        
        # Ya están todas las vacas en depósito?
        if self.vacas_entregadas() == self.p.cantidad_vacas:
            self.paso_final = self.t
            self.stop()
            
    # llama update después de setup y de cada step
    def update(self):
        self.historial.append({
            "t": self.t,
            "agentes": [a.estado_visual() for a in self.agentes],
            "vacas": np.array(self.grid.vacas).copy(),
        })
            
    # Métricas
    def vacas_entregadas(self):
        return int(self.grid.vacas[self.esquina])
    
    def estadisticas(self):
        return {
            "agentes": self.p.cantidad_agentes,
            "vacas": self.p.cantidad_vacas,
            "completado": self.paso_final is not None,
            "pasos": self.paso_final if self.paso_final is not None else self.t,
            "movimientos": sum(a.movimientos for a in self.agentes),
            "esperas": sum(a.esperas for a in self.agentes),
            "vacas en depósito": self.vacas_entregadas(),
        }
        
    def end(self):
        for clave, valor in self.estadisticas().items():
            self.report(clave, valor)
            
            
# Prueba en consola
if __name__ == "__main__":
    parametros = {
        "tamano": 10,
        "cantidad_agentes": 5,
        "cantidad_vacas": 10,
        "steps": 3000,      # con 1 agente la exploración al azar tarda ~800-1200 pasos
        "seed": 42,
    }
    modelo = MundoModelo(parametros)
    modelo.run(display=False)
        
    print("\nResultados")
    for clave, valor in modelo.estadisticas().items():
        print(f"  {clave}: {valor}")
        
    