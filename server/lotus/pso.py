import pyswarms as ps
import pyswarms as ps
import numpy as np
from pyswarms.single.global_best import GlobalBestPSO
from pyswarms.utils import Reporter
from .cost import cost
from pyswarms.utils.plotters import (
    plot_cost_history, plot_contour, plot_surface)
import matplotlib.pyplot as plt
from pyswarms.utils.plotters.formatters import Mesher


def particleSwarmOptimization(request, nStudents, gradList):

    # hyperparameters and bounds
    x_max = 1 * np.ones(4)
    x_min = 0 * x_max
    bounds = (x_min, x_max)
    print("inside pso")
    print(gradList)
    # instatiate the optimizer
    options = {'c1': .5, 'c2': .6, 'w': .8}
    optimizer = GlobalBestPSO(
        n_particles=10, dimensions=4, options=options, bounds=bounds)

    # now run the optimization
    bestcost, pos = optimizer.optimize(cost, 100, nStudents=nStudents, gradList=gradList)
    plot_cost_history(cost_history=optimizer.cost_history)
    plt.show()

    # if(bestcost - 1 > 0.05):
    #     print("Bestcost - 1")
    #     particleSwarmOptimization(request, nStudents)

    return pos
