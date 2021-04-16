import numpy as np
import random as rm


def cohortTrain(nStudents, s, b, a, isTransfer, isMarkov, steadyStateTrigger, excelData, retrieveX):
    """
    Description:
    - Model a cohort of students as they progress through program
    inputs:
    - nstudents: number of students. EX: College of engineering 700 students
    - s: Determined by the pyswarm, decimal value of students that will leave everys semester.
    - b: Determined by pywarm, decimal value for the rate of students who don't advance becauyse of dfw
    # - a:
    """

    # This is for when the model is already trained
    nStudents = int(nStudents)
    # n number of semesters in road map
    n = 4 if isTransfer else 8

    # number of semesters to model (upper limit not worth modeling )
    k = 15
    # steady state trigger, if p=1 steady-state, p=0 only add students in year 1 	(boolean)
    p = 1 if steadyStateTrigger else 0

    # boolena to calculate the number of units in college or units in University
    h = 0  # college trigger, if h=1, only calc College, if =0, calc university
    q = 0  # system shock trigger, if q=1, add shock semester 15, if q=0 just steady state

    # Calibration Factors:
    # Calibration factors for PSO
    ones = [0, 1, 1, 1, 1, 1, 1, 1, 1]
    COEUnits = [0, 3.5, 3.5, 5, 5, 12, 12, 13, 13]
    # [.47,0.01,.01,0.01,.47,0.01,.01,0.01];%number of student entering into each class at time k
    incoming = nStudents * np.asarray([0, 1, 0, 0, 0, 0, 0, 0, 0])
    # LOAD PARAMETER MODEL
    # Department name, '4year graduation', maybe other things
    # University withdrawal rate (1-retained)for each class at time k
    sigma = s * np.asarray(ones)
    # DFW rate for each class at time k (need to repeat)
    beta = b * np.asarray(ones)
    # slowing factor to account for students taking less than 15 units per semester (need additional semester to complete class)
    alpha = a * np.asarray(ones)
    # 0.025 * [..] could include "migrating" to allow calculation of grad in and out of COE
    lmbda = h * 0.58 * np.asarray([0, 4, 2, 2, 1, .5, .5, .5, .5, .5])
    # Preallocate Matrices
    # row_size 16 rows
    # Ask what data in the excel file will substitude one of these matrices
    row_size = k + 1
    column_size = n + 1
    time = np.linspace(1, k - 1, row_size - 2)
    time1 = np.linspace(0, k - 1, k)
    x = np.zeros((column_size, row_size), dtype=float)
    x_migration = np.zeros((column_size, row_size), dtype=float)
    x_DFW = np.zeros((column_size, row_size), dtype=float)
    x_slowed = np.zeros((column_size, row_size), dtype=float)
    x_Withdraw = np.zeros((column_size, row_size), dtype=float)
    x_advance = np.zeros((column_size, row_size), dtype=float)
    y = np.zeros((1, row_size), dtype=float)
    retained = np.zeros((1, row_size), dtype=float)
    graduated = np.zeros((1, row_size), dtype=float)
    number_of_units_attempted = np.zeros((1, row_size), dtype=float)
    number_of_units_DFWed = np.zeros((1, row_size), dtype=float)
    cohortretention = np.zeros((1, row_size), dtype=float)
    cohortpersistance = np.zeros((1, row_size), dtype=float)
    cohortgrad = np.zeros((1, row_size), dtype=float)

    # STUDENT FLOW MODEL### (REVISED)
    # Time (semesters 1...15)
    for t in range(1, row_size):  # TIME
        # Semester blocks (freshman semester 1 ...)
        for s in range(1, column_size):
            # Matrix x: How many students are there at a given time
            # How many students are present in any given semester at any given time
            # If time is (semester 1)
            if t <= 1:
                x[s, t] = x_advance[s - 1, t - 1] + incoming[s] + \
                    x_DFW[s, t - 1] + x_slowed[s, t - 1]
            else:
                # Mod is to find only ppl in fall
                # ASK: .. + incoming[s] * (1 - np.mod(t + 1, 2)) + ..
                x[s, t] = x_advance[s - 1, t - 1] + incoming[s] * \
                    p + x_DFW[s, t - 1] + x_slowed[s, t - 1]

            ## Ordering matters here ##
            # Students withdrawing
            x_Withdraw[s, t] = x[s, t] * (sigma[s])
            # If student withdrew they cannot migrate (can't come back to university deparment if withdrew)
            x_migration[s, t] = x[s, t] * (lmbda[s]) * (1 - sigma[s])
            # If student withdrew they are not coming back next semester
            x_DFW[s, t] = x[s, t] * (beta[s]) * (1 - lmbda[s]) * (1 - sigma[s])
            # If student withdrew they are not coming back next semester
            # TODO: May need to subtract lambda
            x_slowed[s, t] = x[s, t] * \
                (alpha[s]) * (1 - sigma[s]) * (1 - beta[s])
            # Students who remaining Woohoo!
            x_advance[s, t] = x[s, t] * (1 - sigma[s]) * \
                (1 - lmbda[s]) * (1 - beta[s]) * (1 - alpha[s])
        # number_of_students_enrolled
        y[0, t] = np.sum(x[:, t])

        # print(x_advance)
        graduated[0, t] = np.sum(x_advance[s, 0:t+1])

        # Assuming student taking 15 units
        # Sum of all the units
        number_of_units_attempted[0, t] = (1 - h) * (np.sum(y[0, t]) - np.sum(x_slowed[:, t])) * 15 + (h) * np.sum(
            (x[:, t] - x_slowed[:, t]) * np.transpose(COEUnits))
        # Sum for DFW
        number_of_units_DFWed[0, t] = (1 - h) * np.sum(x_DFW[:, t] * 15) + h * np.sum(
            x_DFW[:, t] * np.transpose(COEUnits))

    ###COHORT CALCULATIONS###
    if p <= 0:
        t = 0
        cohortretention[0, t] = y[0, t + 1] / incoming[1]
        cohortpersistance[0, t] = y[0, t + 1] / incoming[1]
        for t in range(1, k):
            cohortpersistance[0, t] = y[0, t + 1] / incoming[1]
            cohortgrad[0, t] = graduated[0, t] / incoming[1]
            cohortretention[0, t] = (
                graduated[0, t] + y[0, t + 1]) / incoming[1]

        units_of_percent = incoming[1] * 100
        yr4gradrate = np.sum(x_advance[n, 1:9]) / units_of_percent
        yr6gradrate = np.sum(x_advance[n, 1:13]) / units_of_percent
        endgradrate = np.sum(x_advance[n, 1:16]) / units_of_percent

        averageunitsperstudent = np.sum(
            number_of_units_attempted) / np.sum(incoming)

    ## ASK ABOUT THIS ##
    ###SHOCK CALCULATIONS###
    if q >= 1:
        time = np.linspace(0, k + k - 1, k + k)
        COEUnits = [0, 3.5, 3.5, 5, 5, 12, 12, 13, 13]
        # [.47,0.01,.01,0.01,.47,0.01,.01,0.01];%number of student entering into each class at time k
        incoming = 710 * [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        # University withdrawal rate (1-retained)for each class at time k
        sigma = 0.02 * [0, 3.6, 1, 1, 1, 1, 1, 1, 1, 1]
        # DFW rate for each class at time k (need to repeat)
        beta = 0.05 * ones
        # slowing factor to account for students taking less than 15 units per semester (need additional semester to complete class)
        alpha = 0.0 * ones
        # could include "migrating" to allow calculation of grad in and out of COE
        lmbda = h * 0.025 * [0, 4, 2, 2, 1, .5, .5, .5, .5, .5]
        ### shock student flow model ###
        for t in range(k + 2, k + k):  # time
            for s in range(2, column_size):  # semesters
                x[s, t] = x_advance(s - 1, t - 1) + incoming(s) * (1 -
                                                                   np.mod(t, 2)) * p + x_DFW(s, t - 1) + x_slowed(s, t - 1)
                x_Withdraw[s, t] = x(s, t) * (sigma(s))
                x_migration[s, t] = x(s, t) * (lmbda(s)) * (1 - sigma(s))
                x_DFW[s, t] = x(s, t) * (beta(s)) * \
                    (1 - lmbda(s)) * (1 - sigma(s))
                x_slowed[s, t] = x(s, t) * (alpha(s)) * \
                    (1 - sigma(s)) * (1 - beta(s))
                x_advance[s, t] = x(s, t) * (1 - sigma(s)) * \
                    (1 - lmbda(s)) * (1 - beta(s)) * (1 - alpha(s))

            y[t] = sum(x[:, t])  # number_of_students_enrolled
            graduated[t] = sum(x_advance[column_size, 1:t])
            # NEED TO FIGURE OUT TRANSPOSE
            number_of_units_attempted[t] = (1 - h) * (y(t) - sum(x_slowed[:, t])) * 15 + (
                h) * sum((x[:, t] - x_slowed[:, t]) * np.transpose(COEUnits))

            number_of_units_DFWed[t] = (
                1 - h) * sum(x_DFW[:, t] * 15) + h * sum(x_DFW[:, t] * np.transpose(COEUnits))

    graduating = x_advance[n - 1, :]
    DataTime = [2, 4, 6, 7, 8, 10, 12]
    # college trigger, if h=1, only calc College, if = 0, calc university
    if h <= 0:
        y1 = y
        graduating1 = graduating
        number_of_units_attempted1 = number_of_units_attempted

    data = {}
    y = y[0]
    # y = np.delete(y,0)
    y= y[1:]
    graduating = graduating[1:]
    x1 = x[1][1:]
    x2 = x[2][1:]
    x3 = x[3][1:]
    x4 = x[4][1:]
    x5 = x[5][1:]
    x6 = x[6][1:]
    x7 = x[7][1:]
    x8 = x[8][1:]

    # This is returning x to be used for the snapshot charts
    if retrieveX: 
        return x

    cohortpersistance[0] = [x *100 for x in cohortpersistance[0]]
    cohortretention[0] =[x *100 for x in cohortretention[0]]
    cohortgrad[0] =[x *100 for x in cohortgrad[0]]


    if isMarkov:
        graduated = graduated[0]
        cohortpersistance = cohortpersistance[0]
        

        data['graduated_data'] = [graduated[0], graduated[1], graduated[2], graduated[3], graduated[4], graduated[5],
                                  graduated[6], graduated[7], graduated[8], graduated[9], graduated[10], graduated[11], graduated[12]]
        data['persistance_data'] = [cohortpersistance[0], cohortpersistance[1], cohortpersistance[2], cohortpersistance[3], cohortpersistance[4], cohortpersistance[5],
                                    cohortpersistance[6], cohortpersistance[7], cohortpersistance[8], cohortpersistance[9], cohortpersistance[10], cohortpersistance[11], cohortpersistance[12]]
        # data = [graduated[1], graduated[2], graduated[3], graduated[4], graduated[5], graduated[6],
        #         graduated[7], graduated[8], graduated[9], graduated[10], graduated[11], graduated[12], graduated[13]]
    
    else:
        data = {'figure1': {'x-axis': time, 'persistence': (y, '#000000'), 'coeGrad': (graduating, '#E69F00'),
                    'description': '(TODO) Description of figure1', 'yLabel': 'Number of Students'},
                'figure2': {'x-axis': time, '0% achieved': (x1, '#000000'), '12.5% achieved': (x2, '#E69F00'),
                    '25% achieved': (x3, '#56B4E9'), '37.5% achieved': (x4, '#009E73'), '50% achieved': (x5, '#F0E442'),
                    '62.5% achieved': (x6, '#0072B2'), '75% achieved': (x7, '#D55E00'), '87.5% achieved': (x8, '#CC79A7'),
                    'description': '(TODO) Description of figure2', 'yLabel': 'Number of Students in Each Class'},
                'figure3': {'x-axis': time, '0% achieved': ((x1 + x2) / 2, '#000000'),
                            '25% achieved': ((x3 + x4) / 2, '#E69F00'),
                            '50% achieved': ((x5 + x6) / 2, '#56B4E9'),
                            '75% achieved': ((x7 + x8) / 2, '#009E73'), 'description': ["(TODO) Description of figure3 (TODO) Description of figure3(TODO)" ,"Description of figure3(TODO)"],
                            'yLabel': 'Number of Students'}}
        # 'figure3': {'x-axis': time, 'persistance': (cohortpersistance[0], '#000000'),
        #             'retention': (cohortretention[0], '#E69F00'), 'graduation': (cohortgrad[0], '#56B4E9'),
        #             'description': 'figure3', 'yLabel': 'Persistance, Retention, and Graduation (%)'}}
        if p != 1:
            excelData['PERSIST COUNT'] = removeTrailingZeroes(excelData['PERSIST COUNT'])
            excelData['RETENTION COUNT'] = removeTrailingZeroes(excelData['RETENTION COUNT'])
            excelData['RETENTION COUNT'] = excelData['RETENTION COUNT'] [0:len(excelData['PERSIST COUNT'])]
            excelData['GRADUATION COUNT']= removeTrailingZeroes(excelData['GRADUATION COUNT'])
            excelData['GRADUATION COUNT'] = excelData['GRADUATION COUNT'][0:len(excelData['PERSIST COUNT'])]

            excelPersistance = [ (i/excelData['HEADCOUNT'][0])*100 for i in excelData['PERSIST COUNT']]
            excelRetention = [ (i/excelData['HEADCOUNT'][0])*100 for i in excelData['RETENTION COUNT']]
            excelGrad = [(i/excelData['HEADCOUNT'][0])*100 for i in excelData['GRADUATION COUNT']]
            # excelPersistance = [
            #     (i / j) *100 for i, j in zip(excelData['PERSIST COUNT'], excelData['HEADCOUNT'])]
            # excelRetention = [
            #     (i / j)*100  for i, j in zip(excelData['RETENTION COUNT'], excelData['HEADCOUNT'])]
            # excelGrad = [
            #     (i / j)*100  for i, j in zip(excelData['GRADUATION COUNT'], excelData['HEADCOUNT'])]
            data['figure4'] ={'x-axis': time, 'Model Persistence': (cohortpersistance[0] , '#000000', 'true'),
                                'Model Retention': (cohortretention[0], '#E69F00', 'true'),
                                'Model Graduation': (cohortgrad[0], '#56B4E9', 'true'),
                                'description': '(TODO) Description of  figure4', 'yLabel': 'Persistance, Retention, and Graduation (%)', 
                                'Persistance Data (Circle)': (excelPersistance, '#000000', 'false'),
                                'Retention Data (Circle)': (excelRetention, '#E69F00', 'false'), 
                                'Graduation Data (Circle)': (excelGrad, '#56B4E9', 'false')}
            # data = {'figure1': {'x-axis': time, 'persistence': (y, '#000000'), 'students graduating': (graduating, '#E69F00'),
            #                     'description': 'figure1', 'yLabel': 'Number of Students'},
            #        'figure2': {'x-axis': time, 'f1': (x1, '#000000'), 'f2': (x2, '#E69F00'),
            #                     's1': (x3, '#56B4E9'), 's2': (x4, '#009E73'), 'j1': (x5, '#F0E442'),
            #                     'j2': (x6, '#0072B2'), 'se1': (x7, '#D55E00'), 'se2': (x8, '#CC79A7'),
            #                     'description': 'figure2', 'yLabel': 'Number of Students in Each Class'},
            #         'figure3': {'x-axis': time, 'persistance': (cohortpersistance[0] , '#000000', 'true'),
            #                     'retention': (cohortretention[0], '#E69F00', 'true'), 'graduation': (cohortgrad[0], '#56B4E9', 'true'),
            #                     'description': 'figure3', 'yLabel': 'Persistance, Retention, and Graduation (decimal)', 
            #                     'persistanceExcelData': (excelPersistance, '#000000', 'false'), 'retentionExcelData': (excelRetention, '#E69F00', 'false'), 
            #                     'graduationExcelData': (excelGrad, '#56B4E9', 'false')},
            #         'figure4': {'x-axis': time, '0-29units': ((x1 + x2) / 2, '#000000'),
            #                     '30-59units': ((x3 + x4) / 2, '#E69F00'),
            #                     '60-89units': ((x5 + x6) / 2, '#56B4E9'),
            #                     '90-119units': ((x7 + x8) / 2, '#009E73'), 'description': 'figure4', 'yLabel': 'Number of Students'}}
    return data

def removeTrailingZeroes(_list):
    i =len(_list)-1
    while(i>=0):
        if _list[i]==0:
            i-=1
        else:
            return _list[0:i+1]
    return _list


# def cohortTest(incomingStudents):
#     # Do the training calculations in here
#     # data = request.POST.get('data')
#     incomingStudents = int(incomingStudents)

#     # Inputs
#     n = 8  # number of semesters in road map
#     k = 15  # number of semesters to model
#     p = 0  # steady state trigger, if p=1 steady-state, p=0 only add students in year 1
#     h = 0  # college trigger, if h=1, only calc College, if =0, calc university
#     q = 0  # system shock trigger, if q=1, add shock semester 15, if q=0 just steady state

#     # Calibration Factors:
#     # Calibration factors for PSO
#     ones = [0, 1, 1, 1, 1, 1, 1, 1, 1]
#     COEUnits = [0, 3.5, 3.5, 5, 5, 12, 12, 13, 13]
#     incoming = incomingStudents * np.asarray([0, 1, 0, 0, 0, 0, 0, 0, 0,
#                                               0])  # [.47,0.01,.01,0.01,.47,0.01,.01,0.01];%number of student entering into each class at time k
#     # LOAD PARAMETER MODEL - NEEDS TO BE UPLOADED FROM HIGHERED/PREDICTIONTYPE DB
#     # Department name, '4year graduation', maybe other things
#     sigma = 0.02 * np.asarray([0.0, 3.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
#                                1.0])  # University withdrawal rate (1-retained)for each class at time k
#     # DFW rate for each class at time k (need to repeat)
#     beta = 0.05 * np.asarray(ones)
#     alpha = 0.15 * np.asarray(
#         ones)  # slowing factor to account for students taking less than 15 units per semester (need additional semester to complete class)
#     lmbda = h * 0.025 * np.asarray(
#         [0, 4, 2, 2, 1, .5, .5, .5, .5, .5])  # could include "migrating" to allow calculation of grad in and out of COE

#     # Preallocate Matrices
#     row_size = k + 1
#     time = np.linspace(0, k, row_size)
#     time1 = np.linspace(0, k - 1, k)
#     x = np.zeros((column_size, row_size), dtype=float)
#     x_migration = np.zeros((column_size, row_size), dtype=float)
#     x_DFW = np.zeros((column_size, row_size), dtype=float)
#     x_slowed = np.zeros((column_size, row_size), dtype=float)
#     x_Withdraw = np.zeros((column_size, row_size), dtype=float)
#     x_advance = np.zeros((column_size, row_size), dtype=float)
#     y = np.zeros((1, row_size), dtype=float)
#     retained = np.zeros((1, row_size), dtype=float)
#     graduated = np.zeros((1, row_size), dtype=float)
#     number_of_units_attempted = np.zeros((1, row_size), dtype=float)
#     number_of_units_DFWed = np.zeros((1, row_size), dtype=float)
#     cohortretention = np.zeros((1, row_size), dtype=float)
#     cohortpersistance = np.zeros((1, row_size), dtype=float)
#     cohortgrad = np.zeros((1, row_size), dtype=float)

#     # STUDENT FLOW MODEL### (REVISED)
#     # Time (semesters 1...15)
#     for t in range(1, row_size):  # TIME
#         # Semester blocks (freshman semester 1 ...)
#         for s in range(1, column_size):
#             # Matrix x: How many students are there at a given time
#             # How many students are present in any given semester at any given time
#             # If time is (semester 1)
#             if t <= 1:
#                 x[s, t] = x_advance[s - 1, t - 1] + incoming[s] + \
#                     x_DFW[s, t - 1] + x_slowed[s, t - 1]
#             else:
#                 # Mod is to find only ppl in fall
#                 x[s, t] = x_advance[s - 1, t - 1] + incoming[s] * p + x_DFW[s, t - 1] + \
#                     x_slowed[s, t -
#                              1]  # .. + incoming[s] * (1 - np.mod(t + 1, 2)) + ..
#             # Ordering matters here:
#             # Students withdrawing
#             x_Withdraw[s, t] = x[s, t] * (sigma[s])
#             # If student withdrew they cannot migrate (can't come back to university deparment if withdrew)
#             x_migration[s, t] = x[s, t] * (lmbda[s]) * (1 - sigma[s])
#             # If student withdrew they are not coming back next semester
#             x_DFW[s, t] = x[s, t] * (beta[s]) * (1 - lmbda[s]) * (1 - sigma[s])
#             # If student withdrew they are not coming back next semester
#             # TODO: May need to subtract lambda
#             x_slowed[s, t] = x[s, t] * \
#                 (alpha[s]) * (1 - sigma[s]) * (1 - beta[s])
#             # Students who remaining Woohoo!
#             x_advance[s, t] = x[s, t] * (1 - sigma[s]) * \
#                 (1 - lmbda[s]) * (1 - beta[s]) * (1 - alpha[s])
#         # print((1-sigma[s]))

#         y[0, t] = np.sum(x[:, t])  # number_of_students_enrolled

#         # print(x_advance)
#         graduated[0, t] = np.sum(x_advance[s, 0:t+1])

#         # Assuming student taking 15 units
#         # Sum of all the units
#         number_of_units_attempted[0, t] = (1 - h) * (np.sum(y[0, t]) - np.sum(x_slowed[:, t])) * 15 + (h) * np.sum(
#             (x[:, t] - x_slowed[:, t]) * np.transpose(COEUnits))
#         # Sum for DFW
#         number_of_units_DFWed[0, t] = (1 - h) * np.sum(x_DFW[:, t] * 15) + h * np.sum(
#             x_DFW[:, t] * np.transpose(COEUnits))

#     ###COHORT CALCULATIONS###
#     if p <= 0:
#         t = 0
#         cohortretention[0, t] = y[0, t + 1] / incoming[1]
#         cohortpersistance[0, t] = y[0, t + 1] / incoming[1]
#         for t in range(1, k):
#             cohortpersistance[0, t] = y[0, t + 1] / incoming[1]
#             cohortgrad[0, t] = graduated[0, t] / incoming[1]
#             cohortretention[0, t] = (
#                 graduated[0, t] + y[0, t + 1]) / incoming[1]

#         # print(cohortpersistance)
#         # print(cohortgrad)
#         # print(cohortretention)
#         yr4gradrate = np.sum(x_advance[n, 1:9]) / \
#             incoming[1] * 100  # in units of percent(%)
#         # in units of percent(%)
#         yr6gradrate = np.sum(x_advance[n, 1:13]) / incoming[1] * 100
#         # in units of percent(%)
#         endgradrate = np.sum(x_advance[n, 1:16]) / incoming[1] * 100
#         averageunitsperstudent = np.sum(
#             number_of_units_attempted) / np.sum(incoming)

#     ###SHOCK CALCULATIONS###
#     if q >= 1:
#         time = np.linspace(0, k + k - 1, k + k)
#         print(time)
#         COEUnits = [0, 3.5, 3.5, 5, 5, 12, 12, 13, 13]
#         incoming = 710 * [0, 1, 0, 0, 0, 0, 0, 0, 0,
#                           0]  # [.47,0.01,.01,0.01,.47,0.01,.01,0.01];%number of student entering into each class at time k
#         sigma = 0.02 * [0, 3.6, 1, 1, 1, 1, 1, 1, 1,
#                         1]  # University withdrawal rate (1-retained)for each class at time k
#         # DFW rate for each class at time k (need to repeat)
#         beta = 0.05 * ones
#         # slowing factor to account for students taking less than 15 units per semester (need additional semester to complete class)
#         alpha = 0.0 * ones
#         lmbda = h * 0.025 * [0, 4, 2, 2, 1, .5, .5, .5, .5,
#                              .5]  # could include "migrating" to allow calculation of grad in and out of COE

#         ###shock student flow model###
#         for t in range(k + 2, k + k):  # time
#             for s in range(2, column_size):  # semesters
#                 x[s, t] = x_advance(s - 1, t - 1) + incoming(s) * (1 - np.mod(t, 2)) * p + x_DFW(s, t - 1) + x_slowed(s,
#                                                                                                                       t - 1)
#                 x_Withdraw[s, t] = x(s, t) * (sigma(s))
#                 x_migration[s, t] = x(s, t) * (lmbda(s)) * (1 - sigma(s))
#                 x_DFW[s, t] = x(s, t) * (beta(s)) * \
#                     (1 - lmbda(s)) * (1 - sigma(s))
#                 x_slowed[s, t] = x(s, t) * (alpha(s)) * \
#                     (1 - sigma(s)) * (1 - beta(s))
#                 x_advance[s, t] = x(s, t) * (1 - sigma(s)) * \
#                     (1 - lmbda(s)) * (1 - beta(s)) * (1 - alpha(s))

#             y[t] = sum(x[:, t])  # number_of_students_enrolled
#             graduated[t] = sum(x_advance[column_size, 1:t])
#             number_of_units_attempted[t] = (1 - h) * (y(t) - sum(x_slowed[:, t])) * 15 + (h) * sum(
#                 (x[:, t] - x_slowed[:, t]) * np.transpose(COEUnits))  # NEED TO FIGURE OUT TRANSPOSE
#             number_of_units_DFWed[t] = (
#                 1 - h) * sum(x_DFW[:, t] * 15) + h * sum(x_DFW[:, t] * np.transpose(COEUnits))

#     graduating = x_advance[n - 1, :]
#     DataTime = [2, 4, 6, 7, 8, 10, 12]
#     if h <= 0:  # college trigger, if h=1, only calc College, if =0, calc university
#         y1 = y
#         graduating1 = graduating
#         number_of_units_attempted1 = number_of_units_attempted

#     data = {'figure1': {'x-axis': time, 'uGrad': (y[0, :], '#000000'), 'coeGrad': (graduating, '#E69F00'),
#                         'description': 'figure1'},
#             'figure2': {'x-axis': time, 'f1': (x[1, :], '#000000'), 'f2': (x[2, :], '#E69F00'),
#                         's1': (x[3, :], '#56B4E9'), 's2': (x[4, :], '#009E73'), 'j1': (x[5, :], '#F0E442'),
#                         'j2': (x[6, :], '#0072B2'), 'se1': (x[7, :], '#D55E00'), 'se2': (x[8, :], '#CC79A7'),
#                         'description': 'figure2'},
#             'figure3': {'x-axis': time, 'persistance': (cohortpersistance[0], '#000000'),
#                         'retention': (cohortretention[0], '#E69F00'), 'graduation': (cohortgrad[0], '#56B4E9'),
#                         'description': 'figure3'},
#             'figure4': {'x-axis': time, '0-29units': ((x[1, :] + x[2, :]) / 2, '#000000'),
#                         '30-59units': ((x[3, :] + x[4, :]) / 2, '#E69F00'),
#                         '60-89units': ((x[5, :] + x[6, :]) / 2, '#56B4E9'),
#                         '90-119units': ((x[7, :] + x[8, :]) / 2, '#009E73'), 'description': 'figure4'}}
#     return data
