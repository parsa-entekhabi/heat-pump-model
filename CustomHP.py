import numpy as np
from scipy import stats

# Defaults:

totalBTU = np.array([32200,31800,31400,30700,30000,29200,28300,27600,26800])
totalWATT = np.array([2300,2450,2600,2750,2900,3050,3200,3450,3700])

EER = []

for i, j in zip(totalBTU, totalWATT):
    sol = i/j
    EER.append(sol)

temp = np.arange(75,120, 5)
EER_line = stats.linregress(temp, EER)

def EERdefault(T):
    return (EER_line.slope*T + EER_line.intercept)

# Had the COP values already from another python script
def COPdefault(T):
    return 0.0236*T + 2.2127

# Customs:

def customEERslope(customEERfile):
    totalBTU = customEERfile['totalBTU']
    totalWATT = customEERfile['totalWATT']
    temp =  customEERfile['temp']
    
    EER = []

    for i, j in zip(totalBTU, totalWATT):
        sol = i/j
        EER.append(sol)

    EER_line = stats.linregress(temp, EER)

    return EER_line.slope

def customEERintercept(customEERfile):
    totalBTU = customEERfile['totalBTU']
    totalWATT = customEERfile['totalWATT']
    temp =  customEERfile['temp']
    
    EER = []

    for i, j in zip(totalBTU, totalWATT):
        sol = i/j
        EER.append(sol)

    EER_line = stats.linregress(temp, EER)

    return EER_line.intercept

def customCOPslope(customCOPfile):
    temp = customCOPfile['Temp']
    COP = customCOPfile['COP']
    
    COP_line = stats.linregress(temp,COP)

    return COP_line.slope

def customCOPintercept(customCOPfile):
    temp = customCOPfile['Temp']
    COP = customCOPfile['COP']
    
    COP_line = stats.linregress(temp,COP)

    return COP_line.intercept


