Compatibilidad, dependencias y validación en Jazzy
==================================================

Versiones y dependencias
------------------------

.. list-table:: Plataforma de referencia
   :header-rows: 1
   :widths: 35 65

   * - Componente
     - Recomendación
   * - Ubuntu
     - 24.04 LTS, arquitectura amd64 o arm64
   * - ROS2
     - Jazzy
   * - Python
     - 3.12 del sistema, paquetes ROS mediante APT
   * - Compilación
     - ``colcon``, ``ament_python`` / ``ament_cmake``, ``rosdep``
   * - MQTT
     - Paho MQTT 2.x, ``CallbackAPIVersion.VERSION2``
   * - ESP32
     - Firmware para ESP32 Arduino core 3.x

Instalación típica de componentes robóticos
-------------------------------------------

.. code-block:: bash

   sudo apt update
   sudo apt install -y ros-jazzy-xacro \
       ros-jazzy-joint-state-publisher-gui \
       ros-jazzy-robot-state-publisher \
       ros-jazzy-tf2-tools ros-jazzy-py-trees \
       ros-jazzy-py-trees-ros python3-opencv python3-yaml

Si falta un paquete APT en una arquitectura concreta, consúltalo en el
`índice oficial de paquetes <https://index.ros.org/>`__ y adapta el
método de instalación, sin mezclar distribuciones de ROS.

Buenas prácticas de seguridad
-----------------------------

- Sustituye ``TU_SSID`` y ``TU_CLAVE_WIFI`` por credenciales propias;
  **no publiques contraseñas reales** dentro del código fuente.
- Evita ``allow_anonymous true`` en MQTT fuera de una red de pruebas
  aislada. En una LAN compartida configura autenticación y una lista de
  acceso por tópico; en redes no confiables, utiliza TLS.
- No expongas por Internet el puerto 1883 de Mosquitto ni los servicios
  de diagnóstico de ROS 2 sin controles de seguridad.
- Antes de mover motores reales, prueba las trayectorias en simulación,
  establece límites de velocidad y dispone de parada de emergencia.

Fuentes oficiales
-----------------

- `ROS 2 Jazzy: instalación <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>`__.
- `Tutoriales ROS 2 Jazzy <https://docs.ros.org/en/jazzy/Tutorials.html>`__.
- `Paho MQTT: migración a API 2 <https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html>`__.
- `PEP 668: entornos Python gestionados externamente <https://peps.python.org/pep-0668/>`__.
