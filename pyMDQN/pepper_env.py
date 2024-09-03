import gymnasium as gym
import numpy as np
import torch
import gymnasium.spaces as spaces
import config as dcfg 
import socket
import time
from os.path import abspath, dirname, join
#images
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image

from subprocess import Popen, PIPE

class UnityEnv(gym.Env):
    sim_process = None 

    def __init__(self, cfg = dcfg, epi=0):
        """
        Initialize the environment with the given configuration and episode number.
        Sets up the observation and action spaces and connects to the simulator.

        :param cfg: Configuration object containing environment settings.
        :param epi: Episode number for tracking.
        """
        super(UnityEnv, self).__init__()
        self.episode = epi
        self.raw_frame_height = cfg.raw_frame_height
        self.raw_frame_width = cfg.raw_frame_width
        self.proc_frame_size = cfg.proc_frame_size
        self.state_size = cfg.state_size
        
        # Define observation space and action space
        self.observation_space = spaces.Box(
            low=0, high=255, 
            shape=(self.state_size, self.proc_frame_size, self.proc_frame_size), 
            dtype=np.float32
            )
        self.action_space = spaces.Discrete(4)
        
        # Connect to Pepper robot
        port = cfg.port        
        host = cfg.host
        self.connect_to_pepper(host, port)
        
    def connect_to_pepper(self, host, port):
        """
        Establish a TCP connection to the Pepper robot or simulator.

        :param host: The IP address or hostname of the robot/simulator.
        :param port: The port number to connect to.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        flag_connection = False
        while not flag_connection:
            try:
                self.client = self.socket.connect((host, port))
                flag_connection = True
            except socket.error:
                print("Can't connect with robot! Trying again...")
                time.sleep(1)

    def send_data_to_pepper(self, data):
        """
        Send data to the Pepper and wait for a response.

        :param data: Data to be sent as an action.
        :return: The response received from peper, converted to a float.
        """
        print(f'Sending data to Pepper: {data}')
        try:
            self.socket.send(data.encode())  
            print('Data sent to Pepper')
            self.socket.settimeout(20)  
            while True:
                try:
                    response_data = self.socket.recv(1024).decode()  
                    if response_data:
                        return float(response_data.replace(',', '.')) 
                except socket.timeout:
                    print("Timeout reached, no response from Pepper")
                    return 0  
                break
        except Exception as e:
            print(f"Error sending data to Pepper: {e}")
            return 0 
    

    def pre_process(self, step):
        """
        Preprocess images for the current step of the episode.

        :param step: The current step in the episode.
        :return: Processed RGB and depth images as tensors.
        """
        try :

            print('Preprocessing images')
            
            proc_image = torch.FloatTensor(self.state_size, self.proc_frame_size, self.proc_frame_size)
            proc_depth = torch.FloatTensor(self.state_size, self.proc_frame_size, self.proc_frame_size)
            
            dirname_rgb = 'dataset/RGB/epvalidation' + str(self.episode)
            dirname_dep = 'dataset/Depth/epvalidation' + str(self.episode)
            
            for i in range(self.state_size):
                grayfile = dirname_rgb + '/image_' + str(step) + '_' + str(i + 1) + '.png'
                depthfile = dirname_dep + '/depth_' + str(step) + '_' + str(i + 1) + '.png'
                proc_image[i] = self.get_tensor_from_image(grayfile)
                proc_depth[i] = self.get_tensor_from_image(depthfile)
            
            return proc_image.unsqueeze(0), proc_depth.unsqueeze(0)
        except Exception as e:
            print(f"Error processing images: {e}")

    def get_tensor_from_image(self, file):
        """
        Convert an image file to a tensor for use in the environment.

        :param file: Path to the image file.
        :return: Processed image as a tensor.
        """
        
        convert = T.Compose([
            T.ToPILImage(),
            T.Resize((self.proc_frame_size, self.proc_frame_size), interpolation=Image.BILINEAR),
            T.ToTensor()
        ])
        screen = Image.open(file)
        screen = np.ascontiguousarray(screen, dtype=np.float32) / 255
        screen = torch.from_numpy(screen)
        screen = convert(screen)
        
        return screen
    
    def reset(self,cfg):
        """
        Reset the environment for a new episode. Closes any existing connections and
        reinitializes the state.

        :param cfg: Configuration object for environment settings.
        """
        self.close()
        time.sleep(5)
        

    def step(self, action, init_step):
        """
        Execute one step in the environment based on the given action.

        :param action: The action to be performed.
        :param init_step: The initial step number in the episode.
        :return: A tuple containing the processed images (screen, depth), the reward, 
                 a done flag, and an empty info dictionary.
        """
       
        reward = self.send_data_to_pepper(action)
        screen, depth = self.pre_process(init_step)
        done = False  

        return (screen, depth), reward, done, {}
    
    def render(self, mode='human'):
        pass

    def close(self):
        """
        Close the connection to the Pepper .
        """
        if self.socket is not None:
            self.socket.close()