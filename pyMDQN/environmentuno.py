import gymnasium as gym
import numpy as np
import torch
import gymnasium.spaces as spaces
import config as dcfg 
import socket
import time
from os.path import abspath, dirname, join

from subprocess import Popen, PIPE

class UnityEnv(gym.Env):
    def __init__(self, cfg = dcfg, epi=0):
        super(UnityEnv, self).__init__()
        self.episode = epi
        self.raw_frame_height = cfg.raw_frame_height
        self.raw_frame_width = cfg.raw_frame_width
        self.proc_frame_size = cfg.proc_frame_size
        self.state_size = cfg.state_size
        
        
        self.observation_space = spaces.Box(low=0, high=255, shape=(self.state_size, self.proc_frame_size, self.proc_frame_size), dtype=np.float32)
        self.action_space = spaces.Discrete(4)

        self.sim_process = self._start_simulator(cfg)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = cfg.port        
        host = cfg.host
        self._connect_to_pepper(host, port)


    def _start_simulator(self, cfg):
        command = './simDRLSR.x86_64'
        directory = '../'
        command = abspath(join(directory, command))
        process = Popen(command)
        time.sleep(10)  # Give it time to start up
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
                        return response_data  # Devuelve la respuesta recibida
                except socket.timeout:
                    print("Timeout reached, no response from Pepper")
                    return "No response"  # Devuelve un mensaje si no se recibió respuesta dentro del tiempo de espera
                break
        except Exception as e:
            print(f"Error sending data to Pepper: {e}")
            return "Error"  # Devuelve un mensaje de error si hubo algún problema al enviar los datos o recibir la respuesta
