import pytest
from API import env
import validation.configValidation as cfg
import os

@pytest.fixture(scope='module')  # Alcance de módulo
def real_config():
    return cfg

@pytest.fixture(scope='module')
def simulation(real_config):
    # Inicia el simulador solo una vez para todas las pruebas
    simulation = env(real_config)
    simulation.start(13)
    yield simulation
    # Cierra el simulador al final de todas las pruebas
    simulation.close()

def test_config_parameters_exist():
    expected_params = [
        't_steps', 'actions', 'simulation_speed', 'robot_fov',
        'raw_frame_height', 'raw_frame_width', 'proc_frame_size',
        'state_size', 'port', 'host',
        'ep_start', 'ep_end', 'ep_endt', 'learn_start'
    ]
    
    for param in expected_params:
        assert hasattr(cfg, param), f"The parameter {param} is missing in configValidation.py"


def test_start_simulator(simulation, mocker):
    
    mocker.patch('subprocess.Popen', return_value=None)
    
    assert simulation.episode == "validation13"
    assert simulation.roag is not None
    assert simulation.agent is not None