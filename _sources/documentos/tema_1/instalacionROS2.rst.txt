Instalación de ROS 2 Jazzy en Ubuntu 24.04
==========================================

Esta guía utiliza **Ubuntu 24.04 LTS (Noble Numbat)** y **ROS 2 Jazzy Jalisco**.
Ambos forman la plataforma objetivo de la capacitación. Jazzy es una distribución
LTS con soporte previsto hasta mayo de 2029.

.. important::

   Los comandos siguientes están destinados a Ubuntu **24.04** de 64 bits
   (``amd64`` o ``arm64``). No combines entornos Humble y Jazzy en una
   misma terminal. En una instalación ya existente, revisa primero las
   fuentes APT para evitar repositorios ROS duplicados.

`Documentación oficial: instalación de Jazzy por paquetes DEB
<https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>`__.

1. Verificar versión y configuración regional
---------------------------------------------

.. code-block:: bash

   lsb_release -a
   uname -m
   locale
   sudo apt update
   sudo apt install -y locales software-properties-common curl
   sudo locale-gen en_US en_US.UTF-8
   sudo update-locale LANG=en_US.UTF-8
   sudo add-apt-repository universe

Usa una terminal nueva tras modificar la configuración regional.

2. Incorporar el repositorio de ROS 2
-------------------------------------

La configuración actual recomendada emplea ``ros2-apt-source`` y evita
mantener manualmente el archivo ``ros2.list`` y su clave GPG.

.. code-block:: bash

   sudo apt update
   export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F 'tag_name' | awk -F'"' '{print $4}')
   curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
   sudo dpkg -i /tmp/ros2-apt-source.deb

.. note::

   La consulta anterior requiere conexión a GitHub. Si no funciona,
   abre el enlace oficial y sigue las instrucciones de la versión
   vigente del paquete ``ros2-apt-source``. Evita usar instrucciones de
   repositorios antiguos junto con esta configuración.

3. Instalar ROS 2 Jazzy
-----------------------

.. code-block:: bash

   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y ros-jazzy-desktop ros-dev-tools
   sudo apt install -y python3-colcon-common-extensions python3-rosdep

``ros-jazzy-desktop`` incluye ROS 2, RViz y los ejemplos de demostración.
``ros-dev-tools`` agrega herramientas útiles para desarrollar y construir
paquetes. Para un equipo sin entorno gráfico se puede instalar
``ros-jazzy-ros-base`` en lugar de la edición Desktop.

4. Inicializar dependencias del workspace
-----------------------------------------

.. code-block:: bash

   sudo rosdep init  # Ejecutar solo una vez en el equipo
   rosdep update

Si ``rosdep init`` informa que ya está inicializado, no es un error:
continúa con ``rosdep update``.

5. Configurar la terminal
-------------------------

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   echo "$ROS_DISTRO"

Para activar Jazzy en nuevas terminales Bash, verifica primero que
``~/.bashrc`` no contenga otros entornos de ROS. Después agrega:

.. code-block:: bash

   grep -qxF 'source /opt/ros/jazzy/setup.bash' ~/.bashrc || echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc

En una terminal nueva, ejecuta ``echo $ROS_DISTRO``. El resultado esperado es
``jazzy``.

6. Verificar con un publicador y un suscriptor
----------------------------------------------

En la primera terminal:

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   ros2 run demo_nodes_cpp talker

En otra terminal:

.. code-block:: bash

   source /opt/ros/jazzy/setup.bash
   ros2 run demo_nodes_py listener

Deben aparecer mensajes publicados y recibidos. Finaliza con ``Ctrl+C``.

7. Preparar un espacio de trabajo
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

8. Dependencias Python externas y entornos virtuales
----------------------------------------------------

Ubuntu 24.04 usa Python 3.12 y protege su intérprete del sistema según
PEP 668. **No uses** ``sudo pip`` ni ``--break-system-packages`` para
instalar dependencias de los ejemplos.

Para mantener disponibles los módulos instalados por ROS mediante APT,
usa un entorno virtual con acceso a paquetes del sistema:

.. code-block:: bash

   sudo apt install -y python3-venv python3-pip python3-opencv python3-yaml
   python3 -m venv --system-site-packages ~/venvs/ros2-jazzy
   source ~/venvs/ros2-jazzy/bin/activate
   python -m pip install 'paho-mqtt>=2,<3' pupil-apriltags pydot

.. warning::

   Si construyes paquetes Python de ROS que necesiten dependencias del
   entorno virtual, activa el entorno **antes** de ``colcon build``.
   No instales otra distribución de ``rclpy`` desde PyPI ni mezcles
   intérpretes Python con ROS Jazzy.

Para el entorno del curso, consulta :doc:`compatibilidad_jazzy`.
