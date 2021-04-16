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
    UnivGrad10 = excelData["GRADUATION COUNT"]
    UnivPersis10 = excelData["PERSIST COUNT"]
    # print('UnivGrad10')
    # print(UnivGrad10)
    # print ('UnivPersis10')
    # print(UnivPersis10)
    # trim persist count to the first 0 (remove trailing 0s)
    graderror1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    persistanterro1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    endsumerror = []
    # temp=[]
    # for i in UnivPersis10:
    #     if i !=0:
    #         temp.append(i)
    # univpersis10=temp
    UnivPersis10 = removeTrailingZeroes(UnivPersis10)
    breakFlag = False
    for j in range(0, len(x)):
        s = x[j, 0]
        b = x[j, 1]
        a = x[j, 2]
        # l = x[j,3]
        cohort_train = cohortTrain(
            nStudents, s, b, a, isTransfer=False, isMarkov=True, steadyStateTrigger=False, excelData={}, retrieveX=False)
        grad = cohort_train['graduated_data']
        persis = cohort_train['persistance_data']
        # grad = cohortTrain(nStudents, s, b, a, isTransfer=False, isMarkov=True)
        # change for loop iteration univgrad10 for univpersis10
        for i in range(0, len(UnivPersis10)):
            # if(UnivPersis10[i] == 0):
            #     breakFlag = True
            #     break
            # graderror1[i] = np.power(
            #     (UnivGrad10[i]-grad[i]), 2)
            # #/np.power((UnivGrad10[i]+.0001), 2)
            # persistanterro1[i] = np.power(
            #     (UnivPersis10[i]-(persis[i] * nStudents)), 2)
            # #/np.power((UnivPersis10[i]), 2)
            graderror1[i] = abs(UnivGrad10[i]-(grad[i] * nStudents)) * 2.5
            # 2.5
            persistanterro1[i] = abs(UnivPersis10[i]-(persis[i]))

        # eventually we will add this endsumerror.append(np.sum(graderror1) + np.sum(persistanterro1))
        # print ('graderror1')
        # print(graderror1)
        # print('persistanterro1')
        # print(persistanterro1)
        # print ('graderror1')
        # print(graderror1)
        # print ('persistanterro1')
        # print(persistanterro1)
        endsumerror.append(np.sum(graderror1) + np.sum(persistanterro1))
        # if breakFlag:
        #     break
    return endsumerror
