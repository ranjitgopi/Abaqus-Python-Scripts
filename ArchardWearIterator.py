"""
ArchardWearIterator.py

This script implements Archard's wear equation using Abaqus Python Scripting.

This script is made to work for input files with orphan meshes created using 3rd party pre-processors.

This script is an alternative in some aspects to the FORTRAN user-subroutine UMESHMOTION for the same work-flow.

The workflow implemented in the script is as follows:

1. For a model, the script obtains results of contact pressure and slip for the required contact pair from the ODB
2. Using these outputs, the script calculates Archad's wear using the input dimensional Archard wear coefficient and stores it as field output
3. The script then imports the final ODB as an input file, edits the input file for those nodes by subtracting calculated wear in the required direction (along normal direction using CNORMF)
   hence creating a new input file with wear included. The user will have to import Stress results from original ODB if further analysis is to be performed.

PROCEDURE:
1. You should have the ODB and INP in the same folder
2. Enter required inputs below as shown
3. Open Abaqus CAE and go to File > Run Script > Locate the script and run
   OR go to command line and go to directory where ODB and INP exisits and run abq2020 cae nogui=Script.py

NOTES:
1. You can test the script with attached Blocks.inp or BallJoint.inp after submitting the job and obtaining the ODB
2. You should have COORD, CDISP, CPRESS and CNORMF field outputs requested for script to work

Revision history:
REV-00: 1st June 2018: First release
REV-01: 9th July 2020: Modified workflow
REV-02: 10th July 2020: Modified workflow for moving wear direction
REV-03: 11th July 2020: House-keeping, fixed some bugs, refined moving direction wear implementation
REV-04: 9th March 2022: Added increment time to wear calculation
REV-05: 10th March 2022: Some house-keeping

Author:
Ranjit Gopi
SIMULIA India Industry Process Consultant
Simulia India Support Frontdesk:+91 44 43443000
Simulia India Support Email: simulia.in.support@3ds.com
"""

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~OBTAIN INPUTS HERE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
x = getInputs((('Enter INP OR ODB NAME', 'JobName'),
               ('Enter Step Name for which wear is to be calculated', 'StepName'),
               ('Enter ALL for wear to be calculated for all frames or LAST for calculation for only last frame of step', 'ALL'),
               ('Enter Node set of contact pair for which wear is to be calculated', 'NodeSetName'),
               ('Enter kd, Dimensional Archard wear coefficient mm2/N', 'kD'),
               ))

JobName=x[0]
WearingStepName=x[1]
FramesForWhichWearToBeCalculated=x[2]
NodeSetName=x[3]
kD=float(x[4])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~INPUTS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ENTER INPUTS OLD DO NOT USE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#JobName='BallJoint'                      #Input INP/ODB name
#WearingStepName='PullAndRotate'          #Step for which wear is to be calculated
#FramesForWhichWearToBeCalculated='ALL'  #Enter 'ALL' for all frames or 'LAST' for last frame of step
#NodeSetName='SEAT-NODES'                 #Node set of contact pair for which wear is to be calculated
#kD=1e-5                                  #Dimensional Archard wear coefficient mm2/N
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ENTER INPUTS OLD DO NOT USE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

from abaqus import*
from abaqusConstants import *
from odbAccess import *
import os
from shutil import copyfile
import math

def StatisticsPrintToFile1():
    with open('Statistics.txt', 'w') as myfile:
    	myfile.write( "" + '\n')
    	myfile.close

def StatisticsPrintToFile2():
    with open('Statistics.txt', 'a') as myfile:
        myfile.write( "node label=" +str(NodeLabel) + '\n')
        myfile.write("WEAR SUM=" + str(WEARSUM.getSubset(region=NodeOfInterest).values[0].data) + '\n')
        myfile.write("CNORMF Direction Magnitude=" +str(CNORMFMAGNITUDE) + '\n')
        myfile.write("CNORMF Direction X Component=" +str(CNORMFX) + '\n')
        myfile.write("CNORMF Direction X Unit Vector=" + str(CNORMFDirectionXUnitVector) + '\n')
        myfile.write("Old X Coordinate=" + str(COORDINATES.getSubset(region=NodeOfInterest).values[0].data[0]) + '\n')
        myfile.write("New X Coordinate=" + str(NewCOORDINATES1) + '\n')
        myfile.write("CNORMF Direction Y Component=" +str(CNORMFY) + '\n')
        myfile.write("CNORMF Direction Y Unit Vector=" + str(CNORMFDirectionYUnitVector) + '\n')
        myfile.write("Old Y Coordinate=" + str(COORDINATES.getSubset(region=NodeOfInterest).values[0].data[1]) + '\n')
        myfile.write("New Y Coordinate=" + str(NewCOORDINATES2) + '\n')
        myfile.write("CNORMF Direction Z Component=" +str(CNORMFZ) + '\n')
        myfile.write("CNORMF Direction Z Unit Vector=" + str(CNORMFDirectionZUnitVector) + '\n')
        myfile.write("Old Z Coordinate=" + str(COORDINATES.getSubset(region=NodeOfInterest).values[0].data[2]) + '\n')
        myfile.write("New Z Coordinate=" + str(NewCOORDINATES3) + '\n')
        myfile.close

def StatisticsPrintToFile3():
    with open('Statistics.txt', 'a') as myfile:
    	myfile.write("before values"+str(line) + '\n')
        myfile.write("after values"+str(line_list) + '\n')
    	myfile.close

StatisticsPrintToFile1()

copyfile(JobName+'.odb',JobName+'WithWearCalculation.odb')

originalodb=openOdb(path=JobName+'.odb', readOnly=True)

odb = openOdb(path=JobName+'WithWearCalculation.odb', readOnly=False)

NodeSetOfSlidingNodes = odb.rootAssembly.instances['PART-1-1'].nodeSets[NodeSetName]
nodeLabelData=()
for node in (NodeSetOfSlidingNodes.nodes):
    nodeLabelData=nodeLabelData+(node.label,)

step=odb.steps[WearingStepName]
NumberOfFrames=len(step.frames)

for firstindex in range(1,NumberOfFrames):

    currentFramei=step.frames[firstindex]
    currentFrameiMinusOne=step.frames[firstindex-1]

    IncrementTimeDelta=currentFramei.frameValue - currentFrameiMinusOne.frameValue

    CSLIP1iNodeList=[]
    CSLIP1iList=[]
    CSLIP1iListFinal=[]

    CSLIP2iNodeList=[]
    CSLIP2iList=[]
    CSLIP2iListFinal=[]

    CSLIP1iMinusOneNodeList=[]
    CSLIP1iMinusOneList=[]
    CSLIP1iMinusOneListFinal=[]

    CSLIP2iMinusOneNodeList=[]
    CSLIP2iMinusOneList=[]
    CSLIP2iMinusOneListFinal=[]

    CPRESSiNodeList=[]
    CPRESSiList=[]
    CPRESSiListFinal=[]

    CPRESSiMinusOneNodeList=[]
    CPRESSiMinusOneList=[]
    CPRESSiMinusOneListFinal=[]

    CSLIP1i =   currentFramei.fieldOutputs['CSLIP1'].getSubset(region=NodeSetOfSlidingNodes)
    for value in (CSLIP1i.values):
        CSLIP1iNodeList.append(value.nodeLabel)
        CSLIP1iList.append(value.data)

    CSLIP1iDictUnSorted = {}

    for secondindex in range(len(CSLIP1iNodeList)):
            CSLIP1iDictUnSorted[CSLIP1iNodeList[secondindex]] = CSLIP1iList[secondindex]

    for node in (NodeSetOfSlidingNodes.nodes):
        if node.label not in CSLIP1iDictUnSorted.keys():
            CSLIP1iDictUnSorted[node.label]=0.0

    CSLIP1iListofDict=list(CSLIP1iDictUnSorted.items())
    CSLIP1iListofDict.sort()

    for secondindex in range(len(CSLIP1iListofDict)):
        CSLIP1iListFinal.append(CSLIP1iListofDict[secondindex][1])

    CSLIP1iMinusOne =   currentFrameiMinusOne.fieldOutputs['CSLIP1'].getSubset(region=NodeSetOfSlidingNodes)
    for value in (CSLIP1iMinusOne.values):
        CSLIP1iMinusOneNodeList.append(value.nodeLabel)
        CSLIP1iMinusOneList.append(value.data)

    CSLIP1iMinusOneDictUnSorted = {}

    for secondindex in range(len(CSLIP1iMinusOneNodeList)):
            CSLIP1iMinusOneDictUnSorted[CSLIP1iMinusOneNodeList[secondindex]] = CSLIP1iMinusOneList[secondindex]

    for node in (NodeSetOfSlidingNodes.nodes):
        if node.label not in CSLIP1iMinusOneDictUnSorted.keys():
            CSLIP1iMinusOneDictUnSorted[node.label]=0.0

    CSLIP1iMinusOneListofDict=list(CSLIP1iMinusOneDictUnSorted.items())
    CSLIP1iMinusOneListofDict.sort()

    for secondindex in range(len(CSLIP1iMinusOneListofDict)):
        CSLIP1iMinusOneListFinal.append(CSLIP1iMinusOneListofDict[secondindex][1])

    CSLIP1DELTA=map(lambda x,y: x-y, CSLIP1iListFinal,CSLIP1iMinusOneListFinal)

    CSLIP1DELTATuple=()
    for secondindex in range(len(CSLIP1DELTA)):
        CSLIP1DELTATuple=CSLIP1DELTATuple+((CSLIP1DELTA[secondindex],),)

    CSLIP2i =   currentFramei.fieldOutputs['CSLIP2'].getSubset(region=NodeSetOfSlidingNodes)
    for value in (CSLIP2i.values):
        CSLIP2iNodeList.append(value.nodeLabel)
        CSLIP2iList.append(value.data)

    CSLIP2iDictUnSorted = {}

    for secondindex in range(len(CSLIP2iNodeList)):
            CSLIP2iDictUnSorted[CSLIP2iNodeList[secondindex]] = CSLIP2iList[secondindex]

    for node in (NodeSetOfSlidingNodes.nodes):
        if node.label not in CSLIP2iDictUnSorted.keys():
            CSLIP2iDictUnSorted[node.label]=0.0

    CSLIP2iListofDict=list(CSLIP2iDictUnSorted.items())
    CSLIP2iListofDict.sort()

    for secondindex in range(len(CSLIP2iListofDict)):
        CSLIP2iListFinal.append(CSLIP2iListofDict[secondindex][1])

    CSLIP2iMinusOne =   currentFrameiMinusOne.fieldOutputs['CSLIP2'].getSubset(region=NodeSetOfSlidingNodes)
    for value in (CSLIP2iMinusOne.values):
        CSLIP2iMinusOneNodeList.append(value.nodeLabel)
        CSLIP2iMinusOneList.append(value.data)

    CSLIP2iMinusOneDictUnSorted = {}

    for secondindex in range(len(CSLIP2iMinusOneNodeList)):
            CSLIP2iMinusOneDictUnSorted[CSLIP2iMinusOneNodeList[secondindex]] = CSLIP2iMinusOneList[secondindex]

    for node in (NodeSetOfSlidingNodes.nodes):
        if node.label not in CSLIP2iMinusOneDictUnSorted.keys():
            CSLIP2iMinusOneDictUnSorted[node.label]=0.0

    CSLIP2iMinusOneListofDict=list(CSLIP2iMinusOneDictUnSorted.items())
    CSLIP2iMinusOneListofDict.sort()

    for secondindex in range(len(CSLIP2iMinusOneListofDict)):
        CSLIP2iMinusOneListFinal.append(CSLIP2iMinusOneListofDict[secondindex][1])

    CSLIP2DELTA=map(lambda x,y: x-y, CSLIP2iListFinal,CSLIP2iMinusOneListFinal)

    CSLIP2DELTATuple=()
    for secondindex in range(len(CSLIP2DELTA)):
        CSLIP2DELTATuple=CSLIP2DELTATuple+((CSLIP2DELTA[secondindex],),)

    RESULTANTCSLIPDELTA=map(lambda x,y: math.sqrt((x**2)+(y**2)), CSLIP1DELTA, CSLIP2DELTA)

    RESULTANTCSLIPDELTATuple=()
    for secondindex in range(len(RESULTANTCSLIPDELTA)):
        RESULTANTCSLIPDELTATuple=RESULTANTCSLIPDELTATuple+((RESULTANTCSLIPDELTA[secondindex],),)

    CPRESSi =   currentFramei.fieldOutputs['CPRESS'].getSubset(region=NodeSetOfSlidingNodes)
    for value in (CPRESSi.values):
        CPRESSiNodeList.append(value.nodeLabel)
        CPRESSiList.append(value.data)

    CPRESSiDictUnSorted = {}

    for secondindex in range(len(CPRESSiNodeList)):
            CPRESSiDictUnSorted[CPRESSiNodeList[secondindex]] = CPRESSiList[secondindex]

    for node in (NodeSetOfSlidingNodes.nodes):
        if node.label not in CPRESSiDictUnSorted.keys():
            CPRESSiDictUnSorted[node.label]=0.0

    CPRESSiListofDict=list(CPRESSiDictUnSorted.items())
    CPRESSiListofDict.sort()

    for secondindex in range(len(CPRESSiListofDict)):
        CPRESSiListFinal.append(CPRESSiListofDict[secondindex][1])

    CPRESSiMinusOne =   currentFrameiMinusOne.fieldOutputs['CPRESS'].getSubset(region=NodeSetOfSlidingNodes)
    for value in (CPRESSiMinusOne.values):
        CPRESSiMinusOneNodeList.append(value.nodeLabel)
        CPRESSiMinusOneList.append(value.data)

    CPRESSiMinusOneDictUnSorted = {}

    for secondindex in range(len(CPRESSiMinusOneNodeList)):
            CPRESSiMinusOneDictUnSorted[CPRESSiMinusOneNodeList[secondindex]] = CPRESSiMinusOneList[secondindex]

    for node in (NodeSetOfSlidingNodes.nodes):
        if node.label not in CPRESSiMinusOneDictUnSorted.keys():
            CPRESSiMinusOneDictUnSorted[node.label]=0.0

    CPRESSiMinusOneListofDict=list(CPRESSiMinusOneDictUnSorted.items())
    CPRESSiMinusOneListofDict.sort()

    for secondindex in range(len(CPRESSiMinusOneListofDict)):
        CPRESSiMinusOneListFinal.append(CPRESSiMinusOneListofDict[secondindex][1])

    CPRESSAVERAGED=map(lambda x,y: 0.5*(x+y), CPRESSiListFinal,CPRESSiMinusOneListFinal)

    CPRESSAVERAGEDTuple=()
    for secondindex in range(len(CPRESSAVERAGED)):
        CPRESSAVERAGEDTuple=CPRESSAVERAGEDTuple+((CPRESSAVERAGED[secondindex],),)

    instance=odb.rootAssembly.instances['PART-1-1']
    uField = currentFramei.FieldOutput(name='CSLIP1DELTA', description='DIFFERENCE IN CSLIP1 FROM CURRENT FRAME AND PREVIOUS FRAME', type=SCALAR)
    uField.addData(position=NODAL, instance=instance,    	labels=nodeLabelData,    	data=CSLIP1DELTATuple)

    instance=odb.rootAssembly.instances['PART-1-1']
    uField = currentFramei.FieldOutput(name='CSLIP2DELTA', description='DIFFERENCE IN CSLIP2 FROM CURRENT FRAME AND PREVIOUS FRAME', type=SCALAR)
    uField.addData(position=NODAL, instance=instance,    	labels=nodeLabelData,    	data=CSLIP2DELTATuple)

    instance=odb.rootAssembly.instances['PART-1-1']
    uField = currentFramei.FieldOutput(name='RESULTANTCSLIPDELTA', description='RESULTANT CSLIP FROM CURRENT FRAME AND PREVIOUS FRAME', type=SCALAR)
    uField.addData(position=NODAL, instance=instance,    	labels=nodeLabelData,    	data=RESULTANTCSLIPDELTATuple)

    instance=odb.rootAssembly.instances['PART-1-1']
    uField = currentFramei.FieldOutput(name='CPRESS_AVERAGED', description='AVERAGED CPRESS FROM CURRENT FRAME AND PREVIOUS FRAME', type=SCALAR)
    uField.addData(position=NODAL, instance=instance,    	labels=nodeLabelData,    	data=CPRESSAVERAGEDTuple)

for index in range(1,NumberOfFrames):

   Currentframe=step.frames[index]

   AVERAGED_CONTACT_PRESSURE= step.frames[index].fieldOutputs['CPRESS_AVERAGED'].getSubset(region=NodeSetOfSlidingNodes)
   RESULANT_SLIPPING_DISTANCE=step.frames[index].fieldOutputs['RESULTANTCSLIPDELTA'].getSubset(region=NodeSetOfSlidingNodes)
   AVG_CONTACT_PRESSURE_MULTIPLIED_RESULTANT_SLIP_DISTANCE=(AVERAGED_CONTACT_PRESSURE*RESULANT_SLIPPING_DISTANCE)
   NewFieldOutput = Currentframe.FieldOutput(name='AVG_CONTACT_PRESSURE_MULTIPLIED_RESULTANT_SLIP_DISTANCE', description='Averaged CONTACT PRESSURE multiplied by RESULTANT CSLIP', field=AVG_CONTACT_PRESSURE_MULTIPLIED_RESULTANT_SLIP_DISTANCE)

ARCHARDWEARSUM=0.0

for index in range(1,NumberOfFrames):

   Currentframe=step.frames[index]

   AVG_CONTACT_PRESSURE_MULTIPLIED_RESULTANT_SLIP_DISTANCE=step.frames[index].fieldOutputs['AVG_CONTACT_PRESSURE_MULTIPLIED_RESULTANT_SLIP_DISTANCE'].getSubset(region=NodeSetOfSlidingNodes)

   #Archard Wear equation = Contact Pressure * Slip Velocity
   #Slip Velocity = Resultant Slip Distance/ Time of Increment 
   ARCHARDWEAR=(AVG_CONTACT_PRESSURE_MULTIPLIED_RESULTANT_SLIP_DISTANCE*kD)/IncrementTimeDelta
   ARCHARDWEARSUM=ARCHARDWEARSUM+ARCHARDWEAR

   NewFieldOutput = Currentframe.FieldOutput(name='ARCHARDWEAR', description='Archard WEAR calculated from Averaged CPRESS and Resultant CSLIP', field=ARCHARDWEAR)
   NewFieldOutput = Currentframe.FieldOutput(name='ARCHARDWEARSUM', description='Sum of Archard WEAR', field=ARCHARDWEARSUM)

if FramesForWhichWearToBeCalculated=='ALL':

    for frameindex in range(1,NumberOfFrames):

        print 'Frame number:' +str(frameindex)

        COORDINATES= step.frames[frameindex].fieldOutputs['COORD'].getSubset(region=NodeSetOfSlidingNodes)
        WEARSUM= step.frames[frameindex].fieldOutputs['ARCHARDWEARSUM'].getSubset(region=NodeSetOfSlidingNodes)
        CNORMF= step.frames[frameindex].fieldOutputs['CNORMF'].getSubset(region=NodeSetOfSlidingNodes)

        NEWCOORDINATES1DICTIONARY={}
        NEWCOORDINATES2DICTIONARY={}
        NEWCOORDINATES3DICTIONARY={}

        for index in range(len(COORDINATES.values)):

            NodeLabel = COORDINATES.values[index].nodeLabel

            NodeOfInterest =  odb.rootAssembly.instances['PART-1-1'].getNodeFromLabel(NodeLabel)

            try:
                CNORMFX=CNORMF.getSubset(region=NodeOfInterest).values[-1].data[0]
            except:
                CNORMFX=0.0

            try:
                CNORMFY=CNORMF.getSubset(region=NodeOfInterest).values[-1].data[1]
            except:
                CNORMFY=0.0

            try:
                CNORMFZ=CNORMF.getSubset(region=NodeOfInterest).values[-1].data[2]
            except:
                CNORMFZ=0.0

            try:
                CNORMFMAGNITUDE=CNORMF.getSubset(region=NodeOfInterest).values[-1].magnitude
            except:
                CNORMFMAGNITUDE=0.0

            try:
                CNORMFDirectionXUnitVector=CNORMFX/CNORMFMAGNITUDE
            except:
                CNORMFDirectionXUnitVector=0.0

            NewCOORDINATES1 = COORDINATES.getSubset(region=NodeOfInterest).values[0].data[0] + (WEARSUM.getSubset(region=NodeOfInterest).values[0].data)*(CNORMFDirectionXUnitVector)
            NEWCOORDINATES1DICTIONARY[NodeLabel] = NewCOORDINATES1

            try:
                CNORMFDirectionYUnitVector=CNORMFY/CNORMFMAGNITUDE
            except:
                CNORMFDirectionYUnitVector=0.0

            NewCOORDINATES2 = COORDINATES.getSubset(region=NodeOfInterest).values[0].data[1] + (WEARSUM.getSubset(region=NodeOfInterest).values[0].data)*(CNORMFDirectionYUnitVector)
            NEWCOORDINATES2DICTIONARY[NodeLabel] = NewCOORDINATES2

            try:
                CNORMFDirectionZUnitVector=CNORMFZ/CNORMFMAGNITUDE
            except:
                CNORMFDirectionZUnitVector=0.0

            NewCOORDINATES3 = COORDINATES.getSubset(region=NodeOfInterest).values[0].data[2] + (WEARSUM.getSubset(region=NodeOfInterest).values[0].data)*(CNORMFDirectionZUnitVector)
            NEWCOORDINATES3DICTIONARY[NodeLabel] = NewCOORDINATES3

            StatisticsPrintToFile2()

        stepnumber=originalodb.steps[WearingStepName].number - 1
        mdb.Model(name=JobName, modelType=STANDARD_EXPLICIT)
        p = mdb.models[JobName].PartFromOdb(name='PART-1-1', instance='PART-1-1', odb=originalodb, shape=DEFORMED, step=stepnumber, frame=frameindex)
        a = mdb.models[JobName].rootAssembly
        p = mdb.models[JobName].parts['PART-1-1']
        a.Instance(name='PART-1-1-1', part=p, dependent=ON)

        mdb.Job(name=JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex), model=JobName)

        mdb.jobs[JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex)].writeInput(consistencyChecking=OFF)

        WriteFile = open(JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex)+'WithWear.inp','w+')

        with open (JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex)+'.inp', 'rt',) as InputFile:
            linecounter=0

            for line in InputFile: # Store each line in a string variable "line"

                line_list =line.split(',') # Split each line in line_list variable

                if line_list[0] == '*Node\n':
                    linecounter=linecounter+1

                if line_list[0] == '*Element':
                    linecounter=linecounter+1

                if len(line_list) == 4 and linecounter<2: # For lines under *Node having node data, after split(',') should contain a length of 4
                    try:
                        line_list = [float(i) for i in line_list] #By default values after Split is a string, convert to float
                    except:
                        print 'pass' #, line_list # Incase line_list contains a list of string previous line will throw an error
                    # Check if line_list[0], the node is in the NEWCOORDINATESDICTIONARY. If yes make changes.
                    if line_list[0] in NEWCOORDINATES1DICTIONARY.keys():
                        line_list[1] = NEWCOORDINATES1DICTIONARY[line_list[0]]
                        line_list[2] = NEWCOORDINATES2DICTIONARY[line_list[0]]
                        line_list[3] = NEWCOORDINATES3DICTIONARY[line_list[0]]
                        StatisticsPrintToFile3()
                        WriteFile.write('\t\t%s,\t\t%s,\t\t%s,\t\t%s\n'%(int(line_list[0]),line_list[1],line_list[2],line_list[3]))
                    else: # if not yes , then write the complete line to new INP
                        WriteFile.write(line)
                else: # if line_list! = 4 then write complete line to INP
                    WriteFile.write(line)

    #  After writing close the files
    InputFile.close()
    WriteFile.close()

else:

    frameindex=len(step.frames)-1

    COORDINATES= step.frames[frameindex].fieldOutputs['COORD'].getSubset(region=NodeSetOfSlidingNodes)
    WEARSUM= step.frames[frameindex].fieldOutputs['ARCHARDWEARSUM'].getSubset(region=NodeSetOfSlidingNodes)
    CNORMF= step.frames[frameindex].fieldOutputs['CNORMF'].getSubset(region=NodeSetOfSlidingNodes)

    NEWCOORDINATES1DICTIONARY={}
    NEWCOORDINATES2DICTIONARY={}
    NEWCOORDINATES3DICTIONARY={}

    for index in range(len(COORDINATES.values)):

        NodeLabel = COORDINATES.values[index].nodeLabel

        NodeOfInterest =  odb.rootAssembly.instances['PART-1-1'].getNodeFromLabel(NodeLabel)

        try:
            CNORMFX=CNORMF.getSubset(region=NodeOfInterest).values[-1].data[0]
        except:
            CNORMFX=0.0

        try:
            CNORMFY=CNORMF.getSubset(region=NodeOfInterest).values[-1].data[1]
        except:
            CNORMFY=0.0

        try:
            CNORMFZ=CNORMF.getSubset(region=NodeOfInterest).values[-1].data[2]
        except:
            CNORMFZ=0.0

        try:
            CNORMFMAGNITUDE=CNORMF.getSubset(region=NodeOfInterest).values[-1].magnitude
        except:
            CNORMFMAGNITUDE=0.0

        try:
            CNORMFDirectionXUnitVector=CNORMFX/CNORMFMAGNITUDE
        except:
            CNORMFDirectionXUnitVector=0.0

        NewCOORDINATES1 = COORDINATES.getSubset(region=NodeOfInterest).values[0].data[0] + (WEARSUM.getSubset(region=NodeOfInterest).values[0].data)*(CNORMFDirectionXUnitVector)
        NEWCOORDINATES1DICTIONARY[NodeLabel] = NewCOORDINATES1

        try:
            CNORMFDirectionYUnitVector=CNORMFY/CNORMFMAGNITUDE
        except:
            CNORMFDirectionYUnitVector=0.0

        NewCOORDINATES2 = COORDINATES.getSubset(region=NodeOfInterest).values[0].data[1] + (WEARSUM.getSubset(region=NodeOfInterest).values[0].data)*(CNORMFDirectionYUnitVector)
        NEWCOORDINATES2DICTIONARY[NodeLabel] = NewCOORDINATES2

        try:
            CNORMFDirectionZUnitVector=CNORMFZ/CNORMFMAGNITUDE
        except:
            CNORMFDirectionZUnitVector=0.0

        NewCOORDINATES3 = COORDINATES.getSubset(region=NodeOfInterest).values[0].data[2] + (WEARSUM.getSubset(region=NodeOfInterest).values[0].data)*(CNORMFDirectionZUnitVector)
        NEWCOORDINATES3DICTIONARY[NodeLabel] = NewCOORDINATES3

        StatisticsPrintToFile2()

    stepnumber=originalodb.steps[WearingStepName].number - 1
    mdb.Model(name=JobName, modelType=STANDARD_EXPLICIT)
    p = mdb.models[JobName].PartFromOdb(name='PART-1-1', instance='PART-1-1', odb=originalodb, shape=DEFORMED, step=stepnumber, frame=frameindex)
    a = mdb.models[JobName].rootAssembly
    p = mdb.models[JobName].parts['PART-1-1']
    a.Instance(name='PART-1-1-1', part=p, dependent=ON)

    mdb.Job(name=JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex), model=JobName)

    mdb.jobs[JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex)].writeInput(consistencyChecking=OFF)

    WriteFile = open(JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex)+'WithWear.inp','w+')

    with open (JobName+'Step'+WearingStepName+'AtFrame'+str(frameindex)+'.inp', 'rt',) as InputFile:
        linecounter=0

        for line in InputFile: # Store each line in a string variable "line"

            line_list =line.split(',') # Split each line in line_list variable

            if line_list[0] == '*Node\n':
                linecounter=linecounter+1

            if line_list[0] == '*Element':
                linecounter=linecounter+1

            if len(line_list) == 4 and linecounter<2: # For lines under *Node having node data, after split(',') should contain a length of 4
                try:
                    line_list = [float(i) for i in line_list] #By default values after Split is a string, convert to float
                except:
                    print 'pass' #, line_list # Incase line_list contains a list of string previous line will throw an error
                # Check if line_list[0], the node is in the NEWCOORDINATESDICTIONARY. If yes make changes.
                if line_list[0] in NEWCOORDINATES1DICTIONARY.keys():
                    line_list[1] = NEWCOORDINATES1DICTIONARY[line_list[0]]
                    line_list[2] = NEWCOORDINATES2DICTIONARY[line_list[0]]
                    line_list[3] = NEWCOORDINATES3DICTIONARY[line_list[0]]
                    StatisticsPrintToFile3()
                    WriteFile.write('\t\t%s,\t\t%s,\t\t%s,\t\t%s\n'%(int(line_list[0]),line_list[1],line_list[2],line_list[3]))
                else: # if not yes , then write the complete line to new INP
                    WriteFile.write(line)
            else: # if line_list! = 4 then write complete line to INP
                WriteFile.write(line)

    #  After writing close the files
    InputFile.close()
    WriteFile.close()

originalodb.close()
odb.save()
odb.close()
