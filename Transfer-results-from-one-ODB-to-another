"""
This script transfers nodal displacement and stress results from one ODB to another.

Run this script in 2 ways:

1. Open Abaqus Viewer > File > Run Script > ODBResultsTransfer.py (Your Abaqus version should be same the version of original ODB)
2. Open Command Prompt > Run command > abq2018 CAE noGUI=ODBResultsTransfer.py (Your Abaqus version should be same the version of original ODB

Notes:

1. Original ODB and INP for datacheck should be the working directory when using Abaqus Viewer or you should go to the the directory when using command prompt

Revision history:
REV-00 (10th August 2019): 1st release
REV-01 (11th August 2019): Modified for better efficiency; Added capability to delete MDL, PRT, RES and STT files of Datacheck ODB to save disk space
"""

from odbAccess import *
from abaqusConstants import *

import time
import os

start = time.clock()

OdbToRead = openOdb(path='BoltedFlange.odb', readOnly=True) #ENTER NAME OF ORIGINAL ODB TO READ FROM WHICH RESULTS NEED TO BE READ

StepName = 'Tighten bolts' #ENTER STEP NAME OF INTEREST OF ORIGINAL ODB FROM WHICH RESULTS NEED TO BE READ

FrameNumber=11 #ENTER FRAME NUMBER IN STEP

SetName= 'BOTFLANGE_ALL' #ENTER SET NAME FOR WHICH RESULTS NEED TO TRANSFERRED

DataCheckJob='BoltedFlange-Rotated' #ENTER NAME OF MODIFIED INPUT FILE USING WHICH ODB WILL BE CREATED BY DATACHECK & THE RESULTS WILL BE TRANSFERRED

StepOfInterest = OdbToRead.steps[StepName]

currentFrame = OdbToRead.steps[StepName].frames[FrameNumber]

NodeSetOfInterest=OdbToRead.rootAssembly.instances['PART-1-1'].nodeSets[SetName] #ANY ORPHAN INPUT FILE CREATED BY ANSA OR HYPERMESH WILL HAVE DEFAULT INSTANCE NAME PART-1-1 IN ABAQUS

nodeLabelData=()

for node in (NodeSetOfInterest.nodes):
	currentnodelabel=node.label
	nodeLabelData=nodeLabelData+(currentnodelabel,)

dispDatacurrentFrame=()

for nodeLabel in (nodeLabelData):

	NodeOfInterest =  OdbToRead.rootAssembly.instances['PART-1-1'].getNodeFromLabel(nodeLabel)

	U1= currentFrame.fieldOutputs['U'].getSubset(region=NodeOfInterest).values[0].data[0]
	U2= currentFrame.fieldOutputs['U'].getSubset(region=NodeOfInterest).values[0].data[1]
	U3= currentFrame.fieldOutputs['U'].getSubset(region=NodeOfInterest).values[0].data[2]

	dispDatacurrentFrame=dispDatacurrentFrame+((U1,U2,U3),)

ElementSetOfInterest=OdbToRead.rootAssembly.instances['PART-1-1'].elementSets[SetName]

elementLabelData=()

for element in (ElementSetOfInterest.elements):
	currentelementlabel=element.label
	elementLabelData=elementLabelData+(currentelementlabel,)

stressDatacurrentFrame=()

for elementLabel in (elementLabelData):

	ElementOfInterest =  OdbToRead.rootAssembly.instances['PART-1-1'].getElementFromLabel(elementLabel)

	StressOfInterest=currentFrame.fieldOutputs['S'].getSubset(region=ElementOfInterest)

	for value in (StressOfInterest.values):

		S11= value.data[0]
		S22= value.data[1]
		S33= value.data[2]
		S12= value.data[3]
		S13= value.data[4]
		S23= value.data[5]

		stressDatacurrentFrame=stressDatacurrentFrame+((S11,S22,S33,S12,S13,S23),)

OdbToRead.close()

from job import *

DataCheckInputfile = DataCheckJob+'.inp'

DataCheckOdb=DataCheckJob+'.odb'

DataCheckStt=DataCheckJob+'.stt'
DataCheckRes=DataCheckJob+'.res'
DataCheckMdl=DataCheckJob+'.mdl'
DatacheckPrt=DataCheckJob+'.prt'

mdb.JobFromInputFile(name=DataCheckJob,inputFileName=DataCheckInputfile)

mdb.jobs[DataCheckJob].submit(datacheckJob=True)

mdb.jobs[DataCheckJob].waitForCompletion()

OdbToWrite= openOdb(path=DataCheckOdb, readOnly=False)

instance1=OdbToWrite.rootAssembly.instances['PART-1-1']

analysisTime=1.0

step1=OdbToWrite.steps[StepName]

frame = step1.Frame(incrementNumber=1,
	frameValue=analysisTime,
	description=\
		'Final Frame')

#  Write nodal displacements.
uField = frame.FieldOutput(name='U',
	description='Displacement', type=VECTOR)

uField.addData(position=NODAL, instance=instance1,
	labels=nodeLabelData,
	data=dispDatacurrentFrame)

#  Write stress
sField = frame.FieldOutput(name='S',
    description='Stress', type=TENSOR_3D_FULL,
    componentLabels=('S11', 'S22', 'S33', 'S12', 'S13', 'S23'),
    validInvariants=(MISES,))

sField.addData(position=INTEGRATION_POINT, instance=instance1,
   labels=elementLabelData, data=stressDatacurrentFrame)

OdbToWrite.save()
OdbToWrite.close()

os.remove(DataCheckStt)
os.remove(DataCheckRes)
os.remove(DataCheckMdl)
os.remove(DatacheckPrt)

end = time.clock()

TimeTaken=end - start

with open('TimeTakenByScriptInSeconds.txt', 'a') as myfile:
	myfile.write('Time taken by script in seconds is: '+str(TimeTaken) +'\n')
	myfile.close
