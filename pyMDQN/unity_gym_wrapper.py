import gym
from gym import spaces
import numpy as np
from environment import Environment

class UnityGymEnv(gym.Env):
    def __init__(self, cfg):
        super(UnityGymEnv, self).__init__()
        
        # Crear una instancia del entorno original
        self.env = Environment(cfg)
        self.env.connect_to_robot()

        # Definir el espacio de acción y observación basado en tu configuración
        self.action_space = spaces.Discrete(5)  # Ejemplo: 5 acciones posibles
        self.observation_space = spaces.Box(
            low=0, high=255, 
            shape=(self.env.state_size, self.env.proc_frame_size, self.env.proc_frame_size),
            dtype=np.float32
        )
        
    def reset(self):
        # Lógica para reiniciar el entorno y devolver el estado inicial
        self.env.send_data_to_pepper("reset")  # Ejemplo de cómo podrías resetear en Unity
        observation, _ = self.env.pre_process(1)

        return observation

    def step(self, action):
        # Enviar la acción a Unity y obtener el nuevo estado y recompensa
        observation, depth, reward, done = self.env.perform_action(str(action), 1)
        info = {}  # Información adicional si es necesario
        return observation, reward, done, info

    def render(self, mode='human'):
        # Renderizado opcional
        pass

    def close(self):
        # Cerrar la conexión con Unity
        self.env.close_connection()
