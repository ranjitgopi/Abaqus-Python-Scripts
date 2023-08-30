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

import csv
import time
import pickle
import os

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

OdbToWrite= openOdb(path=OdbToWriteName, readOnly=False)

instance1=OdbToWrite.rootAssembly.instances['PART-1-1']

OdbToWriteStepName=OdbToReadStepName

step1=OdbToWrite.steps[OdbToWriteStepName]

fileObject = open('NumberofFrames','r')
NumberofFrames = pickle.load(fileObject)
fileObject.close()

fileObject = open('nodeLabelData','r')
nodeLabelData = pickle.load(fileObject)
fileObject.close()

for frame in range(1,NumberofFrames):

	fileObject = open('frameTimeData'+str(frame),'r')
	frameTimeData= pickle.load(fileObject)
	fileObject.close()

	fileObject = open('dispDatacurrentFrame'+str(frame),'r')
	dispDatacurrentFrame = pickle.load(fileObject)
	fileObject.close()

	fileObject = open('accDatacurrentFrame'+str(frame),'r')
	accDatacurrentFrame = pickle.load(fileObject)
	fileObject.close()

	analysisTime=frameTimeData

	frameFinal = step1.Frame(incrementNumber=int(frame),
		frameValue=analysisTime,
		description='Step Time= '+str(analysisTime))

	#  Write nodal Displacement vector components U1, U2 and U3
	uField = frameFinal.FieldOutput(name='U',
		description='Displacement', type=VECTOR)

	uField.addData(position=NODAL, instance=instance1,
		labels=nodeLabelData,
		data=dispDatacurrentFrame)

	#  Write nodal acceleration vector components A1, A2 and A3
	uField = frameFinal.FieldOutput(name='A',
		description='Acceleration', type=VECTOR)

	uField.addData(position=NODAL, instance=instance1,
		labels=nodeLabelData,
		data=accDatacurrentFrame)

OdbToWrite.save()
OdbToWrite.close()

os.remove('NumberofFrames')
os.remove('nodeLabelData')

for frame in range(1,NumberofFrames):
	os.remove('frameTimeData'+str(frame))
	os.remove('dispDatacurrentFrame'+str(frame))
	os.remove('accDatacurrentFrame'+str(frame))

end = time.clock()

TimeTaken=end - start

with open('Time_Taken_By_Script_'+'ODBResultsTransferNewerToOlderVersionWrite.py'+'_InSeconds.txt', 'a') as myfile:
	myfile.write('Time taken by script in seconds is: '+str(TimeTaken) +'\n')
	myfile.close
