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


def particleSwarmOptimization(request, nStudents, excelData):

    # hyperparameters and bounds
    # edit each position to have a more accurate upper bound (and lower bound maybe)
    # x_max = 1 * np.ones(4)
    # sigma, Beta, alpha, 
    x_max = np.array([0.035,0.125,0.000,1])
    x_min = np.array([0,0.116,0,0])
    bounds = (x_min, x_max)
    # instatiate the optimizer
    options = {'c1': .5, 'c2': .6, 'w': .8}
    # options = {'c1': 1, 'c2': 1, 'w': 1}

    optimizer = GlobalBestPSO(
        n_particles=10, dimensions=4, options=options, bounds=bounds)

    # now run the optimization
    bestcost, pos = optimizer.optimize(
        cost, 100, nStudents=nStudents, excelData=excelData)

    # if(bestcost - 1 > 0.05):
    #     print("Bestcost - 1")
    #     particleSwarmOptimization(request, nStudents)
    return pos
