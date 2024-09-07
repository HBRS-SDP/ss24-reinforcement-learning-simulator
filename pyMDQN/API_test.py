from API import env
import validation.configValidation as config


if __name__ == "__main__":
    config = config  
    
    sim_manager = env(config)

    sim_manager.start(ep=13)

    observations, rewards, dones= sim_manager.step(num_steps=5)
    
    print("Rewards after steps:", rewards)
    print("Dones after steps:", dones)

    # Reset the simulation
    observation = sim_manager.reset(ep=13)  

    # Step the simulation after reset
    observations_after_reset, rewards_after_reset, dones_after_reset = sim_manager.step(num_steps=5)
    
    print("Rewards after reset steps:", rewards_after_reset)
    print("Dones after reset steps:", dones_after_reset)

    # Close the simulation
    sim_manager.close() 