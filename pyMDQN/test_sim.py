import pytest
from API import env
import validation.configValidation as cfg
import os
import torch 


@pytest.fixture(scope='module')  
def real_config():
    """
    Fixture that provides the real configuration for the tests.

    Returns:
        The configuration module (configValidation.py).
    """   

    return cfg


@pytest.fixture(scope='module')
def simulation(real_config):
    """
    Fixture to initialize the simulation environment. The simulation is only started once
    for all the tests and closed at the end.

    Args:
        real_config: The configuration for the environment.

    Yields:
        The initialized simulation environment.
    """
    # Initialize the simulation environment
    simulation = env(real_config)
    simulation.start(13)
    yield simulation
    # Close the simulation environment after all tests
    simulation.close()

def test_config_parameters_exist():
    """
    Test to ensure that all necessary configuration parameters exist in the configValidation.py file.
    """
    expected_params = [
        't_steps', 'actions', 'simulation_speed', 'robot_fov',
        'raw_frame_height', 'raw_frame_width', 'proc_frame_size',
        'state_size', 'port', 'host',
        'ep_start', 'ep_end', 'ep_endt', 'learn_start'
    ]
    
    # Assert that each expected parameter is present in the configuration module
    for param in expected_params:
        assert hasattr(cfg, param), f"The parameter {param} is missing in configValidation.py"


def test_start_simulator(simulation, mocker):
    
    """
    Test the start function of the simulator to ensure it initializes correctly.

    Args:
        simulation: The simulation environment fixture.
        mocker: Used to mock subprocess calls.
    """
    # Mock subprocess.Popen to avoid actual process creation during tests
    mocker.patch('subprocess.Popen', return_value=None)
    # Check that the episode and key components are initialized correctly
    assert simulation.episode == "validation13"
    assert simulation.roag is not None
    assert simulation.agent is not None

def test_step_function(simulation):
    """
    Test the step function of the simulation to ensure it behaves as expected.
    
    Args:
        simulation: The initialized simulation environment fixture.
    """
    # Number of steps to execute in the simulation
    num_steps = 5

    # Call the step function to perform actions in the simulation
    observations, rewards, dones = simulation.step(num_steps)

    # Validate that observations, rewards, and done flags are not None
    assert observations is not None, "Observations should not be None"
    assert rewards is not None, "Rewards should not be None"
    assert dones is not None, "Dones should not be None"

    # Validate the length of the lists matches the number of steps
    assert len(rewards) == num_steps, "The number of rewards should match the number of steps"
    assert len(dones) == num_steps, "The number of dones should match the number of steps"

    # Validate that rewards are numeric (either int or float)
    for reward in rewards:
        assert isinstance(reward, (int, float)), f"Reward should be a number, but received {type(reward)}"
        
    # Validate that done flags are boolean
    for done in dones:
        assert isinstance(done, bool), f"Done flag should be a boolean, but received {type(done)}"

    # Validate each observation (screen, depth)
    for obs in observations:
            assert isinstance(obs, tuple), f"Observation should be a tuple, but received {type(obs)}"
            assert len(obs) == 2, "Each observation must contain exactly two elements (screen, depth)"

            screen, depth = obs

            # Validar que screen y depth sean tensores de torch
            assert isinstance(screen, torch.Tensor), f"Screen should be a torch tensor, but received {type(screen)}"
            assert isinstance(depth, torch.Tensor), f"Depth should be a torch tensor, but received {type(depth)}"

            # Validar dimensiones de los tensores de screen y depth
            assert screen.dim() == 4, f"Screen should be a 4-dimensional tensor, but has {screen.dim()} dimensions"
            assert depth.dim() == 4, f"Depth should be a 4-dimensional tensor, but has {depth.dim()} dimensions"

            # Validate the size of the tensors matches the configuration
            assert screen.size(1) == cfg.state_size,f"Screen tensor size does not match state_size in the configuration"
            assert depth.size(1) == cfg.state_size, f"Depth tensor size does not match state_size in the configuration"
            assert screen.size(2) == cfg.proc_frame_size, f"Screen tensor size does not match proc_frame_size in the configuration"
            assert depth.size(2) == cfg.proc_frame_size, f"Depth tensor size does not match proc_frame_size in the configuration"


