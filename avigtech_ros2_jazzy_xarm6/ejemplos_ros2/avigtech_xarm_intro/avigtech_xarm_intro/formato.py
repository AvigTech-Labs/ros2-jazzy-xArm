"""Formateo didáctico del estado articular del xArm 6.

En JointState, las articulaciones rotativas se expresan en radianes.
Las articulaciones prismáticas se expresan en metros. El mensaje recibido
no se modifica: únicamente construimos una representación de texto.
"""

from math import degrees

JUNTAS_ROTATIVAS_XARM6 = {f'joint{i}' for i in range(1, 7)}


def formatear_articulaciones(nombres, posiciones, unidad='rad'):
    """Formatea las seis juntas del brazo en radianes o grados.

    Otros nombres se muestran sin conversión ni unidad impuesta:
    verifica el tipo de junta en el URDF antes de atribuirle unidades.
    """
    if unidad not in ('rad', 'deg'):
        raise ValueError("unidad debe ser 'rad' o 'deg'")

    partes = []
    for nombre, posicion in zip(nombres, posiciones):
        if nombre in JUNTAS_ROTATIVAS_XARM6:
            if unidad == 'deg':
                partes.append(f'{nombre}={degrees(posicion):.2f} deg')
            else:
                partes.append(f'{nombre}={posicion:.3f} rad')
        else:
            partes.append(f'{nombre}={posicion:.3f} (revisar unidad URDF)')

    return ', '.join(partes) if partes else 'sin articulaciones con posicion publicada'
