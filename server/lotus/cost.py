import numpy as np
import random as rm

#include graduation, retention, # of students, and units
def cost(x, nStudents):
	UnivGrad10 =[0,0,1,33,195,305]
	graderror1 = [0,0,0,0,0,0]
	graderror2 = [0,0,0,0,0,0]
	graderror3 = [0,0,0,0,0,0]
	endsumerror = []
	for j in range(0, len(x)):
		s = x[j,0]
		b = x[j,1]
		a = x[j,2]
		#l = x[j,3] 
		grad = Markov(nStudents,s,b,a)
		for i in range(0,5):
			graderror1[i] = np.power((UnivGrad10[i]-grad[i]),2)/np.power((UnivGrad10[i]+.0001),2)
		endsumerror.append(np.sum(graderror1)) #+ np.sum(graderror2) + np.sum(graderror3)
	return endsumerror

def Markov(nStudents,s,b,a):
	n = 8 #number of semesters in road map
	k = 15 #number of semesters to model
	p = 0 #steady state trigger, if p=1 steady-state, p=0 only add students in year 1 
	h = 0 #college trigger, if h=1, only calc College, if =0, calc university
	q =0 #system shock trigger, if q=1, add shock semester 15, if q=0 just steady state
	l = 0.025
	
	#Calibration Factors
	ones=[0,1,1,1,1,1,1,1,1]
	COEUnits=[0,3.5,3.5,5,5,12,12,13,13]
	incoming=nStudents*np.asarray([0,1,0,0,0,0,0,0,0,0]) #[.47,0.01,.01,0.01,.47,0.01,.01,0.01];%number of student entering into each class at time k
	sigma=s*np.asarray([0.0,3.6,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]) #University withdrawal rate (1-retained)for each class at time k
	beta=b*np.asarray(ones) #DFW rate for each class at time k (need to repeat)
	alpha=a*np.asarray(ones) #slowing factor to account for students taking less than 15 units per semester (need additional semester to complete class)
	lmbda=h*l*np.asarray([0,4,2,2,1,.5,.5,.5,.5,.5]) #could include "migrating" to allow calculation of grad in and out of COE

	#Preallocate Matrices 
	time=np.linspace(0,k,k+1)
	time1=np.linspace(0,k-1,k)
	x=np.zeros((n+1, k+2),dtype=float)
	x_migration=np.zeros((n+1, k+2),dtype=float)
	x_DFW=np.zeros((n+1, k+2),dtype=float)
	x_slowed=np.zeros((n+1, k+2),dtype=float)
	x_Withdraw=np.zeros((n+1, k+2),dtype=float)
	x_advance=np.zeros((n+1, k+2),dtype=float)
	y=np.zeros((1, k+2),dtype=float)
	retained=np.zeros((1, k+2),dtype=float)
	graduated=np.zeros((1, k+2),dtype=float)
	number_of_units_attempted=np.zeros((1, k+2),dtype=float)
	number_of_units_DFWed=np.zeros((1, k+2),dtype=float)
	cohortretention=np.zeros((1, k+2),dtype=float)
	cohortpersistance=np.zeros((1, k+2),dtype=float)
	cohortgrad=np.zeros((1, k+2),dtype=float)

	###STUDENT FLOW MODEL###
	for t in range(1, k+2): #TIME
		for s in range(1, n+1):
			if t <= 1:
				x[s,t]=x_advance[s-1,t-1]+incoming[s]+x_DFW[s,t-1]+x_slowed[s,t-1]
			else:
				x[s,t]=x_advance[s-1,t-1]+incoming[s]*(1-np.mod(t+1,2))*p+x_DFW[s,t-1]+x_slowed[s,t-1]

			x_Withdraw[s,t]=x[s,t]*(sigma[s])
			x_migration[s,t]=x[s,t]*(lmbda[s])*(1-sigma[s])
			x_DFW[s,t]=x[s,t]*(beta[s])*(1-lmbda[s])*(1-sigma[s])
			x_slowed[s,t]=x[s,t]*(alpha[s])*(1-sigma[s])*(1-beta[s])
			x_advance[s,t]=x[s,t]*(1-sigma[s])*(1-lmbda[s])*(1-beta[s])*(1-alpha[s])

		y[0,t]= np.sum(x[:,t]) #number_of_students_enrolled
		graduated[0,t]=np.sum(x_advance[s,1:t])
		number_of_units_attempted[0,t]=(1-h)*(np.sum(y[0,t])-np.sum(x_slowed[:,t]))*15+(h)*np.sum((x[:,t]-x_slowed[:,t])*np.transpose(COEUnits))
		number_of_units_DFWed[0,t]=(1-h)*np.sum(x_DFW[:,t]*15)+h*np.sum(x_DFW[:,t]*np.transpose(COEUnits))

	###COHORT CALCULATIONS###
	if p <= 0:
		t = 0
		cohortretention[0,t]=y[0,t+1]/incoming[1]
		cohortpersistance[0,t]=y[0,t+1]/incoming[1]
		for t in range(1, k+1):
			cohortpersistance[0,t]=y[0,t+1]/incoming[1]
			cohortgrad[0,t]=graduated[0,t]/incoming[1]
			cohortretention[0,t]=(graduated[0,t]+y[0,t+1])/incoming[1]
		yr4gradrate=np.sum(x_advance[n,1:8])/incoming[1]*100      #in units of percent(%)
		yr6gradrate=np.sum(x_advance[n,1:12])/incoming[1]*100  #in units of percent(%)
		endgradrate=np.sum(x_advance[n,1:15])/incoming[1]*100  #in units of percent(%)
		averageunitsperstudent=np.sum(number_of_units_attempted)/np.sum(incoming)

	graduating=x_advance[n-1,:]

	DataTime=[2,4,6,7,8,10,12]
	if h<=0: #college trigger, if h=1, only calc College, if =0, calc university
		y1=y;
		graduating1=graduating;
		number_of_units_attempted1=number_of_units_attempted;

	graduated = graduated[0]
	y = y[0]
	grad = [graduated[3], graduated[5], graduated[7], graduated[9], graduated[11],graduated[13]]
	return grad
