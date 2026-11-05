
from Bresenham import rellenar_poligono, rellenar_poligono_alpha, dibujar_segmento_2d


def dibujar_caras(superficie, caras):

    caras.sort(key=lambda cara: cara[0], reverse=True)

    # Bloquear la superficie una vez: set_at ya no la bloquea en cada píxel
    superficie.lock()
    for _, puntos, relleno, borde in caras:
        if len(relleno) == 4:
            # Cara translúcida (r, g, b, alpha): blit necesita la superficie
            # desbloqueada. Se mezcla con lo que ya está dibujado detrás.
            superficie.unlock()
            rellenar_poligono_alpha(superficie, puntos, relleno)
            superficie.lock()
        else:
            rellenar_poligono(superficie, puntos, relleno)

        if borde is not None:
            n = len(puntos)
            for i in range(n):
                dibujar_segmento_2d(superficie, puntos[i], puntos[(i + 1) % n], borde)
    superficie.unlock()
