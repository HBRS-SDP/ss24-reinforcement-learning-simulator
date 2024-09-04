from API import env
import validation.configValidation as config


if __name__ == "__main__":
    config = config  
    
    sim_manager = env(config)

    #start the simulation
    sim_manager.start(ep=13)

    #n_steps 
    sim_manager.step(num_steps=5)

    #close the simulation
    sim_manager.close()