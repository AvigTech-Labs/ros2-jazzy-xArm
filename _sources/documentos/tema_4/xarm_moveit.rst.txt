Práctica xArm: planificación con MoveIt 2
==========================================

Propósito
---------

Estudiar el paso desde una **posición articular** hasta una trayectoria
planificada y validada en RViz 2 utilizando el modelo xArm 6 de la rama
Jazzy. Se trabaja inicialmente sin actuadores reales.

Conceptos
---------

- **Espacio articular:** vector ``q = [q1, q2, q3, q4, q5, q6]``.
- **Pose cartesiana:** posición y orientación del efector final.
- **Cinemática directa:** obtener la pose del efector a partir de ``q``.
- **Cinemática inversa:** encontrar configuraciones ``q`` para una pose.
- **Planificación:** generar una trayectoria compatible con los límites,
  el escenario de colisión y el grupo de planificación.
- **Ejecución fake:** representar el movimiento sin controlar el brazo real.

Primera práctica
----------------

Con el entorno configurado automáticamente en ``~/.bashrc``:

.. code-block:: bash

   ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py

En RViz 2, ubica el panel **MotionPlanning**:

#. Selecciona el grupo de planificación que corresponda al brazo.
#. Revisa la configuración articular inicial y los límites mostrados.
#. Configura un objetivo alcanzable mediante el panel interactivo.
#. Pulsa **Plan** y analiza la trayectoria previa a ejecutarla.
#. Con el controlador de demostración, compara lo planificado con la
   visualización del movimiento sin usar hardware real.

El nombre del grupo y los pasos exactos del panel pueden variar con
la configuración MoveIt de la rama instalada. Registra el nombre que
aparezca en tu sesión.

Observar qué ocurre en ROS 2
----------------------------

En otra terminal:

.. code-block:: bash

   ros2 node list
   ros2 topic list -t
   ros2 action list -t
   ros2 control list_controllers

**Actividad:** identifica un nodo de planificación, un tópico de
estado y una acción o controlador que intervenga en el flujo, si los
expone esta configuración. Explica por qué no son lo mismo.

Planificación mediante API: siguiente nivel
-------------------------------------------

El repositorio oficial incluye ``xarm_planner`` para ejemplos de
planificación mediante interfaces de MoveIt 2. Para ejecutar sus demos
utiliza **una sesión alternativa**, no simultánea con el lanzamiento
anterior:

.. code-block:: bash

   ros2 launch xarm_planner xarm6_planner_fake.launch.py

El fabricante ofrece clientes de prueba para planificación en
espacio articular y cartesiano. Antes de ejecutarlos, estudia qué
trayectorias solicitan, examina su código y verifica que estés en
modo ``fake``. Consulta las instrucciones actualizadas en
`ReadMe.md de Jazzy
<https://github.com/xArm-Developer/xarm_ros2/blob/jazzy/ReadMe.md>`__.

Ampliación opcional: Gazebo Harmonic
------------------------------------

La rama Jazzy indica soporte para Gazebo Harmonic. Su README también
menciona limitaciones de plugins, de modo que no se presupone paridad
con los ejemplos antiguos de Gazebo Classic. La guía básica utiliza
RViz 2 y MoveIt fake para evitar requisitos gráficos y controladores
adicionales; un laboratorio de física requiere validar las dependencias
de Gazebo para la revisión exacta del repositorio.

Reto de evaluación
------------------

Documenta dos objetivos articulares seguros (en representación fake),
compara sus rutas y explica cómo influyen el estado inicial, los
límites de las juntas y las restricciones de colisión.
