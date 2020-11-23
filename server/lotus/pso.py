import pyswarms as ps
import pyswarms as ps
import numpy as np
from pyswarms.single.global_best import GlobalBestPSO
from .cost import cost

def particleSwarmOptimization(request, nStudents):

	# hyperparameters and bounds
	x_max = 1* np.ones(4)
	x_min = 0 * x_max
	bounds = (x_min, x_max)

	# instatiate the optimizer
	options = {'c1': .5, 'c2': .6, 'w': .8}
	optimizer = GlobalBestPSO(n_particles=10, dimensions=4, options=options, bounds=bounds)

	# now run the optimization
	bestcost, pos = optimizer.optimize(cost,100, nStudents = nStudents)

	return pos



