import signal
import torch
import torchvision.transforms as T
import os.path
from pathlib import Path
from RobotNQL import RobotNQL
from robot_agent import RobotAgent
import time
import shutil
import logging
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
class env: #env name
    def __init__(self, config):
        self.config = config
        self.process = None
        self.roag = None
        self.agent = None
        self.episode = None

    def openSim(self, process,command):
        process.terminate()
        time.sleep(5)
        process = Popen(command)
        time.sleep(5)
        return process    

    def killsim(self, process):
        process.terminate()
        time.sleep(10)    
    
    ### START
    
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

       
        self.roag = RobotAgent(self.config, epi=episode)
        self.agent = RobotNQL(epi=str(episode), cfg=self.config, validation=True)  

        # initialize the agent
        self.roag.send_data_to_pepper("start")
        time.sleep(1)
        self.roag.close_connection() 
        time.sleep(1)
        #print("acabe de iniciar")

        #Set or create directories for the images
        dirname_rgb = f'dataset/RGB/ep{episode}'
        dirname_dep = f'dataset/Depth/ep{episode}'
        dirname_model = f'validation/{episode}'
        
        os.makedirs(dirname_rgb, exist_ok=True)
        os.makedirs(dirname_dep, exist_ok=True)
        os.makedirs(dirname_model, exist_ok=True)

    # Validate if the directories for the model are created if not create them and copy the files
    def prepare_validation_directory(self, ep):
        episode_str = str(ep)
        validation_dir = f'validation/validation{episode_str}/'
        os.makedirs(validation_dir, exist_ok=True)
        #print("episode_str", episode_str)
        #print("validation_dir", validation_dir)
        shutil.copy(self.config.__file__, validation_dir)
        shutil.copy(f'results/ep{episode_str}/modelDepth.net', validation_dir)
        shutil.copy(f'results/ep{episode_str}/tModelDepth.net', validation_dir)
        shutil.copy(f'results/ep{episode_str}/modelGray.net', validation_dir)
        shutil.copy(f'results/ep{episode_str}/tModelGray.net', validation_dir)

    ### STEP
    # Perform n steps in the simulation (can be set in validation/configValidation.py) or in the parameter num_steps
    def step(self, num_steps):
        self.agent= RobotNQL(epi=self.episode, cfg=self.config, validation=True)
        self.roag= RobotAgent(self.config, epi=self.episode)

        if self.roag and self.agent:
            t_steps = max(self.config.t_steps, num_steps) #takes the min btw the # of steps in the config file and the parameter num_steps
            aset = self.config.actions  # ['1','2','3','4'] wait, wave, handshake, do nothing

            step = 0
            terminal = 1

            try:
                # Send initial data to Pepper
                self.roag.send_data_to_pepper("step" + str(step))
                self.roag.send_data_to_pepper("episode" + str(self.episode))
                self.roag.send_data_to_pepper("speed" + str(self.config.simulation_speed))
                self.roag.send_data_to_pepper("workdir" + str(Path(__file__).parent.absolute()))
                self.roag.send_data_to_pepper("fov" + str(self.config.robot_fov))
                self.roag.close_connection()
                self.roag = RobotAgent(self.config,epi=self.episode)
            except OSError as e: #make sure the connection is still open
                print("Into OSError")
                if e.errno == 9: #if the connection is closed, restart the environment
                    self.roag = RobotAgent(self.config, epi=self.episode)
                    self.roag.send_data_to_pepper("step" + str(step))

            # Make the first action 
            screen, depth, reward, terminal = self.roag.perform_action('-', step+1) #+1 because the first step is 1
            step= step+1            
            while step <= t_steps+1:
                print(f"Step={step}")
                action_index=0
                testing = -1

                #agent percives the environment
                action_index = self.agent.perceive(screen, depth, terminal, False, 0, step, testing)

                # update the step
                step += 1

                # Perform the action corresponding to the action_index (perceived)
                if action_index is None:
                    action_index = 1
                if not terminal:
                    screen, depth, reward, terminal = self.roag.perform_action(aset[action_index], step)
                else:
                    screen, depth, reward, terminal = self.roag.perform_action('-', step)

                logger.info(f"Step {step}: Action {aset[action_index]}, Reward {reward}, Terminal {terminal}")

                if step > t_steps or terminal:
                    time.sleep(2)
                    self.close()
                    self.killsim(process)
                    break

                time.sleep(self.config.simulation_speed)
                
    ### RESET
    def reset(self, episode):
        self.close()
        time.sleep(5)
        self.start(episode)

    ### CLOSE
    def close(self):
        if self.process is not None:
            self.roag.send_data_to_pepper("stop")
            self.process.terminate()
            self.process.wait()
            self.process = None
            logger.info("Simulation terminated.")

    def cleanup(self):
        self.close()


signal.signal(signal.SIGINT, lambda sig, frame: env.cleanup())
