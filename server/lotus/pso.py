import numpy as np
from pyswarms.single.global_best import GlobalBestPSO
from .cost import cost


def particleSwarmOptimization(request, nStudents, excelData, isTransfer):

    beta = 0.35 if isTransfer else 0.125
    # The following values represent the upper and lower bounds
    x_max = np.array([0.035, beta, 0.0005, 1])
    x_min = np.array([0.01, 0.116, 0, 0])
    bounds = (x_min, x_max)

    # instatiate the optimizer
    options = {'c1': .5, 'c2': .6, 'w': .8}
    # options = {'c1': 1, 'c2': 1, 'w': 1}

    optimizer = GlobalBestPSO(
        n_particles=10, dimensions=4, options=options, bounds=bounds)

    # now run the optimization
    bestcost, pos = optimizer.optimize(
        cost, 100, nStudents=nStudents, excelData=excelData)

    return pos
