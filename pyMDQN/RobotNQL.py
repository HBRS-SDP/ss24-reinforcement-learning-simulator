import torch
import torch.optim as optim
import numpy as np
import config as dcfg

class RobotNQL:
    def __init__(self, epi, cfg=dcfg, validation=False):
        # cpu or cuda
        self.device = "cpu"  # torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.state_dim = cfg.proc_frame_size  # State dimensionality 84x84.
        self.actions = cfg.actions
        self.n_actions = len(self.actions)
        self.win = None
        # epsilon annealing
        self.ep_start = cfg.ep_start
        self.ep = self.ep_start  # Exploration probability.
        self.ep_end = cfg.ep_end
        self.ep_endt = cfg.ep_endt
        self.learn_start = cfg.learn_start
        self.episode = epi

        if validation:
            file_modelGray = 'validation/validation' + epi + '/modelGray.net'
            file_modelDepth = 'validation/validation' + epi + '/modelDepth.net'
        else:
            file_modelGray = 'results/ep' + str(self.episode - 1) + '/modelGray.net'
            file_modelDepth = 'results/ep' + str(self.episode - 1) + '/modelDepth.net'

        print(f"Loading modelGray from: {file_modelGray}")
        print(f"Loading modelDepth from: {file_modelDepth}")

        self.modelGray = torch.load(file_modelGray).to(self.device)
        self.modelDepth = torch.load(file_modelDepth).to(self.device)

        print("Models loaded successfully")

    def perceive(self, state, depth, terminal, testing, numSteps, steps, testing_ep):
            curState = state.to(self.device)
            curDepth = depth.to(self.device)
            actionIndex = 0
           
            if not terminal:
                  actionIndex = self.eGreedy(curState, curDepth, numSteps, steps, testing_ep)
                  print("Action: ", self.actions[actionIndex])
                  return actionIndex
            else:
                  return 0
				  
    def eGreedy(self, state, depth, numSteps, steps, testing_ep):
        self.ep = testing_ep or (self.ep_end +
                                 max(0, (self.ep_start - self.ep_end) * (self.ep_endt -
                                 max(0, numSteps - self.learn_start)) / self.ep_endt))
        print('Exploration probability ', self.ep)
        #-- Epsilon greedy

        if torch.rand(1) < self.ep:
            action = np.random.randint(0, self.n_actions)
            print(f"Random action selected: {action}")
            return action
        else:
            action = self.greedy(state, depth)
            print(f"Greedy action selected: {action}")
            return action

    def greedy(self, state, depth):
        print("greedy")
        self.modelGray.eval()
        self.modelDepth.eval()

        q1 = self.modelGray.forward(state).cpu().detach().numpy()[0]
        q2 = self.modelDepth.forward(depth).cpu().detach().numpy()[0]

        print(f"Q values from modelGray: {q1}")
        print(f"Q values from modelDepth: {q2}")

        ts = np.sum(q1)
        td = np.sum(q2)

        q_fus = (q1 / ts) * 0.5 + (q2 / td) * 0.5
        print(f"Fused Q values: {q_fus}")

        maxq = q_fus[0]
        besta = [0]
        for a in range(1, self.n_actions):
            if q_fus[a] > maxq:
                besta = [a]
                maxq = q_fus[a]
            elif q_fus[a] == maxq:
                besta.append(a)
        self.bestq = maxq
        r = np.random.randint(0, len(besta))
        self.lastAction = besta[r]
        print(f"Selected action: {besta[r]} with Q value: {maxq}")
        return besta[r]
