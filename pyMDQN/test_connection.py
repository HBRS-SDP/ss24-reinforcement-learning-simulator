import config as dcfg  # Asegúrate de que config está correctamente configurado con el host y port
from environmentuno import UnityEnv  # Suponiendo que tu clase está en environment.py
from pathlib import Path

def test_connection(env):
    print("Iniciando la prueba de conexión...")
    try:
        # Aquí ya estamos usando la instancia pasada como argumento
        print("¡Conexión exitosa!")
    except Exception as e:
        print(f"Error al intentar conectarse: {e}")

def test_robot_information(env):
    print("Iniciando la prueba para obtener información del robot...")
    try:
        # Usamos la instancia pasada como argumento
        env.send_data_to_pepper("step0")
        env.send_data_to_pepper("episode0")
        env.send_data_to_pepper("speed1")  # Configura la velocidad de simulación
        env.send_data_to_pepper("workdir" + str(Path(__file__).parent.absolute()))  # Configura el directorio de trabajo
        env.send_data_to_pepper("fov90") 
        robot_info = env.get_robot_status()
        print(f"Información del robot: {robot_info}")
    except Exception as e:
        print(f"Error al intentar obtener información del robot: {e}")

def test_robot_images(env):
    print("Iniciando la prueba para obtener una imagen del robot...")
    try:
        screen, depth, reward, terminal = env.perform_action("-", step=1)  # Solicitar imágenes en el paso 1
        print(f"Imagen obtenida. Tamaño de screen: {screen.shape}, depth: {depth.shape}")
    except Exception as e:
        print(f"Error al intentar obtener la imagen del robot: {e}")

if __name__ == "__main__":
    env = None
    try:
        env = UnityEnv(cfg=dcfg, epi=0)
        test_connection(env)
        test_robot_information(env)
        test_robot_images(env)
    finally:
        if env:
            env.close()
            UnityEnv.close_simulation()  # Cierra la simulación solo una vez al final
