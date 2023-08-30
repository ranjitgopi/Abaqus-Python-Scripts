""""
AutomationofContactControlStabilization.py

This script repeatedly  submits a job till the total stabilization energy (ALLSD) is less than required percentage of total internal energy (ALLIE).

Notes:

1. The input file should have this line in *Step definition:
*Contact Controls, stabilize=1.0

2. Run the script in 2 ways:
    - Go to Abaqus CAE > File > Run Script > AutomationofContactControlStabilization.py
    - Go to command prompt > Run command > abq2018 CAE noGUI=AutomationofContactControlStabilization.py

Release notes:
REV-00- 28th July 2019 - First release

Ranjit GOPI
Solution Consultant, SIMULIA India COE
ranjit.gopi@3ds.com
Simulia India Support Frontdesk:+91 44 43443000
Simulia India Support Email: simulia.in.support@3ds.com
3DS.COM/SIMULIA
'"""

import os,string,sys

import odbAccess

from job import *

JobName='wheel-contact-stabilization' #ENTER NAME OF JOB HERE

FRACTION=0.01 #ENTER WHAT FRACTION OF ALLIE IS ACCEPTABLE FOR ALLSD

fileName = JobName+'.inp'

fileJob= JobName

f = open(fileName,"r")
lines = f.readlines()

for i,line in enumerate(lines):
    if line.find("*Contact Controls")>=0:
        b = line.split(",")
        lcl = i

f.close()

count=1

factor=1.0

while True:

    outFile = JobName+'-trial'+str(count)+'.inp'

    outODB= JobName+'-trial'+str(count)+'.odb'

    outJOB= JobName+'-trial'+str(count)

    outLine=[]

    outLine.append('*Contact Controls, stabilize='+str(factor)+'\n')

    lines=lines[:lcl-1] + outLine + lines[lcl+1:]

    f = open(outFile,"w")
    f.writelines(lines)
    f.close()

    mdb.JobFromInputFile(atTime=None, explicitPrecision=SINGLE,
        getMemoryFromAnalysis=True, inputFileName=outFile,
        memory=90, memoryUnits=PERCENTAGE, multiprocessingMode=DEFAULT, name=
        outJOB, nodalOutputPrecision=SINGLE, numCpus=1, numGPUs=0, queue=
        None, resultsFormat=ODB, scratch='', type=ANALYSIS, userSubroutine='',
        waitHours=0, waitMinutes=0)

    mdb.jobs[outJOB].submit(consistencyChecking=OFF)

    mdb.jobs[outJOB].waitForCompletion()

    odb = odbAccess.openOdb(outODB,readOnly=True)

    ALLIEValue=odb.steps['Step-1'].historyRegions['Assembly Assembly-1'].historyOutputs['ALLIE'].data[-1][-1]

    ALLSDValue=odb.steps['Step-1'].historyRegions['Assembly Assembly-1'].historyOutputs['ALLSD'].data[-1][-1]

    ALLSDCheck=ALLSDValue/ALLIEValue

    with open('StabilizationVsInternalEnergyCheck.txt', 'a') as myfile:
    	myfile.write(outJOB+','+str(ALLSDCheck) +'\n')
    	myfile.close

    if ALLSDCheck < FRACTION:
        break

    count=count+1

    factor=factor/10
