import os
import torch
import logging
from pathlib import Path
from pepper_env import UnityEnv
from RobotNQL import RobotNQL

logger = logging.getLogger()

def initialize_directories(episode):
    """Add directories to save the validation results"""

    dirname_rgb = f'dataset/RGB/epvalidation{episode}'
    dirname_dep = f'dataset/Depth/epvalidation{episode}'
    dirname_model = f'validation/validation{episode}'
    
    Path(dirname_rgb).mkdir(parents=True, exist_ok=True)
    Path(dirname_dep).mkdir(parents=True, exist_ok=True)
    Path(dirname_model).mkdir(parents=True, exist_ok=True)
    #print("Validation directories created.")

def load_history(episode):

    """Load reward and action history if it exists."""
    file_paths = {
        "recent_rewards": f'validation/validation{episode}/recent_rewards.dat',
        "recent_actions": f'validation/validation{episode}/recent_actions.dat',
        "reward_history": f'validation/validation{episode}/reward_history.dat',
        "action_history": f'validation/validation{episode}/action_history.dat',
        "ep_rewards": f'validation/validation{episode}/ep_rewards.dat'
    }
    
    history = {
        key: torch.load(path) if os.path.exists(path) else []
        for key, path in file_paths.items()
    }
    
    return history, file_paths

def initialize_logging(episode):
    """Logger configuration."""
    fh = logging.FileHandler(f'validation/validation{episode}/results.log')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    #print("Logger configured.")

def setup_environment(cfg, episode):
    """Environment and agent initiation"""
    env = UnityEnv(cfg=cfg, epi=episode)
    agent = RobotNQL(epi=str(episode), cfg=cfg, validation=True)
    return env, agent

def send_initial_commands(env, episode, simulation_speed, cfg):
    """ Send the initial commands to the simulator."""
    env.send_data_to_pepper(f"step")
    env.send_data_to_pepper(f"episodevalidation{episode}")
    env.send_data_to_pepper(f"speed{simulation_speed}")
    env.send_data_to_pepper(f"workdir{str(Path(__file__).parent.absolute())}")
    env.send_data_to_pepper(f"fov{cfg.robot_fov}")
    print("Commands send.")

def calculate_handshake_reward(action, reward, cfg):
    """Handshake reward calculation."""
    if action == '4':
        if reward > 0:
            return cfg.hs_success_reward
        else:
            return cfg.hs_fail_reward
    return cfg.neutral_reward

def log_step_results(step, wait, look, wave, hspos, hsneg, total_reward):
    """Logger results"""
    logger.info('###################')
    logger.info(f"STEP:\t{step}")
    logger.info(f'Wait\t{wait}')
    logger.info(f'Look\t{look}')
    logger.info(f'Wave\t{wave}')
    logger.info(f'HS Suc.\t{hspos}')
    logger.info(f'HS Fail\t{hsneg}')
    if hspos + hsneg > 0:
        logger.info(f'Accuracy\t{(hspos / (hspos + hsneg))}')
    logger.info('================>')
    logger.info(f"Total Reward: {total_reward}")
    logger.info('================>')

def save_final_results(history, file_paths):
    """Save final results."""
    torch.save(history['ep_rewards'], file_paths['ep_rewards'])
    torch.save(history['reward_history'], file_paths['reward_history'])
    torch.save(history['action_history'], file_paths['action_history'])
    torch.save([], file_paths['recent_rewards'])
    torch.save([], file_paths['recent_actions'])
    #print("Final results saved.")


def run_validation(episode, cfg):
    """Validation of the agent into the environment."""
    
    
    initialize_directories(episode)
    history, file_paths = load_history(episode)
    initialize_logging(episode)
    
    # Agent and environment initiation
    env, agent = setup_environment(cfg, episode)
    simulation_speed = cfg.simulation_speed
    
    
    send_initial_commands(env, episode, simulation_speed, cfg)
    
    # Restart the environment
    env.close()
    env, agent = setup_environment(cfg, episode)
    
    # Validation variables
    total_reward = 0
    hspos = hsneg = wave = wait = look = 0
    actions = history['recent_actions']
    rewards = history['recent_rewards']
    
    t_steps = cfg.t_steps
    aset = cfg.actions
    init_step = 0
    testing = -1

    # First observation
    (screen, depth), reward, terminal, _ = env.step('-', init_step + 1)
    actual_step = init_step
    
    # Validation loop
    while actual_step <= t_steps + 1:
        action_index = agent.perceive(screen, depth, terminal, False, 0, actual_step, testing)
        actual_step += 1

        if action_index is None:
            action_index = 1
        
        if not terminal:
            (screen, depth), reward, terminal, _ = env.step(aset[action_index], actual_step)
        else:
            (screen, depth), reward, terminal, _ = env.step('-', actual_step)
        
        if actual_step >= t_steps:
            terminal = 1
        
        reward = calculate_handshake_reward(cfg.actions[action_index], reward, cfg)
        rewards.append(reward)
        actions.append(action_index)
        total_reward += reward

        if cfg.actions[action_index] == '4':
            if reward > 0:
                hspos += 1
            elif reward == cfg.hs_fail_reward:
                hsneg += 1
        elif cfg.actions[action_index] == '1':
            wait += 1
        elif cfg.actions[action_index] == '2':
            look += 1
        elif cfg.actions[action_index] == '3':
            wave += 1

        log_step_results(actual_step, wait, look, wave, hspos, hsneg, total_reward)
        torch.save(rewards, file_paths['recent_rewards'])
        torch.save(actions, file_paths['recent_actions'])
    
    # Save results
    history['reward_history'].append(rewards)
    history['action_history'].append(actions)
    history['ep_rewards'].append(total_reward)
    save_final_results(history, file_paths)
    
    env.close()