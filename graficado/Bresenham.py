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


"""
    Relleno por scanline de un polígono CONVEXO (3 o más vértices).
    1. Bresenham recorre cada orilla y, por cada fila y, guarda el x más
       a la izquierda y el más a la derecha.
    2. Cada fila se pinta de x_min a x_max con pygame.draw.line (por velocidad).
"""


def rellenar_poligono(superficie, puntos, color, revisar_tamano=True):
    screen_width, screen_height = superficie.get_size()

    ys = [p[1] for p in puntos]
    y_min, y_max = max(0, min(ys)), min(screen_height - 1, max(ys))
    if y_min > y_max:
        return  # el polígono está completamente arriba o abajo de la pantalla

    # Protección: polígonos enormes (vértices casi en el plano cercano)
    # harían que Bresenham recorra millones de píxeles fuera de pantalla.
    xs = [p[0] for p in puntos]
    if revisar_tamano and (max(xs) - min(xs) > 8 * screen_width
                           or max(ys) - min(ys) > 8 * screen_height):
        return

    orillas = {}  # y -> [x_min, x_max]
    n = len(puntos)
    for i in range(n):
        for x, y in bresenham_2d(puntos[i], puntos[(i + 1) % n]):
            if y_min <= y <= y_max:
                fila = orillas.get(y)
                if fila is None:
                    orillas[y] = [x, x]
                elif x < fila[0]:
                    fila[0] = x
                elif x > fila[1]:
                    fila[1] = x

    ultimo_x = screen_width - 1
    for y, (x0, x1) in orillas.items():
        if x1 < 0 or x0 > ultimo_x:
            continue
        pygame.draw.line(superficie, color,
                         (max(0, x0), y), (min(ultimo_x, x1), y))


"""
    Relleno TRANSLÚCIDO: color = (r, g, b, alpha).
    1. Se crea una capa con canal alfa (SRCALPHA) del tamaño del recuadro
       que ocupa el polígono en pantalla (recortado a la pantalla).
    2. Se rellena el polígono en esa capa con el mismo scanline.
    3. blit mezcla la capa con lo que ya estaba dibujado.
    Ojo: blit no funciona con la superficie bloqueada (lock).
"""


def rellenar_poligono_alpha(superficie, puntos, color):
    screen_width, screen_height = superficie.get_size()

    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    if max(xs) - min(xs) > 8 * screen_width or max(ys) - min(ys) > 8 * screen_height:
        return

    x0, x1 = max(0, min(xs)), min(screen_width - 1, max(xs))
    y0, y1 = max(0, min(ys)), min(screen_height - 1, max(ys))
    if x0 > x1 or y0 > y1:
        return  # fuera de pantalla

    capa = pygame.Surface((x1 - x0 + 1, y1 - y0 + 1), pygame.SRCALPHA)
    desplazados = [(x - x0, y - y0) for x, y in puntos]
    rellenar_poligono(capa, desplazados, color, revisar_tamano=False)
    superficie.blit(capa, (x0, y0))