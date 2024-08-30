#!/usr/bin/env python
import signal
import torch
import torchvision.transforms as T
import numpy as np
from PIL import Image
from pathlib import Path
import copy
from TrainNQL import TrainNQL
import os.path
from os import path
import torch.nn as nn
from pathlib import Path
from RobotNQL import RobotNQL
from environment import Environment
import pickle
import time
import shutil
import logging
import sys
import subprocess
from subprocess import Popen
from os.path import abspath, dirname, join
from UnityEnv import UnityEnv  # Importamos el entorno Gymnasium

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Process everything, even if everything isn't printed

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # or any other level
logger.addHandler(ch)

def openSim(process, command):
    process.terminate()
    time.sleep(5)
    process = Popen(command)
    time.sleep(5)
    return process

def killSim(process):
    process.terminate()
    time.sleep(10)

def signalHandler(sig, frame):
    process.terminate()
    sys.exit(0)

def datavalidation(episode, cfg):
    hspos = 0
    hsneg = 0
    wave = 0
    wait = 0
    look = 0
    t_steps = cfg.t_steps
    dirname_rgb = 'dataset/RGB/ep' + str(episode)
    dirname_dep = 'dataset/Depth/ep' + str(episode)
    dirname_model = 'validation/' + str(episode)
    agent = RobotNQL(epi=episode, cfg=cfg, validation=True)
    
    print("Agent created successfully")

    # Usamos Gymnasium para crear el entorno
    env = UnityEnv(cfg, episode)
    simulation_speed = cfg.simulation_speed

    Path(dirname_rgb).mkdir(parents=True, exist_ok=True)
    Path(dirname_dep).mkdir(parents=True, exist_ok=True)
    Path(dirname_model).mkdir(parents=True, exist_ok=True)

    env = UnityEnv(cfg, episode)


    file_recent_rewards = 'validation/' + str(episode) + '/recent_rewards.dat'
    file_recent_actions = 'validation/' + str(episode) + '/recent_actions.dat'
    file_reward_history = 'validation/' + str(episode) + '/reward_history.dat'
    file_action_history = 'validation/' + str(episode) + '/action_history.dat'
    file_ep_rewards = 'validation/' + str(episode) + '/ep_rewards.dat'

    if not path.exists(file_recent_rewards):
        torch.save([], file_recent_rewards)
    if not path.exists(file_recent_actions):
        torch.save([], file_recent_actions)
    if not path.exists(file_reward_history):
        torch.save([], file_reward_history)
    if not path.exists(file_action_history):
        torch.save([], file_action_history)
    if not path.exists(file_ep_rewards):
        torch.save([], file_ep_rewards)

    recent_rewards = torch.load(file_recent_rewards)
    recent_actions = torch.load(file_recent_actions)
    reward_history = torch.load(file_reward_history)
    action_history = torch.load(file_action_history)
    ep_rewards = torch.load(file_ep_rewards)

    fh = logging.FileHandler('validation/' + str(episode) + '/results.log')
    fh.setLevel(logging.INFO)  # or any level you want
    logger.addHandler(fh)

    aset = cfg.actions
    testing = -1
    init_step = 0

    aux_total_rewards = 0

    actions = []
    rewards = []

    if init_step != 0:
        actions = recent_actions
        rewards = recent_rewards

    total_reward = aux_total_rewards
    print("Resetting the environment...")

    env.reset()
    env.send_data_to_pepper("step"+str(init_step))
    env.send_data_to_pepper("episode"+str(episode))
    env.send_data_to_pepper("speed"+str(simulation_speed))
    env.send_data_to_pepper("workdir"+str(Path(__file__).parent.absolute()))
    env.send_data_to_pepper("fov"+str(cfg.robot_fov))
	#env.close_connection()

    env = UnityEnv(cfg, episode)
    print("Environment reset successfully") 
    done = False
    step = init_step + 1
    reward = 0 #temp
    terminal = 0
    screen = None
    depth = None
    screen, depth, reward, terminal = env.step('-')


    print(f"Starting the while loop with step={step} and t_steps={t_steps}")
    while step <= t_steps + 1:
        print("Step=", step)
        print("Calling perceive function...")
        action_index = agent.perceive(observation, None, done, False, numSteps=0, steps=step, testing_ep=testing)
        print(f"Action index received: {action_index}")
        step += 1
        if action_index is None:
            action_index = 1

        observation, reward, done, _ = env.step(action_index)

        if step >= t_steps:
            done = True

        if aset[action_index] == '4':
            if reward > 0:
                reward = cfg.hs_success_reward
            else:
                reward = cfg.hs_fail_reward
        else:
            reward = cfg.neutral_reward

        rewards.append(reward)
        actions.append(action_index)
        total_reward += reward

        if aset[action_index] == '4':
            if reward > 0:
                hspos += 1
            elif reward == cfg.hs_fail_reward:
                hsneg += 1
        elif aset[action_index] == '1':
            wait += 1
        elif aset[action_index] == '2':
            look += 1
        elif aset[action_index] == '3':
            wave += 1

        logger.info('###################')
        logger.info("STEP:\t" + str(step))
        logger.info('Wait\t' + str(wait))
        logger.info('Look\t' + str(look))
        logger.info('Wave\t' + str(wave))
        logger.info('HS Suc.\t' + str(hspos))
        logger.info('HS Fail\t' + str(hsneg))
        if (hspos + hsneg):
            logger.info('Accuracy\t' + str(((hspos) / (hspos + hsneg))))

        logger.info('================>')
        logger.info("Total Reward: " + str(total_reward))
        logger.info('================>')
        torch.save(rewards, file_recent_rewards)
        torch.save(actions, file_recent_actions)

    reward_history.append(rewards)
    action_history.append(actions)
    ep_rewards.append(total_reward)
    print('\n')

    torch.save(ep_rewards, file_ep_rewards)
    torch.save(reward_history, file_reward_history)
    torch.save(action_history, file_action_history)

    torch.save([], file_recent_rewards)
    torch.save([], file_recent_actions)

    env.close()

def main(cfg, ep):
    torch.manual_seed(torch.initial_seed())
    global process
    process = Popen('false')  # something long running
    signal.signal(signal.SIGINT, signalHandler)

    ep_validation = "validation"
    n_validation = ep

    name_ep = ep_validation + str(n_validation)
    print(name_ep)
    Path('validation/' + name_ep).mkdir(parents=True, exist_ok=True)

    shutil.copy(cfg.__file__, 'validation/' + name_ep + '/')

    episodeLoad = str(ep)

    shutil.copy('results/ep' + episodeLoad + '/modelDepth.net', 'validation/' + name_ep + '/')
    shutil.copy('results/ep' + episodeLoad + '/tModelDepth.net', 'validation/' + name_ep + '/')
    shutil.copy('results/ep' + episodeLoad + '/modelGray.net', 'validation/' + name_ep + '/')
    shutil.copy('results/ep' + episodeLoad + '/tModelGray.net', 'validation/' + name_ep + '/')

    command = './simDRLSR.x86_64'
    directory = '../'
    command = abspath(join(directory, command))

    process = openSim(process, command)
    env = UnityEnv(cfg, episode=name_ep)

    env.send_data_to_pepper("start")
    time.sleep(1)
    env.close()
    time.sleep(1)

    datavalidation(name_ep, cfg)

    env = UnityEnv(cfg, episode=name_ep)
    env.send_data_to_pepper("stop")
    killSim(process)

if __name__ == "__main__":
    import validation.configValidation as cfg
    episode = torch.load('files/episode.dat')
    main(cfg, 13)

