Práctica xArm: servicios, acciones y parámetros
===============================================

Objetivos
---------

- Comprender que un **tópico** distribuye mensajes, mientras que un
  **servicio** realiza una solicitud y devuelve una respuesta.
- Diferenciar **acciones** (objetivos de ejecución prolongada,
  realimentación y resultado) de servicios síncronos.
- Localizar los parámetros y endpoints ofrecidos por un sistema real.

1. Servicio propio: lectura del estado
--------------------------------------

Con el monitor de :doc:`xarm_comunicacion` en marcha, ejecuta:

.. code-block:: bash

   ros2 service list -t
   ros2 service type /avigtech/xarm/obtener_estado
   ros2 interface show std_srvs/srv/Trigger
   ros2 service call /avigtech/xarm/obtener_estado \
       std_srvs/srv/Trigger '{}'

El nodo devuelve ``success: true`` si ha recibido un estado y un resumen
en ``message``. Si aún no llegaron datos, devuelve ``success: false``.

Un servicio ``Trigger`` resulta adecuado para esta consulta porque no
requiere argumentos; la decisión de mover un manipulador **no** se
implementa como parte de este ejercicio.

2. Parámetros del nodo
----------------------

.. code-block:: bash

   ros2 param list /avigtech_xarm/monitor_articular
   ros2 param get /avigtech_xarm/monitor_articular topic_articular
   ros2 param get /avigtech_xarm/monitor_articular frecuencia_hz
   ros2 param describe /avigtech_xarm/monitor_articular frecuencia_hz

El parámetro ``frecuencia_hz`` configura la tasa del resumen al
**arrancar** el nodo. En esta versión didáctica cambiarlo con
``ros2 param set`` durante la ejecución no recrea automáticamente el
temporizador. Reinicia el nodo para aplicar otro valor.

3. Descubrir acciones en MoveIt 2
---------------------------------

Detén el monitor y el escenario anterior si hay conflictos, e inicia:

.. code-block:: bash

   ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py

Abre una segunda terminal con el entorno del workspace:

.. code-block:: bash

   ros2 action list -t
   ros2 node list
   ros2 service list -t

Según los controladores y el planificador que se hayan lanzado, puede
haber acciones de trayectoria basadas en
``control_msgs/action/FollowJointTrajectory`` u otras interfaces.
Comprueba las existentes en vez de asumir un nombre de endpoint.

.. code-block:: bash

   ros2 interface show control_msgs/action/FollowJointTrajectory
   ros2 pkg executables xarm_planner

**Actividad:** identifica qué información tiene el objetivo, qué
proporciona la realimentación y qué aparece al terminar una acción.
No envíes objetivos a un robot físico como parte de esta lección.

4. Interfaces del robot real: solo lectura y estudio
----------------------------------------------------

El paquete oficial ``xarm_api`` expone servicios de control y tópicos
asociados al equipo físico. El fabricante documenta, entre otros,
``/xarm/motion_enable``, ``/xarm/set_mode``, ``/xarm/set_state`` y
``/xarm/set_position`` para un xArm 6 (los nombres dependen del
namespace y de la configuración). Estas interfaces **no tienen por qué
existir** al lanzar solamente ``xarm6_moveit_fake.launch.py``.

Para el laboratorio de hardware real deben comprobarse la versión del
firmware, zona libre, límites, paro de emergencia y procedimiento de
recuperación. El primer laboratorio es exclusivamente de inspección.

`Referencia oficial de xarm_api
<https://github.com/xArm-Developer/xarm_ros2/tree/jazzy/xarm_api>`__.

Reto
----

Dibuja un esquema con cuatro flechas distintas: el flujo
``JointState`` hacia el monitor, el resumen de texto hacia otros
nodos, la llamada al servicio ``Trigger`` y una acción de planificación
identificada mediante ``ros2 action list -t``.
