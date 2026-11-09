Práctica xArm: nodos, tópicos y mensajes
========================================

**Objetivo:** observar el grafo ROS 2 de xArm y crear un nodo educativo
que lea posiciones articulares sin enviar comandos de movimiento.

Conceptos relacionados: :doc:`conceptos_basicos` y :doc:`tutoriales`.

Paso 1. Iniciar un escenario de práctica
----------------------------------------

Ejecuta uno de los escenarios descritos en :doc:`../tema_1/xarm_instalacion`.
Para trabajar con un modelo sin hardware puedes comenzar con:

.. code-block:: bash

   ros2 launch xarm_description xarm6_rviz_display.launch.py

En una nueva terminal, después de activar Jazzy y el workspace mediante
``~/.bashrc``, ejecuta:

.. code-block:: bash

   ros2 node list
   ros2 topic list -t
   ros2 topic find sensor_msgs/msg/JointState

**Importante:** identifica el nombre real del tópico que publica
``sensor_msgs/msg/JointState``. La presencia de un modelo URDF por sí
sola no garantiza que un determinado tópico publique datos.

Paso 2. Inspeccionar el mensaje
-------------------------------

En este ejemplo, sustituye ``/joint_states`` por el resultado de la
inspección anterior si utiliza otro nombre:

.. code-block:: bash

   ros2 interface show sensor_msgs/msg/JointState
   ros2 topic info /joint_states -v
   ros2 topic echo /joint_states --once
   ros2 topic hz /joint_states

El mensaje contiene ``name``, ``position``, ``velocity`` y ``effort``.
Las posiciones de juntas rotativas se expresan en **radianes** en la
convención del mensaje. Consulta los valores y verifica sus nombres:
no presupongas que todas las entradas corresponden a las seis juntas
del brazo (puede aparecer una pinza).

Paso 3. Crear un paquete educativo independiente
------------------------------------------------

El archivo descargable de este curso contiene el proyecto
``ejemplos_ros2/avigtech_xarm_intro``. Copia esa carpeta dentro del
workspace existente **sin modificar el repositorio oficial**:

.. code-block:: bash

   cp -r /RUTA/AL_CURSO/ejemplos_ros2/avigtech_xarm_intro \
       ~/ros2_ws/src/
   cd ~/ros2_ws
   colcon build --symlink-install --packages-select avigtech_xarm_intro
   source install/setup.bash

Paso 4. Ejecutar el nodo monitor
--------------------------------

La práctica no controla el robot. Lee mensajes ``JointState``,
publica un resumen de texto y ofrece un servicio de consulta.

.. code-block:: bash

   ros2 launch avigtech_xarm_intro monitor_articular.launch.py \
       topic_articular:=/joint_states

El argumento ``topic_articular`` permite cambiar la fuente sin
modificar el código Python. Si el tópico real es otro, utiliza ese
nombre en el lanzamiento.

En otra terminal:

.. code-block:: bash

   ros2 node info /avigtech_xarm/monitor_articular
   ros2 topic echo /avigtech/xarm/resumen --once
   ros2 param get /avigtech_xarm/monitor_articular topic_articular

.. note::

   El servicio y el tópico de resumen solo devuelven datos útiles una
   vez que el monitor haya recibido un ``JointState``. Si el simulador
   no publica, revisa los nombres y el QoS de ambos extremos.

Comprender el fragmento de Python
---------------------------------

El ejemplo incluido en el paquete utiliza las funciones de ``rclpy``.
El siguiente extracto muestra el **concepto** (la clase completa y las
importaciones están en ``monitor_articular.py``):

.. code-block:: python

   self.crear_suscriptor = self.create_subscription(
       JointState,
       self.topic_articular,
       self.recibir_estado,
       qos_profile_sensor_data,
   )
   self.publicador = self.create_publisher(
       String, '/avigtech/xarm/resumen', 10
   )
   self.servicio = self.create_service(
       Trigger, '/avigtech/xarm/obtener_estado', self.consultar_estado
   )

- ``JointState`` es el tipo del mensaje recibido.
- ``self.recibir_estado`` es el callback que se ejecuta al llegar un dato.
- ``qos_profile_sensor_data`` prioriza recibir datos recientes de sensores
  y puede comunicarse con publicadores de QoS fiable.
- ``String`` identifica el tipo del tópico de resumen.
- ``Trigger`` implementa una respuesta a una solicitud puntual.

El proyecto completo contiene ``package.xml``, ``setup.py``,
``setup.cfg`` y un lanzamiento ROS 2 para repetir la práctica.

Reto de programación
--------------------

#. Localiza en ``monitor_articular.py`` la función suscriptora.
#. Explica el uso de ``self.create_subscription`` y del ``timer``.
#. Identifica el parámetro del nombre del tópico.
#. Modifica el formato del resumen para mostrar posiciones en grados,
   sin alterar el mensaje original (que usa radianes).
#. Compara ``ros2 topic hz`` antes y después del cambio. ¿Cambia la
   tasa de publicación original o solo la del resumen?


Solución del reto: de radianes a grados
---------------------------------------

Este reto está **resuelto y explicado paso a paso** en
:doc:`xarm_reto_resuelto`. El paquete educativo adjunto ya admite el
parámetro ``unidad_resumen``. Para probarlo, recompila el paquete y ejecuta:

.. code-block:: bash

   cd ~/ros2_ws
   colcon build --symlink-install --packages-select avigtech_xarm_intro
   ros2 launch avigtech_xarm_intro monitor_articular.launch.py \
       topic_articular:=/joint_states unidad_resumen:=deg

La conversión solo afecta al texto publicado en
``/avigtech/xarm/resumen``. El mensaje ``JointState`` original no cambia.

La práctica siguiente incorpora **servicios y acciones**:
:doc:`xarm_servicios`.
