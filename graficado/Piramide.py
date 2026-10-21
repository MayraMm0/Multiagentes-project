import numpy as np
from OpMat import OpMat3D
from Bresenham import dibujar_segmento_2d

class Piramide:
    def __init__(self):
        # Vértices de pirámide base cuadrada
        self.points = np.array([
            [-5.0,  5.0,  5.0, -5.0,  0.0],
            [-2.5, -2.5, -2.5, -2.5,  7.0],
            [-5.0, -5.0,  5.0,  5.0,  0.0],
            [ 1.0,  1.0,  1.0,  1.0,  1.0]
        ], dtype = float)
        
        # Pares de índices que representan aristas
        self.edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            (0, 4),
            (1, 4),
            (2, 4),
            (3, 4)
        ]
        
        # para transformaciones 3D
        self.opMat = OpMat3D()
        
        # Ángulo actual de rotación
        self.deg = 0.0
        
        # Color de aristas
        self.color = (232, 139, 221)
      
    # Actualizar el ángulo que determina rotación  
    def update(self, delta_deg):
        self.deg += delta_deg
        
    # Conecta transformaciones, cámara y Bresenham
    def render(self, superficie, camara):
        # Reiniciar transformaciones del frame anterior
        self.opMat.loadId()
        
        # Aplicar rotación actual
        self.opMat.rotate_y(self.deg)
        
        # Transformar vértices
        transformed_points = self.opMat.transform_points(self.points)
        
        # Recorrer todas las aristas
        for inicio, fin in self.edges:
            # Obtener los extremos en coordenadas 3D
            punto_a = transformed_points[:3, inicio]
            punto_b = transformed_points[:3, fin]
            
            # Proyectar ambos extremos a coordenadas de pantalla
            extremo_a = camara.proyectar(punto_a)
            extremo_b = camara.proyectar(punto_b)
            
            # Dibujar solo si ambos extremos son proyectables
            if extremo_a is not None and extremo_b is not None:
                dibujar_segmento_2d(
                    superficie,
                    extremo_a,
                    extremo_b,
                    self.color
                )