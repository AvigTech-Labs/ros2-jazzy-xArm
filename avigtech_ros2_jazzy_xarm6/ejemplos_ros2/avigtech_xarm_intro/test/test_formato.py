import pytest
from avigtech_xarm_intro.formato import formatear_articulaciones


def test_formato_seis_juntas():
    result = formatear_articulaciones(['joint1', 'joint2'], [0.0, 1.25])
    assert 'joint1=0.000 rad' in result
    assert 'joint2=1.250 rad' in result


def test_conversion_a_grados():
    result = formatear_articulaciones(['joint1', 'joint2'], [0.0, 3.141592653589793 / 2], 'deg')
    assert 'joint1=0.00 deg' in result
    assert 'joint2=90.00 deg' in result


def test_no_convierte_junta_no_identificada_como_rotativa():
    result = formatear_articulaciones(['finger_joint'], [0.02], 'deg')
    assert 'finger_joint=0.020 (revisar unidad URDF)' in result


def test_unidad_invalida():
    with pytest.raises(ValueError):
        formatear_articulaciones(['joint1'], [1.0], 'metro')


def test_sin_datos():
    assert formatear_articulaciones([], []) == 'sin articulaciones con posicion publicada'
