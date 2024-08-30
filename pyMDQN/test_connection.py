import config as dcfg  # Asegúrate de que config está correctamente configurado con el host y port
from environmentuno import UnityEnv  # Suponiendo que tu clase está en environment.py
from pathlib import Path
def test_connection():
    print("Iniciando la prueba de conexión...")
    try:
        # Intenta crear una instancia del entorno, lo que debería iniciar la conexión
        env = UnityEnv(cfg=dcfg, epi=0)
        print("¡Conexión exitosa!")
    except Exception as e:
        print(f"Error al intentar conectarse: {e}")

def test_robot_information():
    print("Iniciando la prueba para obtener información del robot...")
    try:
        env = UnityEnv(cfg=dcfg, epi=0)

        env.send_data_to_pepper("step0")
        env.send_data_to_pepper("episode0")
        env.send_data_to_pepper("speed1")  # Configura la velocidad de simulación
        env.send_data_to_pepper("workdir" + str(Path(__file__).parent.absolute()))  # Configura el directorio de trabajo
        env.send_data_to_pepper("fov90") 
        robot_info = env.get_robot_status()
        print(f"Información del robot: {robot_info}")
    except Exception as e:
        print(f"Error al intentar obtener información del robot: {e}")

if __name__ == "__main__":
    test_connection()
    test_robot_information()