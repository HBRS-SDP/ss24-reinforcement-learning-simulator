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
from subprocess import Popen
from os.path import abspath, dirname, join
import validation.configValidation as cfg

# logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

# CLass API to interact with the simulation
class API_Functions:
    def __init__(self, config):
        self.config = config
        self.process = None
        self.env = None
        self.agent = None
        self.episode = None

    def openSim(self, process,command):
        process.terminate()
        time.sleep(5)
        process = Popen(command)
        time.sleep(5)
        return process
    
    def signalHandler(self, sig, frame): #no creo q sirve pa nada
        process.terminate()
        sys.exit(0)
    
    
    def start(self, ep=13):
        torch.manual_seed(torch.initial_seed())  
        global process
        process = Popen('false') 
        
    
        episode = "validation" +str(ep) #name_ep = eiposde,,,,"validation13"
        self.episode = episode
        
        
        # call the function to prepare the validation directory
        self.prepare_validation_directory(ep)
        
        # Start the simulation
        command = './simDRLSR.x86_64'
        directory = '../'
        command = abspath(join(directory,command))
        process = self.openSim(process, command)

        # Start the environment and the agent
        self.env = Environment(self.config, epi=episode)
        self.agent = RobotNQL(epi=str(episode), cfg=self.config, validation=True)  

        # initialize the agent
        self.env.send_data_to_pepper("start")
        time.sleep(1)
        self.env.close_connection() 
        time.sleep(1)
        print("acabe de iniciar") # debuggging
        
        dirname_rgb = f'dataset/RGB/ep{episode}'
        dirname_dep = f'dataset/Depth/ep{episode}'
        dirname_model = f'validation/{episode}'
        
        # Create directories for the episode where the images will be stored and read
        os.makedirs(dirname_rgb, exist_ok=True)
        os.makedirs(dirname_dep, exist_ok=True)
        os.makedirs(dirname_model, exist_ok=True)

    # Prepare the validation
    def prepare_validation_directory(self, ep):
        episode_str = str(ep)
        validation_dir = f'validation/validation{episode_str}/'
        os.makedirs(validation_dir, exist_ok=True)
        print("episode_str", episode_str)
        print("validation_dir", validation_dir)
        shutil.copy(self.config.__file__, validation_dir)
        shutil.copy(f'results/ep{episode_str}/modelDepth.net', validation_dir)
        shutil.copy(f'results/ep{episode_str}/tModelDepth.net', validation_dir)
        shutil.copy(f'results/ep{episode_str}/modelGray.net', validation_dir)
        shutil.copy(f'results/ep{episode_str}/tModelGray.net', validation_dir)

    def reset(self, episode):
        self.close()
        time.sleep(5)
        self.start(episode)

    def close(self):
        if self.process is not None:
            self.env.send_data_to_pepper("stop")
            self.process.terminate()
            self.process.wait()
            self.process = None
            logger.info("Simulation terminated.")

    def step(self, num_steps=5): #by default 5 steps
        self.agent= RobotNQL(epi=self.episode, cfg=self.config, validation=True)
        self.env= Environment(self.config, epi=self.episode)

        if self.env and self.agent:
            "entro al IFFFFFFFFFFFFFFFFFF"
            t_steps = min(self.config.t_steps, num_steps)
            aset = self.config.actions  # here we co

            # Inicialización del entorno y configuración inicial
            step = 0
            terminal = 0

            try:
                # nviarr comandos iniciales a Pepper
                self.env.send_data_to_pepper("step" + str(step))
                self.env.send_data_to_pepper("episode" + str(self.episode))
                self.env.send_data_to_pepper("speed" + str(self.config.simulation_speed))
                self.env.send_data_to_pepper("workdir" + str(Path(__file__).parent.absolute()))
                self.env.send_data_to_pepper("fov" + str(self.config.robot_fov))
                self.env.close_connection()
                self.env = Environment(self.config,epi=self.episode)
            except OSError as e:
                print("Into OSError")
                if e.errno == 9:
                    self.env = Environment(self.config, epi=self.episode)
                    self.env.send_data_to_pepper("step" + str(step))

            # Realizar la primera acción para inicializar el entorno
            screen, depth, reward, terminal = self.env.perform_action('-', step+1) #poner +1
            while step <= t_steps+1:
                print(f"Step={step}")
                action_index=0
                testing = -1
                action_index = self.agent.perceive(screen, depth, terminal, False, 0, step, testing)

                if action_index is None:
                    action_index = 1

                try:
                    # Realizar la acción seleccionada
                    if not terminal:
                        screen, depth, reward, terminal = self.env.perform_action(aset[action_index], step)
                    else:
                        screen, depth, reward, terminal = self.env.perform_action('-', step)
                except OSError as e:
                    if e.errno == 9:
                        print("Socket closed unexpectedly during step. Restarting environment...")
                        self.env = Environment(self.config, epi=self.episode)
                        screen, depth, reward, terminal = self.env.perform_action(aset[action_index], step)

                # Actualización de paso
                step += 1

                logger.info(f"Step {step}: Action {aset[action_index]}, Reward {reward}, Terminal {terminal}")

                if step > t_steps or terminal:
                    break

                time.sleep(self.config.simulation_speed)



    def ensure_socket_is_open(self):
        try:
            self.env.socket.send(b"ping")  # verifica si el socket está abierto
        except (OSError, AttributeError):
            print("Socket is not open, reinitializing...")
            self.env.close_connection()
            self.env = Environment(self.config, epi=self.episode)

    def signal_handler(self, sig, frame):
        self.close()
        sys.exit(0)

    def cleanup(self):
        self.close()


signal.signal(signal.SIGINT, lambda sig, frame: API_Functions.cleanup())
