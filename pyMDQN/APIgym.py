import torch
import os 
from pathlib import Path
from pepper_env import UnityEnv
import validation.configValidation as dcfg
import logging
import time
from os.path import abspath, dirname, join
from subprocess import Popen, PIPE
from RobotNQL import RobotNQL
from os import path
from simulator_utils import start_simulator, kill_simulation


logger = logging.getLogger()
logger.setLevel(logging.INFO)  
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

def run_validation(episode, cfg):
    # Inicializar variables
    hspos = 0
    hsneg = 0
    wave = 0
    wait = 0
    look = 0
    t_steps = cfg.t_steps
    dirname_rgb = f'dataset/RGB/epvalidation{episode}'
    dirname_dep = f'dataset/Depth/epvalidation{episode}'
    dirname_model = f'validation/validation{episode}'
    print("Running validation...")

    agent = RobotNQL(epi=str(episode),cfg=cfg,validation=True)  # Reemplazar con la lógica correspondiente si hay un agente NQL
    print("Agent created...")
    
    env = UnityEnv(cfg=cfg, epi=episode)
    print("Environment created...")
    simulation_speed = cfg.simulation_speed

    # Crear directorios necesarios
    Path(dirname_rgb).mkdir(parents=True, exist_ok=True)
    Path(dirname_dep).mkdir(parents=True, exist_ok=True)
    Path(dirname_model).mkdir(parents=True, exist_ok=True)
    
    env = UnityEnv(cfg=cfg, epi=episode)

    # Inicializar o cargar archivos de historial
    file_recent_rewards = f'validation/validation{episode}/recent_rewards.dat'
    file_recent_actions = f'validation/validation{episode}/recent_actions.dat'
    file_reward_history = f'validation/validation{episode}/reward_history.dat'
    file_action_history = f'validation/validation{episode}/action_history.dat'
    file_ep_rewards = f'validation/validation{episode}/ep_rewards.dat'


       
          
          
    recent_rewards = torch.load(file_recent_rewards) if os.path.exists(file_recent_rewards) else []
    recent_actions = torch.load(file_recent_actions) if os.path.exists(file_recent_actions) else []
    reward_history = torch.load(file_reward_history) if os.path.exists(file_reward_history) else []
    action_history = torch.load(file_action_history) if os.path.exists(file_action_history) else []
    ep_rewards = torch.load(file_ep_rewards) if os.path.exists(file_ep_rewards) else []

    # Configuración del logger para el episodio
    fh = logging.FileHandler(f'validation/validation{episode}/results.log')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    aset = cfg.actions
    testing = -1
    init_step = 0
    aux_total_rewards = 0
    
    actions = []
    rewards = []

    if(init_step!=0):
        actions= recent_actions
        rewards= recent_rewards
    
    total_reward = aux_total_rewards
    print(init_step)

    # Iniciar simulación
    env.send_data_to_pepper(f"step")
    env.send_data_to_pepper(f"episodevalidation{episode}")
    env.send_data_to_pepper(f"speed{simulation_speed}")
    env.send_data_to_pepper(f"workdir{str(Path(__file__).parent.absolute())}")
    env.send_data_to_pepper(f"fov{cfg.robot_fov}")
    env.close()
    env = UnityEnv(cfg=cfg, epi=episode)
    agent = RobotNQL(epi=str(episode),cfg=cfg,validation=True)  # Reemplazar con la lógica correspondiente si hay un agente NQL
 
    reward = 0 #temp
    terminal = 0
    screen = None
    depth = None
    (screen, depth), reward, terminal,_ = env.step('-',init_step+1)
  
    actual_step=init_step+1
    while actual_step <= t_steps + 1:
 
        
        action_index = 0
        numSteps = 0
        
        action_index = agent.perceive(screen, depth, terminal, False, numSteps, actual_step, testing)
        actual_step+=1	

        if action_index == None:
            action_index=1
        if not terminal:
            (screen, depth), reward, terminal,_ = env.step(aset[action_index], actual_step)
            
        else:
            (screen, depth), reward, terminal,_ = env.step('-', actual_step)
            
        
        if actual_step >= t_steps:
            terminal=1
        
        
        # Handshake reward calculation
        if cfg.actions[action_index] == '4':
            if reward > 0:
                reward = cfg.hs_success_reward
            else:
                reward = cfg.hs_fail_reward
        else:
            reward = cfg.neutral_reward

        recent_rewards.append(reward)
        recent_actions.append(action_index)
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

        # Logging results
        logger.info('###################')
        logger.info(f"STEP:\t{actual_step}")
        logger.info(f'Wait\t{wait}')
        logger.info(f'Look\t{look}')
        logger.info(f'Wave\t{wave}')
        logger.info(f'HS Suc.\t{hspos}')
        logger.info(f'HS Fail\t{hsneg}')
        if hspos + hsneg > 0:
            logger.info(f'Acuracy\t{(hspos / (hspos + hsneg))}')
        logger.info('================>')
        logger.info(f"Total Reward: {total_reward}")
        logger.info('================>')

        torch.save(recent_rewards, file_recent_rewards)
        torch.save(recent_actions, file_recent_actions)

        
    # Save final results
    reward_history.append(recent_rewards)
    action_history.append(recent_actions)
    ep_rewards.append(total_reward)
    print('\n')


    torch.save(ep_rewards, file_ep_rewards)
    torch.save(reward_history, file_reward_history)
    torch.save(action_history, file_action_history)

    torch.save([], file_recent_rewards)
    torch.save([], file_recent_actions)

    env.close()
        

def main(cfg, episode):

    torch.manual_seed(torch.initial_seed())  
    process = start_simulator()
    env = UnityEnv(cfg=cfg, epi=episode)
    
    
    
    env.send_data_to_pepper("start")
    time.sleep(1)

    try:
        # Ejecutar validación
        rewards, actions = run_validation(episode, cfg)
        logger.info(f"Recompensas: {rewards}")
        logger.info(f"Acciones: {actions}")
    finally:
        kill_simulation(process)

if __name__ == "__main__":
    episode = 13
    main(dcfg, episode)
