import numpy as np

class OpMat3D:

    def __init__(self):
        # Atributo que almacena matriz de modelado, inicializada como identidad
        self.matriz_modelado = np.identity(4)
    
    # Restablece todas las transformaciones acumuladas
    def loadId(self):
        self.matriz_modelado = np.identity(4)
    
    def translate(self, tx, ty, tz):
        T = np.identity(4)
        T[0, 3] = tx
        T[1, 3] = ty
        T[2, 3] = tz
        
        self.matriz_modelado = self.matriz_modelado @ T
        
    def scale(self, sx, sy, sz):
        S = np.identity(4)
        S[0, 0] = sx
        S[1, 1] = sy
        S[2, 2] = sz
        self.matriz_modelado = self.matriz_modelado @ S
        
    def rotate_x(self, deg):
        rad = np.deg2rad(deg)
        
        Rx = np.identity(4)
        
        Rx[1, 1] = np.cos(rad)
        Rx[1, 2] = -np.sin(rad)
        Rx[2, 1] = np.sin(rad)
        Rx[2, 2] = np.cos(rad)
        
        self.matriz_modelado = self.matriz_modelado @ Rx
        
    def rotate_y(self, deg):
        rad = np.deg2rad(deg)
        
        Ry = np.identity(4)
        
        Ry[0, 0] = np.cos(rad)
        Ry[0, 2] = np.sin(rad)
        Ry[2, 0] = -np.sin(rad)
        Ry[2, 2] = np.cos(rad)
        
        self.matriz_modelado = self.matriz_modelado @ Ry
        
    def rotate_z(self, deg):
        rad = np.deg2rad(deg)
        
        Rz = np.identity(4)
        
        Rz[0, 0] = np.cos(rad)
        Rz[0, 1] = -np.sin(rad)
        Rz[1, 0] = np.sin(rad)
        Rz[1, 1] = np.cos(rad)
        
        self.matriz_modelado = self.matriz_modelado @ Rz
        
    # Espera que points ya esté en coordenadas homogéneas
    def transform_points(self, points):
        return self.matriz_modelado @ points