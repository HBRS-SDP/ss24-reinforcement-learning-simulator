import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision.transforms as T
import numpy as np
import socket
import time
from PIL import Image
import config as dcfg  # default config

class Environment:
    def __init__(self, cfg=dcfg, epi=0):
        # if gpu is to be used
        #self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        #self.r_len=8
        self.episode = epi
        self.raw_frame_height = cfg.raw_frame_height
        self.raw_frame_width = cfg.raw_frame_width
        self.proc_frame_size = cfg.proc_frame_size
        print(self.proc_frame_size)
        self.state_size = cfg.state_size
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

    def get_tensor_from_image(self, file):
        convert = T.Compose([
            T.ToPILImage(),
            T.Resize((self.proc_frame_size, self.proc_frame_size), interpolation=Image.BILINEAR),
            T.ToTensor()
        ])
        screen = Image.open(file)
        screen = np.ascontiguousarray(screen, dtype=np.float32) / 255
        screen = torch.from_numpy(screen)
        screen = convert(screen)  # .to(self.device)
        return screen

    def pre_process(self, step):
        print('Preprocessing images')
        
        proc_image = torch.FloatTensor(self.state_size, self.proc_frame_size, self.proc_frame_size)
        proc_depth = torch.FloatTensor(self.state_size, self.proc_frame_size, self.proc_frame_size)
        
        dirname_rgb = 'dataset/RGB/ep' + str(self.episode)
        dirname_dep = 'dataset/Depth/ep' + str(self.episode)
        
        for i in range(self.state_size):
            grayfile = dirname_rgb + '/image_' + str(step) + '_' + str(i + 1) + '.png'
            depthfile = dirname_dep + '/depth_' + str(step) + '_' + str(i + 1) + '.png'
            print(f"Loading image {grayfile} and depth {depthfile}")
            proc_image[i] = self.get_tensor_from_image(grayfile)
            proc_depth[i] = self.get_tensor_from_image(depthfile)
        
        return proc_image.unsqueeze(0), proc_depth.unsqueeze(0)

    def send_data_to_pepper(self, data):
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

    def perform_action(self, action, step):
        print(f"Performing action: {action} at step: {step}")
        
        r = self.send_data_to_pepper(action)
        print(f"Reward received: {r}")
        
        print("Starting preprocessing of images")
        s, d = self.pre_process(step)
        print(f"Preprocessing complete. Screen shape: {s.shape}, Depth shape: {d.shape}")

        term = False  # Assuming term is false here; modify as per your logic
        print(f"Returning from perform_action: Screen shape: {s.shape}, Depth shape: {d.shape}, Reward: {r}, Terminal: {term}")
        return s, d, r, term

    def close_connection(self):
        print("Closing socket connection")
        self.socket.close()
