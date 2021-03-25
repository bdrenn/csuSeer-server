import numpy as np
import random as rm
from .cohortModel import cohortTrain

# include graduation, retention, # of students, and units


def cost(x, nStudents, gradList):
    # [0, 0, 1, 33, 195, 305]
    UnivGrad10 = gradList["GRADUATION COUNT"]
    UnivPersis10 = gradList["PERSIST COUNT"]
    graderror1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    persistanterro1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    endsumerror = []
    breakFlag = False
    for j in range(0, len(x)):
        s = x[j, 0]
        b = x[j, 1]
        a = x[j, 2]
        # l = x[j,3]
        cohort_train = cohortTrain(
            nStudents, s, b, a, isTransfer=False, isMarkov=True, steadyStateTrigger=False, excelData={})
        grad = cohort_train['graduated_data']
        persis = cohort_train['persistance_data']
        # grad = cohortTrain(nStudents, s, b, a, isTransfer=False, isMarkov=True)

        for i in range(0, len(UnivGrad10)):
            # if(UnivPersis10[i] == 0):
            #     breakFlag = True
            #     break
            graderror1[i] = np.power(
                (UnivGrad10[i]-grad[i]), 2)/np.power((UnivGrad10[i]+.0001), 2)
            persistanterro1[i] = np.power(
                (UnivPersis10[i]-(persis[i] * nStudents)), 2)/np.power((UnivPersis10[i]+.0001), 2)
        # eventually we will add this endsumerror.append(np.sum(graderror1) + np.sum(persistanterro1))
        endsumerror.append(np.sum(graderror1))
        # if breakFlag:
        #     break
    return endsumerror
