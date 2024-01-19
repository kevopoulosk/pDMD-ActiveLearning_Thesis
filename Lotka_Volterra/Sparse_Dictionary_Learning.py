from Lotka_Volterra_model import Lotka_Volterra_Snapshot
import numpy as np
from numba import njit
from tqdm import tqdm
import matplotlib.pyplot as plt
from Lotka_Volterra_Deriv import *


@njit
def Permute(X):
    """
    Function that takes as input a snapshot matrix and randomly permutes its columns
    :param X: The snapshot matrix
    :return: The same snapshot matrix, with randomly permuted columns.
    """

    random_permutation = np.random.permutation(X.shape[1])

    Permuted_X = X[:, random_permutation]

    return Permuted_X, random_permutation


def SparseDictionary(SnapMat, kernel, tolerance):
    """
    Function that generates the sparse dictionary
    :param SnapMat: The permuted snapshot matrix X
    :param kernel: The kernel function used. Could be linear, quadratic, RBF etc.
    :param tolerance: The sparsity parameter. Increase this value for a more sparse dictionary and vice versa

    :return: The generated sparse dictionary "Xtilde".
    """

    # initialise the sparse dictionary with the first sample of the randomly permuted matrix
    sparse_dict = SnapMat[:, 0].reshape(-1, 1)

    # initialise the Cholesky factor of K_Tilde
    k_tt = kernel(SnapMat[:, 0].reshape(-1, 1), SnapMat[:, 0].reshape(-1, 1))
    C = np.sqrt(k_tt).reshape(-1, 1)
    m = 1  # needed for the Cholesky update
    # Iterate through the randomly permuted snapshot matrix, from the first column and on
    pbar = tqdm(total=SnapMat.shape[1] - 1, desc="Progress of Sparse Dictionary Learning")
    m_vals = np.zeros(SnapMat.shape[1])
    delta_vals = np.zeros(SnapMat.shape[1])
    m_vals[0] = m
    for i in range(1, SnapMat.shape[1]):
        CandidateSample = SnapMat[:, i].reshape(-1, 1)
        k_tilde_prev = kernel(sparse_dict, CandidateSample).reshape(-1, 1)
        # calculate pi with two back substitutions
        y = np.linalg.solve(C, k_tilde_prev)
        pi = np.linalg.solve(C.T, y)

        k_tt = kernel(CandidateSample, CandidateSample)
        delta = k_tt - k_tilde_prev.T @ pi
        delta_vals[i] = delta[0]

        if np.abs(delta) > tolerance:
            # Update the dictionary
            sparse_dict = np.concatenate((sparse_dict, CandidateSample), axis=1)

            st = np.linalg.solve(C, k_tilde_prev)
            # Check for ill-conditioning
            if k_tt <= np.linalg.norm(st) ** 2:
                print('The Cholesky factor is ill-conditioned.\n '
                      'Perhaps increase the sparsity parameter (tolerance) or change the kernel hyperparameters.')
            # Update the Cholesky factor
            C = np.vstack([C, st.T])
            new_column_vals = np.concatenate(
                [np.zeros((m, 1)), np.maximum(np.abs(np.sqrt(k_tt - np.linalg.norm(st) ** 2)), 0)])

            C = np.hstack([C, new_column_vals.reshape(-1, 1)])
            m += 1
        pbar.update()
        m_vals[i] = m
    pbar.close()

    return sparse_dict, m_vals, delta_vals


def quadratic_kernel(u, v, c=0.1, d=2, slope=1):
    return (slope * u.T @ v + c) ** d


def linear_kernel(u, v, c=0.1):
    return u.T @ v + c


# parameters = [0.1, 0.002, 0.2, 0.0025]
# tol = 1e-5
# #x = np.arange(0, 500)
# SnapshotMat, _ = Lotka_Volterra_Snapshot(params=parameters)
# SparseDict, m_vals, deltas = SparseDictionary(SnapshotMat, quadratic_kernel, tolerance=tol)
# print(f"The sparse dictionary is {SparseDict} with shape {SparseDict.shape}")
# plt.plot(m_vals, '.-')
# plt.xlabel("Current sample t")
# plt.ylabel("Dictionary size")
# plt.show()
#
# plt.figure()
# plt.semilogy(deltas, '.-')
# plt.axhline(tol, linestyle='--', color='red')
# plt.xlabel("Current sample t")
# plt.ylabel(r"$\delta_t$")
# plt.show()

