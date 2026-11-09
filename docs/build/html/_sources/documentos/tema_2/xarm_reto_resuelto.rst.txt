Solución del reto de programación: monitor de articulaciones
============================================================

Este solucionario corresponde a :doc:`xarm_comunicacion` y al paquete
``avigtech_xarm_intro`` incluido en el material. Se utiliza exclusivamente
un nodo de **lectura de estados**, sin enviar comandos de movimiento.

1. Localizar la función suscriptora
-----------------------------------

En ``avigtech_xarm_intro/monitor_articular.py`` el callback es
``recibir_estado(self, mensaje)``. Cada vez que llega un
``sensor_msgs/msg/JointState`` guarda una copia de los nombres y
posiciones en ``self.ultimo_estado``:

.. code-block:: python

   def recibir_estado(self, mensaje):
       self.ultimo_estado = (
           list(mensaje.name),
           list(mensaje.position),
       )

Este callback **no mueve** el robot ni modifica el mensaje recibido.

2. Comprender el suscriptor y el temporizador
---------------------------------------------

``self.create_subscription(JointState, ..., self.recibir_estado, qos)``
conecta el nodo a un tópico y entrega los mensajes al callback. El
``timer`` se ejecuta a intervalos independientes del ritmo de llegada:

.. code-block:: python

   self.timer = self.create_timer(1.0 / frecuencia_hz, self.publicar_resumen)

Por ejemplo, ``frecuencia_hz = 2.0`` implica un periodo nominal de
``1 / 2 = 0.5 s``. El monitor solo publica cuando ya recibió un estado.
El QoS del suscriptor es ``qos_profile_sensor_data``, diseñado para
manejar información reciente de sensores.

3. Identificar el parámetro del nombre del tópico
-------------------------------------------------

``topic_articular`` se declara dentro del constructor del nodo:

.. code-block:: python

   self.declare_parameter('topic_articular', '/joint_states')
   self.topic_articular = self.get_parameter('topic_articular').value

En ``launch/monitor_articular.launch.py`` existe el argumento
``topic_articular``. Por eso puede cambiarse sin editar Python:

.. code-block:: bash

   ros2 launch avigtech_xarm_intro monitor_articular.launch.py \
       topic_articular:=/joint_states

Comprueba el parámetro que realmente utiliza el nodo:

.. code-block:: bash

   ros2 param get /avigtech_xarm/monitor_articular topic_articular

4. Mostrar grados sin alterar JointState
----------------------------------------

El mensaje ``JointState`` expresa las **juntas rotativas** en radianes.
La fórmula para convertir al presentar un resumen es:

.. math::

   q_{grados} = q_{radianes} \frac{180}{\pi}

El archivo ``avigtech_xarm_intro/formato.py`` incorpora esa conversión
con ``math.degrees()``. Esta es la función completa de la solución:

.. code-block:: python

   from math import degrees

   JUNTAS_ROTATIVAS_XARM6 = {f'joint{i}' for i in range(1, 7)}

   def formatear_articulaciones(nombres, posiciones, unidad='rad'):
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

La aplicación se puede lanzar directamente en grados:

.. code-block:: bash

   cd ~/ros2_ws
   colcon build --symlink-install --packages-select avigtech_xarm_intro
   ros2 launch avigtech_xarm_intro monitor_articular.launch.py \
       topic_articular:=/joint_states unidad_resumen:=deg

En otra terminal:

.. code-block:: bash

   ros2 param get /avigtech_xarm/monitor_articular unidad_resumen
   ros2 topic echo /avigtech/xarm/resumen --once
   ros2 topic echo /joint_states --once

**Ejemplo:** ``1.5708 rad`` equivale aproximadamente a ``90.00 deg``.
No conviertas de forma indiscriminada las juntas de la pinza: las
prismáticas se expresan en metros. Antes de convertir, verifica los
nombres y los tipos de juntas en el URDF. En el paquete entregado la
conversión se limita a ``joint1`` ... ``joint6``. Si tu modelo usa
otros nombres, ajusta la lista tras comprobar el URDF.

5. Comparar las frecuencias de publicación
------------------------------------------

Abre terminales distintas mientras el escenario produce ``JointState``:

.. code-block:: bash

   ros2 topic hz /joint_states

Y para el mensaje de resumen:

.. code-block:: bash

   ros2 topic hz /avigtech/xarm/resumen

**Respuesta:** transformar radianes en grados **no altera la frecuencia
ni los datos del publicador original** de ``/joint_states``. El resumen
sale por otro tópico, controlado por ``frecuencia_hz`` (por defecto
aproximadamente 1 Hz), sujeto a la ejecución del temporizador y a que
existan estados recibidos. La frecuencia real de ``/joint_states``
depende de su propio publicador y puede variar independientemente.

Para comprobarlo de forma más clara, cambia la frecuencia del resumen:

.. code-block:: bash

   ros2 launch avigtech_xarm_intro monitor_articular.launch.py \
       topic_articular:=/joint_states unidad_resumen:=deg frecuencia_hz:=2.0

Esperarías alrededor de **2 Hz en el resumen**, manteniéndose la tasa
original de ``/joint_states``. Las cifras reales se deben medir, no
suponer. Detén antes el monitor anterior para evitar nodos duplicados.

Verificación del ejercicio
--------------------------

El paquete incluye pruebas unitarias de conversión, validación de unidades
y tratamiento de juntas no identificadas como rotativas:

.. code-block:: bash

   cd ~/ros2_ws/src/avigtech_xarm_intro
   python3 -m pytest -q test/test_formato.py

Esta prueba verifica las funciones de formato sin necesitar un robot físico.
