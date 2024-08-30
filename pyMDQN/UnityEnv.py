import gymnasium as gym
import gymnasium.spaces as spaces
import numpy as np
#from environment import Environment  # Asegúrate de que este es tu environment.py
import torch
import socket
import config as dcfg 
import time


class UnityEnv(gym.Env):
    def __init__(self, cfg, episode):
        super(UnityEnv, self).__init__()
        
        self.cfg = cfg
        self.episode = episode
        self.env = Environment(cfg, epi=episode)  # Inicializas el entorno
        self.step_count = 0 
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        port = cfg.port        
        host = cfg.host
        flag_connection = False

        while not flag_connection:
            try:
                self.client = self.socket.connect((host, port))
                flag_connection = True
            except socket.error:
                print("Can't connect with robot! Trying again...")
                with open('flag_simulator.txt', 'w') as f:
                    f.write(str(1))	
                time.sleep(1)
        
        with open('flag_simulator.txt', 'w') as f:
            f.write(str(0))

        # Define las dimensiones de observación y acción
        obs_shape = (3, 224, 224)  # Esto es solo un ejemplo, ajusta según tu entorno
        self.observation_space = spaces.Box(low=0, high=255, shape=obs_shape, dtype=np.uint8)

        action_space_size = len(cfg.actions)  # Asumiendo que cfg.actions es una lista de acciones posibles
        self.action_space = spaces.Discrete(action_space_size)

    def send_data_to_pepper(self, data):
        # Asume que el método `send_data_to_pepper` simplemente delega a `self.env.send_data_to_pepper`
        print('Send data connected to Pepper')
        try:
            self.socket.send(data.encode())
            print('Sending data to Pepper')
            self.socket.settimeout(10)  # Añade un tiempo de espera de 10 segundos
            while True:
                try:
                    response_data = self.socket.recv(1024).decode()
                    if response_data:
                        print(f"Received data from Pepper: {response_data}")
                        return float(response_data.replace(',', '.'))
                except socket.timeout:
                    print("Timeout reached, no response from Pepper")
                    return 0
                break
        except Exception as e:
            print(f"Error sending data to Pepper: {e}")
            return 0
        print("Connected with the server")
        return 0
       # return self.env.send_data_to_pepper(data)
    
    def reset(self):

        self.step_count = 0 
        print("Inside reset: Closing connection if exists")
        self.env.close_connection()
        
        print("Inside reset: Reinitializing the environment")
        self.env = Environment(self.cfg, epi=self.episode)  # Reinicializar el entorno
        
        print("Inside reset: Performing initial action to get the observation")
        screen, depth, reward, terminal = self.env.perform_action('-', 1)
        
        # Crear una observación inicial
        print("Inside reset: Processing observation")
        #observation = self._process_observation(screen, depth)
        
       

    def step(self, action_index):
        
        #implemente preproses and perform actions here 

        self.step_count += 1 
        print(f"Action taken: {action_index}")
        action = self.cfg.actions[action_index]
        screen, depth, reward, terminal = self.env.perform_action(action, self.step_count)
        print(f"Observation: {screen.shape}, Reward: {reward}, Terminal: {terminal}")
        
        #observation = self._process_observation(screen, depth)
        done = terminal or (self.step_count >= self.cfg.t_steps)
        info = {}

        return  reward, done, info
    
    def render(self, mode='human'):
        pass  

    def close(self):
        self.env.close_connection()
