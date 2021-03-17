import numpy as np
import random as rm
from .cohortModel import cohortTrain

# include graduation, retention, # of students, and units


def cost(x, nStudents, gradList):
    #[0, 0, 1, 33, 195, 305]
    # UnivGrad10 = [gradList["GRADUATION COUNT"][2], gradList["GRADUATION COUNT"][4], gradList["GRADUATION COUNT"]
    #              [6], gradList["GRADUATION COUNT"][8], gradList["GRADUATION COUNT"][10], gradList["GRADUATION COUNT"][12]]
    UnivGrad10 = gradList["GRADUATION COUNT"]
    graderror1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    endsumerror = []
    for j in range(0, len(x)):
        s = x[j, 0]
        b = x[j, 1]
        a = x[j, 2]
        #l = x[j,3]
        grad = cohortTrain(nStudents, s, b, a, isTransfer=False, isMarkov=True)
        for i in range(0, len(UnivGrad10)):
            # TODO add persistant data - model
            graderror1[i] = np.power(
                (UnivGrad10[i]-grad[i]), 2)/np.power((UnivGrad10[i]+.0001), 2)
        endsumerror.append(np.sum(graderror1))
    return endsumerror
