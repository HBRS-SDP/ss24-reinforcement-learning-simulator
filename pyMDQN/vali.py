#!/usr/bin/env python
import gym
import torch
import logging
import time
import shutil
from pathlib import Path
from unity_gym_wrapper import UnityGymEnv  # Asegúrate de que este archivo exista con el wrapper
from RobotNQL import RobotNQL
import validation.configValidation as cfg  # Asegúrate de tener este archivo de configuración

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

def datavalidation(env, agent, t_steps, episode):
    total_reward = 0
    state = env.reset()
    
    for step in range(t_steps):
        print(f"Step={step}")
        action = agent.perceive(state, None, False, False, 0, step, -1)
        if action is None:
            action = 1  # Acción por defecto
        
        next_state, reward, done, _ = env.step(action)
        total_reward += reward
        
        if done or step == t_steps - 1:
            break
        
        state = next_state

    print(f"Episode {episode} finished with reward {total_reward}")
    return total_reward

def main(cfg, episode):
    # Inicializar el entorno de Gymnasium con Unity
    env = UnityGymEnv(cfg)
    agent = RobotNQL(epi=episode, cfg=cfg, validation=True)
    
    total_steps = cfg.t_steps
    reward = datavalidation(env, agent, total_steps, episode)
    
    # Cerrar el entorno
    env.close()

    # Guardar el resultado en un archivo de log
    name_ep = f"validation{episode}"
    log_dir = Path(f'validation/{name_ep}')
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_dir / 'results.log')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.info(f"Episode {episode} finished with reward {reward}")

    # Copiar archivos de configuración y modelos
    shutil.copy(cfg.__file__, log_dir / Path(cfg.__file__).name)
    shutil.copy('results/ep{episode}/modelDepth.net', log_dir / 'modelDepth.net')
    shutil.copy('results/ep{episode}/tModelDepth.net', log_dir / 'tModelDepth.net')
    shutil.copy('results/ep{episode}/modelGray.net', log_dir / 'modelGray.net')
    shutil.copy('results/ep{episode}/tModelGray.net', log_dir / 'tModelGray.net')

if __name__ == "__main__":
    episode = 13
    main(cfg, episode)
