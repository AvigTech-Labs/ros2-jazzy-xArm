Práctica xArm: URDF, Xacro, TF2 y control
==========================================

El paquete ``xarm_description`` es el punto de partida para comprender
la geometría y la estructura cinemática del xArm 6. Esta unidad conecta
los conceptos de :doc:`modelo_digital` y :doc:`gemelo_digital` con un
modelo real mantenido por su fabricante.

URDF y Xacro: qué estudiar
--------------------------

- ``link``: define un eslabón con geometría visual, colisión e inercia.
- ``joint``: representa una relación móvil o fija entre dos eslabones.
- ``origin``: define la transformación geométrica entre marcos.
- ``axis`` y ``limit``: describen el eje y rango articular.
- Xacro: permite macros y parámetros para mantener variantes de modelos.

En el workspace, examina los archivos oficiales **sin editarlos**:

.. code-block:: bash

   cd ~/ros2_ws/src/xarm_ros2
   find xarm_description -type f \( -name '*.xacro' -o -name '*.urdf' \) | head -30
   ros2 pkg prefix xarm_description

.. note::

   El archivo de entrada Xacro puede cambiar con las revisiones del
   repositorio. Identifícalo en el lanzamiento oficial, en vez de
   copiar rutas del paquete de ROS 1 o generar un URDF alternativo.

Transformaciones y TF2
----------------------

Inicia la visualización de la descripción:

.. code-block:: bash

   ros2 launch xarm_description xarm6_rviz_display.launch.py

Con el entorno activo en otra terminal:

.. code-block:: bash

   ros2 topic list -t | grep -E 'tf|joint_states'
   ros2 run tf2_tools view_frames

``view_frames`` genera información gráfica sobre los marcos recibidos
(si hay un publicador TF activo). Si no aparece un marco, no se debe
inventar un nombre: revisa las transformaciones efectivamente emitidas.

**Ejercicio:** elige tres eslabones consecutivos y explica qué
transformaciones dependen de las posiciones articulares y cuáles son
fijas. Contrasta con las matrices homogéneas que conoces.

De URDF a ros2_control
----------------------

``ros2_control`` permite separar la descripción del hardware, los
controladores y las interfaces de comando/estado. El paquete
``xarm_controller`` contiene integraciones propias del fabricante.

Para aprender los comandos de inspección, primero inicia el escenario
con controlador de demostración de MoveIt:

.. code-block:: bash

   ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py

En otra terminal:

.. code-block:: bash

   ros2 control list_controllers
   ros2 control list_hardware_interfaces
   ros2 action list -t

La disponibilidad de ``controller_manager`` y el conjunto de
interfaces depende del escenario que inicies. Si una consulta falla,
registra el mensaje e identifica qué componente no se lanzó.

**Diferencia clave:** los controladores fake no son un banco de pruebas
para esfuerzo, fricción, golpes o seguridad del equipo físico.

Lecturas
--------

- `xarm_ros2 oficial <https://github.com/xArm-Developer/xarm_ros2/tree/jazzy>`__.
- `ros2_control para Jazzy <https://control.ros.org/jazzy/index.html>`__.
