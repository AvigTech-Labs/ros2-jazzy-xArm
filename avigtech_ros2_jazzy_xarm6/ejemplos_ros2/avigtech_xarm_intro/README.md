# avigtech_xarm_intro — ROS 2 Jazzy

Paquete educativo independiente del repositorio oficial UFACTORY. No envía
comandos de movimiento ni se comunica con un robot por IP. Lee `JointState`,
publica `/avigtech/xarm/resumen` y responde al servicio de consulta
`/avigtech/xarm/obtener_estado` (`std_srvs/srv/Trigger`).

1. Copiar este paquete en `~/ros2_ws/src/`, junto a `xarm_ros2`.
2. Compilar: `cd ~/ros2_ws && colcon build --symlink-install --packages-select avigtech_xarm_intro`.
3. En terminales nuevas, cargar automáticamente los entornos con `~/.bashrc` como se explica en el curso; si no se configuró, activarlos manualmente con `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash`.
4. Descubrir tópico: `ros2 topic find sensor_msgs/msg/JointState`.
5. Ejecutar: `ros2 launch avigtech_xarm_intro monitor_articular.launch.py topic_articular:=/joint_states unidad_resumen:=deg`.
6. Consultar: `ros2 service call /avigtech/xarm/obtener_estado std_srvs/srv/Trigger '{}'`.

**Nota:** cambia `/joint_states` si tu escenario usa otro namespace. El nodo no
recibirá nada hasta que un componente publique datos. Un monitor de solo lectura
NO demuestra que el robot esté configurado para mover sus articulaciones.

Prueba unitaria pura (sin ROS instalado, desde la carpeta del paquete):
`python3 -m pytest test/test_formato.py`.

El parámetro `unidad_resumen` acepta `rad` (por defecto) o `deg`. Solo convierte
las seis juntas rotativas `joint1` a `joint6`; para otros nombres consulta
el URDF y adapta la lista de juntas rotativas antes de convertir.
