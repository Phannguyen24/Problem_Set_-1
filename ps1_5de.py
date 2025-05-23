# -*- coding: utf-8 -*-
"""ps1_5DE

Original file is located at
    https://colab.research.google.com/drive/1lOCQYLvThpTxohE-7fDKL2SGfSxrIefv
"""

"""

model.py
--------
This code sets up the model.

"""

#%% Imports from Python
from numpy import count_nonzero,exp,expand_dims,linspace,log,tile
from scipy import stats
from types import SimpleNamespace

#%% Deterministic Growth Model.
class planner():
    '''

    Methods:
        __init__(self,**kwargs) -> Set the household's attributes.
        setup(self,**kwargs) -> Sets parameters.

    '''

    #%% Constructor.
    def __init__(self,**kwargs):
        '''

        This initializes the model.

        Optional kwargs:
            All parameters changed by setting kwarg.

        '''

        print('--------------------------------------------------------------------------------------------------')
        print('Model')
        print('--------------------------------------------------------------------------------------------------\n')
        print('   The model is the deterministic growth model and is solved via Value Function Iteration.')

        print('\n--------------------------------------------------------------------------------------------------')
        print('Household')
        print('--------------------------------------------------------------------------------------------------\n')
        print('   The household is infintely-lived.')
        print('   It derives utility from consumption.')
        print('    -> He/she can saves capital, which is used in production, for next period.')

    #%% Set up model.
    def setup(self,**kwargs):
        '''

        This sets the parameters and creates the grids for the model.

            Input:
                self : Model class.
                kwargs : Values for parameters if not using the default.

        '''

        # Namespace for parameters, grids, and utility function.
        setattr(self,'par',SimpleNamespace())
        par = self.par

        print('\n--------------------------------------------------------------------------------')
        print('Parameters:')
        print('--------------------------------------------------------------------------------\n')

        # Preferences.
        par.beta = 0.96 # Discount factor.
        par.sigma = 2.00 # CRRA.

        par.gamma = 1.00 # Weight on leisure: Higher values mean that leisure has a higher weight in the utility function.
        par.nu = 0.04 # Frisch Elasticity: Higher values of this mean that the labor choice becomes more sensitive to productivity shocks.

        # Technology.

        par.alpha = 0.33 # Capital's share of income.
        par.delta = 0.05 # Depreciation rate of physical capital.

        par.sigma_eps = 0.07 # Std. dev of productivity shocks.
        par.rho = 0.90 # Persistence of AR(1) process.
        par.mu = 0.0 # Intercept of AR(1) process.

        # Simulation parameters.
        par.seed_sim = 2025 # Seed for simulation.
        par.T = 100 # Number of time periods.

        # Set up capital grid.
        par.kss = (par.alpha/((1.0/par.beta)-1+par.delta))**(1.0/(1.0-par.alpha)) # Steady state capital.

        par.klen = 300 # Grid size for k.
        par.kmax = 1.25*par.kss # Upper bound for k.
        par.kmin = 0.75*par.kss # Minimum k.

        # Discretize productivity.
        par.Alen = 7 # Grid size for A.
        par.m = 3.0 # Scaling parameter for Tauchen.

        # Update parameter values to kwarg values if you don't want the default values.
        for key,val in kwargs.items():
            setattr(par,key,val)

        assert par.main != None
        assert par.figout != None
        assert par.beta > 0 and par.beta < 1.00
        assert par.sigma >= 1.00
        assert par.gamma > 0
        assert par.nu > 0
        assert par.alpha > 0 and par.alpha < 1.00
        assert par.delta >= 0 and par.delta <= 1.00
        assert par.sigma_eps > 0
        assert abs(par.rho) < 1
        assert par.Alen > 3
        assert par.m > 0.0
        assert par.klen > 5
        assert par.kmax > par.kmin

        # Set up capital grid.
        par.kgrid = linspace(par.kmin,par.kmax,par.klen) # Equally spaced, linear grid for k (and k').

        # Discretize productivity.
        Agrid,pmat = tauchen(par.mu,par.rho,par.sigma_eps,par.Alen,par.m) # Tauchen's Method to discretize the AR(1) process for log productivity.
        par.Agrid = exp(Agrid) # The AR(1) is in logs so exponentiate it to get A.
        par.pmat = pmat # Transition matrix.

        # Utility function.
        par.util = util

        print('beta: ',par.beta)
        print('sigma: ',par.sigma)
        print('nu: ',par.nu)
        print('gamma: ',par.gamma)
        print('kmin: ',par.kmin)
        print('kmax: ',par.kmax)
        print('alpha: ',par.alpha)
        print('delta: ',par.delta)
        print('sigma_eps: ',par.sigma_eps)
        print('rho: ',par.rho)
        print('mu: ',par.mu)

#%% CRRA Utility Function.
def util(c,n,sigma,nu,gamma):

    # Leisure.
    un = ((1.0-n)**(1.0+(1.0/nu)))/(1.0+(1.0/nu))

    # Consumption.
    if sigma == 1:
        uc = log(c) # Log utility.
    else:
        uc = (c**(1.0-sigma))/(1.0-sigma) # CRRA utility.

    # Total.
    u = uc + gamma*un;

    return u

#%% Tauchen's Method.
def tauchen(mu,rho,sigma,N,m):
    """

    This function discretizes an AR(1) process.

            y(t) = mu + rho*y(t-1) + eps(t), eps(t) ~ NID(0,sigma^2)

    Input:
        mu    : Intercept of AR(1).
        rho   : Persistence of AR(1).
        sigma : Standard deviation of error term.
        N     : Number of states.
        m     : Parameter such that m time the unconditional std. dev. of the AR(1) is equal to the largest grid point.

    Output:
        y    : Grid for the AR(1) process.
        pmat : Transition probability matrix.

    """

    #%% Construct equally spaced grid.

    ar_mean = mu/(1.0-rho) # The mean of a stationary AR(1) process is mu/(1-rho).
    ar_sd = sigma/((1.0-rho**2.0)**(1/2)) # The std. dev of a stationary AR(1) process is sigma/sqrt(1-rho^2)

    y1 = ar_mean-(m*ar_sd) # Smallest grid point is the mean of the AR(1) process minus m*std.dev of AR(1) process.
    yn = ar_mean+(m*ar_sd) # Largest grid point is the mean of the AR(1) process plus m*std.dev of AR(1) process.

    y,d = linspace(y1,yn,N,endpoint=True,retstep=True) # Equally spaced grid. Include endpoint (endpoint=True) and record stepsize, d (retstep=True).

    #%% Compute transition probability matrix from state j (row) to k (column).

    ymatk = tile(expand_dims(y,axis=0),(N,1)) # Container for state next period.
    ymatj = mu+rho*ymatk.T # States this period.

    # In the following, loc and scale are the mean and std used to standardize the variable. # For example, norm.cdf(x,loc=y,scale=s) is the standard normal CDF evaluated at (x-y)/s.
    pmat = stats.norm.cdf(ymatk,loc=ymatj-(d/2.0),scale=sigma)-stats.norm.cdf(ymatk,loc=ymatj+(d/2.0),scale=sigma) # Transition probabilities to state 2, ..., N-1.
    pmat[:,0] = stats.norm.cdf(y[0],loc=mu+rho*y-(d/2.0),scale=sigma) # Transition probabilities to state 1.
    pmat[:,N-1] = 1.0-stats.norm.cdf(y[N-1],loc=mu+rho*y+(d/2.0),scale=sigma) # Transition probabilities to state N.

    #%% Output.

    y = expand_dims(y,axis=0) # Convert 0-dimensional array to a row vector.

    if count_nonzero(pmat.sum(axis=1)<0.999999) > 0:
        raise Exception("Some columns of transition matrix don't sum to 1.")

    return y,pmat

"""

solve.py
--------
This code solves the model.

"""

#%% Imports from Python
from numpy import argmax,expand_dims,inf,squeeze,tile,zeros,seterr
from numpy.linalg import norm
from scipy.optimize import fminbound
from types import SimpleNamespace
import time
seterr(all='ignore')

#%% Solve the model using VFI.
def plan_allocations(myClass):
    '''

    This function solves the stochastic growth model.

    Input:
        myClass : Model class with parameters, grids, and utility function.

    '''

    print('\n--------------------------------------------------------------------------------------------------')
    print('Solving the Model by Value Function Iteration')
    print('--------------------------------------------------------------------------------------------------\n')

    # Namespace for optimal policy funtions.
    setattr(myClass,'sol',SimpleNamespace())
    sol = myClass.sol

    # Model parameters, grids and functions.

    par = myClass.par # Parameters.

    beta = par.beta # Discount factor.
    sigma = par.sigma # CRRA.
    gamma = par.gamma # Weight on leisure.
    nu = par.nu # Frisch elasticity.

    alpha = par.alpha # Capital's share of income.
    delta = par.delta # Depreciation rate

    klen = par.klen # Grid size for k.
    kgrid = par.kgrid # Grid for k (state and choice).

    Alen = par.Alen # Grid size for A.
    Agrid = par.Agrid[0] # Grid for A.
    pmat = par.pmat # Grid for A.

    kmat = tile(expand_dims(kgrid,axis=1),(1,Alen)) # k for each value of A.
    Amat = tile(expand_dims(Agrid,axis=0),(klen,1)) # A for each value of k.

    util = par.util # Utility function.
    n0 = zeros((klen,klen,Alen))# Container for n.

    t0 = time.time()

    # Solve for labor choice.
    print('--------------------------------------Solving for Labor Supply------------------------------------\n')
    for h1 in range(0,klen): # Loop over k state.
        for h2 in range(0,klen): # Loop over k choice.
            for h3 in range(0,Alen): # Loop over A state.
                # Intratemporal condition.
                foc = lambda n: intra_foc(n,kgrid[h2],Agrid[h3],kgrid[h1],alpha,delta,sigma,nu,gamma)
                n0[h1,h2,h3] = fminbound(foc,0.0,1.0)

        # Print counter.
        if h1%25 == 0:
            print('Capital State: ',h1,'.\n')

    print('--------------------------------------Iterating on Bellman Eq.------------------------------------\n')

    # Value Function Iteration.
    y0 = Amat*(kmat**alpha)*(squeeze(n0[:,1,:])**(1.0-alpha)) # Given combinations of k and A and the value of n associated with the lowest possible k'.
    i0 = delta*kmat # In steady state, k=k'=k*.
    c0 = y0-i0 # Steady-state consumption.
    c0[c0<0.0] = 0.0
    v0 = util(c0,squeeze(n0[:,1,:]),sigma,nu,gamma)/(1.0-beta) # Guess of value function for each value of k.
    v0[c0<=0.0] = -inf # Set the value function to negative infinity number when c <= 0.

    crit = 1e-6;
    maxiter = 10000;
    diff = 1;
    iter = 0;

    while (diff > crit) and (iter < maxiter): # Iterate on the Bellman Equation until convergence.

        v1 = zeros((klen,Alen)) # Container for V.
        k1 = zeros((klen,Alen)) # Container for k'.
        n1 = zeros((klen,Alen)) # Container for n.

        for p in range(0,klen): # Loop over the k-states.
            for j in range(0,Alen): # Loop over the A-states.

                # Macro variables.
                y = Agrid[j]*(kgrid[p]**alpha)*(squeeze(n0[p,:,j])**(1.0-alpha)) # Output in the "last period", given combinations of k and A and the value of n associated with the lowest possible k'.
                i = kgrid-((1-delta)*kgrid[p]) # Possible values for investment, i=k'-(1-delta)k, when choosing k' from kgrid and given k.
                c = y-i # Possible values for consumption, c = y-i, given y and i.
                c[c<0.0] = 0.0

                # Solve the maximization problem.
                ev = squeeze(v0@pmat[j,:].T); #  The next-period value function is the expected value function over each possible next-period A, conditional on the current state j.
                vall = util(c,n0[p,:,j],sigma,nu,gamma) + beta*ev # Compute the value function for each choice of k', given k.
                vall[c<=0.0] = -inf # Set the value function to negative infinity number when c <= 0.
                v1[p,j] = max(vall) # Maximize: vmax is the maximized value function; ind is where it is in the grid.
                k1[p,j] = kgrid[argmax(vall)] # Optimal k'.
                n1[p,j] = n0[p,argmax(vall),j] # Choice of n given k,k', and A.

        diff = norm(v1-v0) # Check convergence.
        v0 = v1; # Update guess.

        iter = iter + 1; # Update counter.

        # Print counter.
        if iter%25 == 0:
            print('Iteration: ',iter,'.\n')

    t1 = time.time()
    print('Elapsed time is ',t1-t0,' seconds.')
    print('Converged in ',iter,' iterations.')

    # Macro variables, value, and policy functions.
    sol.y = Amat*(kmat**alpha)*(n1**(1.0-alpha)) # Output.
    sol.k = k1 # Capital policy function.
    sol.n = n1 # Labor supply policy function.
    sol.i = k1-((1.0-delta)*kmat) # Investment policy function.
    sol.c = sol.y-sol.i # Consumption policy function.
    sol.c[sol.c<0.0] = 0.0
    sol.v = v1 # Value function.
    sol.v[sol.c<=0.0] = -inf

#%% Intra-temporal conditions for labor.
def intra_foc(n,kp,A,k,alpha,delta,sigma,nu,gamma):

    c = (A*(k**alpha)*(n**(1.0-alpha)))+((1.0-delta)*k-kp)
    mpl = A*(1.0-alpha)*((k/n)**alpha)

    # Leisure.
    un = -gamma*(1.0-n)**(1.0/nu)

    # Consumption.
    if sigma == 1.0:
        uc = 1.0/c # Log utility.
    else:
        uc = c**(-sigma) # CRRA utility.

    # Total.
    ucn = uc*mpl + un

    return ucn

"""

simulate.py
-----------
This code simulates the model.

"""

#%% Imports from Python
from numpy import sin, pi, linspace, cumsum, squeeze, where, zeros
from numpy.random import choice, rand, seed
from numpy.linalg import matrix_power
from types import SimpleNamespace

def grow_economy(myClass):
    print('\n--------------------------------------------------------------------------------------------------')
    print('Simulate the Model with Taste Shock')
    print('--------------------------------------------------------------------------------------------------\n')

    setattr(myClass,'sim',SimpleNamespace())
    sim = myClass.sim

    par = myClass.par
    sol = myClass.sol

    sigma = par.sigma
    nu = par.nu
    util = par.util
    seed_sim = par.seed_sim

    klen = par.klen
    Alen = par.Alen
    kgrid = par.kgrid
    Agrid = par.Agrid[0]
    pmat = par.pmat

    yout = sol.y
    kpol = sol.k
    cpol = sol.c
    ipol = sol.i
    npol = sol.n

    T = par.T
    gamma_base = par.gamma
    gamma_series = gamma_base + 0.3 * sin(linspace(0, 4 * pi, 2 * T))
    sim.gamma_series = gamma_series[T:2 * T + 1]

    Asim = zeros(2 * T)
    ysim = zeros(2 * T)
    ksim = zeros(2 * T)
    csim = zeros(2 * T)
    nsim = zeros(2 * T)
    isim = zeros(2 * T)
    usim = zeros(2 * T)

    seed(seed_sim)
    pmat0 = matrix_power(pmat,1000)[0,:]
    cmat = cumsum(pmat, axis=1)

    A0_ind = choice(range(Alen), 1, p=pmat0)
    k0_ind = choice(range(klen), 1)

    Asim[0] = Agrid[A0_ind]
    ysim[0] = yout[k0_ind, A0_ind]
    csim[0] = cpol[k0_ind, A0_ind]
    ksim[0] = kpol[k0_ind, A0_ind]
    nsim[0] = npol[k0_ind, A0_ind]
    isim[0] = ipol[k0_ind, A0_ind]
    usim[0] = util(csim[0], nsim[0], sigma, nu, gamma_series[0])

    A1_ind = where(rand(1) <= squeeze(cmat[A0_ind,:]))
    At_ind = A1_ind[0][0]

    for j in range(1, 2 * T):
        kt_ind = where(ksim[j-1] == kgrid)
        Asim[j] = Agrid[At_ind]
        ysim[j] = yout[kt_ind, At_ind]
        csim[j] = cpol[kt_ind, At_ind]
        nsim[j] = npol[kt_ind, At_ind]
        ksim[j] = kpol[kt_ind, At_ind]
        isim[j] = ipol[kt_ind, At_ind]
        usim[j] = util(csim[j], nsim[j], sigma, nu, gamma_series[j])
        A1_ind = where(rand(1) <= squeeze(cmat[At_ind,:]))
        At_ind = A1_ind[0][0]

    sim.Asim = Asim[T:2 * T + 1]
    sim.ysim = ysim[T:2 * T + 1]
    sim.ksim = ksim[T:2 * T + 1]
    sim.csim = csim[T:2 * T + 1]
    sim.nsim = nsim[T:2 * T + 1]
    sim.isim = isim[T:2 * T + 1]
    sim.usim = usim[T:2 * T + 1]

"""

my_graph.py
-----------
This code plots the value and policy functions.

"""

#%% Imports from Python
from matplotlib.pyplot import close,figure,plot,xlabel,ylabel,title,savefig,show
from numpy import linspace
import matplotlib.pyplot as plt


#%% Plot the model functions and simulations.
def track_growth(myClass):
    '''

    This function plots the model functions and simulations.

    Input:
        myClass : Model class with parameters, grids, utility function, policy functions, and simulations.

    '''

    # Model parameters, policy and value functions, and simulations.
    par = myClass.par # Parameters.
    sol = myClass.sol # Policy functions.
    sim = myClass.sim # Simulations.

    # Production function.

    figure(1)
    plot(par.kgrid,sol.y)
    xlabel('$k_{t}$')
    ylabel('$y_{t}$')
    title('Production Function')

    figname = myClass.par.figout+"\\ypol.png"
    print(figname)
    savefig(figname)

    # Plot capital policy function.

    figure(2)
    plot(par.kgrid,sol.k)
    xlabel('$k_{t}$')
    ylabel('$k_{t+1}$')
    title('Capital Policy Function')

    figname = myClass.par.figout+"\\kpol.png"
    savefig(figname)

    # Plot consumption policy function.

    figure(3)
    plot(par.kgrid,sol.c)
    xlabel('$k_{t}$')
    ylabel('$c_{t}$')
    title('Consumption Policy Function')

    figname = myClass.par.figout+"\\cpol.png"
    savefig(figname)

    # Plot investment policy function.

    figure(4)
    plot(par.kgrid,sol.i)
    xlabel('$k_{t}$')
    ylabel('$i_{t}$')
    title('Investment Policy Function')

    figname = myClass.par.figout+"\\ipol.png"
    savefig(figname)

    # Plot labor supply policy function.

    figure(5)
    plot(par.kgrid,sol.n)
    xlabel('$k_{t}$')
    ylabel('$n_t$')
    title('Labor Supply Policy Function')

    figname = myClass.par.figout+"\\npol.png"
    savefig(figname)

    # Plot value function.

    figure(6)
    plot(par.kgrid,sol.v)
    xlabel('$k_{t}$')
    ylabel('$V_t(k_t)$')
    title('Value Function')

    figname = myClass.par.figout+"\\vfun.png"
    savefig(figname)

    # Plot simulated output.

    tgrid = linspace(1,par.T,par.T,dtype=int)

    figure(7)
    plot(tgrid,sim.ysim)
    xlabel('Time')
    ylabel('$y^{sim}_t$')
    title('Simulated Output')

    figname = myClass.par.figout+"\\ysim.png"
    savefig(figname)

    # Plot simulated capital choice.

    figure(8)
    plot(tgrid,sim.ksim)
    xlabel('Time')
    ylabel('$k^{sim}_{t+1}$')
    title('Simulated Capital Choice')

    figname = myClass.par.figout+"\\ksim.png"
    savefig(figname)

    # Plot simulated consumption.

    figure(9)
    plot(tgrid,sim.csim)
    xlabel('Time')
    ylabel('$c^{sim}_{t}$')
    title('Simulated Consumption')

    figname = myClass.par.figout+"\\csim.png"
    savefig(figname)

    # Plot simulated investment.

    figure(10)
    plot(tgrid,sim.isim)
    xlabel('Time')
    ylabel('$i^{sim}_{t}$')
    title('Simulated Investment')

    figname = myClass.par.figout+"\\isim.png"
    savefig(figname)

    # Plot simulated utility.

    figure(11)
    plot(tgrid,sim.usim)
    xlabel('Time')
    ylabel('$u^{sim}_t$')
    title('Simulated Utility')

    figname = myClass.par.figout+"\\usim.png"
    savefig(figname)

    # Plot simulated productivity.

    figure(12)
    plot(tgrid,sim.Asim)
    xlabel('Time')
    ylabel('$A^{sim}_t$')
    title('Simulated Productivity')

    figname = myClass.par.figout+"\\Asim.png"
    savefig(figname)

    # Plot simulated labor supply.

    figure(13)
    plot(tgrid,sim.nsim)
    xlabel('Time')
    ylabel('$n^{sim}_t$')
    title('Simulated Labor Supply')

    figname = myClass.par.figout+"\\nsim.png"
    savefig(figname)

     # Plot simulated taste shock γₜ
    if hasattr(sim, 'gamma_series'):
        plt.figure(14)
        plt.plot(tgrid, sim.gamma_series)
        plt.xlabel('Time')
        plt.ylabel('$\\gamma_t$')
        plt.title('Simulated Taste Shock')
        plt.savefig(par.figout + "\\gammat.png")

    #show()
    #close('all')

"""
run_colab.py
------------
This code solves and simulates the stochastic growth model on Google Colab.
"""

#%% Import Python and set project directory
import os

main = os.getcwd()  # current working directory in Colab
figout = os.path.join(main, "output", "figures")  # output folder for figures
os.makedirs(figout, exist_ok=True)  # create directory if not exists

#%% Import from uploaded code files
from model import planner
from solve import plan_allocations
from simulate import grow_economy
from my_graph import track_growth

#%% Create model instance
benevolent_dictator = planner()

# Set parameters, state space, utility function
benevolent_dictator.setup(main=main, figout=figout, beta=0.96, sigma=2.00)

# Solve model
plan_allocations(benevolent_dictator)

# Simulate model
grow_economy(benevolent_dictator)

# Plot results
track_growth(benevolent_dictator)

#%% PART (D): Load actual saving rate and re-simulate the model

import pandas as pd
import matplotlib.pyplot as plt

# Load actual saving rate data from Excel
df = pd.read_excel("dataps5.xlsx", sheet_name="E02.37")
saving_data = df.iloc[1:101, 9].values

# Normalize saving rate (optional): if in percent, divide by 100
saving_data = saving_data / 100

# Replace simulated saving behavior with actual data
# Update the law of motion: k_{t+1} = s_t * y_t + (1 - delta) * k_t
par = benevolent_dictator.par
sol = benevolent_dictator.sol
sim = SimpleNamespace()

T = 100
sim.ksim = [par.kss]  # start at steady-state capital
sim.Asim = benevolent_dictator.sim.Asim[:T]  # keep same simulated A_t
sim.ysim = []
sim.csim = []
sim.isim = []
sim.nsim = []
sim.usim = []

for t in range(T):
    A = sim.Asim[t]
    k = sim.ksim[-1]
    n = 1  # assume fixed labor supply for this part (or use mean)
    y = A * (k ** par.alpha) * (n ** (1 - par.alpha))
    s = saving_data[t]
    i = s * y
    c = y - i
    k_next = i + (1 - par.delta) * k
    u = par.util(c, n, par.sigma, par.nu, par.gamma)

    # Save
    sim.ysim.append(y)
    sim.csim.append(c)
    sim.isim.append(i)
    sim.nsim.append(n)
    sim.usim.append(u)
    sim.ksim.append(k_next)

# Remove last k
sim.ksim = sim.ksim[:-1]

# Plot all variables
time = range(1, T + 1)
plt.figure(figsize=(10, 6))
plt.plot(time, sim.ysim)
plt.title("Simulated Output $y_t$ with Actual Saving Rate")
plt.xlabel("Time")
plt.ylabel("Output")
plt.grid()
plt.savefig("output/figures/d_ysim.png")
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(time, sim.ksim)
plt.title("Simulated Capital $k_t$ with Actual Saving Rate")
plt.xlabel("Time")
plt.ylabel("Capital")
plt.grid()
plt.savefig("output/figures/d_ksim.png")
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(time, sim.csim)
plt.title("Simulated Consumption $c_t$ with Actual Saving Rate")
plt.xlabel("Time")
plt.ylabel("Consumption")
plt.grid()
plt.savefig("output/figures/d_csim.png")
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(time, sim.isim)
plt.title("Simulated Investment $i_t$ with Actual Saving Rate")
plt.xlabel("Time")
plt.ylabel("Investment")
plt.grid()
plt.savefig("output/figures/d_isim.png")
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(time, sim.usim)
plt.title("Simulated Utility $u_t$ with Actual Saving Rate")
plt.xlabel("Time")
plt.ylabel("Utility")
plt.grid()
plt.savefig("output/figures/d_usim.png")
plt.show()

track_growth(benevolent_dictator)

#%% PART (E): Policy experiment – reduce gamma_t to simulate pro-labor policy

from types import SimpleNamespace
import numpy as np
import matplotlib.pyplot as plt

par = benevolent_dictator.par

# Reuse same productivity shock (for fair comparison)
Asim_base = benevolent_dictator.sim.Asim

# Use same gamma structure but scaled down (e.g., -0.2)
T = par.T
gamma_base = par.gamma
gamma_policy = gamma_base + 0.3 * np.sin(np.linspace(0, 4 * np.pi, 2 * T)) - 0.2
gamma_policy = gamma_policy[T:2*T+1]  # burn-in drop

# Simulate again with policy gamma_t
sim = SimpleNamespace()
sim.Asim = Asim_base
sim.gamma_series = gamma_policy

ysim, ksim, csim, nsim, isim, usim = [], [], [], [], [], []
k = par.kss  # start at steady-state

for t in range(T):
    A = sim.Asim[t]
    gamma_t = gamma_policy[t]
    n = 1.0  # keep same labor policy function (or approximate)
    y = A * k ** par.alpha * n ** (1 - par.alpha)
    c = 0.75 * y  # assume 75% for consumption
    i = y - c
    k_next = i + (1 - par.delta) * k
    u = par.util(c, n, par.sigma, par.nu, gamma_t)

    ysim.append(y)
    csim.append(c)
    isim.append(i)
    usim.append(u)
    nsim.append(n)
    ksim.append(k)

    k = k_next

# Save to sim-policy
sim.ysim = ysim
sim.ksim = ksim
sim.csim = csim
sim.nsim = nsim
sim.isim = isim
sim.usim = usim
sim.gamma_series = gamma_policy

# Plot policy experiment results
plt.figure()
plt.plot(range(1, T + 1), benevolent_dictator.sim.ysim, label='Baseline')
plt.plot(range(1, T + 1), sim.ysim, label='Policy: lower gamma')
plt.xlabel("Time")
plt.ylabel("Output")
plt.title("Output Comparison: Baseline vs Policy")
plt.legend()
plt.savefig("output/figures/e_output_compare.png")
plt.show()
