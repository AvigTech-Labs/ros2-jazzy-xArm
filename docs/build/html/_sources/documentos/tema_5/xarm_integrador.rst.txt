Proyecto integrador: laboratorio xArm 6 con ROS 2 Jazzy
=======================================================

Desafío
-------

Construir una pequeña aplicación que **observe** el estado del robot,
lo represente y planifique una tarea de manipulación en un entorno
simulado, reuniendo los conceptos estudiados.

**Escenario:** un objeto debe trasladarse desde una estación A a una
estación B mediante una secuencia lógica de aproximación, agarre,
traslado y liberación. En el curso inicial, se evalúa la planificación
en RViz y se **simulan los eventos de agarre**; no se afirma que un
objeto se mueva físicamente si no hay simulación del objeto, sensor,
colisiones y pinza apropiados.

Arquitectura recomendada
------------------------

::

   [xarm_description / robot_state_publisher]
                       |
                  JointState
                       v
              [monitor_articular]
                   |       \
          /avigtech/xarm/  servicio Trigger
              resumen       (consulta)
                   |
          [panel o registro]

   [operador] -> [planificador MoveIt 2]
                         |
                  [controlador fake]
                         |
                   [RViz 2]

Fase 1. Preparación
-------------------

#. Instala y compila ``xarm_ros2`` (rama Jazzy).
#. Incorpora ``avigtech_xarm_intro`` como paquete adicional.
#. Ejecuta el lanzamiento fake del robot con MoveIt 2.
#. Descubre el tópico ``JointState`` que está activo y configúralo en
   el monitor educativo.

Fase 2. Registro de estados
---------------------------

#. Publica el resumen y consulta el servicio ``Trigger``.
#. Registra las posiciones antes y después de dos planificaciones.
#. Agrega una marca de tiempo de captura en un registro CSV propio.
#. Explica las unidades y el uso de nombres de articulaciones.

Fase 3. Planificación de la tarea
---------------------------------

#. Define dos puntos de trabajo alcanzables en una escena virtual.
#. Identifica posiciones de aproximación y retiro.
#. Planifica cada movimiento con los controles de RViz 2.
#. Registra el resultado de planificación y los cambios de estado.
#. Representa la secuencia de eventos de agarre/liberación, dejando
   claro que el proceso es lógico y no controla una pinza física.

Fase 4. Ampliaciones
--------------------

Una vez dominada la base pueden incluirse:

- Cámara RealSense y AprilTags (ver :doc:`proyecto_1`).
- Lectura de señales remotas desde ESP32 y MQTT
  (ver :doc:`../tema_3/dispositivos`).
- Control de secuencias con árboles de comportamiento
  (ver :doc:`../tema_4/behavior_trees`).
- Gazebo Harmonic, tras validar las dependencias y plugins concretos
  del repositorio xArm para Jazzy.

Entregables
-----------

- Diagrama de nodos, tópicos, parámetros, servicios y acciones.
- Código del paquete creado por el estudiante.
- Evidencias del modelo en RViz y de los planes de MoveIt.
- Descripción de los límites y riesgos antes de un ensayo real.
- Bitácora con nombres exactos de tópicos y tipos observados.

Criterios de aceptación
-----------------------

#. El paquete educativo se compila sin modificar el código del fabricante.
#. Un mensaje ``JointState`` real o de demostración llega al monitor.
#. El servicio de consulta devuelve el último estado observado.
#. Se visualiza al menos una trayectoria planificada en RViz.
#. Se distinguen explícitamente tres escenarios: visualización del
   modelo, controlador fake y robot físico.

.. warning::

   No se incluyen instrucciones automáticas de ejecución sobre el xArm
   real en esta evaluación inicial. Un laboratorio con actuadores
   necesita revisión profesional de límites, colisiones, E-stop,
   acceso a red y procedimiento de operación segura.
