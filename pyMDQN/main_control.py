import torch
import logging
import time
from pepper_env import UnityEnv
import validation.configValidation as dcfg
from simulator_utils import start_simulator, kill_simulation  
from agent_validation import run_validation  

# Logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)  
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

def main(cfg, episode):
    """
    Main function to execute the simulator, create the environment 
    and run the agent validation.
    """
    
    torch.manual_seed(torch.initial_seed())

    process = start_simulator()
    
    # Environment creation
    env = UnityEnv(cfg=cfg, epi=episode)
    
    # Send initial command to simulator
    env.send_data_to_pepper("start")
    time.sleep(1)  

    try:
        
        rewards, actions = run_validation(episode, cfg)
        
        # Log validation results
        logger.info(f"Rewards: {rewards}")
        logger.info(f"Actions: {actions}")
    finally:
        
        kill_simulation(process)

if __name__ == "__main__":
    episode = 13  
    main(dcfg, episode)
