from API import API_Functions


import validation.configValidation as config# Importar la configuración del archivo config.py


if __name__ == "__main__":
    config = config  # Usar la configuración del archivo config.py
    
    sim_manager = API_Functions(config)

    # Iniciar la simulación
    sim_manager.start(ep=13)

    # Ejecutar pasos en la simulación
    sim_manager.step(num_steps=5)

    # Terminar la simulación
    sim_manager.close()