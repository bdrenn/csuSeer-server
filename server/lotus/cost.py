import numpy as np
import random as rm
from .cohortModel import cohortTrain

# include graduation, retention, # of students, and units


def removeTrailingZeroes(_list):
    i = len(_list)-1
    while(i >= 0):
        if _list[i] == 0:
            i -= 1
        else:
            return _list[0:i+1]
    return _list


def cost(x, nStudents, excelData):
    # [0, 0, 1, 33, 195, 305]
    cohort_grad = excelData["GRADUATION COUNT"]
    cohort_persis = excelData["PERSIST COUNT"]
    graderror1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    persistanterror1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    endsumerror = []
    cohort_persis = removeTrailingZeroes(cohort_persis)
    for j in range(0, len(x)):
        s = x[j, 0]
        b = x[j, 1]
        a = x[j, 2]
        # l = x[j,3]
        cohort_train = cohortTrain(
            nStudents, s, b, a, isTransfer=False, isMarkov=True, steadyStateTrigger=False, excelData={}, retrieveX=False)
        grad = cohort_train['graduated_data']
        persis = cohort_train['persistance_data']

        for i in range(0, len(cohort_persis)):
            # The error is calculated by subtracting data - model
            # The value 2.5 is just to give more weight to graderror than persistanerror (it can be adjusted as needed)
            graderror1[i] = abs(cohort_grad[i]-(grad[i] * nStudents)) * 2.5
            persistanterror1[i] = abs(cohort_persis[i]-(persis[i]))

        endsumerror.append(np.sum(graderror1) + np.sum(persistanterror1))

    return endsumerror
