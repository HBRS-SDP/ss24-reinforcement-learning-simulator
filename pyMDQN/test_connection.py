import config as dcfg
from pepper_env import UnityEnv  
from pathlib import Path

def test_connection(env):
    print("Starting connection test...")
    try:
        print("Connection successful!")
    except Exception as e:
        print(f"Error while trying to connect: {e}")

def test_robot_information(env):
    print("Starting test to retrieve robot information...")
    try:
        
        env.send_data_to_pepper("step0")
        env.send_data_to_pepper("episode0")
        env.send_data_to_pepper("speed1")  
        env.send_data_to_pepper("workdir" + str(Path(__file__).parent.absolute()))  
        env.send_data_to_pepper("fov90") 
        robot_info = env.get_robot_status()
        print(f"Robot information: {robot_info}")
    except Exception as e:
        print(f"Error while trying to retrieve robot information: {e}")

def test_robot_images(env):
    print("Starting test to retrieve an image from the robot...")
    try:
        screen, depth, reward, terminal = env.perform_action("-", step=1)  
        print(f"Image retrieved. Screen size: {screen.shape}, depth: {depth.shape}")  
    except Exception as e:
        print(f"Error while trying to retrieve an image from the robot: {e}")

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
            UnityEnv.close_simulation()  
