Práctica xArm 6: ROS 2, MoveIt 2 y planificación sin robot físico
===================================================================

.. note::

   Esta práctica se basa en **ROS 2 Jazzy, Ubuntu 24.04 y el xArm 6**.
   Se utilizan exclusivamente los lanzamientos con hardware ``fake``.
   No es necesario el manipulador físico, el driver ``xarm_api`` ni Gazebo.
   La planificación no simula fuerzas, pares ni dinámica de contacto.

**Objetivos de aprendizaje**

- Diferenciar los lanzamientos de visualización, MoveIt 2, planificador y driver.
- Identificar nodos, tópicos, mensajes, servicios y controladores **observados**.
- Explicar la arquitectura cliente/servidor de ``xarm_planner``.
- Planificar y ejecutar de forma controlada una trayectoria articular A → B.
- Programar un cliente ``rclpy`` que sustituya ``ros2 service call``.
- Comparar planificación articular/por pose con planificación cartesiana lineal.

**Prerrequisitos:** tener compilado ``xarm_ros2`` (rama ``jazzy``), disponer de
``~/ros2_ws`` y haber configurado la carga del entorno. Si no se configuró el
``~/.bashrc``, en una nueva terminal se requiere ``source ~/ros2_ws/install/setup.bash``.

1. ¿Qué hace cada lanzamiento de xArm?
--------------------------------------

El fabricante ofrece diferentes puntos de entrada. **No se deben ejecutar al
mismo tiempo** dos lanzamientos fake completos que compartan nombres de nodos,
controladores o interfaces, porque pueden competir por recursos.

.. list-table:: Lanzamientos relevantes
   :header-rows: 1
   :widths: 29 35 36

   * - Lanzamiento
     - Componentes / propósito
     - Uso didáctico
   * - ``xarm_description xarm6_rviz_display.launch.py``
     - Modelo URDF y visualización en RViz 2; no equivale a MoveIt
     - Introducción al robot, eslabones, articulaciones y TF2
   * - ``xarm_moveit_config xarm6_moveit_fake.launch.py``
     - ``move_group``, RViz 2, controladores ROS 2 y hardware fake
     - Descubrir nodos, mensajes, servicios, acciones y controladores
   * - ``xarm_planner xarm6_planner_fake.launch.py``
     - Incluye la configuración MoveIt fake y añade ``xarm_planner_node``
     - Planificación articular y cartesiana mediante servicios
   * - ``xarm_api xarm6_driver.launch.py robot_ip:=...``
     - Inicia el driver/SDK e intenta conectarse al controlador físico
     - **Fuera de alcance** de esta práctica sin robot físico

Los servicios del SDK como ``/xarm/motion_enable``, ``/xarm/set_mode``,
``/xarm/set_position`` y ``/xarm/set_servo_angle`` no forman parte de la
interfaz predeterminada del planificador fake; su ausencia es esperada.

**Primera terminal: exploración de MoveIt 2**

.. code-block:: bash

   ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py

**Para los ejercicios de planificación por servicio:** detén el lanzamiento
anterior (``Ctrl+C``), comprueba que sus procesos han finalizado y ejecuta:

.. code-block:: bash

   ros2 launch xarm_planner xarm6_planner_fake.launch.py

La rama ``jazzy`` de UFACTORY define este segundo lanzamiento como una
configuración que incluye el launch interno de MoveIt fake y habilita el
planificador de servicios.

2. Fundamentos: nodos, tópicos, mensajes y servicios
----------------------------------------------------

**Nodo:** proceso o componente ROS 2 que realiza tareas concretas. Un mismo
sistema puede contener un nodo de planificación, uno de control, otro de
publicación de estados y otro de visualización.

**Tópico:** canal de comunicación publicador/suscriptor. Permite un flujo de
datos asíncrono. **Mensaje:** estructura tipada que viaja por el tópico.
Por ejemplo, ``/joint_states`` publica mensajes ``sensor_msgs/msg/JointState``
con nombres y estados articulares. Las posiciones de las juntas rotativas se
expresan en **radianes**.

**Servicio:** comunicación solicitud/respuesta. Un cliente envía una petición
con un tipo conocido, y un servidor la procesa y devuelve una respuesta.
La respuesta ``success: true`` de una planificación confirma que se obtuvo un
plan; **no confirma la ejecución** del movimiento.

.. code-block:: text

   Cliente ROS 2   -- Request -->   Servidor de servicio
       (rclpy)                       (xarm_planner_node)
           ^                              |
           +----------- Response ---------+

**Comandos iniciales de exploración (segunda terminal):**

.. code-block:: bash

   ros2 node list
   ros2 node info /move_group
   ros2 topic list -t
   ros2 topic info /joint_states -v
   ros2 interface show sensor_msgs/msg/JointState
   ros2 service list -t
   ros2 action list -t

.. tip::

   La salida de ``ros2 service list`` depende del instante de arranque, los
   namespaces y el lanzamiento seleccionado. Si no se ve algún servicio,
   espera la inicialización y vuelve a consultar.

3. Análisis de los resultados reales del xArm 6
-----------------------------------------------

Esta tabla utiliza las **salidas registradas en el equipo de prácticas**,
no una lista hipotética de servicios. La última prueba confirmó la
planificación de un objetivo de seis articulaciones, mientras que la ejecución
A → B todavía debe comprobarse en esa instalación.

.. list-table:: ¿Qué hemos comprobado realmente?
   :header-rows: 1
   :widths: 22 32 46

   * - Componente
     - Resultado observado
     - Comando de comprobación
   * - ``move_group``
     - Nodo activo con servicios y acciones de MoveIt 2
     - ``ros2 node info /move_group``
   * - MoveIt 2 y OMPL
     - ``move_group`` usa la pipeline ``ompl``; una planificación fue exitosa
     - Ver logs del lanzamiento y llamar a ``/xarm_joint_plan``
   * - ``ros2_control``
     - Controladores cargados y activos
     - ``ros2 control list_controllers``
   * - Hardware fake
     - Aparece ``uf_robot_hardware_ufrobotfakesystemhardware``
     - ``ros2 control list_hardware_components`` y ``ros2 node list``
   * - ``/joint_states``
     - Publica seis posiciones para ``joint1`` ... ``joint6``
     - ``ros2 topic echo /joint_states --once``
   * - ``/move_action``
     - Servidor de la acción ``MoveGroup`` presente
     - ``ros2 action info /move_action``
   * - ``/execute_trajectory``
     - Servidor de acción disponible
     - ``ros2 action info /execute_trajectory``
   * - Control de trayectorias
     - ``xarm6_traj_controller`` activo
     - ``ros2 control list_controllers`` y ``ros2 action list -t``
   * - ``/xarm_joint_plan``
     - **Verificado:** respuesta ``success: true``
     - ``ros2 service call /xarm_joint_plan ...``
   * - Ejecución de A → B
     - **Pendiente de confirmar** en el registro aportado
     - ``/xarm_exec_plan`` + ``/joint_states``

**Comprobaciones complementarias:**

.. code-block:: bash

   ros2 node info /move_group
   ros2 service list -t | grep -E 'compute_fk|compute_ik|compute_cartesian_path|plan_kinematic_path'
   ros2 action list -t
   ros2 control list_controllers
   ros2 control list_hardware_components
   ros2 topic echo /joint_states --once
   ros2 topic info /xarm6_traj_controller/controller_state

En el registro real, ``/move_group`` anunció, entre otros, estos servicios:

- ``/compute_fk`` (``moveit_msgs/srv/GetPositionFK``): cinemática directa.
- ``/compute_ik`` (``moveit_msgs/srv/GetPositionIK``): cinemática inversa.
- ``/compute_cartesian_path`` (``moveit_msgs/srv/GetCartesianPath``): ruta cartesiana.
- ``/plan_kinematic_path`` (``moveit_msgs/srv/GetMotionPlan``): petición de planificación.
- ``/check_state_validity`` (``moveit_msgs/srv/GetStateValidity``): comprobar un estado.
- ``/apply_planning_scene`` (``moveit_msgs/srv/ApplyPlanningScene``): actualizar escena.
- ``/clear_octomap`` (``std_srvs/srv/Empty``): limpiar mapa de ocupación.

No todos estos servicios se utilizarán todavía; algunos corresponden a las
lecciones futuras de cinemática y percepción.

**Interpretación del mensaje de estados**

.. code-block:: bash

   ros2 topic echo /joint_states --once
   ros2 topic echo /xarm6_traj_controller/controller_state
   ros2 topic hz /joint_states

``JointState`` contiene ``name``, ``position``, ``velocity`` y ``effort``.
En las pruebas, los seis valores de ``effort`` aparecieron como ``.nan``:
esto **no representa un esfuerzo medido**, sino datos no disponibles en el
hardware fake. Los valores de ``position`` deben asociarse siempre con la
lista ``name``; no hay que suponer que el orden es fijo si cambia el modelo.

**Controladores activos observados:**

.. code-block:: text

   joint_state_broadcaster  joint_state_broadcaster/JointStateBroadcaster          active
   xarm6_traj_controller    joint_trajectory_controller/JointTrajectoryController active

**Avisos del entorno VirtualBox:** ``Overrun detected`` indica que el ciclo
de control (150 Hz en la sesión registrada, equivalente a 6,67 ms) incumplió
su período. ``/recognize_objects not available`` puede aparecer sin un módulo
de reconocimiento; no impide planificar. Los avisos de nodos duplicados y
pérdida de mensajes requieren comprobar que no queden otros lanzamientos
activos y observar si se repiten continuamente.

4. Arquitectura de planificación y ejecución simuladas
------------------------------------------------------

El flujo que debemos comprender es el siguiente:

.. code-block:: text

    Cliente ROS 2 de AvigTech
       |     solicitud PlanJoint / PlanSingleStraight
       v
    /xarm_joint_plan o /xarm_straight_plan
       |
       v
    xarm_planner_node (servidor C++ UFACTORY)
       |
       v
    move_group / MoveIt 2 (planificacion)
       |
       | plan valido almacenado en el planificador
       v
    /xarm_exec_plan (servicio de ejecucion)
       |
       v
    MoveIt Execution / xarm6_traj_controller
       |
       v
    UFRobotFakeSystemHardware
       |
       v
    joint_state_broadcaster -> /joint_states -> RViz 2

La separación entre **planificar** y **ejecutar** es deliberada. La
trayectoria encontrada por MoveIt no altera por sí sola las posiciones del
robot. El hardware fake actualiza posiciones al procesar los comandos de
trayectoria; RViz muestra ese estado, no un robot conectado.

5. ¿Cómo funciona el servicio ``xarm_planner``?
-----------------------------------------------

``xarm_planner_node`` implementa los servidores. En la rama Jazzy se pueden
consultar las siguientes interfaces de UFACTORY:

.. list-table:: Servicios didácticos del planificador
   :header-rows: 1
   :widths: 31 30 39

   * - Nombre
     - Tipo
     - Objetivo
   * - ``/xarm_joint_plan``
     - ``xarm_msgs/srv/PlanJoint``
     - Planificar un objetivo en radianes (seis juntas)
   * - ``/xarm_pose_plan``
     - ``xarm_msgs/srv/PlanPose``
     - Planificar hasta una pose del efector (sin exigir recta)
   * - ``/xarm_straight_plan``
     - ``xarm_msgs/srv/PlanSingleStraight``
     - Calcular una ruta cartesiana hacia una pose
   * - ``/xarm_exec_plan``
     - ``xarm_msgs/srv/PlanExec``
     - Ejecutar la última trayectoria planificada

**Descubrimiento y definición de los mensajes de servicio:**

.. code-block:: bash

   ros2 service list -t | grep -E 'xarm_(joint|pose|straight|exec)_plan'
   ros2 service type /xarm_joint_plan
   ros2 interface show xarm_msgs/srv/PlanJoint
   ros2 interface show xarm_msgs/srv/PlanExec
   ros2 interface show xarm_msgs/srv/PlanPose
   ros2 interface show xarm_msgs/srv/PlanSingleStraight

Por ejemplo, ``PlanJoint`` intercambia:

.. code-block:: text

   float64[] target
   ---
   bool success

El **cliente** puede ser el comando ``ros2 service call`` o nuestro propio
nodo Python. El **servidor** seguirá siendo ``xarm_planner_node``,
que llama al planificador de MoveIt; no hay que reescribir el SDK.

**¿Qué significan los seis valores de ``target``?**

En ``xarm_msgs/srv/PlanJoint``, ``target`` es un **arreglo de posiciones
articulares objetivo**, no una posición cartesiana. En el modelo xArm 6 hay
seis articulaciones rotativas; sus posiciones se expresan en **radianes** y
se indican en el mismo orden que las juntas ``joint1`` a ``joint6``.

Por ejemplo, para la siguiente solicitud:

.. code-block:: bash

   ros2 service call /xarm_joint_plan xarm_msgs/srv/PlanJoint \
     "{target: [0.25, -0.3, 0.0, 0.0, 0.0, 0.0]}"

se está solicitando esta configuración articular:

.. list-table:: Interpretación del arreglo ``target``
   :header-rows: 1
   :widths: 24 21 21 34

   * - Elemento
     - Articulación
     - Valor (rad)
     - Valor aproximado (grados)
   * - ``target[0]``
     - ``joint1``
     - ``0.25``
     - ``+14.32°``
   * - ``target[1]``
     - ``joint2``
     - ``-0.30``
     - ``-17.19°``
   * - ``target[2]``
     - ``joint3``
     - ``0.0``
     - ``0°``
   * - ``target[3]``
     - ``joint4``
     - ``0.0``
     - ``0°``
   * - ``target[4]``
     - ``joint5``
     - ``0.0``
     - ``0°``
   * - ``target[5]``
     - ``joint6``
     - ``0.0``
     - ``0°``

Los ángulos en grados son una representación para facilitar la lectura.
La petición ROS 2 **debe conservar los radianes**. La conversión es:

.. math::

   \theta_{\mathrm{grados}} = \theta_{\mathrm{radianes}} \frac{180}{\pi}

**Cómo interpretar los signos y el cero:**

- Los seis números especifican **ángulos absolutos** respecto al cero de
  cada articulación definido por el modelo cinemático; no son incrementos
  respecto a la posición actual ni velocidades.
- Un ángulo positivo o negativo indica el sentido de giro **según el eje
  local de esa articulación** y la convención de signos del modelo. No
  significa que todas las juntas giren en el mismo sentido espacial.
- ``0.0`` solicita llevar la articulación a su referencia angular cero.
  **No significa «no mover esa articulación»**. Si actualmente no está en
  cero, también deberá desplazarse.
- ``target`` no representa ``[X, Y, Z, roll, pitch, yaw]`` ni la pose del
  efector final. El posicionamiento del efector se obtiene mediante la
  cinemática directa de las seis juntas.
- La planificación se realiza desde el **estado articular actual** hasta
  esos ángulos, siempre que el objetivo y la trayectoria satisfagan los
  límites, las colisiones y las demás restricciones configuradas.
  Una trayectoria articular no obliga al efector a recorrer una línea recta.

Por ejemplo, si ``joint1`` está en ``1.0`` rad y se envía
``target[0] = 0.25``, se solicita acabar en **0.25 rad**, no sumar
0.25 rad a la posición existente.

**Comprobación con el estado publicado:**

.. code-block:: bash

   ros2 topic echo /joint_states --once

En el mensaje ``sensor_msgs/msg/JointState``, compara la lista ``name``
con la lista ``position``: cada posición corresponde a la articulación
cuyo nombre ocupa **el mismo índice**. Verifica los nombres antes de
comparar, ya que el orden debe leerse del mensaje y no asumirse.
Después de ejecutar correctamente la trayectoria, los valores deberían
aproximarse al objetivo solicitado, dentro de la tolerancia del controlador.

.. note::

   En el ejercicio A se pide ``joint1 = 0.0`` rad; en el ejercicio B se
   pide ``joint1 = 0.25`` rad. Las otras cinco posiciones objetivo son
   iguales. Si A se ejecutó completamente antes que B, el cambio objetivo
   de ``joint1`` es **+0.25 rad (aprox. +14.32°)**. El resultado de
   ``/xarm_joint_plan`` confirma planificación, **no movimiento**: el
   movimiento simulado se solicita aparte con ``/xarm_exec_plan``.

**Ejercicio A: planificar y ejecutar un objetivo articular.**

.. code-block:: bash

   ros2 service call /xarm_joint_plan xarm_msgs/srv/PlanJoint \
     "{target: [0.0, -0.3, 0.0, 0.0, 0.0, 0.0]}"

La respuesta observada fue ``success: true``. Eso significa que se generó
una trayectoria. En el modo fake y **solo cuando el plan fue exitoso**:

.. code-block:: bash

   ros2 service call /xarm_exec_plan xarm_msgs/srv/PlanExec \
     "{wait: true}"

``wait: true`` hace que el servidor espere a que termine la ejecución antes
de devolver la respuesta. Verifica ``success`` y el nuevo ``/joint_states``.

**Ejercicio B: segunda posición articular** (objetivo ilustrativo,
requiere planificador y validación de límites/colisiones):

.. code-block:: bash

   ros2 service call /xarm_joint_plan xarm_msgs/srv/PlanJoint \
     "{target: [0.25, -0.3, 0.0, 0.0, 0.0, 0.0]}"

Si devuelve ``success: true``, ejecuta únicamente en fake:

.. code-block:: bash

   ros2 service call /xarm_exec_plan xarm_msgs/srv/PlanExec \
     "{wait: true}"

Comprueba la diferencia entre los estados A y B:

.. code-block:: bash

   ros2 topic echo /joint_states --field position
   ros2 topic echo /xarm6_traj_controller/controller_state

La diferencia teórica esperada en ``joint1`` es 0,25 rad (aprox. 14,32°),
si ambos movimientos se ejecutan completamente. No se debe confundir un
``success: true`` de planificación con un movimiento ya realizado.

6. Programar nuestro propio cliente ROS 2 con Python
----------------------------------------------------

**Utilizaremos el paquete principal ``mi_pkg_python``**, creado previamente
en :doc:`tutoriales`. **No se crea ningún paquete adicional** ni se cambia
el servidor C++ de UFACTORY. El cliente Python usa ``rclpy`` para enviar
las mismas solicitudes que ``ros2 service call``. Se mantienen los nodos
publicador, suscriptor y demás ejercicios que ya estén en el paquete.

**Paso 1. Incorporar los archivos al paquete que ya existe**

En el ZIP del curso se incluyen los archivos Python sueltos en
``ejemplos_ros2/archivos_para_mi_pkg_python/``; no son otro paquete.
En la raíz del proyecto descargado, copia los archivos siguiendo estas rutas
(o escribe los códigos completos que aparecen a continuación):

.. code-block:: bash

   # Ejecutar desde la raíz del proyecto de documentación descargado
   cp ejemplos_ros2/archivos_para_mi_pkg_python/cliente_plan_*.py \
       ~/ros2_ws/src/mi_pkg_python/mi_pkg_python/

La estructura **existente** quedará así, sin borrar sus archivos anteriores:

.. code-block:: text

   ~/ros2_ws/src/mi_pkg_python/
   ├── package.xml
   ├── setup.py
   ├── setup.cfg
   ├── resource/mi_pkg_python
   ├── mi_pkg_python/
   │   ├── __init__.py
   │   ├── publicador.py             # De las clases anteriores
   │   ├── suscriptor.py             # De las clases anteriores
   │   ├── formato.py                # Monitor de práctica anterior
   │   ├── monitor_articular.py      # Monitor de práctica anterior
   │   ├── cliente_plan_articular.py # Nuevo cliente
   │   ├── cliente_plan_pose.py      # Nuevo cliente
   │   └── cliente_plan_lineal.py    # Nuevo cliente
   ├── launch/
   │   └── monitor_articular.launch.py
   └── test/

**Paso 2. Añadir dependencias en ``package.xml``**

Abre el archivo existente:

.. code-block:: bash

   nano ~/ros2_ws/src/mi_pkg_python/package.xml

**Conserva sus dependencias actuales** (por ejemplo ``rclpy`` y
``std_msgs``) y añade estas líneas dentro de ``<package>``; no dupliques
las que ya estén presentes:

.. code-block:: xml

   <exec_depend>xarm_msgs</exec_depend>
   <exec_depend>geometry_msgs</exec_depend>
   <exec_depend>tf2_ros</exec_depend>

   <!-- Requeridas también por la práctica anterior de monitorización -->
   <exec_depend>sensor_msgs</exec_depend>
   <exec_depend>std_srvs</exec_depend>
   <exec_depend>launch</exec_depend>
   <exec_depend>launch_ros</exec_depend>

``xarm_msgs`` proporciona ``PlanJoint``, ``PlanPose``, ``PlanExec`` y
``PlanSingleStraight``; ``geometry_msgs`` proporciona ``Pose`` y
``tf2_ros`` permite conocer la pose actual mediante transformaciones TF2.
No agregues aquí ``xarm_api`` como dependencia del controlador físico: las
prácticas trabajan con el servidor ``xarm_planner`` en modo fake. El paquete
``xarm_msgs`` debe estar en el mismo workspace o instalado correctamente,
como parte de la compilación de ``xarm_ros2``.

**Paso 3. Registrar los clientes en ``setup.py``**

Abre:

.. code-block:: bash

   nano ~/ros2_ws/src/mi_pkg_python/setup.py

Busca la lista ``'console_scripts'`` dentro de ``entry_points``. **Añade las tres
entradas sin borrar las anteriores**. Por ejemplo, si ya
registraste ``publicador1`` y ``suscriptor1``, el bloque debe quedar:

.. code-block:: python

   entry_points={
       'console_scripts': [
           'publicador1 = mi_pkg_python.publicador:main',
           'suscriptor1 = mi_pkg_python.suscriptor:main',
           'monitor_articular = mi_pkg_python.monitor_articular:main',
           'cliente_plan_articular = mi_pkg_python.cliente_plan_articular:main',
           'cliente_plan_pose = mi_pkg_python.cliente_plan_pose:main',
           'cliente_plan_lineal = mi_pkg_python.cliente_plan_lineal:main',
       ],
   },

Este es **solo el apartado ``entry_points``**, no un reemplazo de todo
``setup.py``. Conserva cualquier otro ejecutable previamente registrado.
Cada entrada sigue el patrón
``nombre_ejecutable = nombre_paquete.nombre_archivo:funcion_principal``.

Si ya has integrado el monitor articular del curso, **conserva su entrada**
``monitor_articular``. Para poder lanzarlo por ``ros2 launch`` también
verifica que ``setup.py`` instale los archivos ``.launch.py``:

.. code-block:: python

   # Agrega esta importación al inicio de setup.py, si no existe:
   from glob import glob

   # Y añade esta tupla a la lista data_files existente:
   ('share/' + package_name + '/launch', glob('launch/*.launch.py')),

No crees un nuevo objeto ``setup()``: modifica el que ya tiene
``mi_pkg_python``, manteniendo ``name``, ``packages``, ``data_files``,
``resource`` y las demás entradas del proyecto original.

**Paso 4. Resolver dependencias y compilar**

.. code-block:: bash

   cd ~/ros2_ws
   rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
   colcon build --symlink-install --packages-select mi_pkg_python
   source install/setup.bash

**Comprobar los ejecutables instalados:**

.. code-block:: bash

   ros2 pkg executables mi_pkg_python

Se espera que aparezcan ``cliente_plan_articular``, ``cliente_plan_pose``
y ``cliente_plan_lineal`` junto con los nodos existentes del curso.
Mantén corriendo ``xarm6_planner_fake.launch.py`` en otra terminal para
que los servicios del fabricante estén disponibles. Los programas de
``mi_pkg_python`` **son clientes**; el servidor original sigue estando
en ``xarm_planner_node``.

**Código: ``cliente_plan_articular.py``**

.. code-block:: python

   """Cliente ROS 2 de planificacion articular y ejecucion opcional de xArm."""

   import argparse
   import math

   import rclpy
   from rclpy.node import Node
   from xarm_msgs.srv import PlanExec, PlanJoint


   class ClientePlanArticular(Node):
       def __init__(self):
           super().__init__('avigtech_cliente_plan_articular')
           self.planificador = self.create_client(PlanJoint, '/xarm_joint_plan')
           self.ejecutor = self.create_client(PlanExec, '/xarm_exec_plan')

       def llamar(self, cliente, solicitud, nombre):
           if not cliente.wait_for_service(timeout_sec=10.0):
               self.get_logger().error(f'No disponible: {nombre}')
               return None

           futuro = cliente.call_async(solicitud)
           rclpy.spin_until_future_complete(self, futuro, timeout_sec=60.0)
           if not futuro.done():
               self.get_logger().error(f'Tiempo de espera agotado: {nombre}')
               return None
           if futuro.exception() is not None:
               self.get_logger().error(f'Error en {nombre}: {futuro.exception()}')
               return None
           return futuro.result()

       def planificar(self, objetivo):
           solicitud = PlanJoint.Request()
           solicitud.target = objetivo
           respuesta = self.llamar(self.planificador, solicitud, '/xarm_joint_plan')
           return respuesta is not None and respuesta.success

       def ejecutar(self):
           solicitud = PlanExec.Request()
           solicitud.wait = True
           respuesta = self.llamar(self.ejecutor, solicitud, '/xarm_exec_plan')
           return respuesta is not None and respuesta.success


   def main(args=None):
       parser = argparse.ArgumentParser(description='Cliente xArm articular (solo fake)')
       parser.add_argument(
           '--target', type=float, nargs=6, required=True,
           metavar=('J1', 'J2', 'J3', 'J4', 'J5', 'J6'),
           help='Seis posiciones articulares en radianes',
       )
       parser.add_argument(
           '--execute', action='store_true',
           help='Ejecutar un plan exitoso, solo tras confirmar el entorno fake',
       )
       opciones, ros_args = parser.parse_known_args(args)
       if not all(math.isfinite(valor) for valor in opciones.target):
           parser.error('Las seis posiciones deben ser valores finitos')

       rclpy.init(args=ros_args)
       nodo = ClientePlanArticular()
       try:
           nodo.get_logger().info(f'Objetivo articular (rad): {opciones.target}')
           if not nodo.planificar(opciones.target):
               nodo.get_logger().error('Planificacion rechazada; no se ejecuta')
               return 1
           nodo.get_logger().info('Planificacion correcta')
           if not opciones.execute:
               nodo.get_logger().info('Solo planificado. Para ejecutar usa --execute.')
               return 0
           if nodo.ejecutar():
               nodo.get_logger().info('Ejecucion informada como exitosa')
               return 0
           nodo.get_logger().error('La ejecucion fallo')
           return 1
       finally:
           nodo.destroy_node()
           rclpy.shutdown()


   if __name__ == '__main__':
       raise SystemExit(main())

**Explicación paso a paso del cliente**

#. ``create_client(PlanJoint, '/xarm_joint_plan')`` construye un cliente con
   el tipo de servicio correcto. No crea un servidor nuevo.
#. ``PlanJoint.Request()`` crea la solicitud y ``target`` contiene las seis
   posiciones articulares **en radianes**.
#. ``call_async()`` envía una petición asíncrona; se usa
   ``spin_until_future_complete()`` para esperar la respuesta en el ejercicio.
#. El atributo ``response.success`` indica si la planificación finalizó bien.
#. Si se solicita ``--execute``, el código usa **otro cliente** del tipo
   ``PlanExec`` y envía ``wait=True``.
#. Ante fallos, tiempos de espera o planificación rechazada, **no ejecuta**.

**Planificar solamente:**

.. code-block:: bash

   ros2 run mi_pkg_python cliente_plan_articular \
     --target 0.0 -0.3 0.0 0.0 0.0 0.0

**Planificar y ejecutar**, solo con el lanzamiento ``planner_fake`` activo:

.. code-block:: bash

   ros2 run mi_pkg_python cliente_plan_articular \
     --target 0.0 -0.3 0.0 0.0 0.0 0.0 --execute

**Segundo punto (B):**

.. code-block:: bash

   ros2 run mi_pkg_python cliente_plan_articular \
     --target 0.25 -0.3 0.0 0.0 0.0 0.0 --execute

.. important::

   Este cliente **no comprueba automáticamente** que el hardware sea fake.
   Confirma ``UFRobotFakeSystemHardware`` con
   ``ros2 control list_hardware_components`` antes de usar ``--execute``.
   Un proceso de planificación y otro cliente que ejecuten simultáneamente
   pueden sobrescribir el último plan del servidor; realiza la práctica
   secuencialmente.

7. Enviar una posición y orientación (pose cartesiana)
--------------------------------------------------------

Hasta ahora se programaron objetivos para las seis articulaciones mediante
``/xarm_joint_plan``. Para solicitar directamente dónde debe llegar el
**efector final** utilizamos ``/xarm_pose_plan``. MoveIt calcula las
configuraciones articulares necesarias, sin que el cliente tenga que
resolver manualmente la cinemática inversa.

.. list-table:: Información del objetivo ``geometry_msgs/Pose``
   :header-rows: 1
   :widths: 30 30 40

   * - Campo
     - Unidad
     - Interpretación
   * - ``position.x`` / ``position.y`` / ``position.z``
     - Metros
     - Posición cartesiana absoluta del efector
   * - ``orientation.x`` / ``orientation.y`` / ``orientation.z`` / ``orientation.w``
     - Cuaternión unitario (sin unidades)
     - Orientación del efector en el marco de planificación

El objetivo se expresa en el marco de planificación de MoveIt. En el
registro de este laboratorio ese marco fue ``world``, y el efector final
fue ``link_eef``. Verifica los nombres si modificas el modelo.

**Diferencia fundamental:** el mensaje ``Pose`` contiene **7 valores**,
pero no son los seis ángulos del robot. El cuaternión representa
orientación, no posición articular. En particular,
``orientation: {x: 0, y: 0, z: 0, w: 1}`` es la rotación identidad con
respecto al marco de planificación; no significa «herramienta vertical».

**Comprobar el servicio:**

.. code-block:: bash

   # Lanzar SOLO la versión planner_fake
   ros2 launch xarm_planner xarm6_planner_fake.launch.py

En una terminal nueva:

.. code-block:: bash

   ros2 service type /xarm_pose_plan
   ros2 interface show xarm_msgs/srv/PlanPose
   ros2 run tf2_ros tf2_echo world link_eef

La definición exacta del servicio es:

.. code-block:: text

   geometry_msgs/Pose target
   ---
   bool success

**Ejemplo: solicitar una pose objetivo absoluta** (valores ilustrativos,
no se garantiza que sean alcanzables ni libres de colisiones):

.. code-block:: bash

   ros2 service call /xarm_pose_plan xarm_msgs/srv/PlanPose \
     "{target: {position: {x: 0.30, y: 0.0, z: 0.25}, \
                orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}"

Si el servidor responde ``success: true``, **ha encontrado un plan**,
pero el robot aún no se ha movido. Para ejecutar el plan en modo fake,
tras comprobar que el controlador corresponde al hardware simulado:

.. code-block:: bash

   ros2 control list_hardware_components
   ros2 service call /xarm_exec_plan xarm_msgs/srv/PlanExec \
     "{wait: true}"

.. warning::

   No reutilices esta práctica de ejecución en un xArm físico sin una
   revisión específica de seguridad. Además, el planificador conserva el
   **último plan generado**: evita que dos clientes planifiquen a la vez
   entre la solicitud y la ejecución.

**¿Y si quiero introducir Roll, Pitch y Yaw en grados?**

El servicio recibe un cuaternión ``(qx, qy, qz, qw)``, no RPY.
Por ejemplo, la rotación de 90° alrededor de Z puede representarse por
``{x: 0, y: 0, z: 0.70710678, w: 0.70710678}``. Este valor describe la
orientación respecto al marco de planificación y no garantiza que la
postura sea alcanzable.

El cliente de AvigTech que sigue permite utilizar RPY en grados y
convierte internamente a un cuaternión empleando la convención
**yaw-pitch-roll (ZYX)**. Como alternativa permite proporcionar las cuatro
componentes directamente con ``--quaternion``.

**Código: ``cliente_plan_pose.py``**

.. code-block:: python

   """Cliente educativo: alcanzar pose XYZ + orientacion en el xArm 6 fake.

   Envia PlanPose al servidor de UFACTORY. La ejecucion es opcional.
   """

   import argparse
   import math

   import rclpy
   from geometry_msgs.msg import Pose
   from rclpy.node import Node
   from xarm_msgs.srv import PlanExec, PlanPose


   def rpy_a_cuaternion(roll, pitch, yaw):
       """Convierte Euler ZYX (roll X, pitch Y, yaw Z), grados -> (x,y,z,w)."""
       r, p, y = (math.radians(v) / 2.0 for v in (roll, pitch, yaw))
       cr, sr = math.cos(r), math.sin(r)
       cp, sp = math.cos(p), math.sin(p)
       cy, sy = math.cos(y), math.sin(y)
       return (
           sr * cp * cy - cr * sp * sy,
           cr * sp * cy + sr * cp * sy,
           cr * cp * sy - sr * sp * cy,
           cr * cp * cy + sr * sp * sy,
       )


   class ClientePlanPose(Node):
       def __init__(self):
           super().__init__('avigtech_cliente_plan_pose')
           self.cliente_pose = self.create_client(PlanPose, '/xarm_pose_plan')
           self.cliente_exec = self.create_client(PlanExec, '/xarm_exec_plan')

       def solicitar(self, cliente, solicitud, nombre):
           if not cliente.wait_for_service(timeout_sec=10.0):
               self.get_logger().error(f'No disponible: {nombre}')
               return None
           futuro = cliente.call_async(solicitud)
           rclpy.spin_until_future_complete(self, futuro, timeout_sec=60.0)
           if not futuro.done():
               self.get_logger().error(f'Tiempo de espera agotado: {nombre}')
               return None
           if futuro.exception() is not None:
               self.get_logger().error(f'Error en {nombre}: {futuro.exception()}')
               return None
           return futuro.result()

       def planificar(self, pose):
           solicitud = PlanPose.Request()
           solicitud.target = pose
           respuesta = self.solicitar(self.cliente_pose, solicitud, '/xarm_pose_plan')
           return respuesta is not None and respuesta.success

       def ejecutar(self):
           solicitud = PlanExec.Request()
           solicitud.wait = True
           respuesta = self.solicitar(self.cliente_exec, solicitud, '/xarm_exec_plan')
           return respuesta is not None and respuesta.success


   def main(args=None):
       parser = argparse.ArgumentParser(description='Objetivo XYZ + orientacion para xArm simulado')
       parser.add_argument('--x', type=float, required=True, help='X absoluta (m)')
       parser.add_argument('--y', type=float, required=True, help='Y absoluta (m)')
       parser.add_argument('--z', type=float, required=True, help='Z absoluta (m)')
       parser.add_argument('--roll', type=float, default=0.0, help='Rotacion X (grados)')
       parser.add_argument('--pitch', type=float, default=0.0, help='Rotacion Y (grados)')
       parser.add_argument('--yaw', type=float, default=0.0, help='Rotacion Z (grados)')
       parser.add_argument('--quaternion', type=float, nargs=4, metavar=('QX','QY','QZ','QW'),
                           help='Cuaternion en lugar de roll/pitch/yaw')
       parser.add_argument('--execute', action='store_true', help='Ejecutar SOLO tras confirmar fake')
       opciones, ros_args = parser.parse_known_args(args)
       valores = [opciones.x, opciones.y, opciones.z,
                  opciones.roll, opciones.pitch, opciones.yaw]
       if not all(math.isfinite(v) for v in valores):
           parser.error('Todos los valores deben ser finitos')
       if opciones.quaternion is not None:
           if any(v != 0.0 for v in (opciones.roll, opciones.pitch, opciones.yaw)):
               parser.error('Usa --quaternion o los angulos RPY, no ambos')
           if not all(math.isfinite(v) for v in opciones.quaternion):
               parser.error('Cuaternion no valido')
           norma = math.sqrt(sum(v*v for v in opciones.quaternion))
           if norma < 1e-9:
               parser.error('El cuaternion no puede ser nulo')
           q = tuple(v / norma for v in opciones.quaternion)
       else:
           q = rpy_a_cuaternion(opciones.roll, opciones.pitch, opciones.yaw)

       objetivo = Pose()
       objetivo.position.x = opciones.x
       objetivo.position.y = opciones.y
       objetivo.position.z = opciones.z
       objetivo.orientation.x, objetivo.orientation.y = q[0], q[1]
       objetivo.orientation.z, objetivo.orientation.w = q[2], q[3]

       rclpy.init(args=ros_args)
       nodo = ClientePlanPose()
       try:
           nodo.get_logger().info(
               f'Meta (world): XYZ=({opciones.x:.3f}, {opciones.y:.3f}, {opciones.z:.3f}) m, '
               f'q=({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f})'
           )
           if not nodo.planificar(objetivo):
               nodo.get_logger().error('La planificacion por pose no fue exitosa')
               return 1
           nodo.get_logger().info('Planificacion por pose exitosa')
           if opciones.execute:
               nodo.get_logger().warn('Ejecutando: verifica previamente que es hardware fake')
               if not nodo.ejecutar():
                   return 1
               nodo.get_logger().info('Ejecucion reportada como exitosa')
           else:
               nodo.get_logger().info('No se ejecuto: anade --execute SOLO en fake')
           return 0
       finally:
           nodo.destroy_node()
           rclpy.shutdown()


   if __name__ == '__main__':
       raise SystemExit(main())

**Compilación:** al agregar ``cliente_plan_pose.py`` al mismo paquete,
recompila ``mi_pkg_python``; el registro en ``setup.py`` y la dependencia
a ``geometry_msgs`` ya quedaron explicados en el paso 3 de la sección 6.

.. code-block:: bash

   cd ~/ros2_ws
   colcon build --symlink-install --packages-select mi_pkg_python
   source install/setup.bash

**Ejemplo con posición XYZ y orientación RPY en grados:**

.. code-block:: bash

   ros2 run mi_pkg_python cliente_plan_pose \
     --x 0.30 --y 0.0 --z 0.25 \
     --roll 0 --pitch 0 --yaw 0

**Ejemplo expresando el cuaternión explícitamente:**

.. code-block:: bash

   ros2 run mi_pkg_python cliente_plan_pose \
     --x 0.30 --y 0.0 --z 0.25 \
     --quaternion 0 0 0.70710678 0.70710678

Para ejecutar después de planificar, **únicamente con**
``xarm6_planner_fake.launch.py`` y verificación previa del hardware,
puedes añadir ``--execute``. La planificación por pose es de tipo PTP:
**no garantiza una recta entre A y B**.

**Comparación con el movimiento rectilíneo:**

- ``/xarm_pose_plan`` establece el objetivo cartesiano y utiliza
  ``setPoseTarget()`` junto con ``plan()``. MoveIt encuentra una ruta
  que cumple las restricciones; la punta puede describir una curva.
- ``/xarm_straight_plan`` usa ``computeCartesianPath()`` para interpolar
  el camino entre la pose actual A y el objetivo B. El código de UFACTORY
  utiliza pasos de 0,005 m y permite una fracción incompleta desde 0,9.
  Por eso el cliente lineal del siguiente apartado **no ejecuta**
  automáticamente el resultado.

El siguiente apartado estudia esa diferencia con detalle.

8. PTP frente a movimiento cartesiano rectilíneo
------------------------------------------------

Hasta aquí hemos solicitado una **configuración articular** de destino.
El planificador de UFACTORY emplea ``MoveGroupInterface``:

- Para ``/xarm_joint_plan`` llama a ``setJointValueTarget()`` y luego
  a ``plan()``.
- Para ``/xarm_pose_plan`` llama a ``setPoseTarget()`` y luego a
  ``plan()``. Aunque la meta sea cartesiana, **no exige** una línea recta
  para el efector final.
- En ambos casos, el pipeline del registro utiliza OMPL. Se busca un
  camino de configuraciones articulares que satisfaga restricciones y evite
  colisiones. La geometría del recorrido del efector **puede ser curva**.

**¿Qué significa una trayectoria rectilínea A → B?**

Tomamos ``A`` como la posición cartesiana actual del efector y ``B`` como
la meta, ambos en el mismo marco (``world`` en el registro del equipo):

.. math::

   \mathbf{p}(s) = \mathbf{p}_A + s(\mathbf{p}_B-\mathbf{p}_A),
   \qquad 0 \leq s \leq 1

Con la orientación del efector fija en este primer ejercicio. El
planificador cartesiano interpola posiciones sucesivas de esa recta, obtiene
soluciones articulares mediante cinemática inversa y valida límites y
colisiones de los puntos intermedios.

El código oficial de la rama Jazzy implementa el servicio
``/xarm_straight_plan`` mediante ``computeCartesianPath()``. En el archivo
``xarm_planner.cpp`` se define ``eef_step = 0.005`` (5 mm) y se acepta como
exitosa una fracción calculada ``>= 0.9``. La respuesta pública solo incluye
``success``; **no permite conocer desde el cliente si se completó el 100 %**.

.. warning::

   **No ejecutes automáticamente** un plan cartesiano basándote solo en
   ``success: true`` de ``/xarm_straight_plan``: puede haberse calculado
   una ruta parcial. Para una aplicación que exija llegar a B, se debe
   recuperar ``fraction``, exigir por ejemplo ``fraction >= 0.999``, validar
   colisiones y verificar la pose final. Una ampliación posible utiliza
   ``/compute_cartesian_path`` directamente o modifica el servidor C++.

9. Crear B a partir de la pose actual A con TF2
-----------------------------------------------

En tu sesión el planificador informó:

.. code-block:: text

   Planning frame: world
   End effector link: link_eef

La siguiente práctica consulta con TF2 la transformación
``world -> link_eef``. Obtiene A, desplaza **20 mm en X** manteniendo Y, Z y
orientación, y envía B a ``/xarm_straight_plan``. Si se usa una configuración
con prefijos o marcos diferentes, hay que ajustar esos nombres.

**Inspección de los marcos de referencia:**

.. code-block:: bash

   ros2 run tf2_ros tf2_echo world link_eef
   ros2 interface show xarm_msgs/srv/PlanSingleStraight
   ros2 service type /xarm_straight_plan

**Código: ``cliente_plan_lineal.py``**

.. code-block:: python

   """Calcula una meta B desde TF2 y solicita una trayectoria cartesiana.

   No ejecuta el plan: el servidor de UFACTORY puede aceptar fracciones >= 0.9.
   """

   import argparse
   import math
   import time

   import rclpy
   from geometry_msgs.msg import Pose
   from rclpy.node import Node
   from rclpy.time import Time
   from tf2_ros import Buffer, TransformListener
   from xarm_msgs.srv import PlanSingleStraight


   class ClientePlanLineal(Node):
       def __init__(self):
           super().__init__('avigtech_cliente_plan_lineal')
           self.buffer = Buffer()
           self.escucha = TransformListener(self.buffer, self)
           self.planificador = self.create_client(
               PlanSingleStraight, '/xarm_straight_plan'
           )

       def pose_actual(self, origen='world', efector='link_eef'):
           fin = time.monotonic() + 10.0
           while rclpy.ok() and time.monotonic() < fin:
               if self.buffer.can_transform(origen, efector, Time()):
                   transformacion = self.buffer.lookup_transform(
                       origen, efector, Time()
                   )
                   actual = Pose()
                   actual.position.x = transformacion.transform.translation.x
                   actual.position.y = transformacion.transform.translation.y
                   actual.position.z = transformacion.transform.translation.z
                   actual.orientation = transformacion.transform.rotation
                   return actual
               rclpy.spin_once(self, timeout_sec=0.1)
           self.get_logger().error(f'TF no disponible: {origen} -> {efector}')
           return None

       def planificar(self, objetivo):
           if not self.planificador.wait_for_service(timeout_sec=10.0):
               self.get_logger().error('No disponible /xarm_straight_plan')
               return False
           solicitud = PlanSingleStraight.Request()
           solicitud.target = objetivo
           futuro = self.planificador.call_async(solicitud)
           rclpy.spin_until_future_complete(self, futuro, timeout_sec=60.0)
           if not futuro.done() or futuro.exception() is not None:
               self.get_logger().error('Error o timeout en la planificacion lineal')
               return False
           return bool(futuro.result().success)


   def main(args=None):
       parser = argparse.ArgumentParser(description='Planificacion lineal xArm (solo fake)')
       parser.add_argument('--dx', type=float, default=0.02, help='Delta X en metros')
       parser.add_argument('--dy', type=float, default=0.0, help='Delta Y en metros')
       parser.add_argument('--dz', type=float, default=0.0, help='Delta Z en metros')
       opciones, ros_args = parser.parse_known_args(args)
       if not all(math.isfinite(v) for v in (opciones.dx, opciones.dy, opciones.dz)):
           parser.error('Los desplazamientos deben ser finitos')

       rclpy.init(args=ros_args)
       nodo = ClientePlanLineal()
       try:
           a = nodo.pose_actual()
           if a is None:
               return 1
           b = Pose()
           b.position.x = a.position.x + opciones.dx
           b.position.y = a.position.y + opciones.dy
           b.position.z = a.position.z + opciones.dz
           b.orientation = a.orientation
           nodo.get_logger().info(
               f'A = ({a.position.x:.3f}, {a.position.y:.3f}, {a.position.z:.3f}) m'
           )
           nodo.get_logger().info(
               f'B = ({b.position.x:.3f}, {b.position.y:.3f}, {b.position.z:.3f}) m'
           )
           exito = nodo.planificar(b)
           nodo.get_logger().info(f'Resultado de planificacion: {exito}')
           nodo.get_logger().warn(
               'NO se ejecuta: success=True puede significar >=90% del recorrido. '
               'Inspecciona la fraccion real antes de ejecutar.'
           )
           return 0 if exito else 1
       finally:
           nodo.destroy_node()
           rclpy.shutdown()


   if __name__ == '__main__':
       raise SystemExit(main())

**Ejecutar la planificación sin mover todavía el robot:**

.. code-block:: bash

   ros2 run mi_pkg_python cliente_plan_lineal --dx 0.02

El programa informa las coordenadas cartesianas A y B **en metros** y devuelve
el booleano de planificación. No llama a ``/xarm_exec_plan`` porque el
servidor oficial no expone la fracción alcanzada; necesitamos inspeccionarla
antes de garantizar el destino.

**¿Cómo haríamos una recta completa A → B en una aplicación posterior?**

#. Leer la pose actual A desde el estado vigente de TF2/MoveIt.
#. Definir B en el **mismo marco de referencia**; por ejemplo, A + 0,02 m
   en el eje X de ``world``.
#. Calcular puntos intermedios de la recta con orientación constante.
#. Invocar ``computeCartesianPath()`` / ``GetCartesianPath`` con control de
   colisiones y un tamaño de paso apropiado (5 mm en el código del fabricante).
#. Exigir una fracción prácticamente completa (por ejemplo ``>= 0.999``)
   y rechazar movimientos con saltos articulares o restricciones incumplidas.
#. Parametrizar tiempos y velocidades, revisar la trayectoria y **solo
   después** solicitar su ejecución fake.
#. Comparar la pose realmente alcanzada con B, con una tolerancia definida.

**Importante:** una ruta cartesiana recta es una restricción sobre la
trayectoria **geométrica** del efector; no implica velocidad cartesiana
constante. El retemporizado y la ejecución son problemas relacionados, pero
separados.

10. Resultados y preguntas de comprobación
------------------------------------------

.. list-table:: Registro del laboratorio
   :header-rows: 1
   :widths: 33 37 30

   * - Evidencia
     - Comando o lectura
     - Resultado esperado
   * - Controladores
     - ``ros2 control list_controllers``
     - Dos controladores activos
   * - Estado inicial A
     - ``/joint_states``
     - Seis posiciones numéricas
   * - Planificación articular A/B
     - ``/xarm_joint_plan``
     - ``success: true`` si hay plan válido
   * - Ejecución A/B
     - ``/xarm_exec_plan``
     - ``success: true`` y cambio en ``/joint_states``
   * - Pose inicial cartesiana
     - ``tf2_echo world link_eef``
     - Traslación y cuaternión
   * - Planificación por posición/orientación
     - ``/xarm_pose_plan``
     - Booleano de planificación, no ejecución
   * - Planificación rectilínea
     - ``/xarm_straight_plan``
     - Booleano; **no** certifica 100 %

**Preguntas y respuestas**

#. ¿Qué diferencias existen entre ``PlanJoint`` y ``PlanPose``? **El primero
   expresa seis ángulos (rad); el segundo una posición XYZ (m) y un
   cuaternión (qx, qy, qz, qw)**.

#. ¿Por qué una respuesta ``success: true`` de ``/xarm_joint_plan`` no
   significa que el robot se haya movido? **Porque solo valida el plan**.
#. ¿Cuál es el servidor y cuál es el cliente? **Servidor:**
   ``xarm_planner_node``. **Clientes:** ``ros2 service call`` o nuestro nodo
   Python de AvigTech.
#. ¿Qué publica ``/joint_states``? **Los nombres, posiciones, velocidades y
   esfuerzos (si están disponibles)** de las juntas.
#. ¿Por qué ``xarm_pose_plan`` no implica una recta A → B? **Porque llama a
   ``plan()`` para una meta cartesiana, sin imponer el camino geométrico**.
#. ¿Qué herramienta se utiliza para una trayectoria recta? **El servicio
   ``/xarm_straight_plan`` basado en ``computeCartesianPath()``**.
#. ¿Por qué se debe revisar ``fraction``? **Porque el servidor de UFACTORY
   acepta fracciones desde 0,9 y un plan parcial no garantiza alcanzar B**.

11. Referencias técnicas
------------------------

- `Repositorio xarm_ros2 (rama Jazzy)
  <https://github.com/xArm-Developer/xarm_ros2/tree/jazzy>`__.
- `xarm_planner_node.cpp (servidores y callbacks)
  <https://github.com/xArm-Developer/xarm_ros2/blob/jazzy/xarm_planner/src/xarm_planner_node.cpp>`__.
- `xarm_planner.cpp (planificación, fracción y ejecución)
  <https://github.com/xArm-Developer/xarm_ros2/blob/jazzy/xarm_planner/src/xarm_planner.cpp>`__.
- `PlanPose.srv
  <https://github.com/xArm-Developer/xarm_ros2/blob/jazzy/xarm_msgs/srv/PlanPose.srv>`__.
- `PlanSingleStraight.srv
  <https://github.com/xArm-Developer/xarm_ros2/blob/jazzy/xarm_msgs/srv/PlanSingleStraight.srv>`__.
- `MoveGroupInterface::computeCartesianPath()
  <https://moveit.picknik.ai/main/api/html/classmoveit_1_1planning__interface_1_1MoveGroupInterface.html>`__.

.. note::

   Las lecciones futuras abordarán en profundidad **acciones ROS 2,
   cinemática y programación de planificación personalizada**. Esta unidad
   se limita a identificar sus interfaces y demostrar el uso de servicios
   y estados articulares en un entorno sin hardware físico.
