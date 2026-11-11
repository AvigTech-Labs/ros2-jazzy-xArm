Instalación de xArm ROS 2 para Jazzy
=====================================

Este tutorial complementa :doc:`instalacionROS2` y utiliza el repositorio
oficial `xarm_ros2 <https://github.com/xArm-Developer/xarm_ros2/tree/jazzy>`__.
Comienza con una ejecución **sin hardware**.

0. Verificar el entorno
-----------------------

Abre una terminal nueva:

.. code-block:: bash

   echo "$ROS_DISTRO"    # Debe imprimir jazzy
   lsb_release -rs       # Debe imprimir 24.04
   python3 --version     # Python 3.12 en Ubuntu 24.04

.. note::

   Se recomienda Ubuntu 24.04 instalado de manera nativa para el trabajo
   con RViz, MoveIt 2 y Gazebo Harmonic.

1. Preparar un espacio de trabajo
---------------------------------

.. code-block:: bash

   mkdir -p ~/ros2_ws/src
   cd ~/ros2_ws
   colcon build --symlink-install
   source install/setup.bash

**Activación automática del espacio de trabajo (solo una vez):**

En lugar de escribir ``source ~/ros2_ws/install/setup.bash`` al abrir
cada terminal, agrega esta instrucción a ``~/.bashrc`` **después** de
haber generado ``install/setup.bash`` con ``colcon build``:

.. code-block:: bash

   echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
   source ~/.bashrc

.. important::

   Agrega la línea una sola vez, para evitar duplicados. El archivo
   ``~/.bashrc`` debe cargar primero ``/opt/ros/jazzy/setup.bash`` y
   después ``~/ros2_ws/install/setup.bash``. Usa ``tail -n 10 ~/.bashrc``
   para comprobar el orden. Cuando crees o actualices paquetes, vuelve a
   ejecutar ``colcon build``; la activación del workspace será automática
   en terminales Bash nuevas.

Cuando agregues paquetes con dependencias nuevas, instálalas antes de
compilar, desde la raíz del workspace:

.. code-block:: bash

   rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
   colcon build --symlink-install
   source install/setup.bash

2. Preparar las herramientas
----------------------------

.. code-block:: bash

   sudo apt update
   sudo apt install -y git python3-colcon-common-extensions \
       python3-rosdep ros-jazzy-moveit ros-jazzy-ros2-control \
       ros-jazzy-ros2-controllers

   rosdep update # Recomendado una vez por mes 

El repositorio puede requerir dependencias adicionales. Se resolverán con
``rosdep`` antes de construir el workspace.

3. Clonar la rama correcta
--------------------------

.. code-block:: bash

   cd ~/ros2_ws/src
   git clone -b jazzy --recursive \
       https://github.com/xArm-Developer/xarm_ros2.git

   # Verificar rama y submódulos:
   git -C xarm_ros2 branch --show-current
   git -C xarm_ros2 submodule status

.. warning::

   No descargues solo el ZIP de GitHub si vas a compilar: el proyecto
   necesita submódulos Git. Si ya clonaste sin ``--recursive``, usa
   ``git -C ~/ros2_ws/src/xarm_ros2 submodule update --init --recursive``.

4. Resolver dependencias y compilar
-----------------------------------

.. code-block:: bash

   cd ~/ros2_ws
   rosdep install --from-paths src --ignore-src \
       --rosdistro jazzy -y
   colcon build --symlink-install
   source install/setup.bash

**Cargar el workspace automáticamente en terminales nuevas (una vez):**

.. code-block:: bash

   grep -qxF 'source ~/ros2_ws/install/setup.bash' ~/.bashrc || \
       echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
   source ~/.bashrc

La configuración de ``~/.bashrc`` debe activar **primero Jazzy** y
**después el workspace**. No repitas el ``echo`` si la línea ya existe;
verifica con ``tail -n 10 ~/.bashrc``. Si prefieres el procedimiento
completo, consulta :doc:`instalacionROS2`.

.. note::

   Las dependencias y la compilación deben verificarse en Ubuntu 24.04
   con ROS Jazzy instalado. No mezcles paquetes de otra distribución.
   Consulta el README de la **rama jazzy** si cambian las dependencias.


5. Resolver incompatibilidades de Gazebo Harmonic en Jazzy
----------------------------------------------------------

Al compilar la rama ``jazzy`` del fabricante puede aparecer el error:

.. code-block:: text

   CMake Error at CMakeLists.txt:20 (find_package):
     Could not find a package configuration file provided by "gz-sim8"
     with any of the following names:
       gz-sim8Config.cmake
       gz-sim8-config.cmake

El problema se presenta en ``xarm_gazebo``. No significa que hayan fallado
los paquetes ``xarm_description``, ``xarm_msgs`` o ``xarm_controller``.
El aviso de ``on_init(const HardwareInfo&) is deprecated`` en
``xarm_controller`` es una **advertencia**, no el fallo de compilación.

**Paso A. Verificar los paquetes vendor de Jazzy**

.. code-block:: bash

   sudo apt update
   sudo apt install -y ros-jazzy-gz-sim-vendor ros-jazzy-sdformat-vendor
   ros2 pkg prefix gz_sim_vendor
   ros2 pkg prefix sdformat_vendor

**Paso B. Adaptar la búsqueda de dependencias en CMake**

Abre el archivo local (esto modifica la copia clonada del fabricante):

.. code-block:: bash

   nano ~/ros2_ws/src/xarm_ros2/xarm_gazebo/CMakeLists.txt

Si la versión de tu rama contiene las instrucciones:

.. code-block:: cmake

   find_package(ament_cmake REQUIRED)
   find_package(gz-sim8 REQUIRED)
   find_package(sdformat14 REQUIRED)

Sustituye esas tres líneas por:

.. code-block:: cmake

   find_package(ament_cmake REQUIRED)
   find_package(gz_sim_vendor REQUIRED)
   find_package(sdformat_vendor REQUIRED)
   find_package(gz-sim REQUIRED)
   find_package(sdformat REQUIRED)

En el mismo archivo, si se enlaza con el objetivo versionado:

.. code-block:: cmake

   target_link_libraries(gazebo_mimic_joint_plugin
     gz-sim8::gz-sim8
   )

Utiliza el objetivo expuesto por el paquete vendor:

.. code-block:: cmake

   target_link_libraries(gazebo_mimic_joint_plugin
     gz-sim::gz-sim
   )

**Paso C. Recompilar y verificar**

.. code-block:: bash

   cd ~/ros2_ws
   colcon build --symlink-install --packages-select xarm_gazebo \
       --cmake-clean-cache
   colcon build --symlink-install
   source install/setup.bash
   ros2 pkg prefix xarm_gazebo

.. important::

   Estas modificaciones se aplican solo si tu copia local contiene las
   instrucciones indicadas. No sustituyas ciegamente un CMakeLists más
   reciente. Si no se encuentran los objetivos ``gz-sim`` o ``sdformat``
   después de instalar los paquetes vendor, verifica los targets que
   exporta tu revisión o usa el SDK de desarrollo compatible con
   Gazebo Harmonic; no mezcles bibliotecas de otras versiones.

**Incidencia documentada por la comunidad**

La incidencia oficial `xarm_ros2 #174
<https://github.com/xArm-Developer/xarm_ros2/issues/174>`__
(registrada el 7 de agosto de 2026) reporta que las dependencias
``gz-sim8`` y ``sdformat14`` tampoco se resuelven correctamente como
**claves rosdep** en Ubuntu 24.04 / Jazzy. Un colaborador recomienda
utilizar ``gz_sim_vendor`` y ``sdformat_vendor`` en ``package.xml``.
Este reporte de ``rosdep`` está **relacionado**, pero no es el mismo
mensaje de error de ``find_package`` que se muestra arriba.

Si ``rosdep install`` falla por esas claves, inspecciona
``xarm_gazebo/package.xml`` y consulta la propuesta de cambio en el
`pull request #175
<https://github.com/xArm-Developer/xarm_ros2/pull/175>`__,
antes de ajustar las dependencias declaradas.

.. note::

   El repositorio oficial puede corregir estos problemas en revisiones
   posteriores. Antes de aplicar un parche local compara la rama
   ``jazzy`` instalada y su ``CMakeLists.txt`` con el código actualizado.

6. Primera ejecución: solo visualización
----------------------------------------

En una terminal nueva, el entorno de Jazzy y el workspace se cargarán
mediante ``~/.bashrc`` (configurado en el paso 4):

.. code-block:: bash

   ros2 launch xarm_description xarm6_rviz_display.launch.py

**Comprueba:** el modelo debe ser visible en RViz 2. Examina su árbol de
juntas y la interfaz de ``joint_state_publisher_gui`` si está habilitada.

En otra terminal, con el mismo entorno activado:

.. code-block:: bash

   ros2 node list
   ros2 topic list -t
   ros2 topic find sensor_msgs/msg/JointState
   ros2 param list

El nombre del tópico articular puede variar según el lanzamiento y
namespace. **No supongas** que es siempre ``/xarm/joint_states``.

7. Segunda ejecución: planificación con MoveIt 2
------------------------------------------------

Cierra la sesión de visualización anterior antes de lanzar el ejemplo
siguiente, para evitar nodos y controladores duplicados.

.. code-block:: bash

   ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py

La opción ``fake`` permite estudiar planificación y ejecución demostrativa
sin conectarse a un xArm real. **No es simulación física de Gazebo**.

.. tip::

   Para añadir el modelo de pinza en sesiones compatibles:
   ``ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py add_gripper:=true``.
   No actives simultáneamente pinza normal y de vacío.

Si no aparece ``xarm_moveit_config`` al ejecutar ``ros2 launch``, comprueba
primero que cargaste el workspace y que se compiló ese paquete:

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   source ~/ros2_ws/install/setup.bash
   ros2 pkg prefix xarm_moveit_config
   colcon list --names-only | grep -x xarm_moveit_config

Si Colcon reconoce el paquete pero ROS 2 todavía no lo encuentra, ejecuta
``colcon build --symlink-install --packages-up-to xarm_moveit_config``
desde ``~/ros2_ws`` y vuelve a cargar ``install/setup.bash``.


Lectura oficial
---------------

`README de xarm_ros2 — rama jazzy
<https://github.com/xArm-Developer/xarm_ros2/blob/jazzy/ReadMe.md>`__.
