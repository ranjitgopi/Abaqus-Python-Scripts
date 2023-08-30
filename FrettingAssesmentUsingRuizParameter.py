"""
FrettingAssesmentUsingRuizParameter.py

This script calculates fretting as a post processing operation in Abaqus Viewer using RUIZ parameter. See attached document for more details.

Procedure:
1. Create Blank ODB using data check
2. Enter required inputs in attached spreadsheet INPUTS.csv
3. Go to Abaqus Viewer> File > Run Script > FrettingAssesmentUsingRuizParameter.py

OR

Go to command prompt > Go to working directory > write command > abq2018 Viewer noGUI=FrettingAssesmentUsingRuizParameter.py (may be faster than GUI, still uses CAE tokens)

OR

Go to command prompt > Go to working directory > write command > abq2018 python FrettingAssesmentUsingRuizParameter.py (may be faster than GUI and uses no CAE tokens)

Please note:
1. Example model (boltedFlange.inp) is provided to test script

Revision history:
REV-00 (18th May 2020): 1st release
REV-01 (19th May 2020): Fixed a bug

Author:
Ranjit GOPI
Solution Consultant, SIMULIA India COE
ranjit.gopi@3ds.com
Simulia India Support Frontdesk:+91 44 43443000
Simulia India Support Email: simulia.in.support@3ds.com
3DS.COM/SIMULIA
"""
from odbAccess import *
from abaqusConstants import *
import time
import math
import csv

STEP_NUMBERS=[]
FRAME_NUMBERS=[]
NODE_SET_NAMES=[]

# Reading all the input values from a csv file
with open('INPUTS.csv', 'r') as f:
	reader = csv.reader(f)
	count= 0
	for row in reader:
		if count == 0:
			OdbToReadName =row[1]
		if count == 1:
			for each in row[1].split(','):
				STEP_NUMBERS.append(each.strip())
		if count == 2:
			for each in row[1].split(','):
				FRAME_NUMBERS.append(each.strip())
		if count == 3:
			OdbToWriteName=row[1]
		if count == 4:
			for each in row[1].split(','):
				NODE_SET_NAMES.append(each.strip())
		count =count + 1

start = time.clock()

CalculatedData1Sum=[]
CalculatedData1SumTuple=()

CalculatedData2Sum=[]
CalculatedData2SumTuple=()

for zerothindex in range(len(STEP_NUMBERS)-1):

	OdbToRead = openOdb(path=OdbToReadName, readOnly=True)

	StepNamei=OdbToRead.steps.keys()[int(STEP_NUMBERS[zerothindex])]
	currentFramei = OdbToRead.steps[StepNamei].frames[int(FRAME_NUMBERS[zerothindex+1])]

	StepNameiMinusOne=OdbToRead.steps.keys()[int(STEP_NUMBERS[zerothindex])-1]
	currentFrameiMinusOne=OdbToRead.steps[StepNameiMinusOne].frames[int(FRAME_NUMBERS[zerothindex])]

	nodeLabelData=()
	CalculatedData1Zero=()
	CalculatedData2Zero=()
	CalculatedData1currentFrame=()
	CalculatedData2currentFrame=()

	for firstindex in range(len(NODE_SET_NAMES)):

		NodeSetOfInterest=OdbToRead.rootAssembly.instances['PART-1-1'].nodeSets[NODE_SET_NAMES[firstindex]] #ANY ORPHAN INPUT FILE CREATED BY ANSA OR HYPERMESH WILL HAVE DEFAULT INSTANCE NAME PART-1-1 IN ABAQUS

		for node in (NodeSetOfInterest.nodes):

			nodeLabelData=nodeLabelData+(node.label,)

		for firstindex in range(len(NodeSetOfInterest.nodes)):
			CalculatedData1Zero=CalculatedData1Zero+((0.0,),)

		for firstindex in range(len(NodeSetOfInterest.nodes)):
			CalculatedData2Zero=CalculatedData2Zero+((0.0,),)

		CSHEAR1iNodeList=[]
		CSHEAR1iList=[]
		CSHEAR1iListFinal=[]

		CSHEAR2iNodeList=[]
		CSHEAR2iList=[]
		CSHEAR2iListFinal=[]

		CSLIP1iNodeList=[]
		CSLIP1iList=[]
		CSLIP1iListFinal=[]

		CSLIP2iNodeList=[]
		CSLIP2iList=[]
		CSLIP2iListFinal=[]

		CSHEAR1iMinusOneNodeList=[]
		CSHEAR1iMinusOneList=[]
		CSHEAR1iMinusOneListFinal=[]

		CSHEAR2iMinusOneNodeList=[]
		CSHEAR2iMinusOneList=[]
		CSHEAR2iMinusOneListFinal=[]

		CSLIP1iMinusOneNodeList=[]
		CSLIP1iMinusOneList=[]
		CSLIP1iMinusOneListFinal=[]

		CSLIP2iMinusOneNodeList=[]
		CSLIP2iMinusOneList=[]
		CSLIP2iMinusOneListFinal=[]

		CSHEAR1i =   currentFramei.fieldOutputs['CSHEAR1'].getSubset(region=NodeSetOfInterest)

		for value in (CSHEAR1i.values):
			CSHEAR1iNodeList.append(value.nodeLabel)
			CSHEAR1iList.append(value.data)

		CSHEAR1iDictUnSorted = {}

		for secondindex in range(len(CSHEAR1iNodeList)):
		        CSHEAR1iDictUnSorted[CSHEAR1iNodeList[secondindex]] = CSHEAR1iList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSHEAR1iDictUnSorted.keys():
				CSHEAR1iDictUnSorted[node.label]=0.0

		CSHEAR1iListofDict=list(CSHEAR1iDictUnSorted.items())
		CSHEAR1iListofDict.sort()

		for secondindex in range(len(CSHEAR1iListofDict)):
			CSHEAR1iListFinal.append(CSHEAR1iListofDict[secondindex][1])

		CSHEAR2i =   currentFramei.fieldOutputs['CSHEAR2'].getSubset(region=NodeSetOfInterest)

		for value in (CSHEAR2i.values):
			CSHEAR2iNodeList.append(value.nodeLabel)
			CSHEAR2iList.append(value.data)

		CSHEAR2iDictUnSorted = {}

		for secondindex in range(len(CSHEAR2iNodeList)):
		        CSHEAR2iDictUnSorted[CSHEAR2iNodeList[secondindex]] = CSHEAR2iList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSHEAR2iDictUnSorted.keys():
				CSHEAR2iDictUnSorted[node.label]=0.0

		CSHEAR2iListofDict=list(CSHEAR2iDictUnSorted.items())
		CSHEAR2iListofDict.sort()

		for secondindex in range(len(CSHEAR2iListofDict)):
			CSHEAR2iListFinal.append(CSHEAR2iListofDict[secondindex][1])

		CSLIP1i =   currentFramei.fieldOutputs['CSLIP1'].getSubset(region=NodeSetOfInterest)

		for value in (CSLIP1i.values):
			CSLIP1iNodeList.append(value.nodeLabel)
			CSLIP1iList.append(value.data)

		CSLIP1iDictUnSorted = {}

		for secondindex in range(len(CSLIP1iNodeList)):
		        CSLIP1iDictUnSorted[CSLIP1iNodeList[secondindex]] = CSLIP1iList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSLIP1iDictUnSorted.keys():
				CSLIP1iDictUnSorted[node.label]=0.0

		CSLIP1iListofDict=list(CSLIP1iDictUnSorted.items())
		CSLIP1iListofDict.sort()

		for secondindex in range(len(CSLIP1iListofDict)):
			CSLIP1iListFinal.append(CSLIP1iListofDict[secondindex][1])

		CSLIP2i =   currentFramei.fieldOutputs['CSLIP2'].getSubset(region=NodeSetOfInterest)

		for value in (CSLIP2i.values):
			CSLIP2iNodeList.append(value.nodeLabel)
			CSLIP2iList.append(value.data)

		CSLIP2iDictUnSorted = {}

		for secondindex in range(len(CSLIP2iNodeList)):
		        CSLIP2iDictUnSorted[CSLIP2iNodeList[secondindex]] = CSLIP2iList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSLIP2iDictUnSorted.keys():
				CSLIP2iDictUnSorted[node.label]=0.0

		CSLIP2iListofDict=list(CSLIP2iDictUnSorted.items())
		CSLIP2iListofDict.sort()

		for secondindex in range(len(CSLIP2iListofDict)):
			CSLIP2iListFinal.append(CSLIP2iListofDict[secondindex][1])

		CSHEAR1iMinusOne =   currentFrameiMinusOne.fieldOutputs['CSHEAR1'].getSubset(region=NodeSetOfInterest)

		for value in (CSHEAR1iMinusOne.values):
			CSHEAR1iMinusOneNodeList.append(value.nodeLabel)
			CSHEAR1iMinusOneList.append(value.data)

		CSHEAR1iMinusOneDictUnSorted = {}

		for secondindex in range(len(CSHEAR1iMinusOneNodeList)):
		        CSHEAR1iMinusOneDictUnSorted[CSHEAR1iMinusOneNodeList[secondindex]] = CSHEAR1iMinusOneList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSHEAR1iMinusOneDictUnSorted.keys():
				CSHEAR1iMinusOneDictUnSorted[node.label]=0.0

		CSHEAR1iMinusOneListofDict=list(CSHEAR1iMinusOneDictUnSorted.items())
		CSHEAR1iMinusOneListofDict.sort()

		for secondindex in range(len(CSHEAR1iMinusOneListofDict)):
			CSHEAR1iMinusOneListFinal.append(CSHEAR1iMinusOneListofDict[secondindex][1])

		CSHEAR2iMinusOne =   currentFrameiMinusOne.fieldOutputs['CSHEAR2'].getSubset(region=NodeSetOfInterest)

		for value in (CSHEAR2iMinusOne.values):
			CSHEAR2iMinusOneNodeList.append(value.nodeLabel)
			CSHEAR2iMinusOneList.append(value.data)

		CSHEAR2iMinusOneDictUnSorted = {}

		for secondindex in range(len(CSHEAR2iMinusOneNodeList)):
		        CSHEAR2iMinusOneDictUnSorted[CSHEAR2iMinusOneNodeList[secondindex]] = CSHEAR2iMinusOneList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSHEAR2iMinusOneDictUnSorted.keys():
				CSHEAR2iMinusOneDictUnSorted[node.label]=0.0

		CSHEAR2iMinusOneListofDict=list(CSHEAR2iMinusOneDictUnSorted.items())
		CSHEAR2iMinusOneListofDict.sort()

		for secondindex in range(len(CSHEAR2iMinusOneListofDict)):
			CSHEAR2iMinusOneListFinal.append(CSHEAR2iMinusOneListofDict[secondindex][1])

		CSLIP1iMinusOne =   currentFrameiMinusOne.fieldOutputs['CSLIP1'].getSubset(region=NodeSetOfInterest)

		for value in (CSLIP1iMinusOne.values):
			CSLIP1iMinusOneNodeList.append(value.nodeLabel)
			CSLIP1iMinusOneList.append(value.data)

		CSLIP1iMinusOneDictUnSorted = {}

		for secondindex in range(len(CSLIP1iMinusOneNodeList)):
				CSLIP1iMinusOneDictUnSorted[CSLIP1iMinusOneNodeList[secondindex]] = CSLIP1iMinusOneList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSLIP1iMinusOneDictUnSorted.keys():
				CSLIP1iMinusOneDictUnSorted[node.label]=0.0

		CSLIP1iMinusOneListofDict=list(CSLIP1iMinusOneDictUnSorted.items())
		CSLIP1iMinusOneListofDict.sort()

		for secondindex in range(len(CSLIP1iMinusOneListofDict)):
			CSLIP1iMinusOneListFinal.append(CSLIP1iMinusOneListofDict[secondindex][1])

		CSLIP2iMinusOne =   currentFrameiMinusOne.fieldOutputs['CSLIP2'].getSubset(region=NodeSetOfInterest)

		for value in (CSLIP2iMinusOne.values):
			CSLIP2iMinusOneNodeList.append(value.nodeLabel)
			CSLIP2iMinusOneList.append(value.data)

		CSLIP2iMinusOneDictUnSorted = {}

		for secondindex in range(len(CSLIP2iMinusOneNodeList)):
				CSLIP2iMinusOneDictUnSorted[CSLIP2iMinusOneNodeList[secondindex]] = CSLIP2iMinusOneList[secondindex]

		for node in (NodeSetOfInterest.nodes):
			if node.label not in CSLIP2iMinusOneDictUnSorted.keys():
				CSLIP2iMinusOneDictUnSorted[node.label]=0.0

		CSLIP2iMinusOneListofDict=list(CSLIP2iMinusOneDictUnSorted.items())
		CSLIP2iMinusOneListofDict.sort()

		for secondindex in range(len(CSLIP2iMinusOneListofDict)):
			CSLIP2iMinusOneListFinal.append(CSLIP2iMinusOneListofDict[secondindex][1])

		A=map(lambda x,y: x-y, CSLIP1iListFinal,CSLIP1iMinusOneListFinal)
		B=map(lambda x,y: x-y, CSLIP2iListFinal,CSLIP2iMinusOneListFinal)

		CalculatedData1=map(lambda w,x,y,z: math.sqrt((w*y)**2+(x*z)**2), CSHEAR1iListFinal, CSHEAR2iListFinal, A, B)

		for secondindex in range(len(CalculatedData1)):

			CalculatedData1currentFrame=CalculatedData1currentFrame+((CalculatedData1[secondindex],),)

		CalculatedData2=map(lambda x,y: math.sqrt(x**2+y**2), A,B)

		for secondindex in range(len(CalculatedData2)):

			CalculatedData2currentFrame=CalculatedData2currentFrame+((CalculatedData2[secondindex],),)

	if 	zerothindex==0:

		for thirdindex in range(0,len(CalculatedData1currentFrame)):

		    CalculatedData1Sum.append(CalculatedData1currentFrame[thirdindex][0])

	else:

		for thirdindex in range(0,len(CalculatedData1currentFrame)):

		    CalculatedData1Sum[thirdindex]=CalculatedData1Sum[thirdindex]+CalculatedData1currentFrame[thirdindex][0]

	if 	zerothindex==0:

		for thirdindex in range(0,len(CalculatedData2currentFrame)):

		    CalculatedData2Sum.append(CalculatedData2currentFrame[thirdindex][0])

	else:

		for thirdindex in range(0,len(CalculatedData2currentFrame)):

		    CalculatedData2Sum[thirdindex]=CalculatedData2Sum[thirdindex]+CalculatedData2currentFrame[thirdindex][0]

	OdbToWrite= openOdb(path=OdbToWriteName, readOnly=False)

	instance1=OdbToWrite.rootAssembly.instances['PART-1-1']

	OdbToWriteStepName=StepNamei+"-"+StepNameiMinusOne

	#  Create a step and a frame.
	step1 = OdbToWrite.Step(name=OdbToWriteStepName,
		description=OdbToWriteStepName,
		domain=TIME, timePeriod=1.0)

	analysisTime=0.0

	frameFinal = step1.Frame(incrementNumber=0,
		frameValue=analysisTime,
		description='Step Time= '+str(analysisTime))

	#  Write nodal calculated Data 1
	uField = frameFinal.FieldOutput(name='RUIZ PARAMETER',
		description='RUIZ PARAMETER', type=SCALAR)

	uField.addData(position=NODAL, instance=instance1,
		labels=nodeLabelData,
		data=CalculatedData1Zero)

	#  Write nodal calculated Data 2
	uField = frameFinal.FieldOutput(name='RELATIVE SLIP',
		description='RELATIVE SLIP', type=SCALAR)

	uField.addData(position=NODAL, instance=instance1,
		labels=nodeLabelData,
		data=CalculatedData2Zero)

	analysisTime=1.0

	frameFinal = step1.Frame(incrementNumber=1,
		frameValue=analysisTime,
		description='Step Time= '+str(analysisTime))

	#  Write nodal calculated Data 1
	uField = frameFinal.FieldOutput(name='RUIZ PARAMETER',
		description='RUIZ PARAMETER', type=SCALAR)

	uField.addData(position=NODAL, instance=instance1,
		labels=nodeLabelData,
		data=CalculatedData1currentFrame)

	#  Write nodal calculated Data 2
	uField = frameFinal.FieldOutput(name='RELATIVE SLIP',
		description='RELATIVE SLIP', type=SCALAR)

	uField.addData(position=NODAL, instance=instance1,
		labels=nodeLabelData,
		data=CalculatedData2currentFrame)

for fourthindex in range(0,len(CalculatedData1Sum)):
	CalculatedData1SumTuple=CalculatedData1SumTuple+((CalculatedData1Sum[fourthindex],),)

for fourthindex in range(0,len(CalculatedData2Sum)):
	CalculatedData2SumTuple=CalculatedData2SumTuple+((CalculatedData2Sum[fourthindex],),)

#  Create a step and a frame
step1 = OdbToWrite.Step(name='Total Results',
	description='Total Results',
	domain=TIME, timePeriod=1.0)

analysisTime=0.0

frameFinal = step1.Frame(incrementNumber=0,
	frameValue=analysisTime,
	description='Step Time= '+str(analysisTime))

#  Write nodal calculated Data 1
uField = frameFinal.FieldOutput(name='RUIZ PARAMETER SUM',
	description='RUIZ PARAMETER SUM', type=SCALAR)

uField.addData(position=NODAL, instance=instance1,
	labels=nodeLabelData,
	data=CalculatedData1Zero)

#  Write nodal calculated Data 2
uField = frameFinal.FieldOutput(name='RELATIVE SLIP SUM',
	description='RELATIVE SLIP SUM', type=SCALAR)

uField.addData(position=NODAL, instance=instance1,
	labels=nodeLabelData,
	data=CalculatedData2Zero)

analysisTime=1.0

frameFinal = step1.Frame(incrementNumber=1,
	frameValue=analysisTime,
	description='Step Time= '+str(analysisTime))

#  Write nodal calculated Data 1
uField = frameFinal.FieldOutput(name='RUIZ PARAMETER SUM',
	description='RUIZ PARAMETER SUM', type=SCALAR)

uField.addData(position=NODAL, instance=instance1,
	labels=nodeLabelData,
	data=CalculatedData1SumTuple)

#  Write nodal calculated Data 2
uField = frameFinal.FieldOutput(name='RELATIVE SLIP SUM',
	description='RELATIVE SLIP SUM', type=SCALAR)

uField.addData(position=NODAL, instance=instance1,
	labels=nodeLabelData,
	data=CalculatedData2SumTuple)

OdbToWrite.save()
OdbToWrite.close()

OdbToRead.close()

end = time.clock()

TimeTaken=end - start

with open('Time_Taken_By_Script_In_Seconds.txt', 'a') as myfile:
	myfile.write('Time taken by script in seconds is: '+str(TimeTaken) +'\n')
	myfile.close
