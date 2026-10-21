import pygame

# Para coordenadas 2D de puntos entre dos segmentos
def bresenham_2d(inicio, fin):
    """Genera todos los píxeles entre dos posiciones de pantalla."""
    x, y = inicio
    x1, y1 = fin

    dx, dy = abs(x1 - x), abs(y1 - y)
    
    sx = 1 if x < x1 else -1
    sy = 1 if y < y1 else -1
    
    error = dx - dy

    while True:
        # yield: pausa la ejecución de la función, para que la función invocante pueda usarlos, 
        # y después sigue la ejecución (Pausas para ir ploteando y calculando coordenadas)
        # por qué? la función padre plotea los puntos, bresenham 2D calcula sus coordenadas
        yield x, y

        if (x, y) == (x1, y1):
            break

        doble_error = 2 * error

        if doble_error > -dy:
            error -= dy
            x += sx

        if doble_error < dx:
            error += dx
            y += sy

"""
    superficie: buffer de dibujado (pantalla)
    inicio, fin: coordenadas 2D, de la línea que queremos
    Cada vez que tenemos coordenadas (de bresenham_2d) verifica que no se salgan de pantalla
    Si no se salen dibuja el pixel (cambia color)
"""
def dibujar_segmento_2d(superficie, inicio, fin, color):
    screen_width, screen_height = superficie.get_size()
    
    # Los extremos deben ser coordenadas enteras de pantalla
    inicio = (round(inicio[0]), round(inicio[1]))
    fin = (round(fin[0]), round(fin[1]))
    
    # Cuando ya se proyectaron 2 voxeles -> pixeles, los conecta con bresenham_2d
    for x, y in bresenham_2d(inicio, fin):
        if 0 <= x < screen_width and 0 <= y < screen_height:
            superficie.set_at((x, y), color)
