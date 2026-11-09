"""Nodo educativo ROS 2 Jazzy: observa JointState; no envía comandos.

  - Suscriptor: nombre configurable del tópico JointState.
  - Publicador: /avigtech/xarm/resumen (std_msgs/String).
  - Servicio: /avigtech/xarm/obtener_estado (std_srvs/Trigger).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger

from avigtech_xarm_intro.formato import formatear_articulaciones


class MonitorArticular(Node):
    def __init__(self):
        super().__init__('monitor_articular', namespace='avigtech_xarm')

        self.declare_parameter('topic_articular', '/joint_states')
        self.declare_parameter('frecuencia_hz', 1.0)
        self.declare_parameter('unidad_resumen', 'rad')

        self.topic_articular = self.get_parameter('topic_articular').value
        frecuencia_hz = float(self.get_parameter('frecuencia_hz').value)
        if frecuencia_hz <= 0.0:
            raise ValueError('frecuencia_hz debe ser mayor que cero')
        self.unidad_resumen = str(self.get_parameter('unidad_resumen').value).lower()
        if self.unidad_resumen not in ('rad', 'deg'):
            raise ValueError("unidad_resumen debe ser 'rad' o 'deg'")

        self.ultimo_estado = None
        self.crear_suscriptor = self.create_subscription(
            JointState,
            self.topic_articular,
            self.recibir_estado,
            qos_profile_sensor_data,
        )
        self.publicador = self.create_publisher(
            String, '/avigtech/xarm/resumen', 10
        )
        self.servicio = self.create_service(
            Trigger, '/avigtech/xarm/obtener_estado', self.consultar_estado
        )
        self.timer = self.create_timer(1.0 / frecuencia_hz, self.publicar_resumen)
        self.get_logger().info(
            f'Monitor de solo lectura escuchando: {self.topic_articular}'
        )

    def recibir_estado(self, mensaje):
        # Copiamos los valores porque el próximo mensaje sobrescribirá el estado.
        self.ultimo_estado = (
            list(mensaje.name),
            list(mensaje.position),
        )

    def obtener_texto(self):
        if self.ultimo_estado is None:
            return None
        nombres, posiciones = self.ultimo_estado
        return formatear_articulaciones(nombres, posiciones, self.unidad_resumen)

    def publicar_resumen(self):
        texto = self.obtener_texto()
        if texto is None:
            return
        mensaje = String()
        mensaje.data = texto
        self.publicador.publish(mensaje)

    def consultar_estado(self, _solicitud, respuesta):
        texto = self.obtener_texto()
        respuesta.success = texto is not None
        respuesta.message = texto if texto is not None else 'Todavia no se recibe JointState'
        return respuesta


def main(args=None):
    rclpy.init(args=args)
    nodo = None
    try:
        nodo = MonitorArticular()
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        if nodo is not None:
            nodo.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
