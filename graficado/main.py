import random
import pygame
 
from OpMat import OpMat3D
from Camara import Camara
from Malla import Malla
from Ovni import Ovni
from Vaca import Vaca
 
# Configuración de la ventana
ANCHO, ALTO = 900, 600
FPS = 60
 
FONDO = (13, 10, 45)
COLOR_OVNI = (255, 255, 255)
COLOR_VACA = (232, 139, 221)
COLOR_SUELO = (45, 40, 110)
 
LIMITE = 8.0          # el campo va de -LIMITE a +LIMITE en X y Z
 
 
def main():
    pygame.init()
 
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Ovni y vaca - modelado 3D con Bresenham")
    reloj = pygame.time.Clock()
 
    # Objetos principales
    camara = Camara(
        screen_width=ANCHO,
        screen_height=ALTO,
        posicion=(0.0, 5.5, 17.0),
        objetivo=(0.0, 3.0, 0.0)
    )
    
    opMat = OpMat3D()
 
    suelo = Malla.rejilla(LIMITE + 2, 2.0, 0.0, COLOR_SUELO)
    ovni = Ovni(COLOR_OVNI, posicion=(0.0, 6.5, 0.0), limite=LIMITE)
    vacas = [
        Vaca(COLOR_VACA, posicion=(random.uniform(-5, 5), 0.0, random.uniform(-5, 5)),
             limite=LIMITE)
        for _ in range(3)
    ]
 
    ejecutando = True
    while ejecutando:
        # Tiempo transcurrido desde el frame anterior, en segundos
        delta_time = reloj.tick(FPS) / 1000.0
 
        # procesar eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                ejecutando = False
 
        # --- 1. Actualizar agentes ---
        ovni.update(delta_time)
        for vaca in vacas:
            vaca.update(delta_time)
 
        # --- 2. Fondo ---
        pantalla.fill(FONDO)
 
        # --- 3. Renderizar ---
        opMat.loadId()
        suelo.render(pantalla, camara, opMat)
 
        for vaca in vacas:
            vaca.render(pantalla, camara, opMat)
        ovni.render(pantalla, camara, opMat)
 
        pygame.display.set_caption(
            f"Ovni y vaca - modelado 3D con Bresenham  |  {reloj.get_fps():.0f} FPS"
        )
        
        # --- 4. Mostrar frame ---
        pygame.display.flip()
 
    pygame.quit()
 
 
if __name__ == "__main__":
    main()
 