# ss24-reinforcement-learning-simulator update
## SimDRLSR: Deep Reinforcement Learning Simulator for Social Robotics

[![Stars][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]
[![Scholar][scholar-shield]][scholar-url]

<!--Table of contents-->

## About the project
This project is an update of the [SimDRLSR](https://github.com/JPedroRBelo/simDRLSR) (Deep Reinforcement Learning and Social Robotics Simulator) simulator and includes the design of an API to improve its existing functions.

The simulation environment enables efficient, safe, and controlled testing and validation of reinforcement learning models. The simulator allows the robot (Pepper) to interact with an avatar (human), performing four main tasks: greeting, following with your gaze, greeting and waiting.
## Prerequites

## Simulator Configuration

## How to setup the conda environment

## How to run the simulator
Follow the next steps  to run the simulator:
1. Change to the simDRLSR directory:
```sh
cd simDRLSR
```
2. Execute the simulation file:

```sh
./simDRLSR.x86_64
 ```

### Validate the simulator
Follow the next steps  to run the validation script :
1. Open a new terminal
2. Change to the simDRLSR/pyMDQN directory:
```sh
  cd simDRLSR/pyMDQN
  ```
3. Execute the validation script using python:
```sh
  python3 validate.py
  ```



### Train pyMDQN model with the simulator

## License

Distributed under the MGNU GPL 3.0. See `LICENSE` for more information.
 
 
## References
This simulator is based on the following works:

- [simDRLSR](https://github.com/JPedroRBelo/simDRLSR)
- [pyMDQN](https://github.com/JPedroRBelo/pyMDQN/)

[1] Ahmed Hussain Qureshi, Yutaka Nakamura, Yuichiro Yoshikawa and Hiroshi Ishiguro "Robot gains social intelligence through Multimodal Deep Reinforcement Learning" Proceedings of IEEE-RAS International Conference on Humanoid Robots (Humanoids) pp. 745-751, Cancun, Mexico 2016.

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[stars-shield]: https://img.shields.io/github/stars/HBRS-SDP/ss24-reinforcement-learning-simulator.svg?style=for-the-badge
[stars-url]: https://github.com/JPedroRBelo/simDRLSR/stargazers
[issues-shield]: https://img.shields.io/github/issues/HBRS-SDP/ss24-reinforcement-learning-simulator.svg?style=for-the-badge
[issues-url]: https://github.com/HBRS-SDP/ss24-reinforcement-learning-simulator/issues
[license-shield]: https://img.shields.io/badge/license-GNU%20GPU%203.0-brightgreen?style=for-the-badge
[license-url]: https://github.com/HBRS-SDP/ss24-reinforcement-learning-simulator/blob/60b6762eeeed9ca5d0001aaf9a77c8b1cf242252/LICENSE
[scholar-shield]: https://img.shields.io/badge/-Google%20Scholar-black.svg?style=for-the-badge&logo=google-scholar&colorB=555
[scholar-url]: https://scholar.google.com.br/citations?user=0nh0sDMAAAAJ&hl
