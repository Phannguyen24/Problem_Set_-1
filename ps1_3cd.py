# -*- coding: utf-8 -*-
"""PS1  3cd.ipynb

Original file is located at
    https://colab.research.google.com/drive/1IzweaCAP2PV5Qz2HxcVT3r-UMYYsA58L
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# (b) Discretize the AR(1) process with gamma1 = 0.85 using Rouwenhorst's Method
def rouwenhorst(N, p):
    """
    Construct the transition probability matrix using Rouwenhorst's method.
    :param N: Number of states
    :param p: Persistence parameter (related to AR(1) coefficient)
    :return: Transition matrix P
    """
    if N == 2:
        return np.array([[p, 1 - p], [1 - p, p]])

    P_prev = rouwenhorst(N - 1, p)
    P = p * np.block([[P_prev, np.zeros((N - 1, 1))], [np.zeros((1, N - 1)), np.zeros((1, 1))]]) + \
        (1 - p) * np.block([[np.zeros((N - 1, 1)), P_prev], [np.zeros((1, N - 1)), np.zeros((1, 1))]]) + \
        (1 - p) * np.block([[np.zeros((1, 1)), np.zeros((1, N - 1))], [P_prev, np.zeros((N - 1, 1))]]) + \
        p * np.block([[np.zeros((1, 1)), np.zeros((1, N - 1))], [np.zeros((N - 1, 1)), P_prev]])

    # Normalize rows (excluding first and last rows)
    P[1:-1] /= 2
    return P

# Parameters
N = 7
gamma1 = 0.85
sigma_epsilon = 1
mu = 0.5 / (1 - gamma1)
sigma_y = sigma_epsilon / np.sqrt(1 - gamma1**2)
c = np.sqrt(N - 1)

# Generate discrete state space
y = np.linspace(mu - c * sigma_y, mu + c * sigma_y, N)

# Compute transition matrix using Rouwenhorst method
p = (1 + gamma1) / 2
P = rouwenhorst(N, p)

# Save transition matrix and state space
tm_085 = pd.DataFrame(P, columns=[f"State {i+1}" for i in range(N)])
tm_085.insert(0, "State Values (y)", np.round(y, 2))
tm_085.to_csv("rouwenhorst_ar1_gamma_085.csv", index=False)

print("State values (y):")
print(y)
print("\nTransition Matrix (P):")
print(tm_085)
np.save("state_space.npy", y)
np.save("transition_matrix.npy", P)

y = np.load("state_space.npy")
P = np.load("transition_matrix.npy")

# Simulate Markov Chain with forced start at State 1 (-1.32)
T = 50
sim_data_fixed_start = simulate_markov_chain_fixed_start(y, P, T)

# Plot results
plt.figure(figsize=(8, 4))
plt.plot(range(T), sim_data_fixed_start, label=f'gamma = {gamma1}', color='orange')
plt.xlabel('Time')
plt.ylabel('State Value')
plt.title('Simulated Markov Chain Starting from -1.32 (gamma = 0.85)')
plt.legend()

# Simulate Markov Chains for different gamma values
for gamma1 in gamma_values:
    mu = 0.5 / (1 - gamma1)  # Unconditional mean
    sigma_y = sigma_epsilon / np.sqrt(1 - gamma1**2)  # Long-run standard deviation
    c = np.sqrt(N - 1)  # Scaling factor

    # Generating the state space
    y = np.linspace(mu - c * sigma_y, mu + c * sigma_y, N)

    # Creating the transition matrix using Rouwenhorst’s method
    p = (1 + gamma1) / 2
    P = rouwenhorst(N, p)

    # Simulate Markov Chain
    def simulate_markov_chain_fixed_start(y, P, T, seed=2025):
        """
        Simulates a Markov Chain starting specifically from State 1 (-1.32).
        """
        np.random.seed(seed)
        N = len(y)
        states = np.zeros(T, dtype=int)

        # Force the start at State 1 (index 0, which corresponds to -1.32)
        states[0] = 0

        # Simulate Markov Chain
        for t in range(1, T):
            states[t] = np.random.choice(N, p=P[states[t - 1]])

        return y[states]

    sim_data = simulate_markov_chain_fixed_start(y, P, T, seed)

    # Plot results
    plt.plot(range(T), sim_data, label=f'gamma = {gamma1}')

plt.xlabel('Time')
plt.ylabel('State Value')
plt.title('Simulated Markov Chains for Different Gamma Values')
plt.legend()
plt.show()
