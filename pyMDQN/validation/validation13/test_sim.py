import pytest
from API import env
import os 


class MockConfig:  # Corrige la ortografía
    def __init__(self):
        self.t_steps = 10
        self.actions = ["1", "2", "3", "4"]
        self.simulation_speed = 1
        self.robot_fov = 90
        self.__file__ = os.path.abspath(__file__) 

@pytest.fixture
def mock_config():
    return MockConfig()

def test_start_simulator(mock_config, mocker):  # Corrige el nombre de la prueba
    # Mock Popen para evitar que inicie el simulador real
    mocker.patch('subprocess.Popen', return_value=None)

    # Mock PepperController y RobotNQL
    mocker.patch('pepper_controller.PepperController')
    mocker.patch('RobotNQL.RobotNQL')

    simulation = env(mock_config)
    simulation.start(13)
    
    assert simulation.episode == "validation13"
    assert simulation.roag is not None
    assert simulation.agent is not None
