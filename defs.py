import numpy as np
from functools import *
from itertools import *
from operator import *
from random import *

def rand(percent):
    '''Returns A percent% of the time'''
    r = random()
    if(r>percent):
        return False
    return True
	
class Agent:
    def __init__(self,idnum,numtime,successrate,debug=False):
        # This is the history of the agent being idle
        self.Debug = debug
        self.idnum=idnum
        self.history = np.zeros((numtime))
        # This function calculates if the agent was sucessful of the task
        self.calcSuccess = partial(rand,successrate)
        # initialize the times
        self.countdown = 0
        self.time = 0
        self.successCount = 0
        self.failCount = 0
    
    def timeStep(self):
        self.countdown-=1
        self.time+=1
        #if self.Debug: print(f'{self.time}:{self.countdown}')
    
    def updateHistory(self):
        # if done with task record idle time
        if self.countdown <0:
            self.history[self.time-1] = 1
            
            
class Robot(Agent):
    def __init__(self,idnum,numtime,successrate,mu,sigma,mintime,debug=False):
        Agent.__init__(self,idnum,numtime,successrate,debug)
        self.calcTime=lambda: int(max(mintime,np.random.normal(mu,sigma)))
        self.countdown = self.calcTime()
        self.auto = True
        
    
    def setAuto(self,auto):
        # if set to auto mode, then start a task
        # if set to false, the robot is controlled and idle count stops
        self.auto = auto
        if self.auto:
            self.countdown = self.calcTime()
        
    def timeStep(self):
        # if done, see if you were successful start a task
        # otherwise wait for help. 
        Agent.timeStep(self)
        if self.countdown ==0:
            if self.calcSuccess():
                self.countdown = self.calcTime()
                self.successCount+=1
            else:
                self.failCount+=1
        if self.Debug: print(f'Robot State\tCount:{self.countdown}\tAuto:{self.auto}')
    
    def updateHistory(self):
        # if done with task record idle time
        if self.countdown <0 and (True == self.auto):
            self.history[self.time-1] = 1
            
            
class Human(Agent):
    def __init__(self,idnum,numtime,successrate,successTime,robot=None,debug=False):
        Agent.__init__(self,idnum,numtime,successrate,debug)
        # time is fixed
        self.calcTime=lambda: int(successTime)
        self.robot = robot
        # history of which robot the human is controlling
        self.robot_history = np.zeros((numtime))

    def setRobot(self,robot):
        # if robot passed, take control of robot by taking it out of auto mode
        # otherwise it should be None and the system stops. 
        self.robot = robot
        if self.robot !=None: self.robot.setAuto(False)
        
    def timeStep(self):
        Agent.timeStep(self)
        # if idle and robot is set, start the task and sync robot to human
        if self.countdown <0 and self.robot !=None:
            self.countdown = self.calcTime()
            self.robot.countdown = self.countdown
            if self.Debug: print(f'Human Attempt: {self.countdown}')
        #if done with a tasks and the robot is attached, calculate if successful
        elif self.countdown ==0 and self.robot !=None:
            result = self.calcSuccess()
            if result: 
                #update the success count, return robot to auto mode and detach the robot
                self.successCount+=1
                self.robot.setAuto(True)
                self.setRobot(None)
            else: 
                # try again
                # Should this be a detach and return to Auto as well? 
                self.failCount+=1
            if self.Debug: print(f'Human {result}')
        
        # update robot history
        rid = 0
        if self.robot !=None: rid=self.robot.idnum
        self.robot_history[self.time-1]=rid
		
def processTimeStep(Robots,Humans,Debug=False):
    # update the robots and find the paused robots
    pausedBots=[]
    for robot in Robots:
        robot.timeStep()
        if robot.countdown<0: pausedBots.append(robot)
    
    if Debug:
        nbots = len(pausedBots)
        print(f'Number Paused: {nbots}')
    
    # for each human, assign the robots to the human worker pool
    # then update the timestep of the humans
    for human in Humans:
        if len(pausedBots)>0 :
            if None == human.robot:
                bot = pausedBots.pop(0)
                human.setRobot(bot)
        human.timeStep()
        
    # update the history of the robots
    agents = Robots+Humans
    for agent in agents:
        agent.updateHistory()


def calcPercentage(group):
    # each time step =1 means system waiting. Sum the system and normalize by number of robots * time
    n_sec = group[0].history.size
    hist  = np.zeros((n_sec))
    for item in group:
        hist = hist + item.history
    p = np.sum(hist)/(len(group)*hist.size)
    return p

def calcSuccess(agents):
    n_success = 0
    n_total = 0
    for agent in agents:
        s = agent.successCount
        f = agent.failCount
        if isinstance(agent,Human):
            n_total +=f
        n_success +=s
        n_total += s
    return n_success, n_total

def simulate(n_sec = 1000,nrobot=3,nhuman=1,p_robot = 0.95,p_human = 0.95,dummy=None):
    
    #Calculation values
    #p_robot = 0.95
    mu = 20
    sigma=10
    mintime = 5
    
    #p_human = 0.95
    e_human = 60
    
    Debug = False
    
    #initialize values
    Robots=[]
    Humans = []
    n_total = 0
    n_success = 0
    # generate robots and humans
    for i in range(0,nrobot):
        Robots.append(Robot(1+i,n_sec,p_robot,mu,sigma,mintime))
    for i in range(0,nhuman):
        Humans.append(Human(1+i,n_sec,p_human,e_human,None,Debug))

        
    # run the simulation
    for i in range(0,n_sec):
        processTimeStep(Robots,Humans)

        
    # Sum up the successes 
    # sum up the total processings of objects. Failures only ocurr when the human and the robot fail
    agents = Robots+Humans

    #calculate downtimes
    p_human_down = calcPercentage(Humans)
    p_robot_down = calcPercentage(Robots)
    
    n_success, n_total = calcSuccess(agents)
    
    successrate = n_success/n_total
    if Debug: print(f'human down {p_human_down}, and robots down {p_robot_down}')
    return p_human_down, p_robot_down, successrate, n_total
	