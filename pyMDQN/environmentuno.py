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
        super(UnityEnv, self).__init__()
        self.episode = epi
        self.raw_frame_height = cfg.raw_frame_height
        self.raw_frame_width = cfg.raw_frame_width
        self.proc_frame_size = cfg.proc_frame_size
        self.state_size = cfg.state_size
        
        
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.state_size, self.proc_frame_size, self.proc_frame_size), dtype=np.float32)
        self.action_space = spaces.Discrete(4)
        
        
        

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = cfg.port        
        host = cfg.host
        self._connect_to_pepper(host, port)


    def _start_simulator(self, cfg):
        command = './simDRLSR.x86_64'
        directory = '../'
        command = abspath(join(directory, command))
        process = Popen(command)
        time.sleep(10)  # Give i    t time to start up
        return process
    
    def _connect_to_pepper(self, host, port):
        flag_connection = False
        while not flag_connection:
            try:
                self.client = self.socket.connect((host, port))
                flag_connection = True
            except socket.error:
                print("Can't connect with robot! Trying again...")
                time.sleep(1)

#funcion de gymnasium obligatoriadef get_robot_status(self):
        # Enviar un comando al robot para obtener su estado (usando "-" para no hacer nada)
    def get_robot_status(self):
        status_command = "3"  # Comando para verificar si el robot responde sin hacer nada
        print("Enviando comando para obtener información del robot...")
        robot_info = self.send_data_to_pepper(status_command)
        return robot_info
    
    def send_data_to_pepper(self, data):
        print(f'Sending data to Pepper: {data}')
        try:
            self.socket.send(data.encode())  # Envía los datos al robot a través del socket
            print('Data sent to Pepper')
            self.socket.settimeout(20)  # Aumenta el tiempo de espera
            while True:
                try:
                    response_data = self.socket.recv(1024).decode()  # Espera recibir datos del robot
                    if response_data:
                        print(f"Received data from Pepper: {response_data}")
                        return float(response_data.replace(',', '.')) # Devuelve la respuesta recibida
                except socket.timeout:
                    print("Timeout reached, no response from Pepper")
                    return 0  # Devuelve un mensaje si no se recibió respuesta dentro del tiempo de espera
                break
        except Exception as e:
            print(f"Error sending data to Pepper: {e}")
            return 0 # Devuelve un mensaje de error si hubo algún problema al enviar los datos o recibir la respuesta
    

    def pre_process(self, step):
        print('Preprocessing images')
        
        proc_image = torch.FloatTensor(self.state_size, self.proc_frame_size, self.proc_frame_size)
        proc_depth = torch.FloatTensor(self.state_size, self.proc_frame_size, self.proc_frame_size)
        
        dirname_rgb = 'dataset/RGB/epvalidation' + str(self.episode)
        dirname_dep = 'dataset/Depth/epvalidation' + str(self.episode)
        
        for i in range(self.state_size):
            grayfile = dirname_rgb + '/image_' + str(step) + '_' + str(i + 1) + '.png'
            depthfile = dirname_dep + '/depth_' + str(step) + '_' + str(i + 1) + '.png'
            print(f"Loading image {grayfile} and depth {depthfile}")
            proc_image[i] = self.get_tensor_from_image(grayfile)
            proc_depth[i] = self.get_tensor_from_image(depthfile)
        
        return proc_image.unsqueeze(0), proc_depth.unsqueeze(0)

    def get_tensor_from_image(self, file):
        print(f"Attempting to load image from file: {file}")
        convert = T.Compose([
            T.ToPILImage(),
            T.Resize((self.proc_frame_size, self.proc_frame_size), interpolation=Image.BILINEAR),
            T.ToTensor()
        ])
        screen = Image.open(file)
        screen = np.ascontiguousarray(screen, dtype=np.float32) / 255
        screen = torch.from_numpy(screen)
        screen = convert(screen)
        print(f"Image loaded and processed: {screen.shape}")
        return screen
    

    def perform_action(self, action, step):
        print(f"Performing action: {action} at step: {step}")
        
        # Enviar la acción al simulador
        r = self.send_data_to_pepper(action)
        print(f"Reward received: {r}")
        
        # Procesar las imágenes recibidas
        s, d = self.pre_process(step)

        term = False  # Por ahora, asumimos que 'term' es falso; esto puede cambiar según tu lógica
        print(f"Returning from perform_action: Screen shape: {s.shape}, Depth shape: {d.shape}, Reward: {r}, Terminal: {term}")
        return s, d, r, term

    
    
    def close(self):
        if self.socket is not None:
            self.socket.close()
    
    @classmethod
    def close_simulation(cls):
        if cls.sim_process is not None:
            cls.sim_process.terminate()
            cls.sim_process = None
