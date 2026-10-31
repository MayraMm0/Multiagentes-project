import pygame


# Calcula los puntos que forman una línea entre dos coordenadas
def bresenham_2d(inicio, fin):
    x, y = inicio
    x1, y1 = fin

    dx, dy = abs(x1 - x), abs(y1 - y)

    sx = 1 if x < x1 else -1
    sy = 1 if y < y1 else -1

    error = dx - dy

    while True:
        # Entrega cada punto para que se pueda dibujar en pantalla
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


# Dibuja una línea conectando dos puntos en pantalla
def dibujar_segmento_2d(superficie, inicio, fin, color):
    screen_width, screen_height = superficie.get_size()

    # Convierte las coordenadas a números enteros
    inicio = (round(inicio[0]), round(inicio[1]))
    fin = (round(fin[0]), round(fin[1]))

    # Dibuja los puntos que estén dentro de la pantalla
    for x, y in bresenham_2d(inicio, fin):
        if 0 <= x < screen_width and 0 <= y < screen_height:
            superficie.set_at((x, y), color)


# Rellena un polígono convexo usando el método scanline
def rellenar_poligono(superficie, puntos, color, revisar_tamano=True):
    screen_width, screen_height = superficie.get_size()

    ys = [p[1] for p in puntos]
    y_min, y_max = max(0, min(ys)), min(screen_height - 1, max(ys))
    if y_min > y_max:
        return  # El polígono queda fuera de la pantalla

    # Evita recorrer polígonos demasiado grandes
    xs = [p[0] for p in puntos]
    if revisar_tamano and (max(xs) - min(xs) > 8 * screen_width
                           or max(ys) - min(ys) > 8 * screen_height):
        return

    orillas = {}  # Guarda los límites de cada fila
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


# Rellena un polígono aplicando transparencia
def rellenar_poligono_alpha(superficie, puntos, color):
    screen_width, screen_height = superficie.get_size()

    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    if max(xs) - min(xs) > 8 * screen_width or max(ys) - min(ys) > 8 * screen_height:
        return

    x0, x1 = max(0, min(xs)), min(screen_width - 1, max(xs))
    y0, y1 = max(0, min(ys)), min(screen_height - 1, max(ys))
    if x0 > x1 or y0 > y1:
        return  # El polígono queda fuera de la pantalla

    # Crea una capa para dibujar el polígono con transparencia
    capa = pygame.Surface((x1 - x0 + 1, y1 - y0 + 1), pygame.SRCALPHA)
    desplazados = [(x - x0, y - y0) for x, y in puntos]
    rellenar_poligono(capa, desplazados, color, revisar_tamano=False)
    superficie.blit(capa, (x0, y0))