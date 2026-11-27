Estructura de programación MQTT con Mosquitto y Python
======================================================

1. Fundamentos generales de MQTT
--------------------------------

**MQTT (Message Queuing Telemetry Transport)** es un protocolo de mensajería
basado en el modelo **publicación/suscripción** (*publish/subscribe*). Los
clientes no intercambian mensajes directamente entre ellos: normalmente se
conectan a un **broker**, que distribuye cada publicación entre los clientes
suscritos a su tópico.

.. code-block:: text

                  +------------------------+
                  |     BROKER MQTT        |
                  |  (ej.: Mosquitto)     |
                  +------------------------+
                      ^              |
                      | Publica      | Reenvía
                      |              v
               +-------------+  +-------------+
               |  Cliente A  |  |  Cliente B  |
               | Publicador  |  | Suscriptor  |
               +-------------+  +-------------+

Un mismo cliente puede publicar, suscribirse a varios tópicos o realizar
ambas operaciones de forma simultánea.

1.1. Componentes fundamentales
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Elementos de una arquitectura MQTT
   :header-rows: 1
   :widths: 24 76

   * - Elemento
     - Función
   * - Protocolo MQTT
     - Define cómo se conectan los clientes y cómo intercambian mensajes.
   * - Broker
     - Recibe publicaciones, gestiona suscripciones y distribuye mensajes.
   * - Cliente
     - Programa o dispositivo que mantiene una conexión con un broker.
   * - Publicador
     - Cliente que envía mensajes a un tópico.
   * - Suscriptor
     - Cliente que declara qué tópicos desea recibir.
   * - Tópico
     - Nombre jerárquico empleado para clasificar mensajes.
   * - Payload
     - Contenido del mensaje, transportado como una secuencia de bytes.
   * - Client ID
     - Identificador de una conexión MQTT ante el broker.
   * - Callback
     - Función que atiende un evento, por ejemplo una conexión o un mensaje.
   * - Bucle de red
     - Procesa comunicaciones, keepalive, respuestas y reconexiones.

1.2. Diferencia entre MQTT, Mosquitto y Paho
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Tres elementos distintos
   :header-rows: 1
   :widths: 24 45 31

   * - Nombre
     - Qué es
     - Dónde se utiliza
   * - MQTT
     - Protocolo de intercambio de mensajes.
     - Entre clientes y broker.
   * - Mosquitto
     - Implementación de un broker MQTT.
     - En un equipo servidor, Raspberry Pi o PC.
   * - Eclipse Paho MQTT
     - Biblioteca cliente para diversos lenguajes, incluido Python.
     - En los programas que publican y se suscriben.
   * - ``mosquitto_pub`` / ``mosquitto_sub``
     - Aplicaciones de consola incluidas en ``mosquitto-clients``.
     - En pruebas y diagnóstico sin escribir Python.

.. important::

   **Instalar Mosquitto no instala automáticamente Paho MQTT para Python.**
   Por otro lado, instalar Paho no crea un broker: el cliente todavía necesita
   conectarse a uno.

1.3. Tópicos y jerarquía
~~~~~~~~~~~~~~~~~~~~~~~~

Los tópicos son cadenas de texto separadas habitualmente por ``/``. No se
necesita crearlos previamente en el broker para publicar un mensaje.

.. code-block:: text

   laboratorio/sensores/temperatura
   laboratorio/sensores/humedad
   laboratorio/estados/conexion

En las suscripciones pueden emplearse comodines:

* ``+``: sustituye **un nivel**; por ejemplo ``laboratorio/sensores/+``.
* ``#``: sustituye **uno o varios niveles, incluidos cero** y debe aparecer
  al final; por ejemplo ``laboratorio/#``.

Los comodines se utilizan como filtros de suscripción, no como nombres para
publicar mensajes. El broker distingue mayúsculas de minúsculas: ``Sensor``
y ``sensor`` son tópicos diferentes.

1.4. Payload y formatos
~~~~~~~~~~~~~~~~~~~~~~~

Un mensaje MQTT contiene un **payload de bytes**. El formato de esos bytes
lo acuerdan las aplicaciones: texto UTF-8, JSON, datos binarios, etc.

Ejemplo conceptual de JSON:

.. code-block:: json

   {
     "temperatura": 24.5,
     "humedad": 60,
     "unidad": "C"
   }

Cuando se utiliza JSON en Python:

* ``json.dumps(diccionario)``: convierte datos Python a texto JSON.
* ``json.loads(texto)``: convierte texto JSON a estructuras Python.
* ``msg.payload.decode('utf-8')``: convierte los bytes de una publicación
  recibida a texto UTF-8.

Ni MQTT ni el broker verifican que un JSON represente valores válidos para
una aplicación. Esa validación corresponde al programa receptor.

1.5. Calidad de servicio: QoS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Niveles de QoS
   :header-rows: 1
   :widths: 10 35 55

   * - QoS
     - Garantía de transporte
     - Consideración
   * - 0
     - Como máximo una entrega.
     - No hay confirmación MQTT de recepción del mensaje por el broker.
   * - 1
     - Al menos una entrega.
     - Puede haber duplicados; la aplicación debe tolerarlos.
   * - 2
     - Entrega exactamente una vez a nivel de protocolo MQTT.
     - Implica más intercambio de paquetes; no garantiza por sí solo que
       una operación física se ejecute exactamente una vez.

El QoS aplicado al reenvío depende también del QoS de la suscripción.
Para órdenes que cambian el estado de una máquina, la aplicación debe
incorporar identificadores, validaciones y mecanismos para prevenir
repeticiones peligrosas, incluso si se usa QoS 1 o 2.

1.6. Retain, keepalive y última voluntad (LWT)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``retain=True`` permite almacenar el último mensaje retenido de un tópico,
para entregarlo a nuevos suscriptores. Resulta útil para ciertos **estados**
pero es arriesgado para **comandos de movimiento**, que podrían ejecutarse
más tarde de lo previsto.

``keepalive`` indica el intervalo máximo aproximado entre intercambios
necesarios para mantener y vigilar la conexión. No es un temporizador de
control de motores.

La **última voluntad** (*Last Will and Testament*, LWT) es un mensaje que el
broker puede publicar cuando detecta una desconexión inesperada del cliente.
Puede servir para anunciar que un dispositivo dejó de estar disponible.

1.7. Identificación, sesiones y reconexión
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dos clientes conectados a un mismo broker no deberían usar simultáneamente
el mismo ``client_id``: el broker puede desconectar la conexión anterior.

Tras una desconexión, el cliente debe recuperar la comunicación y, cuando
corresponda, las suscripciones. Una práctica sencilla consiste en realizar
``subscribe()`` dentro de ``on_connect()``, que se ejecuta después de una
conexión o reconexión exitosa.

Los mecanismos de sesión persistente y mensajes pendientes dependen de la
versión del protocolo, de los parámetros de sesión y de la configuración
del broker; no deben asumirse por el mero hecho de usar QoS 1.

2. Anatomía de un programa MQTT en Python
-----------------------------------------

Un cliente MQTT completo suele contener los siguientes elementos.

.. list-table:: Estructura mínima y componentes opcionales
   :header-rows: 1
   :widths: 31 69

   * - Elemento
     - Responsabilidad
   * - Importaciones
     - Importar Paho y bibliotecas adicionales, como ``json`` y ``os``.
   * - Configuración
     - Definir dirección del broker, puerto, tópicos e identificación.
   * - Funciones callback
     - Atender conexión, recepción, desconexión y otros eventos necesarios.
   * - Creación del cliente
     - Instanciar ``mqtt.Client`` con ``CallbackAPIVersion.VERSION2``.
   * - Asociación de callbacks
     - Registrar las funciones mediante ``client.on_connect = ...`` y similares.
   * - Autenticación (si aplica)
     - Configurar usuario y contraseña antes de iniciar la conexión.
   * - Conexión
     - Invocar ``connect()`` o ``connect_async()``.
   * - Bucle de red
     - Utilizar ``loop_forever()`` o ``loop_start()`` para atender MQTT.
   * - Operación
     - Suscribirse, publicar, procesar mensajes o combinar tareas.
   * - Cierre
     - Desconectar y liberar los recursos de red.

El orden lógico habitual es:

.. code-block:: text

   Importar bibliotecas
          |
          v
   Leer configuración
          |
          v
   Definir callbacks
          |
          v
   Crear cliente MQTT
          |
          v
   Registrar callbacks / autenticación
          |
          v
   Conectar y procesar el bucle de red
          |
          v
   Publicar y/o recibir mensajes
          |
          v
   Desconectar ordenadamente

2.1. Callbacks de Paho MQTT 2.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La versión 2.x introduce una API de callbacks versionada. En esta guía
**todas las funciones utilizan ``CallbackAPIVersion.VERSION2``**.

.. list-table:: Firmas utilizadas en esta guía
   :header-rows: 1
   :widths: 38 62

   * - Función
     - Evento
   * - ``on_connect(client, userdata, flags, reason_code, properties)``
     - El broker responde a la solicitud de conexión. Suele incluir las
       suscripciones del programa.
   * - ``on_message(client, userdata, msg)``
     - Se recibe un mensaje publicado en un tópico suscrito.
   * - ``on_disconnect(client, userdata, disconnect_flags, reason_code, properties)``
     - Finaliza la conexión, de forma esperada o inesperada.
   * - ``on_publish(client, userdata, mid, reason_code, properties)``
     - Se informa sobre el progreso o confirmación de una publicación
       según su QoS.
   * - ``on_subscribe(client, userdata, mid, reason_code_list, properties)``
     - El broker responde a una solicitud de suscripción.

La firma antigua ``on_connect(client, userdata, flags, rc)`` no debe
mezclarse con ``CallbackAPIVersion.VERSION2``. Es una diferencia entre
versiones de **Paho MQTT**, no una diferencia propia de ROS 2 Jazzy.

2.2. Instrucciones que debe reconocer el estudiante
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: API principal de Paho
   :header-rows: 1
   :widths: 38 62

   * - Expresión
     - Significado
   * - ``mqtt.Client(...)``
     - Construye una instancia de cliente MQTT.
   * - ``client.username_pw_set(...)``
     - Configura autenticación con usuario y contraseña.
   * - ``client.connect(host, port, keepalive)``
     - Abre una conexión TCP inicial con el broker.
   * - ``client.connect_async(...)``
     - Prepara una conexión asíncrona que requiere procesar el bucle de red.
   * - ``client.subscribe(topic, qos=...)``
     - Solicita al broker recibir publicaciones de un tópico.
   * - ``client.publish(topic, payload, qos=..., retain=...)``
     - Publica contenido y devuelve información de su envío.
   * - ``client.loop_forever()``
     - Procesa eventos de red ocupando el hilo llamante.
   * - ``client.loop_start()``
     - Inicia un hilo interno para procesar eventos MQTT.
   * - ``client.loop_stop()``
     - Detiene el hilo creado con ``loop_start()``.
   * - ``client.disconnect()``
     - Solicita la desconexión del broker.
   * - ``client.reconnect_delay_set(...)``
     - Ajusta esperas entre reintentos automáticos de reconexión.

**``connect()`` no sustituye el bucle de red.** Los callbacks y las
confirmaciones requieren que el programa procese los paquetes MQTT.

3. Instalación correcta en Ubuntu 24.04
---------------------------------------

3.1. Instalar el broker y los clientes de terminal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instala Mosquitto mediante APT, sin usar ``pip`` para el broker.

.. code-block:: bash

   sudo apt update
   sudo apt install -y mosquitto mosquitto-clients python3-pip

   # Habilitar el servicio ahora y después de reiniciar.
   sudo systemctl enable --now mosquitto

   # Verificar que el servicio está activo.
   systemctl is-active mosquitto
   sudo ss -lntp | grep 1883

El resultado esperado de ``systemctl is-active`` es ``active``. Con una
configuración local predeterminada de Mosquitto 2.x, el puerto 1883 puede
escuchar únicamente en ``localhost``; esto es adecuado para comenzar.

3.2. Probar Mosquitto sin Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

En dos terminales distintas del mismo computador:

**Terminal 1: suscribirse**

.. code-block:: bash

   mosquitto_sub -h localhost -t "laboratorio/datos" -v

**Terminal 2: publicar**

.. code-block:: bash

   mosquitto_pub -h localhost -t "laboratorio/datos" \
     -m '{"temperatura":24.5,"unidad":"C"}'

En la primera terminal debería verse el tópico y su contenido JSON.

3.3. Instalar la biblioteca Python Paho MQTT 2.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

En Ubuntu 24.04, el paquete APT ``python3-paho-mqtt`` ofrece la serie
**1.6.1**, pero los ejemplos de esta guía utilizan la API de callbacks
``CallbackAPIVersion.VERSION2``, disponible en Paho MQTT **2.x**.

En este curso **no se crean ni activan entornos virtuales**. Se instala
Paho MQTT para el usuario actual y se comprueba explícitamente su
funcionamiento con ``/usr/bin/python3``, el intérprete de Python de
Ubuntu 24.04 empleado normalmente por ROS 2 Jazzy.

.. code-block:: bash

   # Instalar pip para el Python del sistema (si aún no está disponible).
   sudo apt update
   sudo apt install -y python3-pip

   # Instalar Paho MQTT 2.x únicamente para el usuario actual.
   /usr/bin/python3 -m pip install \
     --user \
     --break-system-packages \
     "paho-mqtt==2.2.0"

   # Consultar versión, ubicación y dependencias instaladas.
   /usr/bin/python3 -m pip show paho-mqtt

   # Verificar que el Python del sistema reconoce la API VERSION2.
   /usr/bin/python3 -c "import importlib.metadata as m; import paho.mqtt.client as mqtt; print('Paho MQTT:', m.version('paho-mqtt')); print('Callback API:', mqtt.CallbackAPIVersion.VERSION2)"

.. note::

   Se fija ``paho-mqtt==2.2.0`` para que los ejemplos sean reproducibles.
   No instales ``python3-paho-mqtt`` mediante APT para estas prácticas,
   porque en Ubuntu 24.04 ese paquete corresponde a la serie 1.x.

.. warning::

   Ubuntu 24.04 protege el Python gestionado por APT mediante el mecanismo
   ``EXTERNALLY-MANAGED`` (PEP 668). La opción
   ``--break-system-packages`` permite instalar Paho en el directorio
   del usuario, pero **puede provocar conflictos con otras bibliotecas**
   que utiliza el Python del sistema. Se usa aquí por la decisión del curso
   de trabajar sin entornos virtuales. No utilices ``sudo pip install``
   ni instales versiones de ``rclpy`` desde PyPI. Si se produce un conflicto,
   revisa primero la ruta y la versión de los módulos importados.

3.4. Comprobar el intérprete utilizado
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ejecuta siempre las comprobaciones con el Python del sistema, incluso
cuando invoques los programas a través de ``ros2 run``:

.. code-block:: bash

   /usr/bin/python3 --version

   # Verificar la ubicación real de Paho y del intérprete.
   /usr/bin/python3 -c "import sys; import paho.mqtt.client as mqtt; print('Python:', sys.executable); print('Paho:', mqtt.__file__)"

   # Verificar que la instalación del usuario está habilitada.
   /usr/bin/python3 -m site --user-site

   # Verificar también ROS 2 Jazzy en la misma sesión.
   source /opt/ros/jazzy/setup.bash
   /usr/bin/python3 -c "import rclpy; import paho.mqtt.client as mqtt; print('rclpy y Paho disponibles')"

Los programas independientes se ejecutan mediante
``/usr/bin/python3 nombre_archivo.py``. Los nodos registrados en
``mi_pkg_python`` se ejecutan con ``ros2 run`` después de compilar el
paquete y cargar ``~/ros2_ws/install/setup.bash``.

3.5. Permitir clientes de otros equipos (opcional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

El acceso remoto **no se habilita simplemente instalando el broker**.
Para admitir dispositivos de una LAN, crea un listener con autenticación.

.. warning::

   Esta configuración debe aplicarse en una red administrada y confiable.
   El puerto MQTT 1883 **no cifra** el contenido ni las credenciales.
   En redes no confiables utiliza TLS (normalmente 8883), controles de
   acceso y credenciales individuales. Nunca publiques contraseñas en GitHub.

**Crear un usuario MQTT** (el comando solicita la contraseña de forma
interactiva):

.. code-block:: bash

   sudo mosquitto_passwd -c /etc/mosquitto/passwd usuario_mqtt
   sudo chown root:mosquitto /etc/mosquitto/passwd
   sudo chmod 640 /etc/mosquitto/passwd

**Crear una configuración**, por ejemplo
``/etc/mosquitto/conf.d/laboratorio.conf``:

.. code-block:: bash

   sudo nano /etc/mosquitto/conf.d/laboratorio.conf

Su contenido será:

.. code-block:: text

   listener 1883 0.0.0.0
   allow_anonymous false
   password_file /etc/mosquitto/passwd

Reinicia y comprueba el servicio:

.. code-block:: bash

   sudo systemctl restart mosquitto
   sudo systemctl status mosquitto
   sudo ss -lntp | grep 1883

Si utilizas UFW, limita el acceso a la subred autorizada; **sustituye la
subred de ejemplo por la red real del laboratorio**:

.. code-block:: bash

   sudo ufw allow from 192.168.100.0/24 to any port 1883 proto tcp

Los clientes remotos deberán configurar usuario y contraseña antes de
``connect()``. Si ya existen otros listeners en la configuración del broker,
revisa sus puertos para evitar conflictos.

4. Ejemplo 1: programa suscriptor
---------------------------------

Este programa demuestra una **suscripción genérica**. No está vinculado
al formato de un sensor o robot particular: muestra el tópico y el payload
recibido. El ejemplo presupone el broker local de la sección 3.2.

.. code-block:: python
   :caption: suscriptor_mqtt.py

   import getpass
   import paho.mqtt.client as mqtt

   # --------------------------------------------
   # 1. Configuración del broker
   # --------------------------------------------
   BROKER = "127.0.0.1"
   PUERTO = 1883
   TOPICO = "rm1/sensores"

   # Usuario creado en Mosquitto
   USUARIO = "usuario_mqtt"

   # Solicitar la contraseña al ejecutar el programa
   CLAVE = getpass.getpass("Contraseña MQTT: ")


   # --------------------------------------------
   # 2. Callback de conexión
   # --------------------------------------------
   def on_connect(client, userdata, flags, reason_code, properties):

      if reason_code == 0:
         print("Conectado correctamente a Mosquitto")

         # Suscribirse cuando la conexión sea aceptada
         client.subscribe(TOPICO, qos=1)
         print(f"Suscrito al tópico: {TOPICO}")

      else:
         print(f"Error de conexión: {reason_code}")


   # --------------------------------------------
   # 3. Callback de recepción
   # --------------------------------------------
   def on_message(client, userdata, msg):

      mensaje = msg.payload.decode("utf-8", errors="replace")

      print(f"Tópico: {msg.topic}")
      print(f"Mensaje: {mensaje}")


   # --------------------------------------------
   # 4. Crear el cliente MQTT
   # --------------------------------------------
   client = mqtt.Client(
      callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
      client_id="suscriptor_python"
   )

   # Registrar las credenciales antes de conectar
   client.username_pw_set(USUARIO, CLAVE)

   # Registrar callbacks
   client.on_connect = on_connect
   client.on_message = on_message


   # --------------------------------------------
   # 5. Conectar y ejecutar
   # --------------------------------------------
   client.connect(BROKER, PUERTO, 60)

   # Mantener el cliente escuchando mensajes
   client.loop_forever()


**Estructura del programa:** importa Paho, define la conexión, crea
callbacks, construye el cliente, registra los callbacks, establece la
conexión, atiende el bucle de red y finaliza.

5. Ejemplo 2: programa publicador
---------------------------------

Este programa publica una estructura JSON una sola vez. Con QoS 1 puede
esperar a que Paho procese la confirmación del broker antes de cerrar.
No garantiza que una aplicación suscriptora haya procesado físicamente
el mensaje.

.. code-block:: python
   :caption: publicador_mqtt.py

   import getpass
   import json
   import paho.mqtt.client as mqtt

   # --------------------------------------------
   # 1. Configuración del broker
   # --------------------------------------------
   BROKER = "192.168.100.248"
   PUERTO = 1883
   TOPICO = "rm1/sensores"

   # Usuario creado en Mosquitto
   USUARIO = "usuario_mqtt"

   # Solicitar la contraseña al ejecutar el programa
   CLAVE = getpass.getpass("Contraseña MQTT: ")

   # Mensaje JSON que queremos publicar
   DATOS = {
      "temperatura": 25.5,
      "humedad": 60.0
   }

   MENSAJE = json.dumps(DATOS)


   # --------------------------------------------
   # 2. Callback de conexión
   # --------------------------------------------
   def on_connect(client, userdata, flags, reason_code, properties):

      if reason_code == 0:
         print("Conectado correctamente a Mosquitto")

         # Publicar el mensaje cuando se establezca
         # correctamente la conexión con el broker
         resultado = client.publish(
            TOPICO,
            payload=MENSAJE,
            qos=1,
            retain=False
         )

         if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Publicando en el tópico: {TOPICO}")

         else:
            print("Error al solicitar la publicación")
            client.disconnect()

      else:
         print(f"Error de conexión: {reason_code}")
         client.disconnect()


   # --------------------------------------------
   # 3. Callback de publicación
   # --------------------------------------------
   def on_publish(client, userdata, mid, reason_code, properties):

      if reason_code == 0:
         print("Mensaje publicado correctamente")
         print(f"Tópico: {TOPICO}")
         print(f"Mensaje: {MENSAJE}")

      else:
         print(f"Error de publicación: {reason_code}")

      # Finalizar conexión después de publicar
      client.disconnect()


   # --------------------------------------------
   # 4. Crear el cliente MQTT
   # --------------------------------------------
   client = mqtt.Client(
      callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
      client_id="publicador_python"
   )

   # Registrar las credenciales antes de conectar
   client.username_pw_set(USUARIO, CLAVE)

   # Registrar callbacks
   client.on_connect = on_connect
   client.on_publish = on_publish


   # --------------------------------------------
   # 5. Conectar y ejecutar
   # --------------------------------------------
   try:
      client.connect(BROKER, PUERTO, 60)

      # Procesar la comunicación MQTT
      # hasta que se complete la publicación
      client.loop_forever()

   except KeyboardInterrupt:
      print("Publicación interrumpida")

   finally:
      client.disconnect()


.. important::

   ``publish()`` devuelve un objeto de seguimiento de la publicación.
   Con QoS 1, ``wait_for_publish()`` sirve para esperar la confirmación
   correspondiente; **no es una confirmación de ejecución por parte de un
   dispositivo remoto**.

6. Ejemplo 3: cliente que publica y se suscribe
-----------------------------------------------

Un mismo cliente puede cumplir ambas funciones. El siguiente ejemplo
se suscribe a mensajes, publica un estado de demostración periódicamente
con ``loop_start()`` y puede recuperar la suscripción tras una reconexión.

.. code-block:: python
   :caption: cliente_mqtt_mixto.py

   import getpass
   import json
   import os
   import time
   import paho.mqtt.client as mqtt

   BROKER = "192.168.100.248"
   PUERTO = 1883
   TOPICO_ENTRADA = "rm1/sensores"
   TOPICO_SALIDA = "rm1/acciones"
   # Usuario creado en Mosquitto
   USUARIO = "usuario_mqtt"

   # Solicitar la contraseña al ejecutar el programa
   CLAVE = getpass.getpass("Contraseña MQTT: ")

   def on_connect(client, userdata, flags, reason_code, properties):
      if reason_code == 0:
         print('Conectado; recuperando suscripción.')
         client.subscribe(TOPICO_ENTRADA, qos=1)
      else:
         print(f'Fallo de conexión: {reason_code}')


   def on_message(client, userdata, msg):
      try:
         texto = msg.payload.decode('utf-8')
      except UnicodeDecodeError:
         print('Mensaje no UTF-8 descartado.')
         return
      print(f'Recibido en {msg.topic}: {texto}')


   def main():
      client = mqtt.Client(
         callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
         client_id=f'curso_mixto_{os.getpid()}',
         protocol=mqtt.MQTTv311
      )
      client.on_connect = on_connect
      client.on_message = on_message
      client.reconnect_delay_set(min_delay=1, max_delay=10)
      client.username_pw_set(USUARIO, CLAVE)

      # La conexión se establece y mantiene desde el hilo MQTT.
      client.connect_async(BROKER, PUERTO, keepalive=60)
      client.loop_start()

      contador = 0
      try:
         while True:
            if client.is_connected():
                  datos = {'estado': 'activo', 'contador': contador}
                  respuesta = client.publish(
                     TOPICO_SALIDA,
                     payload=json.dumps(datos),
                     qos=0,
                     retain=False
                  )
                  if respuesta.rc == mqtt.MQTT_ERR_SUCCESS:
                     contador += 1
                  else:
                     print(f'Publicación rechazada localmente: {respuesta.rc}')
            time.sleep(2)
      except KeyboardInterrupt:
         print('Finalizando...')
      finally:
         client.disconnect()
         client.loop_stop()


   if __name__ == '__main__':
      main()

.. note::

   ``loop_start()`` procesa MQTT en un hilo secundario. No es necesario
   llamar simultáneamente a ``loop_forever()`` sobre el mismo cliente.
   Evita operaciones prolongadas dentro de ``on_message()`` y otros
   callbacks: pueden retrasar la recepción de nuevas publicaciones.

.. code-block:: bash

   mosquitto_sub \
      -h 192.168.100.248 \
      -p 1883 \
      -u usuario_mqtt \
      -P "$MQTT_PASSWORD" \
      -t "rm1/acciones" -v


7. Comparación de los tipos de programas
----------------------------------------

.. list-table:: ¿Qué estructura necesita cada programa?
   :header-rows: 1
   :widths: 22 42 36

   * - Tipo
     - Elementos principales
     - Bucle apropiado
   * - Suscriptor
     - ``on_connect``, ``subscribe``, ``on_message``.
     - ``loop_forever()`` o ``loop_start()``.
   * - Publicador puntual
     - ``connect``, ``publish``, confirmación y cierre.
     - ``loop_start()`` durante el envío.
   * - Cliente mixto
     - Callbacks, ``subscribe``, ``publish`` y reconexión.
     - ``loop_start()`` más lógica principal.
   * - Puente MQTT–ROS 2
     - Paho, nodo ``rclpy``, cola de mensajes y callbacks de ROS 2.
     - ``loop_start()`` para MQTT y ``rclpy.spin()`` para ROS.

8. Integración general de MQTT con ROS 2 Jazzy
----------------------------------------------

MQTT y ROS 2 tienen mecanismos de comunicación distintos. Los tópicos
MQTT y ROS 2 no se convierten automáticamente. Un **nodo puente** puede
traducir mensajes entre ambos sistemas.

.. code-block:: text

   Cliente MQTT --> Broker Mosquitto --> Puente Python --> ROS 2
                                                |
                                                v
                                          Tópico ROS 2

   Tópico ROS 2 --> Puente Python --> Broker Mosquitto --> Cliente MQTT

8.1. Diferencia entre ``loop_start()`` y ``rclpy.spin()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``loop_start()`` mantiene la comunicación MQTT mediante un hilo propio.
* ``rclpy.spin(node)`` atiende eventos ROS 2 mediante su executor.
* Un callback MQTT puede ejecutarse en un hilo diferente del que atiende
  los callbacks ROS 2.
* Para intercambiar datos entre ambos contextos conviene utilizar una
  estructura segura para hilos, por ejemplo ``queue.Queue``.

No se debe colocar ``rclpy.spin_once(node)`` dentro de un callback que ya
está siendo procesado por el mismo executor. Esta precaución es
especialmente relevante al combinar recepción asíncrona, servicios y
acciones de ROS 2 Jazzy.

8.2. Ejemplo mínimo de puente bidireccional
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Este ejemplo utiliza mensajes ROS 2 ``std_msgs/String`` y nombres de
tópicos genéricos. Los nombres MQTT y ROS 2 de entrada y salida son
distintos para evitar reenviar los mensajes en un bucle involuntario.

.. code-block:: python
   :caption: puente_mqtt_ros2.py

   import getpass
   import os
   from queue import Queue, Empty, Full

   import rclpy
   from rclpy.node import Node
   from std_msgs.msg import String
   import paho.mqtt.client as mqtt

   # Configuración MQTT
   BROKER = "192.168.100.248"
   PUERTO = 1883
   USUARIO = "usuario_mqtt"
   TOPICO_ENTRADA = "rm1/sensores"
   TOPICO_SALIDA = "rm1/acciones"


   class PuenteMQTTROS(Node):

      def __init__(self, clave):
         super().__init__('puente_mqtt_ros')

         # Comunicación ROS 2
         self.publicador = self.create_publisher(String, '/rm1/sensores', 10)
         self.suscriptor = self.create_subscription(String, '/rm1/acciones', self.callback_ros, 10)

         # Cola para transferir mensajes del hilo MQTT al executor ROS 2
         self.cola_mqtt = Queue(maxsize=100)
         self.timer = self.create_timer(0.05, self.procesar_mqtt)

         # Comunicación MQTT
         self.cliente = mqtt.Client(
               callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
               client_id=f'puente_mqtt_ros_{os.getpid()}',
               protocol=mqtt.MQTTv311
         )

         self.cliente.username_pw_set(USUARIO, clave)
         self.cliente.on_connect = self.on_connect
         self.cliente.on_message = self.on_message
         self.cliente.on_disconnect = self.on_disconnect
         self.cliente.reconnect_delay_set(min_delay=1, max_delay=10)

         self.cliente.connect_async(BROKER, PUERTO, keepalive=60)
         self.cliente.loop_start()

         self.get_logger().info('Puente MQTT - ROS 2 iniciado')

      def on_connect(self, client, userdata, flags, reason_code, properties):
         if reason_code == 0:
               print('MQTT conectado correctamente')
               client.subscribe(TOPICO_ENTRADA, qos=1)
         else:
               print(f'Error de conexión MQTT: {reason_code}')

      def on_message(self, client, userdata, msg):
         try:
               texto = msg.payload.decode('utf-8')
               self.cola_mqtt.put_nowait(texto)
         except UnicodeDecodeError:
               print('Mensaje MQTT no UTF-8 descartado')
         except Full:
               print('Cola MQTT llena. Mensaje descartado.')

      def procesar_mqtt(self):
         for _ in range(20):
               try:
                  texto = self.cola_mqtt.get_nowait()
               except Empty:
                  break

               mensaje = String()
               mensaje.data = texto
               self.publicador.publish(mensaje)
               self.get_logger().info(f'MQTT -> ROS 2: {texto}')

      def callback_ros(self, msg):
         if not self.cliente.is_connected():
               self.get_logger().warn('MQTT desconectado')
               return

         resultado = self.cliente.publish(TOPICO_SALIDA, payload=msg.data, qos=1, retain=False)

         if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
               self.get_logger().info(f'ROS 2 -> MQTT: {msg.data}')
         else:
               self.get_logger().error(f'Error de publicación MQTT: {resultado.rc}')

      def on_disconnect(self, client, userdata, flags, reason_code, properties):
         print(f'MQTT desconectado: {reason_code}')

      def cerrar(self):
         self.cliente.disconnect()
         self.cliente.loop_stop()


   def main(args=None):
      clave = getpass.getpass('Contraseña MQTT: ')
      rclpy.init(args=args)
      nodo = PuenteMQTTROS(clave)

      try:
         rclpy.spin(nodo)
      except KeyboardInterrupt:
         print('Finalizando puente MQTT - ROS 2')
      finally:
         nodo.cerrar()
         nodo.destroy_node()
         if rclpy.ok():
               rclpy.shutdown()


   if __name__ == '__main__':
      main()

.. warning::

   El puente es una **demostración de interoperabilidad de mensajes**, no
   un controlador en tiempo real ni un mecanismo de seguridad. Para controlar
   actuadores se necesitan comprobaciones de origen y frescura de órdenes,
   límites y una parada segura independiente de la red.

8.3. Verificación del puente
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cuando el archivo se haya registrado como ejecutable del paquete, ejecuta:

.. code-block:: bash

   # Terminal 1: puente MQTT-ROS 2.
   ros2 run mi_pkg_python puente_mqtt_ros2

   # Terminal 2: suscripción a mensajes ROS 2 provenientes de MQTT.
   ros2 topic echo /mqtt/entrada

   # Terminal 3: publicar un mensaje MQTT.
   mosquitto_pub -h localhost -t laboratorio/datos -m "Hola desde MQTT"

   # Terminal 4: observar el otro sentido del puente.
   mosquitto_sub -h localhost -t laboratorio/salida -v

   # Terminal 5: enviar el mensaje de ROS 2 hacia MQTT.
   ros2 topic pub --once /mqtt/salida std_msgs/msg/String \
     "{data: 'Hola desde ROS 2'}"

9. Diagnóstico y problemas frecuentes
--------------------------------------

.. list-table:: Errores habituales
   :header-rows: 1
   :widths: 37 63

   * - Síntoma
     - Causa probable y comprobación
   * - ``ModuleNotFoundError: No module named 'paho'``
     - La biblioteca no está instalada en el intérprete que ejecuta el
       programa. Revisar ``/usr/bin/python3 -m pip show paho-mqtt`` y ``/usr/bin/python3 -m site --user-site``.
   * - Error de firma en ``on_connect``
     - Callback antiguo mezclado con ``CallbackAPIVersion.VERSION2``.
   * - ``Connection refused``
     - Broker inactivo, puerto incorrecto o listener no disponible.
       Comprobar ``systemctl status mosquitto`` y ``ss -lntp``.
   * - Conexión local correcta, pero no desde la ESP32
     - Mosquitto escucha solo en loopback, firewall o red inaccesible.
   * - Autenticación rechazada
     - Credenciales incorrectas o configuración del broker incompleta.
   * - No se reciben mensajes
     - Tópicos diferentes, suscripción no realizada, ausencia del bucle
       de red o problemas de conexión.
   * - El broker desconecta un cliente cuando entra otro
     - Posible ``client_id`` duplicado entre conexiones.
   * - Mensajes repetidos
     - Posible redelivery con QoS 1; usar identificadores y deduplicación
       cuando la aplicación lo requiera.
   * - ``externally-managed-environment`` al instalar con pip
     - Python del sistema protegido por Ubuntu 24.04; utilizar
       ``--user --break-system-packages`` como en la sección 3, teniendo
       en cuenta su advertencia de compatibilidad.
   * - Un nodo ROS 2 deja de atender callbacks
     - Código bloqueante o mezcla incorrecta de bucles; usar el executor
       ROS 2 y Paho en hilos apropiados, con cola de intercambio.

Comandos útiles de diagnóstico:

.. code-block:: bash

   # Estado del broker.
   systemctl is-active mosquitto
   sudo journalctl -u mosquitto -n 30 --no-pager

   # Puertos abiertos.
   sudo ss -lntp | grep 1883

   # Suscripción de prueba.
   mosquitto_sub -h localhost -t 'laboratorio/#' -v

   # Comprobar instalación Paho para el intérprete activo.
   /usr/bin/python3 -m pip show paho-mqtt


Arduino IDE 2.x y ESP32 core 3.x
--------------------------------

Para usar ESP32 se recomienda el **core ESP32 de Arduino 3.x** y
comprobar la compatibilidad de las librerías con ese core antes de
compilar. Una vez configurado Mosquitto, descarga Arduino IDE; el
programa que se utilazará para programar la ESP32.

.. _instalación-1:

Instalación
~~~~~~~~~~~

1. **Descargar Arduino IDE**

Enlace de descargar, AppImage
`arduino <https://www.arduino.cc/en/software/>`__

En la carpeta donde se descargó el AppImage, cambiar el nombre al
archivo descargado por ``arduino-ide``

.. code:: bash

   sudo apt update
   sudo apt upgrade
   sudo apt install -y libfuse2t64  # Ubuntu 24.04; solo si el AppImage requiere FUSE
   sudo chmod +x arduino-ide.AppImage
   ./arduino-ide.AppImage

2. **Instalar soporte para ESP32**

   1. Ir a ``Archivo → Preferencias``
   2. En el campo **URLs adicionales para tarjetas**, agregar:

   ::

      https://espressif.github.io/arduino-esp32/package_esp32_index.json

   3. Ir a ``Herramientas → Placa → Gestor de tarjetas``
   4. Buscar ``esp32`` e instalar **versión 3.x**

El core 3.x integra ``WiFi.h`` y requiere verificar que las demás
bibliotecas del firmware sean compatibles. Para estos ejemplos, instala
``PubSubClient`` 2.8 y ``ArduinoJson`` 7.x desde el gestor de librerías.
No conectes cargas de potencia directamente a GPIO: utiliza un driver o relé
adecuado, con protección y alimentación apropiadas.



3. Acceso a puertos USB
-----------------------

El ESP32 se conecta como un dispositivo serie (``/dev/ttyUSB*`` o
``/dev/ttyACM*``) generalmente la conexión se realiza en el puerto
ttyUSB. Para acceder sin sudo:

Añadir usuario al grupo ``dialout``:

.. code:: bash

   sudo usermod -aG dialout $USER

Reiniciar sesión para aplicar cambios.

Ver dispositivos conectados

.. code:: bash

   ls /dev/ttyUSB*

Ver cambios al conectar o desconectar

.. code:: bash

   watch -n 1 ls /dev/ttyUSB*

--------------

4. Instalación de bibliotecas recomendadas en Arduino IDE

Tabla de librerías recomendadas para tu proyecto ESP32 con WiFiManager y MQTT

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 60

   * - Librería
     - Autor
     - Versión recomendada
     - Notas importantes
   * - WiFiManager
     - tzapu
     - 2.0.17
     - Compatible con ESP32 core 3.x. Asegura el uso del namespace correcto para ESP32. Soporta parámetros personalizados.
   * - WiFi
     - Espressif
     - Incluida en el core
     - No requiere instalación manual. Ya viene con el core de ESP32.
   * - EEPROM
     - Espressif
     - Incluida en el core
     - Opcional migrar a Preferences si deseas mayor robustez.
   * - PubSubClient
     - Nick O’Leary
     - 2.8.0
     - Para conexión MQTT (broker IP, topic, publish/subscribe). Ligera y muy estable.
   * - ArduinoJson
     - Benoit Blanchon
     - 7.x.x
     - Emplea JsonDocument; DynamicJsonDocument y StaticJsonDocument son APIs anteriores.


Ejemplos de Uso.
----------------

1. Uso de MQTT desde Arduino

Crear 2 pestañas: ``Esp32_mqtt`` y ``Conf_mqtt``

.. tabs:: 

   .. group-tab:: Esp32_mqtt

      .. code:: cpp

         #include <PubSubClient.h>
         #include <WiFi.h>
         #include <ArduinoJson.h>

         // Variable de Control Alarmar
         int activar  = 0;
         int estado   = 0;
         int encoderi = 0;
         int encoderd = 0;

         // GPIO de salidad Digital
         int pin_led   = 2;

         //  Credenciales Wifi 
         const char* ssid = "TU_SSID";
         const char* password = "TU_CLAVE_WIFI";

         // Credenciales MQTT
         const char* mqtt_broker = "192.168.100.178";
         const int mqtt_port = 1883;
         const char* cliente = "rm1_esp32";

         // Temas MQTT Publicar
         const char* tema_sub = "rm1/acciones";
         const char* tema_pub_est = "rm1/estados";
         const char* tema_pub_sen = "rm1/sensores";

         // Variables de control de tiempo
         unsigned long lastTime = 0;

         // Creacion del objeto cliente
         WiFiClient espClient;
         PubSubClient client(espClient);

         // Tamaño de mensaje JSON

         void setup() {
         // Setup Serial
         Serial.begin(115200);
         // Setup Wifi
         setup_wifi();
         // Setup MQTT
         conexion();
         // Manejo del rele
         pinMode(pin_led, OUTPUT);     
         
         }

         void loop() {
         Loop_MQTT();
         if (millis() - lastTime >= 100){
            estado = 1;
            encoderi = encoderi+1;
            envioDatos(tema_pub_est, estado, encoderi, encoderd);
            envioDatos(tema_pub_sen, estado, encoderi, encoderd);
            lastTime = millis();
         }
         if (activar == 1){
            digitalWrite(pin_led, HIGH);  // Enciende el LED
            
            }
         else {
            digitalWrite(pin_led, LOW);  // Enciende el LED
         }
         
         }

   .. group-tab:: Conf_mqtt

      .. code:: cpp

         void setup_wifi() {
         // Conexión Wifi
         delay(10);
         Serial.println();
         Serial.print("Conectando a ");
         Serial.println(ssid);
         WiFi.begin(ssid, password);
         while (WiFi.status() != WL_CONNECTED) {
            delay(500);
            Serial.print(".");
         }
         Serial.println("");
         Serial.print("WiFi conectado - Dirección IP del ESP: ");
         Serial.println(WiFi.localIP());
         }

         void reconnect() {

            // Reintentos espaciados sin while/delay (connect aún puede bloquear).

            static unsigned long ultimoIntento = 0;

            if (client.connected()) return;

            if (millis() - ultimoIntento < 2000UL) return;

            ultimoIntento = millis();

            if (client.connect(cliente)) {

               Serial.println("MQTT conectado");

               client.subscribe(tema_sub, 1);

            } else {

               Serial.print("Reintento MQTT: estado ");

               Serial.println(client.state());

            }

         }


         void conexion() {
         // Conexión MQTT
         client.setServer(mqtt_broker, mqtt_port);
         client.setCallback(callback);
         }

         void Loop_MQTT() {
         // Manejo MQTT 
         if (!client.connected()) {
            reconnect();
         }
         client.loop();
         }

         void envioDatos(const char* mqtt_topic_publicar, int estado, int encoderi, int encoderd) {
         JsonDocument mensaje;

         if (strcmp(mqtt_topic_publicar, tema_pub_est) == 0) {
            mensaje["estado"]   = estado;
            String mensaje_json;
            serializeJson(mensaje, mensaje_json);
            client.publish(mqtt_topic_publicar, mensaje_json.c_str(), false);
         }

         if (strcmp(mqtt_topic_publicar, tema_pub_sen) == 0) {
            mensaje["EncoderI"]   = encoderi;
            mensaje["EncoderD"]   = encoderd;
            String mensaje_json;
            serializeJson(mensaje, mensaje_json);
            client.publish(mqtt_topic_publicar, mensaje_json.c_str(), false);
         }
         
         
         }

         void callback(char* topic, byte* payload, unsigned int length) {
         JsonDocument doc;
         DeserializationError error = deserializeJson(doc, payload, length);

         if (error) {
            Serial.print("Error al deserializar JSON: ");
            Serial.println(error.c_str());
            return;
         }

         String topico(topic);
         if (topico == "rm1/acciones") {
               activar  = doc["avanzar"];
         }
         }

Notas adicionales: **Publicar mensaje:**

.. code:: cpp

   client.publish("topic", mensaje_json.c_str(), false);  // QoS 0; tercer argumento = retain

.. important::

   En ``PubSubClient``, ``publish()`` envía con **QoS 0** y su tercer
   argumento es el indicador **retained**, no la calidad de servicio.
   ``subscribe(topic, 1)`` sí pide QoS 1 para las suscripciones.
   Para telemetría crítica se requiere un protocolo con confirmaciones
   o una biblioteca MQTT que implemente publicación QoS 1.

**Suscribirse a un tópico:**

.. code:: cpp

   client.subscribe("Carrito_1/Acciones", 0);  // QoS 0



Referencias técnicas
---------------------

* `Documentación oficial de Eclipse Paho MQTT Python
  <https://eclipse.dev/paho/clients/python/docs/>`_.
* `Referencia de la API de Paho MQTT Python
  <https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html>`_.
* `Migración de Paho MQTT 1.x a 2.x
  <https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html>`_.
* `Paquete Paho MQTT en PyPI
  <https://pypi.org/project/paho-mqtt/>`_.
* `Migración a Mosquitto 2.x
  <https://mosquitto.org/documentation/migrating-to-2-0/>`_.
* `Autenticación en Mosquitto
  <https://mosquitto.org/documentation/authentication-methods/>`_.
* `Paquete python3-paho-mqtt de Ubuntu 24.04
  <https://packages.ubuntu.com/noble/python3-paho-mqtt>`_.
* `PEP 668: entornos Python gestionados externamente
  <https://peps.python.org/pep-0668/>`_.
* `Documentación ROS 2 sobre dependencias Python
  <https://docs.ros.org/en/rolling/How-To-Guides/Using-Python-Packages.html>`_.
