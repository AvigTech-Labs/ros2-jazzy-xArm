Estructura de programación MQTT con Mosquitto y Python
======================================================

1. ¿Qué es Mosquitto y qué programa se escribe en Python?
---------------------------------------------------------

**Mosquitto** es un **broker MQTT**: recibe mensajes publicados por los
clientes y los distribuye a los clientes suscritos a los tópicos
correspondientes.

**Paho MQTT** es la biblioteca usada por los programas Python para
comunicarse con Mosquitto. No se necesita escribir el broker en Python.

.. code-block:: text

                       Broker Mosquitto
                            :1883
                        /            \
                       /              \
              Publica y recibe    Publica y recibe
                     /                  \
          Equipo 1: Python       Equipo 2: ESP32 o Python
          rm1/acciones  -------->  Suscripción a acciones
          rm1/sensores  <--------  Publicación de sensores
          rm1/estados   <--------  Publicación de estados

.. important::

   Los **tópicos MQTT** (por ejemplo ``rm1/sensores``) no son tópicos ROS 2.
   La coincidencia en la palabra «tópico» no implica que un mensaje pase
   automáticamente entre ambos sistemas. Para eso se programa un **puente**.

1.1. Elementos de un sistema MQTT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Conceptos básicos
   :header-rows: 1
   :widths: 24 41 35

   * - Concepto
     - Función
     - Ejemplo del curso
   * - Broker
     - Recibe y distribuye mensajes.
     - Mosquitto en el puerto 1883.
   * - Cliente
     - Aplicación conectada al broker.
     - ``equipo1.py``, ``equipo2.py`` o ESP32.
   * - Publicador
     - Envía un contenido a un tópico.
     - Equipo 2 publica ``rm1/sensores``.
   * - Suscriptor
     - Recibe publicaciones de un tópico.
     - Equipo 1 se suscribe a ``rm1/sensores``.
   * - Tópico MQTT
     - Dirección lógica para distribuir mensajes.
     - ``rm1/acciones``.
   * - Payload
     - Datos transportados (bytes).
     - ``{"EncoderI": 20, "EncoderD": 30}``.
   * - Client ID
     - Identifica una conexión ante el broker.
     - ``avigtech_equipo1``.
   * - Callback
     - Función invocada cuando ocurre un evento.
     - ``on_connect()`` y ``on_message()``.
   * - QoS
     - Nivel de entrega MQTT.
     - QoS 0 en las prácticas de ESP32.

1.2. Tópicos y estructuras JSON del repositorio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

En esta guía se mantienen los nombres usados en ``dispositivos.rst``.

.. list-table:: Contrato de comunicación del laboratorio
   :header-rows: 1
   :widths: 22 18 60

   * - Tópico
     - Dirección habitual
     - Ejemplo de contenido
   * - ``rm1/sensores``
     - Equipo 2 → Equipo 1
     - ``{"EncoderI": 20, "EncoderD": 30}``
   * - ``rm1/estados``
     - Equipo 2 → Equipo 1
     - ``{"Estado": "Encendido"}``
   * - ``rm1/acciones``
     - Equipo 1 → Equipo 2
     - ``{"vel": {"u_meta": 0.34, "w_meta": 0.10}, "avanzar": 0, "soltar_obj": 0, "parar": 1}``

``EncoderI`` y ``EncoderD`` son nombres de campos del JSON del ejemplo; no
son tipos de mensaje ROS. ``u_meta`` y ``w_meta`` representan consignas de
velocidad lineal y angular **según la lógica definida por la aplicación**;
sus unidades físicas deben documentarse en el firmware que las consume.

**No se debe asumir que un JSON recibido es válido o una orden segura**:
debe validarse antes de actuar sobre un robot.

2. ¿Qué debe contener un programa Python con MQTT?
--------------------------------------------------

Los programas Paho MQTT suelen seguir **ocho etapas**.

#. Importar bibliotecas (``json``, ``time`` y ``paho.mqtt.client``).
#. Definir broker, puerto, identificador y tópicos MQTT.
#. Definir los callbacks de conexión, recepción y desconexión.
#. Crear la instancia ``mqtt.Client`` con la versión de callbacks.
#. Asociar callbacks al cliente.
#. Conectarse y **mantener activo el bucle de red**.
#. Publicar o procesar mensajes mientras la aplicación funciona.
#. Desconectarse y liberar recursos al finalizar.

.. list-table:: Estructura equivalente a la guía ROS 2
   :header-rows: 1
   :widths: 31 34 35

   * - Función
     - ROS 2 (rclpy)
     - MQTT (Paho)
   * - Inicializar cliente
     - ``rclpy.init()`` y ``Node()``
     - ``mqtt.Client(...)``
   * - Publicar
     - ``publisher.publish(msg)``
     - ``client.publish(topic, payload)``
   * - Suscribirse
     - ``create_subscription(...)``
     - ``client.subscribe(...)``
   * - Recibir datos
     - Callback ROS de suscripción
     - ``on_message(...)``
   * - Recibir eventos de conexión
     - Gestión del contexto y entidades ROS
     - ``on_connect(...)``
   * - Procesar eventos de red
     - ``rclpy.spin(node)``
     - ``loop_start()`` o ``loop_forever()``
   * - Terminar
     - ``destroy_node()``, ``rclpy.shutdown()``
     - ``disconnect()``, ``loop_stop()``

.. warning::

   ``rclpy.spin()`` y el bucle de red MQTT **no son intercambiables**.
   Un programa que utiliza únicamente Paho **no necesita** ``rclpy.init()``.
   Si se combinan ROS 2 y MQTT, cada sistema necesita procesar sus propios
   eventos sin bloquear al otro.

3. Preparación del entorno
--------------------------

3.1. Instalación y comprobación de Mosquitto
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La instalación básica ya está cubierta en ``dispositivos.rst``. Aquí solo
se incluyen los comandos necesarios para ejecutar las prácticas.

.. code-block:: bash

   sudo apt update
   sudo apt install mosquitto mosquitto-clients
   sudo systemctl enable --now mosquitto
   sudo systemctl status mosquitto
   sudo ss -lntp | grep 1883

Para una prueba **en el mismo computador** no es necesario abrir Mosquitto
a toda la red:

.. code-block:: bash

   # Terminal 1: observar un tópico
   mosquitto_sub -h localhost -t rm1/sensores -v

   # Terminal 2: publicar un JSON de ejemplo
   mosquitto_pub -h localhost -t rm1/sensores \
     -m '{"EncoderI":20,"EncoderD":30}'

Si el broker recibe conexiones desde una ESP32, será necesario configurar
un listener accesible desde la LAN, autenticación y reglas de acceso.

.. important::

   La configuración ``listener 1883`` con ``allow_anonymous true`` que
   aparece en el repositorio es **exclusivamente para una red aislada de
   laboratorio**. No debe utilizarse en una red pública o de producción.
   Para equipos reales usa autenticación, ACL y, cuando corresponda, TLS.
   No incluyas credenciales en el código publicado en GitHub.

3.2. Instalar Paho MQTT 2.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~

De acuerdo con el entorno virtual definido en el repositorio para
Ubuntu 24.04:

.. code-block:: bash

   source ~/venvs/ros2-jazzy/bin/activate
   python -m pip install 'paho-mqtt>=2,<3'
   python -m pip show paho-mqtt

El entorno virtual debe tener acceso a las dependencias ROS 2 si también
se van a ejecutar nodos ``rclpy``. Compila y ejecuta los programas con el
mismo entorno Python; evita mezclar un ejecutable instalado con un intérprete
diferente al que tiene Paho.

4. Esqueleto mínimo de un programa MQTT
---------------------------------------

El siguiente ejemplo contiene los elementos fundamentales de un cliente
que **se suscribe** y además **publica** periódicamente.

.. code-block:: python
   :caption: mi_pkg_python/mqtt/cliente_mqtt_base.py

   import json
   import os
   import time
   import paho.mqtt.client as mqtt

   # 1. Configuración de conexión.
   BROKER = os.getenv('MQTT_BROKER', 'localhost')
   PUERTO = 1883
   CLIENT_ID = 'avigtech_mqtt_base'
   TOPICO_RECIBIR = 'rm1/sensores'
   TOPICO_PUBLICAR = 'rm1/acciones'


   # 2. Callback: el broker confirmó la conexión.
   def on_connect(client, userdata, flags, reason_code, properties):
       if reason_code == 0:
           print('Conectado a Mosquitto')
           # Repetir suscripción al reconectar.
           client.subscribe(TOPICO_RECIBIR, qos=0)
       else:
           print(f'Conexión rechazada: {reason_code}')


   # 3. Callback: llegó un mensaje al tópico suscrito.
   def on_message(client, userdata, msg):
       try:
           datos = json.loads(msg.payload.decode('utf-8'))
           if msg.topic == TOPICO_RECIBIR:
               print('Encoder izquierdo:', datos['EncoderI'])
       except (UnicodeDecodeError, ValueError, KeyError, TypeError) as error:
           print(f'Mensaje inválido: {error}')


   # 4. Callback: se perdió o cerró la conexión.
   def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
       print(f'Desconectado de MQTT: {reason_code}')


   def main():
       # 5. Crear el cliente con la API de callbacks de Paho 2.x.
       client = mqtt.Client(
           callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
           client_id=CLIENT_ID,
           protocol=mqtt.MQTTv311
       )

       # 6. Asociar cada evento a su función.
       client.on_connect = on_connect
       client.on_message = on_message
       client.on_disconnect = on_disconnect

       # 7. Mantener la conexión, incluyendo reintentos automáticos.
       client.reconnect_delay_set(min_delay=1, max_delay=10)
       client.connect_async(BROKER, PUERTO, keepalive=60)
       client.loop_start()

       try:
           while True:
               # Solo publicar después de establecer conexión.
               if client.is_connected():
                   comando = {'avanzar': 0, 'parar': 1}
                   texto = json.dumps(comando)
                   resultado = client.publish(
                       TOPICO_PUBLICAR, texto, qos=0, retain=False
                   )
                   if resultado.rc != mqtt.MQTT_ERR_SUCCESS:
                       print('Publicación no aceptada por el cliente local')
               time.sleep(1)
       except KeyboardInterrupt:
           print('Finalizando cliente MQTT...')
       finally:
           # 8. Desconectar y terminar el hilo de red.
           client.disconnect()
           client.loop_stop()


   if __name__ == '__main__':
       main()

.. note::

   Este programa transmite una **orden de ejemplo**. No debe conectarse a
   actuadores reales sin validación del mensaje y una estrategia de parada
   segura ante desconexiones. ``retain=False`` evita que esa orden quede
   almacenada como mensaje retenido por el broker.

5. Anatomía del cliente MQTT: instrucciones fundamentales
---------------------------------------------------------

5.1. Creación del cliente
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   client = mqtt.Client(
       callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
       client_id='avigtech_equipo1',
       protocol=mqtt.MQTTv311
   )

* ``CallbackAPIVersion.VERSION2``: firma moderna de callbacks de Paho 2.x.
* ``client_id``: nombre que identifica al cliente ante el broker.
* ``protocol=mqtt.MQTTv311``: protocolo MQTT 3.1.1, habitual en las prácticas
  con ``PubSubClient`` de ESP32.

**Cada programa conectado simultáneamente debe usar un ``client_id``
distinto**; si comparten identificador, el broker puede desconectar
al cliente anterior.

5.2. Asociación de callbacks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   client.on_connect = on_connect
   client.on_message = on_message
   client.on_disconnect = on_disconnect

La asignación **no ejecuta** inmediatamente las funciones. Únicamente
registra qué función debe invocar Paho cuando ocurra cada evento.

.. list-table:: Callbacks Paho API VERSION2
   :header-rows: 1
   :widths: 30 70

   * - Callback
     - Cuándo se ejecuta y para qué sirve
   * - ``on_connect(client, userdata, flags, reason_code, properties)``
     - Cuando se recibe la respuesta CONNACK. Conviene suscribirse aquí
       para recuperar las suscripciones después de una reconexión.
   * - ``on_message(client, userdata, msg)``
     - Cuando llega una publicación coincidente con una suscripción.
   * - ``on_disconnect(client, userdata, disconnect_flags, reason_code, properties)``
     - Cuando se cierra o pierde la conexión.
   * - ``on_publish(client, userdata, mid, reason_code, properties)``
     - Cuando progresa o se confirma una publicación, según QoS.
   * - ``on_subscribe(client, userdata, mid, reason_code_list, properties)``
     - Cuando el broker responde a una solicitud de suscripción.

.. warning::

   El callback antiguo ``on_connect(client, userdata, flags, rc)``
   pertenece a la API previa. No debe mezclarse con
   ``mqtt.CallbackAPIVersion.VERSION2``. Este cambio es de **Paho MQTT
   1.x a 2.x**, no un cambio propio de ROS 2 Humble a Jazzy.

5.3. Conexión y bucle de red
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   client.connect_async(BROKER, 1883, keepalive=60)
   client.loop_start()

``connect_async()`` prepara una conexión no bloqueante. ``loop_start()``
crea un hilo que procesa los mensajes MQTT, gestiona las respuestas del
broker y permite reconectarse. Alternativamente, para un programa MQTT
simple y exclusivamente receptor, se puede emplear ``loop_forever()``,
que bloquea el hilo principal hasta la desconexión.

.. important::

   Un programa MQTT que llama solamente a ``connect()`` y luego termina,
   sin procesar el bucle de red, no mantiene de manera adecuada la recepción
   de mensajes, los keepalive ni las reconexiones.

5.4. Suscripción
~~~~~~~~~~~~~~~~

.. code-block:: python

   def on_connect(client, userdata, flags, reason_code, properties):
       if reason_code == 0:
           client.subscribe('rm1/sensores', qos=0)
           client.subscribe('rm1/estados', qos=0)

``subscribe()`` expresa el interés en un tópico. **No es la función que
procesa su contenido**: los mensajes llegan a ``on_message()``.

5.5. Publicación y codificación JSON
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   comando = {
       'vel': {'u_meta': 0.34, 'w_meta': 0.10},
       'avanzar': 0,
       'soltar_obj': 0,
       'parar': 1
   }
   texto = json.dumps(comando)
   client.publish('rm1/acciones', texto, qos=0, retain=False)

* ``dict``: estructura Python con nombres y valores.
* ``json.dumps()``: convierte el diccionario a una cadena JSON.
* ``publish()``: envía el contenido al tópico MQTT.
* ``qos=0``: adecuado para comparar con el uso de ``PubSubClient`` del
  firmware del curso, que publica con QoS 0.
* ``retain=False``: no conservar esta orden como último mensaje retenido.

5.6. Recepción y decodificación JSON
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def on_message(client, userdata, msg):
       if msg.topic != 'rm1/sensores':
           return

       try:
           texto = msg.payload.decode('utf-8')
           datos = json.loads(texto)
           encoder_i = int(datos['EncoderI'])
           encoder_d = int(datos['EncoderD'])
           print(f'EncoderI={encoder_i}, EncoderD={encoder_d}')
       except (UnicodeDecodeError, ValueError, KeyError, TypeError) as error:
           print(f'Datos descartados: {error}')

* ``msg.topic`` identifica el tópico MQTT del mensaje recibido.
* ``msg.payload`` contiene bytes, que deben interpretarse correctamente.
* ``json.loads()`` convierte el texto JSON a un objeto Python.
* ``datos['EncoderI']`` accede a una clave esperada en la estructura.
* La validación evita que una publicación malformada interrumpa la aplicación.

5.7. QoS, mensajes retenidos y reconexión
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Decisiones de comunicación
   :header-rows: 1
   :widths: 20 33 47

   * - Opción
     - Significado
     - Recomendación didáctica
   * - QoS 0
     - Entrega de mejor esfuerzo.
     - Telemetría periódica y compatibilidad con ``PubSubClient``.
   * - QoS 1
     - Al menos una entrega al receptor MQTT correspondiente.
     - Requiere gestionar duplicados en aplicaciones sensibles.
   * - QoS 2
     - Flujo de entrega exactamente una vez a nivel MQTT.
     - No significa que un actuador ejecute una acción exactamente una vez.
   * - ``retain=True``
     - El broker conserva el último mensaje retenido del tópico.
     - Estados publicados, cuando convenga; no comandos de movimiento.
   * - ``on_connect``
     - Recibe confirmación de conexión y reconexión.
     - Suscribirse aquí para restaurar las suscripciones.

.. important::

   ``publish()`` no significa que el actuador haya obedecido la orden.
   Si se necesita conocer el resultado de una acción, el dispositivo
   debe publicar un **acuse o estado de aplicación** independiente.

6. Práctica del repositorio: Equipo 1 y Equipo 2
------------------------------------------------

Los programas siguientes reproducen el intercambio de la práctica existente
pero con funciones separadas, manejo de conexión y comentarios. Ambos pueden
funcionar **en un solo computador** utilizando ``localhost``.

6.1. Equipo 1: recibe sensores y envía acciones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: mi_pkg_python/mqtt/equipo1.py

   import json
   import os
   import time
   import paho.mqtt.client as mqtt

   BROKER = os.getenv('MQTT_BROKER', 'localhost')
   TOPICO_SENSORES = 'rm1/sensores'
   TOPICO_ESTADOS = 'rm1/estados'
   TOPICO_ACCIONES = 'rm1/acciones'


   def on_connect(client, userdata, flags, reason_code, properties):
       # Se ejecuta al conectar o reconectar con Mosquitto.
       if reason_code == 0:
           print('[Equipo 1] Conexión establecida')
           client.subscribe(TOPICO_SENSORES, qos=0)
           client.subscribe(TOPICO_ESTADOS, qos=0)
       else:
           print(f'[Equipo 1] Conexión rechazada: {reason_code}')


   def on_message(client, userdata, msg):
       # Identificar el tópico y decodificar el JSON recibido.
       try:
           datos = json.loads(msg.payload.decode('utf-8'))
           if msg.topic == TOPICO_SENSORES:
               print('[Equipo 1] EncoderI:', datos['EncoderI'])
               print('[Equipo 1] EncoderD:', datos['EncoderD'])
           elif msg.topic == TOPICO_ESTADOS:
               print('[Equipo 1] Estado:', datos['Estado'])
       except (UnicodeDecodeError, ValueError, KeyError, TypeError) as error:
           print(f'[Equipo 1] Datos inválidos: {error}')


   def main():
       # Identificador único para no desplazar a otros clientes.
       client = mqtt.Client(
           callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
           client_id='avigtech_equipo1',
           protocol=mqtt.MQTTv311
       )
       client.on_connect = on_connect
       client.on_message = on_message
       client.reconnect_delay_set(min_delay=1, max_delay=10)
       client.connect_async(BROKER, 1883, keepalive=60)
       client.loop_start()

       try:
           while True:
               if client.is_connected():
                   # Mensaje con los mismos campos del repositorio.
                   orden = {
                       'vel': {'u_meta': 0.34, 'w_meta': 0.10},
                       'nombre': 'robot1',
                       'avanzar': 0,
                       'soltar_obj': 0,
                       'parar': 1
                   }
                   client.publish(
                       TOPICO_ACCIONES, json.dumps(orden),
                       qos=0, retain=False
                   )
                   print('[Equipo 1] Orden de demostración publicada')
               time.sleep(1.0)
       except KeyboardInterrupt:
           print('[Equipo 1] Finalizando')
       finally:
           client.disconnect()
           client.loop_stop()


   if __name__ == '__main__':
       main()

6.2. Equipo 2: recibe acciones y publica sensores
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: mi_pkg_python/mqtt/equipo2.py

   import json
   import os
   import time
   import paho.mqtt.client as mqtt

   BROKER = os.getenv('MQTT_BROKER', 'localhost')
   TOPICO_SENSORES = 'rm1/sensores'
   TOPICO_ESTADOS = 'rm1/estados'
   TOPICO_ACCIONES = 'rm1/acciones'


   def on_connect(client, userdata, flags, reason_code, properties):
       if reason_code == 0:
           print('[Equipo 2] Conectado a Mosquitto')
           client.subscribe(TOPICO_ACCIONES, qos=0)
       else:
           print(f'[Equipo 2] Conexión rechazada: {reason_code}')


   def on_message(client, userdata, msg):
       if msg.topic != TOPICO_ACCIONES:
           return
       try:
           orden = json.loads(msg.payload.decode('utf-8'))
           if not isinstance(orden, dict):
               raise ValueError('La orden debe ser un objeto JSON')
           print('[Equipo 2] Comando recibido:', orden)
       except (UnicodeDecodeError, ValueError, TypeError) as error:
           print(f'[Equipo 2] Comando descartado: {error}')


   def main():
       client = mqtt.Client(
           callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
           client_id='avigtech_equipo2',
           protocol=mqtt.MQTTv311
       )
       client.on_connect = on_connect
       client.on_message = on_message
       client.reconnect_delay_set(min_delay=1, max_delay=10)
       client.connect_async(BROKER, 1883, keepalive=60)
       client.loop_start()

       contador = 0
       try:
           while True:
               if client.is_connected():
                   # Simulación de lecturas de encoders.
                   sensores = {
                       'EncoderI': 20 + contador,
                       'EncoderD': 30 + contador
                   }
                   estados = {'Estado': 'Encendido'}

                   client.publish(
                       TOPICO_SENSORES, json.dumps(sensores), qos=0
                   )
                   client.publish(
                       TOPICO_ESTADOS, json.dumps(estados), qos=0
                   )
                   contador += 1
                   print('[Equipo 2] Sensores publicados:', sensores)
               time.sleep(1.0)
       except KeyboardInterrupt:
           print('[Equipo 2] Finalizando')
       finally:
           client.disconnect()
           client.loop_stop()


   if __name__ == '__main__':
       main()

.. note::

   El **Equipo 2** es una simulación del intercambio de mensajes que puede
   realizar la ESP32 del curso. No controla motores reales: las lecturas
   de encoders se generan artificialmente para probar la comunicación.

6.3. Ejecutar los dos equipos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si los programas se guardaron dentro del paquete, sigue la configuración
del capítulo 8 y ejecuta:

.. code-block:: bash

   # Terminal 1: broker ya en ejecución
   sudo systemctl status mosquitto

   # Terminal 2: cliente receptor de sensores
   ros2 run mi_pkg_python mqtt_equipo1

   # Terminal 3: cliente emisor de sensores
   ros2 run mi_pkg_python mqtt_equipo2

Para verificar sin depender de los scripts:

.. code-block:: bash

   mosquitto_sub -h localhost -t 'rm1/#' -v

El comodín MQTT ``#`` permite observar todos los niveles bajo ``rm1/``.
Los mensajes deben contener los campos definidos en la tabla del apartado 1.

7. Puente MQTT ↔ ROS 2 dentro de ``mi_pkg_python``
--------------------------------------------------

El repositorio ya incluye una práctica de puente entre MQTT y ROS 2.
Esta sección detalla la **estructura de programación** que debe seguirse
para que el programa sea más robusto.

7.1. ¿Cuál es su función?
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ESP32 / Equipo 2
     |  Publica JSON
     v
   Mosquitto: rm1/sensores
     |
     v
   Paho MQTT: on_message()       [hilo MQTT]
     |
     v
   Cola de datos thread-safe
     |
     v
   Temporizador del nodo ROS 2   [executor ROS 2]
     |
     v
   ROS 2: /sensores  (std_msgs/Float32)

   ROS 2: /acciones (std_msgs/Int32)
     |
     v
   Callback de suscripción ROS 2
     |
     v
   Paho MQTT: publish()
     |
     v
   Mosquitto: rm1/acciones  ---> ESP32 / Equipo 2

.. important::

   ``on_message()`` se ejecuta en el hilo de Paho cuando se usa
   ``loop_start()``. No conviene hacer trabajo pesado ni llamar a
   ``rclpy.spin()`` desde ese callback. En este ejemplo se utiliza una
   ``queue.Queue`` segura entre hilos y el temporizador ROS 2 procesa
   las lecturas. El nodo ROS se procesa mediante **un solo**
   ``rclpy.spin(node)`` en ``main()``.

7.2. Ejemplo comentado de puente bidireccional
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :caption: mi_pkg_python/mqtt/puente_mqtt_ros2.py

   import json
   import os
   import queue
   import threading
   import time

   import paho.mqtt.client as mqtt
   import rclpy
   from rclpy.node import Node
   from std_msgs.msg import Float32, Int32


   class PuenteMQTTROS2(Node):

       def __init__(self):
           # 1. Crear el nodo ROS 2.
           super().__init__('mqtt_bridge')

           # 2. Parámetros configurables desde ROS 2.
           self.declare_parameter('broker', os.getenv('MQTT_BROKER', 'localhost'))
           self.declare_parameter('puerto', 1883)
           self.declare_parameter('topic_mqtt_sensores', 'rm1/sensores')
           self.declare_parameter('topic_mqtt_acciones', 'rm1/acciones')
           self.declare_parameter('timeout_s', 2.0)

           self.broker = self.get_parameter('broker').value
           self.puerto = int(self.get_parameter('puerto').value)
           self.topic_sensores = self.get_parameter('topic_mqtt_sensores').value
           self.topic_acciones = self.get_parameter('topic_mqtt_acciones').value
           self.timeout_s = float(self.get_parameter('timeout_s').value)

           # 3. ROS 2: publicación de datos y recepción de acciones.
           self.pub = self.create_publisher(Float32, 'sensores', 10)
           self.sub = self.create_subscription(
               Int32, 'acciones', self.recibir_accion_ros, 10
           )

           # 4. Compartición segura entre hilo MQTT y executor ROS 2.
           self.cola_lecturas = queue.Queue(maxsize=100)
           self.mqtt_conectado = threading.Event()
           self.ultima_lectura = None
           self.datos_activos = False

           # 5. ROS 2 revisa periódicamente la cola y el watchdog.
           self.timer_lectura = self.create_timer(0.1, self.publicar_lecturas_ros)
           self.timer_watchdog = self.create_timer(0.5, self.revisar_timeout)

           # 6. Crear cliente Paho MQTT con API de callbacks VERSION2.
           self.mqtt_client = mqtt.Client(
               callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
               client_id='avigtech_puente_ros2',
               protocol=mqtt.MQTTv311
           )
           self.mqtt_client.on_connect = self.on_connect
           self.mqtt_client.on_message = self.on_message
           self.mqtt_client.on_disconnect = self.on_disconnect

           # 7. Iniciar conexión sin bloquear el executor ROS 2.
           self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=10)
           self.mqtt_client.connect_async(self.broker, self.puerto, 60)
           self.mqtt_client.loop_start()

           self.get_logger().info('Puente MQTT ↔ ROS 2 iniciado')

       def on_connect(self, client, userdata, flags, reason_code, properties):
           # Callback de Paho (hilo MQTT).
           if reason_code == 0:
               self.mqtt_conectado.set()
               client.subscribe(self.topic_sensores, qos=0)
           else:
               self.mqtt_conectado.clear()
               print(f'MQTT: conexión rechazada: {reason_code}')

       def on_disconnect(
           self, client, userdata, disconnect_flags, reason_code, properties
       ):
           # Callback de Paho (hilo MQTT).
           self.mqtt_conectado.clear()

       def on_message(self, client, userdata, msg):
           # Callback de Paho (hilo MQTT).
           # No procesar nodos ni bloquear aquí: solo validar y encolar.
           if msg.topic != self.topic_sensores:
               return

           try:
               datos = json.loads(msg.payload.decode('utf-8'))
               valor = float(datos['EncoderI'])
               self.cola_lecturas.put_nowait(valor)
           except (UnicodeDecodeError, ValueError, KeyError, TypeError):
               print('MQTT: mensaje de sensor inválido')
           except queue.Full:
               print('MQTT: cola llena, se descarta una lectura')

       def publicar_lecturas_ros(self):
           # Callback del temporizador ROS 2 (hilo del executor ROS).
           # Limitar el número de elementos por ciclo evita saturarlo.
           for _ in range(20):
               try:
                   valor = self.cola_lecturas.get_nowait()
               except queue.Empty:
                   break

               # La marca de tiempo se maneja solo desde ROS 2.
               self.ultima_lectura = time.monotonic()
               self.datos_activos = True

               msg = Float32()
               msg.data = float(valor)
               self.pub.publish(msg)

       def revisar_timeout(self):
           # Watchdog: detectar datos desactualizados.
           if self.ultima_lectura is None:
               return

           if time.monotonic() - self.ultima_lectura > self.timeout_s:
               if self.datos_activos:
                   self.get_logger().warning(
                       'Sin lecturas MQTT recientes; datos marcados como inactivos'
                   )
               self.datos_activos = False

       def recibir_accion_ros(self, msg):
           # Callback ROS 2: convertir mensaje Int32 a JSON MQTT.
           if not self.mqtt_conectado.is_set():
               self.get_logger().warning('No se publica: MQTT desconectado')
               return

           orden = {
               'vel': {'u_meta': 0.34, 'w_meta': 0.10},
               'avanzar': int(msg.data)
           }
           respuesta = self.mqtt_client.publish(
               self.topic_acciones,
               json.dumps(orden),
               qos=0,
               retain=False
           )
           if respuesta.rc != mqtt.MQTT_ERR_SUCCESS:
               self.get_logger().warning('La publicación MQTT no fue aceptada')

       def detener_mqtt(self):
           # Liberar recursos MQTT al cerrar el nodo.
           self.mqtt_client.disconnect()
           self.mqtt_client.loop_stop()


   def main(args=None):
       # 8. Arranque de ROS 2: un único spin, independiente de loop_start().
       rclpy.init(args=args)
       node = PuenteMQTTROS2()
       try:
           rclpy.spin(node)
       except KeyboardInterrupt:
           pass
       finally:
           node.detener_mqtt()
           node.destroy_node()
           if rclpy.ok():
               rclpy.shutdown()


   if __name__ == '__main__':
       main()

.. warning::

   Este puente muestra una **arquitectura educativa**, no un controlador
   de seguridad industrial. El valor fijo de velocidad del ejemplo proviene
   del repositorio y debe reemplazarse por consignas verificadas antes de
   controlar motores. El watchdog solo marca telemetría como inactiva;
   **no constituye por sí solo un mecanismo de parada segura**.

7.3. Ejecutar y comprobar el puente
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Terminal 1: iniciar el puente.
   ros2 run mi_pkg_python puente_mqtt_ros2 \
     --ros-args -p broker:=localhost

   # Terminal 2: publicar datos MQTT para el puente.
   mosquitto_pub -h localhost -t rm1/sensores \
     -m '{"EncoderI":20,"EncoderD":30}'

   # Terminal 3: visualizar el mensaje convertido a ROS 2.
   ros2 topic echo /sensores

   # Terminal 4: enviar un mensaje ROS 2 para publicarlo en MQTT.
   ros2 topic pub --once /acciones std_msgs/msg/Int32 '{data: 1}'

   # Terminal 5: observar lo que el puente publicó a MQTT.
   mosquitto_sub -h localhost -t rm1/acciones -v

El último suscriptor debe iniciarse **antes** de enviar el comando, porque
las publicaciones de esta práctica no se guardan como retenidas.

8. Incorporación de programas en ``mi_pkg_python``
--------------------------------------------------

No se necesita otro paquete ROS 2. En el paquete existente puedes mantener
los módulos de cada tema y agregar un subdirectorio para MQTT.

.. code-block:: text

   ~/ros2_ws/src/mi_pkg_python/
   ├── package.xml
   ├── setup.py
   ├── setup.cfg
   └── mi_pkg_python/
       ├── __init__.py
       ├── publicador.py                 # Otros temas del curso
       ├── suscriptor.py
       └── mqtt/
           ├── __init__.py              # Necesario para importar el subpaquete
           ├── cliente_mqtt_base.py
           ├── equipo1.py
           ├── equipo2.py
           └── puente_mqtt_ros2.py

8.1. Registrar los ejecutables en ``setup.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cuando los archivos Python se encuentran dentro del subdirectorio
``mi_pkg_python/mqtt/``, el módulo completo es
``mi_pkg_python.mqtt.nombre_del_archivo``.

El **``setup.py`` existente** debe incluir ese subpaquete. Si utilizas
``packages=[package_name]``, cambia únicamente ese apartado por
``find_packages(exclude=['test'])`` (importando ``find_packages`` desde
``setuptools``), o incluye explícitamente ``mi_pkg_python.mqtt``.

.. code-block:: python

   # Fragmentos de setup.py: integrar en el archivo existente,
   # conservando todos los demás ejecutables del curso.
   from setuptools import setup, find_packages

   # Dentro de la llamada setup(...):
   # packages=find_packages(exclude=['test']),

   # Dentro de entry_points['console_scripts'] agregar:
   # 'mqtt_base = mi_pkg_python.mqtt.cliente_mqtt_base:main',
   # 'mqtt_equipo1 = mi_pkg_python.mqtt.equipo1:main',
   # 'mqtt_equipo2 = mi_pkg_python.mqtt.equipo2:main',
   # 'puente_mqtt_ros2 = mi_pkg_python.mqtt.puente_mqtt_ros2:main',

.. important::

   No reemplaces toda la lista ``console_scripts`` por este fragmento:
   perderías los ejecutables de nodos, servicios y acciones ya definidos
   en ``mi_pkg_python``.

8.2. Dependencias
~~~~~~~~~~~~~~~~~

Para el **puente ROS 2** confirma que ``package.xml`` declara:

.. code-block:: xml

   <exec_depend>rclpy</exec_depend>
   <exec_depend>std_msgs</exec_depend>

``paho-mqtt>=2,<3`` es una dependencia de Python instalada mediante
``pip`` en el entorno virtual descrito en el apartado 3.2. Su instalación
**no se obtiene automáticamente** al declarar ``rclpy`` o ``std_msgs``.
Si se añade un archivo ``requirements.txt`` al paquete, puede contener:

.. code-block:: text

   paho-mqtt>=2,<3

8.3. Compilación y ejecución
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Mantener activo el entorno que tiene instalado Paho 2.x.
   source ~/venvs/ros2-jazzy/bin/activate
   cd ~/ros2_ws
   colcon build --symlink-install --packages-select mi_pkg_python
   source install/setup.bash

   # Comprobar que el módulo MQTT está instalado.
   ros2 pkg executables mi_pkg_python

   # Ejecutar un programa del curso.
   ros2 run mi_pkg_python mqtt_equipo1

.. tip::

   Si ``ros2 run`` informa ``ModuleNotFoundError: No module named 'paho'``,
   comprueba la instalación en el **intérprete Python que ejecuta ese
   entry point**. Es posible tener Paho instalado en un entorno virtual y
   ejecutar un script que utiliza otro intérprete. Si ``ros2 run`` no
   encuentra ``mqtt_equipo1``, revisa ``setup.py``, la instalación del
   subpaquete y recompila.

9. Problemas frecuentes y soluciones
------------------------------------

.. list-table:: Diagnóstico de MQTT y ROS 2
   :header-rows: 1
   :widths: 32 37 31

   * - Síntoma
     - Posible causa
     - Primera comprobación
   * - ``Connection refused``
     - Broker apagado, puerto incorrecto o permisos de acceso.
     - ``systemctl status mosquitto`` y ``ss -lntp``.
   * - Conecta, pero no recibe datos.
     - Tópico diferente, suscripción no realizada o publicador ausente.
     - ``mosquitto_sub -t 'rm1/#' -v``.
   * - Los mensajes llegan con retraso.
     - Bloqueo del callback o carga elevada.
     - Evitar tareas largas en ``on_message``.
   * - Un cliente desconecta a otro.
     - Ambos usan el mismo ``client_id``.
     - Asignar identificadores diferentes.
   * - Error de argumentos en ``on_connect``.
     - Mezcla de firmas Paho 1.x y VERSION2.
     - Comprobar firma y versión instalada.
   * - Un JSON produce excepción.
     - Claves ausentes o payload no válido.
     - Validar ``msg.payload`` antes de usarlo.
   * - ``ros2 topic echo /sensores`` no muestra datos.
     - El puente no está conectado o no recibe ``EncoderI``.
     - Inspeccionar ambos tópicos y parámetros.
   * - Fallo al importar Paho mediante ``ros2 run``.
     - El ejecutable utiliza otro entorno Python.
     - Revisar intérprete de los ejecutables instalados.
   * - ``Executor is already spinning``.
     - ``spin()`` / ``spin_once()`` anidado sobre un executor ocupado.
     - Usar un solo spin ROS y el bucle propio de Paho.



12. Referencias
---------------

* Eclipse Paho, documentación Python:
  https://eclipse.dev/paho/files/paho.mqtt.python/html/
* Eclipse Paho, migración a callbacks API 2.x:
  https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html
* Eclipse Mosquitto, configuración y autenticación:
  https://mosquitto.org/documentation/authentication-methods/
* Eclipse Mosquitto, referencia de configuración:
  https://mosquitto.org/man/mosquitto-conf-5.html
* Documentación de ROS 2 Jazzy:
  https://docs.ros.org/en/jazzy/
