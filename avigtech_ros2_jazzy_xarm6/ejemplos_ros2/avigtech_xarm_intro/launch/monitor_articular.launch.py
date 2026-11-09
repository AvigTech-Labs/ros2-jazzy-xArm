"""Configura el tópico JointState sin cambiar el código del nodo."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('topic_articular', default_value='/joint_states'),
        DeclareLaunchArgument('frecuencia_hz', default_value='1.0'),
        DeclareLaunchArgument('unidad_resumen', default_value='rad'),
        Node(
            package='avigtech_xarm_intro',
            executable='monitor_articular',
            output='screen',
            parameters=[{
                'topic_articular': LaunchConfiguration('topic_articular'),
                'frecuencia_hz': LaunchConfiguration('frecuencia_hz'),
                'unidad_resumen': LaunchConfiguration('unidad_resumen'),
            }],
        ),
    ])
