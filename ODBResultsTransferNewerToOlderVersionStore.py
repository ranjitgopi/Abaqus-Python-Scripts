"""
This script transfers nodal displacement, velocity and acceleration results from one ODB which is higher version to another older version.

FIRST RUN ODBResultsTransferNewerToOlderVersionStore.py (in HIGHER VERSION OF ABAQUS), then run ODBResultsTransferNewerToOlderVersionWrite.py (IN LOWER VERSION OF ABAQUS)

Revision history:
REV-00 (15th August 2019): 1st release
REV-01 (16th August 2019): Added capability for Velocity and Acceleration in addition to Displacement
REV-02 (18th August 2019): (1) Improved efficiency
						   (2) Added capability to handle multiple frames
REV-03 (22nd August 2019): (1) Improved efficiency
						   (2) Removed un-necessary fields of storage
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
import csv
import pickle

start = time.clock()

# Reading all the input values from a csv file
with open('INPUTS.csv', 'r') as f:
	reader = csv.reader(f)
	count= 0
	for row in reader:
		# FieldName
		if count == 0:
			OdbToReadName =row[1]+'.odb'
		if count == 1:
			OdbToReadStepName = row[1]
		if count == 2:
			OdbToWriteName=row[1]+'.odb'
		count =count + 1

OdbToRead = openOdb(path=OdbToReadName, readOnly=True)

StepOfInterest = OdbToRead.steps[OdbToReadStepName]

NumberofFrames=len(OdbToRead.steps[OdbToReadStepName].frames)

fileObject = open('NumberofFrames','wb')
pickle.dump(NumberofFrames,fileObject)
fileObject.close()

NodeSetOfInterest=OdbToRead.rootAssembly.instances['PART-1-1'] #ANY ORPHAN INPUT FILE CREATED BY ANSA OR HYPERMESH WILL HAVE DEFAULT INSTANCE NAME PART-1-1 IN ABAQUS

nodeLabelData=()

for node in (NodeSetOfInterest.nodes):

	currentnodelabel=node.label

	nodeLabelData=nodeLabelData+(currentnodelabel,)

fileObject = open('nodeLabelData','wb')
pickle.dump(nodeLabelData,fileObject)
fileObject.close()

for frame in range(1,NumberofFrames):

	currentFrame = OdbToRead.steps[OdbToReadStepName].frames[frame]

	frameTime= currentFrame.frameValue

	fileObject = open('frameTimeData'+str(frame),'wb')
	pickle.dump(frameTime,fileObject)
	fileObject.close()

	U= currentFrame.fieldOutputs['U'].values
	A= currentFrame.fieldOutputs['A'].values

	dispDatacurrentFrame=()

	accDatacurrentFrame=()

	for value in (U):

		dispDatacurrentFrame=dispDatacurrentFrame+((value.data[0],value.data[1],value.data[2]),)

	for value in (A):

		accDatacurrentFrame=accDatacurrentFrame+((value.data[0],value.data[1],value.data[2]),)

	fileObject = open('dispDatacurrentFrame'+str(frame),'wb')
	pickle.dump(dispDatacurrentFrame,fileObject)
	fileObject.close()

	fileObject = open('accDatacurrentFrame'+str(frame),'wb')
	pickle.dump(accDatacurrentFrame,fileObject)
	fileObject.close()

OdbToRead.close()

end = time.clock()

TimeTaken=end - start

with open('Time_Taken_By_Script_'+'ODBResultsTransferNewerToOlderVersionStore.py'+'_InSeconds.txt', 'a') as myfile:
	myfile.write('Time taken by script in seconds is: '+str(TimeTaken) +'\n')
	myfile.close
