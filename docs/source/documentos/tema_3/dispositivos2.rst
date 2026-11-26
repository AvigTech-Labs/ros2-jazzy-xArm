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

   import os
   import paho.mqtt.client as mqtt

   # 1. Datos de conexión.
   BROKER = os.getenv('MQTT_BROKER', 'localhost')
   PUERTO = int(os.getenv('MQTT_PORT', '1883'))
   TOPICO = 'laboratorio/datos'


   # 2. Callback de conexión (API Paho 2.x).
   def on_connect(client, userdata, flags, reason_code, properties):
       if reason_code == 0:
           print('Conexión establecida con el broker.')

           # Suscribirse aquí permite recuperar la suscripción
           # si la conexión se interrumpe y después se restablece.
           client.subscribe(TOPICO, qos=1)
       else:
           print(f'Conexión rechazada: {reason_code}')


   # 3. Callback de recepción de mensajes.
   def on_message(client, userdata, msg):
       try:
           texto = msg.payload.decode('utf-8')
       except UnicodeDecodeError:
           print('El payload recibido no contiene texto UTF-8.')
           return

       print(f'Tópico: {msg.topic}')
       print(f'Contenido: {texto}')
       print(f'QoS de recepción: {msg.qos}')


   # 4. Callback de desconexión.
   def on_disconnect(client, userdata, flags, reason_code, properties):
       print(f'Conexión finalizada: {reason_code}')


   def main():
       # 5. Crear el cliente con callbacks VERSION2.
       client = mqtt.Client(
           callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
           client_id=f'curso_suscriptor_{os.getpid()}',
           protocol=mqtt.MQTTv311
       )

       # 6. Asociar callbacks a los eventos MQTT.
       client.on_connect = on_connect
       client.on_message = on_message
       client.on_disconnect = on_disconnect

       # 7. Configurar credenciales solamente si se han definido.
       usuario = os.getenv('MQTT_USER')
       clave = os.getenv('MQTT_PASSWORD')
       if usuario:
           if not clave:
               raise RuntimeError('Falta la variable MQTT_PASSWORD.')
           client.username_pw_set(usuario, clave)

       # 8. Conectarse y procesar la red en el hilo principal.
       try:
           client.connect(BROKER, PUERTO, keepalive=60)
           print('Esperando mensajes; Ctrl+C para terminar.')
           client.loop_forever()
       except KeyboardInterrupt:
           print('Finalizando suscriptor...')
       finally:
           client.disconnect()


   if __name__ == '__main__':
       main()

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

   import json
   import os
   import threading
   import paho.mqtt.client as mqtt

   BROKER = os.getenv('MQTT_BROKER', 'localhost')
   PUERTO = int(os.getenv('MQTT_PORT', '1883'))
   TOPICO = 'laboratorio/datos'


   def main():
       # 1. Evento utilizado para saber cuándo el broker confirma
       # la conexión; connect() por sí solo no significa CONNACK.
       conectado = threading.Event()

       def on_connect(client, userdata, flags, reason_code, properties):
           if reason_code == 0:
               print('Broker conectado.')
               conectado.set()
           else:
               print(f'Conexión rechazada: {reason_code}')

       # 2. Construir cliente y asociar callback.
       client = mqtt.Client(
           callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
           client_id=f'curso_publicador_{os.getpid()}',
           protocol=mqtt.MQTTv311
       )
       client.on_connect = on_connect

       # 3. Autenticación opcional.
       usuario = os.getenv('MQTT_USER')
       clave = os.getenv('MQTT_PASSWORD')
       if usuario:
           if not clave:
               raise RuntimeError('Falta la variable MQTT_PASSWORD.')
           client.username_pw_set(usuario, clave)

       # 4. Conectar e iniciar el bucle de red en un hilo.
       client.connect(BROKER, PUERTO, keepalive=60)
       client.loop_start()

       try:
           if not conectado.wait(timeout=10):
               raise TimeoutError('No se confirmó la conexión MQTT.')

           # 5. Convertir un diccionario Python a JSON.
           datos = {'valor': 24.5, 'unidad': 'C'}
           payload = json.dumps(datos)

           # 6. Publicar el mensaje. No se retiene en el broker.
           envio = client.publish(
               TOPICO, payload=payload, qos=1, retain=False
           )

           if envio.rc != mqtt.MQTT_ERR_SUCCESS:
               raise RuntimeError(f'Error al publicar: {envio.rc}')

           # 7. Esperar la confirmación MQTT con un límite de tiempo.
           envio.wait_for_publish(timeout=10)
           if not envio.is_published():
               raise TimeoutError('La publicación no se confirmó.')

           print('Publicación MQTT confirmada por el broker.')
       finally:
           # 8. Cierre ordenado del cliente y su hilo MQTT.
           client.disconnect()
           client.loop_stop()


   if __name__ == '__main__':
       main()

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

   import json
   import os
   import time
   import paho.mqtt.client as mqtt

   BROKER = os.getenv('MQTT_BROKER', 'localhost')
   PUERTO = int(os.getenv('MQTT_PORT', '1883'))
   TOPICO_ENTRADA = 'laboratorio/datos'
   TOPICO_SALIDA = 'laboratorio/estados'


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

       usuario = os.getenv('MQTT_USER')
       clave = os.getenv('MQTT_PASSWORD')
       if usuario:
           if not clave:
               raise RuntimeError('Falta la variable MQTT_PASSWORD.')
           client.username_pw_set(usuario, clave)

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

   import os
   import queue
   import threading

   import paho.mqtt.client as mqtt
   import rclpy

   from rclpy.node import Node
   from std_msgs.msg import String


   class PuenteMQTTROS2(Node):

       def __init__(self):
           super().__init__('puente_mqtt_ros2')

           # 1. Configuración independiente de una aplicación concreta.
           self.declare_parameter('broker', 'localhost')
           self.declare_parameter('puerto', 1883)

           broker = self.get_parameter('broker').value
           puerto = self.get_parameter('puerto').value

           self.mqtt_entrada = 'laboratorio/datos'
           self.mqtt_salida = 'laboratorio/salida'

           # 2. Recursos de comunicación entre hilos.
           self.cola = queue.Queue(maxsize=100)
           self.mqtt_conectado = threading.Event()

           # 3. Entidades ROS 2.
           self.publicador = self.create_publisher(
               String, '/mqtt/entrada', 10
           )
           self.suscriptor = self.create_subscription(
               String,
               '/mqtt/salida',
               self.enviar_desde_ros,
               10
           )
           self.temporizador = self.create_timer(
               0.1, self.publicar_en_ros
           )

           # 4. Cliente MQTT con API de callbacks VERSION2.
           self.cliente = mqtt.Client(
               callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
               client_id=f'puente_mqtt_ros2_{os.getpid()}',
               protocol=mqtt.MQTTv311
           )
           self.cliente.on_connect = self.on_connect
           self.cliente.on_disconnect = self.on_disconnect
           self.cliente.on_message = self.on_message

           usuario = os.getenv('MQTT_USER')
           clave = os.getenv('MQTT_PASSWORD')
           if usuario:
               if not clave:
                   raise RuntimeError('Falta MQTT_PASSWORD.')
               self.cliente.username_pw_set(usuario, clave)

           # 5. Iniciar MQTT sin bloquear el executor ROS 2.
           self.cliente.reconnect_delay_set(1, 10)
           self.cliente.connect_async(broker, puerto, keepalive=60)
           self.cliente.loop_start()

       def on_connect(self, client, userdata, flags, reason_code, properties):
           # Se ejecuta en el hilo de red de Paho.
           if reason_code == 0:
               self.mqtt_conectado.set()
               client.subscribe(self.mqtt_entrada, qos=1)
           else:
               self.mqtt_conectado.clear()
               print(f'Conexión MQTT rechazada: {reason_code}')

       def on_disconnect(self, client, userdata, flags, reason_code, properties):
           # Se ejecuta cuando la conexión se cierra o se pierde.
           self.mqtt_conectado.clear()

       def on_message(self, client, userdata, msg):
           # Se ejecuta en el hilo MQTT: validar y encolar rápidamente.
           if msg.topic != self.mqtt_entrada:
               return
           try:
               texto = msg.payload.decode('utf-8')
               if len(texto) > 2048:
                   raise ValueError('Mensaje demasiado grande')
               self.cola.put_nowait(texto)
           except (UnicodeDecodeError, ValueError, queue.Full):
               print('Mensaje MQTT descartado.')

       def publicar_en_ros(self):
           # El temporizador procesa la cola desde el executor ROS 2.
           for _ in range(20):
               try:
                   texto = self.cola.get_nowait()
               except queue.Empty:
                   break

               mensaje = String()
               mensaje.data = texto
               self.publicador.publish(mensaje)

       def enviar_desde_ros(self, mensaje):
           # Callback de suscripción ROS 2: enviar hacia MQTT.
           if not self.mqtt_conectado.is_set():
               self.get_logger().warning('Broker MQTT desconectado.')
               return

           informacion = self.cliente.publish(
               self.mqtt_salida,
               payload=mensaje.data,
               qos=0,
               retain=False
           )
           if informacion.rc != mqtt.MQTT_ERR_SUCCESS:
               self.get_logger().warning('No se pudo encolar la publicación.')

       def detener(self):
           # Cerrar MQTT antes de destruir el nodo ROS 2.
           self.cliente.disconnect()
           self.cliente.loop_stop()


   def main(args=None):
       rclpy.init(args=args)
       nodo = PuenteMQTTROS2()
       try:
           # Un único spin para el nodo ROS 2.
           rclpy.spin(nodo)
       except KeyboardInterrupt:
           pass
       finally:
           nodo.detener()
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

Si el broker requiere autenticación, configura las credenciales del cliente
Python y de las herramientas de consola antes de realizar la prueba.

9. Uso con el paquete ``mi_pkg_python`` del repositorio
-------------------------------------------------------

Los conceptos MQTT anteriores son **generales**. Para conservar la
organización del curso, los programas pueden añadirse opcionalmente a
``mi_pkg_python``. No se crea un paquete adicional.

9.1. Organización sugerida
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ~/ros2_ws/src/mi_pkg_python/
   ├── package.xml
   ├── setup.py
   ├── setup.cfg
   └── mi_pkg_python/
       ├── __init__.py
       ├── ...                       # Programas previos del curso
       └── mqtt/
           ├── __init__.py
           ├── suscriptor_mqtt.py
           ├── publicador_mqtt.py
           ├── cliente_mqtt_mixto.py
           └── puente_mqtt_ros2.py

También puedes ejecutar las tres prácticas MQTT puras como archivos Python
independientes: ``/usr/bin/python3 suscriptor_mqtt.py`` y así sucesivamente.

9.2. Registrar programas en ``setup.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si tu paquete ya usa ``packages=[package_name]``, debes incluir el
subpaquete ``mi_pkg_python.mqtt`` mediante ``find_packages()`` o listarlo
explícitamente. Dentro del archivo existente:

.. code-block:: python

   # Importación de setuptools (fusionar con la que ya tengas).
   from setuptools import find_packages, setup

   # Dentro de setup(...), mantener las demás opciones:
   # packages=find_packages(exclude=['test']),

   # Dentro de entry_points['console_scripts'], conservar los anteriores
   # y añadir estas cadenas:
   # 'mqtt_suscriptor = mi_pkg_python.mqtt.suscriptor_mqtt:main',
   # 'mqtt_publicador = mi_pkg_python.mqtt.publicador_mqtt:main',
   # 'mqtt_mixto = mi_pkg_python.mqtt.cliente_mqtt_mixto:main',
   # 'puente_mqtt_ros2 = mi_pkg_python.mqtt.puente_mqtt_ros2:main',

.. important::

   Las cuatro líneas anteriores son **fragmentos de configuración**. No
   sustituyas el contenido de ``setup.py`` ni elimines los ejecutables de
   nodos, servicios y acciones existentes. Cada nombre corresponde a un
   archivo Python que debe existir en el paquete.

9.3. Dependencias y ejecución con ROS 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

El puente utiliza ``rclpy`` y ``std_msgs``. En ``package.xml`` comprueba
que estén declaradas las dependencias, sin duplicarlas:

.. code-block:: xml

   <exec_depend>rclpy</exec_depend>
   <exec_depend>std_msgs</exec_depend>

Paho MQTT 2.x se instala **para el usuario actual del Python del
sistema**, según la sección 3. Para documentar esa dependencia adicional,
puedes incluir un ``requirements.txt`` que contenga:

.. code-block:: text

   paho-mqtt==2.2.0

El ``requirements.txt`` no implica utilizar un entorno virtual. Para
instalarlo explícitamente con el Python de Ubuntu, utiliza:

.. code-block:: bash

   /usr/bin/python3 -m pip install \
     --user --break-system-packages \
     -r requirements.txt

En Ubuntu 24.04, declarar ``python3-paho-mqtt`` como dependencia APT
podría instalar Paho 1.6.1 en lugar de la versión 2.x requerida; por eso
no se utiliza esa vía para estos ejemplos.

.. code-block:: bash

   # Cargar ROS 2 Jazzy y el espacio de trabajo habitual.
   source /opt/ros/jazzy/setup.bash
   cd ~/ros2_ws

   # Compilar el paquete existente sin crear otro.
   colcon build --symlink-install --packages-select mi_pkg_python
   source install/setup.bash

   # Comprobar la importación desde el mismo Python del sistema.
   /usr/bin/python3 -c "import rclpy; import paho.mqtt.client as mqtt; print('Dependencias disponibles')"

   # Comprobar los ejecutables registrados.
   ros2 pkg executables mi_pkg_python

   # Iniciar la práctica deseada.
   ros2 run mi_pkg_python mqtt_suscriptor

.. note::

   La instalación ``--user`` persiste entre terminales y reinicios; no
   requiere ejecutar ningún comando de activación. Si el workspace ya se
   carga desde ``~/.bashrc``, no hace falta repetir ``source`` al abrir
   una terminal Bash nueva. Si se cambia de usuario o se ejecuta mediante
   ``sudo``, la ubicación de los paquetes Python puede ser diferente.

10. Diagnóstico y problemas frecuentes
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

11. Buenas prácticas para proyectos reales
------------------------------------------

* Mantener las credenciales fuera del código fuente y usar secretos o
  archivos de configuración protegidos.
* Activar autenticación y ACL; usar TLS fuera de una LAN controlada.
* Usar identificadores de cliente únicos cuando las conexiones sean
  independientes.
* Suscribirse en ``on_connect`` si se espera recuperar la suscripción.
* Elegir QoS y ``retain`` según la semántica del mensaje, no solo por
  comodidad.
* Evitar comandos de actuadores como mensajes retenidos.
* Definir versiones y límites para los datos intercambiados.
* Comprobar desconexiones, reconexiones y datos vencidos.
* Mantener los callbacks breves y evitar bloqueos prolongados.
* No confundir entrega MQTT con ejecución segura y confirmada de una orden.
* Separar el procesamiento ROS 2 del hilo de recepción Paho.

12. Actividades de aprendizaje
------------------------------

#. Identificar las partes de un publicador MQTT y de un suscriptor MQTT.
#. Explicar qué sucede si dos programas utilizan el mismo ``client_id``.
#. Modificar los ejemplos para transmitir un JSON de dos campos y
   comprobar su recepción.
#. Suscribirse al filtro ``laboratorio/#`` y observar dos tópicos diferentes.
#. Comparar QoS 0 y QoS 1 durante la publicación de mensajes de prueba.
#. Explicar por qué ``retain=True`` puede ser inconveniente para un comando.
#. Simular la desconexión y reconexión del broker; observar ``on_connect``.
#. Identificar qué parte del puente ejecuta ``rclpy.spin()`` y cuál
   utiliza ``loop_start()``.
#. Añadir una verificación de formato JSON al receptor sin cambiar los
   conceptos generales del protocolo.

13. Referencias técnicas
------------------------

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
