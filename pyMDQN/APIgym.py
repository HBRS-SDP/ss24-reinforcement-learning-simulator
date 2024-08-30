import torch
import os
from pathlib import Path
from environmentuno import UnityEnv
import validation.configValidation as dcfg
import logging
import time
from os.path import abspath, dirname, join
from subprocess import Popen, PIPE
from RobotNQL import RobotNQL

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Procesa todo, aunque no se imprima todo
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

def open_simulation(command):
    if UnityEnv.sim_process is None:  # Solo abre si no está ya abierto
        process = Popen(command)
        time.sleep(5)
        UnityEnv.sim_process = process  # Guarda la referencia del proceso en UnityEnv
    else:
        process = UnityEnv.sim_process  # Usa el proceso existente
    return process

def kill_simulation(process):
     if process is not None:
        process.terminate()
        UnityEnv.sim_process = None 

def run_validation(episode, cfg):
    # Inicializar variables
    hspos = 0
    hsneg = 0
    wave = 0
    wait = 0
    look = 0
    t_steps = cfg.t_steps
    dirname_rgb = f'dataset/RGB/ep{episode}'
    dirname_dep = f'dataset/Depth/ep{episode}'
    dirname_model = f'validation/{episode}'
    
    agent = RobotNQL(epi=str(episode),cfg=cfg,validation=True)  # Reemplazar con la lógica correspondiente si hay un agente NQL
    env = UnityEnv(cfg=cfg, epi=episode)
    simulation_speed = cfg.simulation_speed

    # Crear directorios necesarios
    Path(dirname_rgb).mkdir(parents=True, exist_ok=True)
    Path(dirname_dep).mkdir(parents=True, exist_ok=True)
    Path(dirname_model).mkdir(parents=True, exist_ok=True)

    # Inicializar o cargar archivos de historial
    file_recent_rewards = f'validation/{episode}/recent_rewards.dat'
    file_recent_actions = f'validation/{episode}/recent_actions.dat'
    file_reward_history = f'validation/{episode}/reward_history.dat'
    file_action_history = f'validation/{episode}/action_history.dat'
    file_ep_rewards = f'validation/{episode}/ep_rewards.dat'

    recent_rewards = torch.load(file_recent_rewards) if os.path.exists(file_recent_rewards) else []
    recent_actions = torch.load(file_recent_actions) if os.path.exists(file_recent_actions) else []
    reward_history = torch.load(file_reward_history) if os.path.exists(file_reward_history) else []
    action_history = torch.load(file_action_history) if os.path.exists(file_action_history) else []
    ep_rewards = torch.load(file_ep_rewards) if os.path.exists(file_ep_rewards) else []

    # Configuración del logger para el episodio
    fh = logging.FileHandler(f'validation/{episode}/results.log')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    testing = -1
    init_step = 0
    aux_total_rewards = 0
    
    # Iniciar simulación
    env.send_data_to_pepper(f"step")
    env.send_data_to_pepper(f"episode{episode}")
    env.send_data_to_pepper(f"speed{simulation_speed}")
    env.send_data_to_pepper(f"workdir{str(Path(__file__).parent.absolute())}")
    env.send_data_to_pepper(f"fov{cfg.robot_fov}")

    # Bucle principal de validación
    step = 1
    terminal = False
    total_reward = 0
    state = None
    depth = None
    while step <= t_steps + 1:
        logger.info(f"Step={step}")
        numSteps=0
        action_index = 0
        
        action_index = agent.perceive(state, depth, terminal, False, numSteps, step, testing)

        print("qu es esta vaina",action_index)       
        if not terminal:
            state, depth, reward, terminal = env.perform_action(cfg.actions[action_index], step)
        else:
            state, depth, reward, terminal = env.perform_action("-", step)
        
        if state is None or depth is None:
            logger.error("State or depth is None after performing action!")
            break  # Esto te ayuda a detectar el problema más temprano
        
        action_index = agent.perceive(state, depth, terminal, False, numSteps, step, testing=-1)


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
        logger.info(f"STEP:\t{step}")
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

        step += 1

    # Save final results
    reward_history.append(recent_rewards)
    action_history.append(recent_actions)
    ep_rewards.append(total_reward)

    torch.save(ep_rewards, file_ep_rewards)
    torch.save(reward_history, file_reward_history)
    torch.save(action_history, file_action_history)

    torch.save([], file_recent_rewards)
    torch.save([], file_recent_actions)

    env.close()
        

def main(cfg, episode):
    # Preparar el entorno de la simulación
    command = './simDRLSR.x86_64'
    directory = '../'
    command = abspath(join(directory, command))

    process = open_simulation(command)

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
