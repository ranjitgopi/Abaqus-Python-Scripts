"""



ROPS-AUTOMATE-INPUTS-FROM-SPREADSHEET.py



This script is used to automate a ROPS (Roll Over Protection System) type analysis.



The script will terminate an Abaqus Standard job when Internal Energy (ALLIE) in the model has reached a certain level and then run a restart job.


For each job which has an energy requirement, the user needs to specify in the spreadsheet what is the energy required to be absorbed by the job before termination.
The Internal Energy (ALLIE) is tracked using DAT file after requesting the keyword *ENERGY PRINT in the input file in the STEP.



 This key-word must be placed in each input file.
The script does not contain any Abaqus CAE modules so it does not consume CAE tokens (which are scarce in most companies), it only consumes Abaqus Standard tokens.




The script is demonstrated with a simple model for two loading and unloading cycles --> FRAME-LOADING-1 --> FRAME-LOADING-2 --> FRAME-LOADING-3 --> FRAME-LOADING-4.





Please note that to terminate an analysis accurately at required energy, the maximum time increment must be properly specified for the jobs with energy requirement.




Please delete all old job files (dat, msg etc) in the folder before running this script.



This script requires the file SPREADSHEET_FOR_JOBS.csv to run. Inputs such as job names, energy requirements are mentioned in this file.



Run the script using commands such as below and in the directory where all the input files have been placed:


C:\SIMULIA\Commands\abq2017 python ROPS-AUTOMATE-INPUTS-FROM-SPREADSHEET.py
OR abaqus python ROPS-AUTOMATE-INPUTS-FROM-SPREADSHEET.py
OR abq2018 python ROPS-AUTOMATE-INPUTS-FROM-SPREADSHEET.py etc



Created by:


Ranjit Gopi


SIMULIA India Technical Specialist





Revision history:


First Release, 16th April 2018


REV-01, 24th April 2018
: Modified script to take inputs from spreadsheet instead of command line since command line inputs are not possible for all setups (such as PBS Works).
REV-02, 9th May 2018: Added additional capability in the script to catch errors in DAT & MSG file and terminate the script if caught, so as to release tokens.
REV-03, 19th June 2018: Added capability for user to specify wait time between job submission.
"""






#Import Abaqus modules



import os




import time



import csv





# Storing all jobs, jobs with energy requirement!



JOBS =[]

JOBS_WITH_ENERGY_REQUIREMENT = []



ENERGY_REQUIREMENT=[]






# Reading all the input values from a csv file!


with open('SPREADSHEET_FOR_JOBS.csv', 'r') as f:


	reader = csv.reader(f)


	count= 0


	for row in reader:


		# FieldName


		if count == 0:


			ABAQUS_PATH =row[1]


		if count == 1:


			NUMBER_OF_JOBS = int(row[1])


		if count == 2:


			CPUS = int(row[1])


		if count == 3:


			for each in row[1].split(','):


				JOBS.append(each.strip())


		if count == 4:


			for each in row[1].split(','):


				JOBS_WITH_ENERGY_REQUIREMENT.append(each.strip())


		if count == 5:


			for each in row[1].split(','):


				ENERGY_REQUIREMENT.append(each.strip())


		if count == 6:
			wait_time_between_jobs = int(row[1])
		count =count + 1




# Save in text files

with open('ALL JOBS.txt', 'w') as myfile:

	myfile.write(str(JOBS)+'\n')

	myfile.close



# Save in text files



with open('JOBS WITH ENERGY REQUIREMENT.txt', 'w') as myfile:


	myfile.write(str(JOBS_WITH_ENERGY_REQUIREMENT)+'\n')


	myfile.close





#Get current working directory



CWD=os.getcwd()







def job_with_energy_requirement(i,index):







	#Run jobs with energy requirement


	# For 1st job index = 0, hence if condition will pass for 1st job only!



	if(i == 0):



				os.system(ABAQUS_PATH + " " + "job=" + JOBS[i] + " " + "cpus=" + str(CPUS))




				FINAL_INTERNAL_ENERGY_STRING_VALUE_PREVIOUS_JOB = 0

	else:



				# For all other jobs we need to specify restart job
				os.system(ABAQUS_PATH + " " + "job=" + JOBS[i] + " " + "oldjob=" + JOBS[i-1]+ " " + "cpus=" + str(CPUS))





        #Obtain the TOTAL STRAIN ENERGY (STRESS POWER) from DAT file of previous job

				#Read DAT file of previous job

				try:

					fileName = CWD + "/" + JOBS[i-1] + ".dat"

				except:

					fileName = CWD + "\\" + JOBS[i-1] + ".dat"


				f = open(fileName,"r")

				lines = f.readlines()


				#Array to store Energy text strings

				INTERNAL_ENERGY_STRING_PREVIOUS_JOB=[]



				#Search DAT file for TOTAL STRAIN ENERGY (STRESS POWER) line and append to array

				for j,line in enumerate(lines):

					if line.upper().find("TOTAL STRAIN ENERGY (STRESS POWER)")>=0:

						b = line

						INTERNAL_ENERGY_STRING_PREVIOUS_JOB.append(b)



				#Find the last entry of TOTAL STRAIN ENERGY (STRESS POWER) in DAT file of previous job

				FINAL_INTERNAL_ENERGY_STRING_PREVIOUS_JOB=INTERNAL_ENERGY_STRING_PREVIOUS_JOB[-1].split(" ")



				#Split line into seperate strings and remove spaces

				FINAL_INTERNAL_ENERGY_STRING_CLEAN_PREVIOUS_JOB=[x for x in FINAL_INTERNAL_ENERGY_STRING_PREVIOUS_JOB if x != '']


				FINAL_INTERNAL_ENERGY_STRING_VALUE_PREVIOUS_JOB = float(FINAL_INTERNAL_ENERGY_STRING_CLEAN_PREVIOUS_JOB[5])



	#Now wait till current DAT file has been created



	try:



		while not os.path.exists(CWD+ "/" + JOBS[i] + ".dat"):



			time.sleep(20)



	except:



		while not os.path.exists(CWD+ "\\" + JOBS[i] + ".dat"):



			time.sleep(20)







	while True:




		try:



			fileName = CWD + "/" + JOBS[i] + ".dat"



		except:



			fileName = CWD + "\\" + JOBS[i] + ".dat"







		f = open(fileName,"r")



		lines = f.readlines()




		#Check DAT file for errors
		for line in lines:
			if line.upper().find('***ERROR')>=0:
				# Save in text files
				with open('THE JOB ' + str(i+1) + ' HAS TERMINATED IN DAT FILE DUE TO ERRORS.txt', 'w') as myfile:
					myfile.write('THE JOB '+ str(i+1) + ' HAS TERMINATED IN DAT FILE DUE TO ERRORS' +'\n')
					myfile.close
				return 1



		#Array to store Energy text strings



		INTERNAL_ENERGY_STRING_CURRENT_JOB=[]







		#Search DAT file for TOTAL STRAIN ENERGY (STRESS POWER) line and append to array



		for j,line in enumerate(lines):



			if line.upper().find("TOTAL STRAIN ENERGY (STRESS POWER)")>=0:



				b = line



				INTERNAL_ENERGY_STRING_CURRENT_JOB.append(b)







		#Run ONLY for valid INTERNAL_ENERGY_STRING_CURRENT_JOB (i.e., after first increment of job has been completed and first set of energy outputs have been printed to DAT file)



		if INTERNAL_ENERGY_STRING_CURRENT_JOB:







			#Find the last entry of TOTAL STRAIN ENERGY (STRESS POWER) in DAT file at current solution stage



			FINAL_INTERNAL_ENERGY_STRING_CURRENT_JOB=INTERNAL_ENERGY_STRING_CURRENT_JOB[-1].split(" ")







			#Split line into seperate strings and remove spaces



			FINAL_INTERNAL_ENERGY_STRING_CLEAN_CURRENT_JOB=[x for x in FINAL_INTERNAL_ENERGY_STRING_CURRENT_JOB if x != '']







			#Obtain the TOTAL STRAIN ENERGY (STRESS POWER) from DAT file as a floating number from string at current solution stage



			FINAL_INTERNAL_ENERGY_STRING_VALUE_CURRENT_JOB = float(FINAL_INTERNAL_ENERGY_STRING_CLEAN_CURRENT_JOB[5])





			ENERGY_ABSORBED_IN_CURRENT_JOB = FINAL_INTERNAL_ENERGY_STRING_VALUE_CURRENT_JOB - FINAL_INTERNAL_ENERGY_STRING_VALUE_PREVIOUS_JOB




			#Write to a text file for easy tracking by user



			with open('TRACKING ENERGY ABSORBED IN CURRENT JOB IF JOB HAS ENERGY REQUIREMENT FOR TERMINATION.txt', 'w') as myfile:



				myfile.write('TRACKING ENERGY ABSORBED IN CURRENT JOB IF JOB HAS ENERGY REQUIREMENT FOR TERMINATION: ')



				myfile.write(str(ENERGY_ABSORBED_IN_CURRENT_JOB)+'\n')



				myfile.close







			#If ENERGY ABSORBED IN CURRENT JOB exceeds a given value, terminate current job



			if ENERGY_ABSORBED_IN_CURRENT_JOB>int(ENERGY_REQUIREMENT[index]):



				os.system (ABAQUS_PATH + " " + "job=" + JOBS[i] + " " + "terminate")



				with open('COMPLETED JOBS.txt', 'a') as myfile:



					myfile.write('THE JOB ' + str(i+1) + ' WHICH HAS TO ABSORB AN ENERGY REQUIREMENT OF ' + ENERGY_REQUIREMENT[index] + ' HAS BEEN TERMINATED AFTER REACHING ENERGY TARGET ' + '\n')



					myfile.close





					break




			#Check for convergence errors in solver stage and terminate script if found
			for j,line in enumerate(lines):
				if line.upper().find("ERROR MESSAGES ON THE MSG FILE")>=0:
						# Save in text files
						with open('THE JOB ' + str(i+1) + ' HAS TERMINATED IN MSG FILE DUE TO CONVERGENCE ISSUES.txt', 'w') as myfile:
							myfile.write('THE JOB ' + str(i+1) + ' HAS TERMINATED IN MSG FILE DUE TO CONVERGENCE ISSUES' +'\n')
							myfile.close
						return 1



def job_without_energy_requirement(i):







	#Run jobs without energy requirement


	if i==0:



		os.system(ABAQUS_PATH + " " + "job=" + JOBS[i] + " " + "cpus=" + str(CPUS))



	else:



		os.system(ABAQUS_PATH + " " + "job=" + JOBS[i] + " " + "oldjob=" + JOBS[i-1] + " " + "cpus=" + str(CPUS))




	#Now wait till current DAT file has been created
	try:
		while not os.path.exists(CWD+ "/" + JOBS[i] + ".dat"):
			time.sleep(20)
	except:
		while not os.path.exists(CWD+ "\\" + JOBS[i] + ".dat"):
			time.sleep(20)

	while True:

		try:
			fileName = CWD + "/" + JOBS[i] + ".dat"
		except:
			fileName = CWD + "\\" + JOBS[i] + ".dat"

		f = open(fileName,"r")
		lines = f.readlines()

		#Check DAT file for errors
		for line in lines:
			if line.upper().find('***ERROR')>=0:
				# Save in text files
				with open('THE JOB '+ str(i+1) + ' HAS TERMINATED IN DAT FILE DUE TO ERRORS.txt', 'w') as myfile:
					myfile.write('THE JOB '+ str(i+1) + ' HAS TERMINATED IN DAT FILE DUE TO ERRORS' +'\n')
					myfile.close
				return 1




		#Wait till STA file has been created




		try:



			while not os.path.exists(CWD+ "/" + JOBS[i] + ".sta"):



				time.sleep(20)



		except:



			while not os.path.exists(CWD+ "\\" + JOBS[i] + ".sta"):



				time.sleep(20)






		while True:

			try:
				fileName = CWD + "/" + JOBS[i] + ".sta"

			except:
				fileName = CWD + "\\" + JOBS[i] + ".sta"

			f = open(fileName,"r")
			lines = f.readlines()

			#Check for convergence errors in solver stage and terminate script if found
			#Search for line "THE ANALYSIS HAS NOT BEEN COMPLETED" has been created in STA file
			for j,line in enumerate(lines):
				if line.upper().find("THE ANALYSIS HAS NOT BEEN COMPLETED")>=0:
					# Save in text files
					with open('THE JOB ' + str(i+1) + ' HAS TERMINATED IN MSG FILE DUE TO CONVERGENCE ISSUES.txt', 'w') as myfile:
						myfile.write('THE JOB ' + str(i+1) + ' HAS TERMINATED IN MSG FILE DUE TO CONVERGENCE ISSUES' +'\n')
						myfile.close
					return 1

			COUNT=0

			#Search for line "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" has been created in STA file
			for j,line in enumerate(lines):
				if line.upper().find("THE ANALYSIS HAS COMPLETED SUCCESSFULLY")>=0:
					COUNT=1

			#If the line "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" has been found, break loop
			if COUNT==1:
				with open('COMPLETED JOBS.txt', 'a') as myfile:
					myfile.write('THE JOB ' + str(i+1) + ' WHICH HAS NO SPECIFIED ENERGY REQUIREMENT HAS BEEN COMPLETED ' + '\n')
					myfile.close
				break
		break




for each in range(0,NUMBER_OF_JOBS):







	if JOBS[each] in JOBS_WITH_ENERGY_REQUIREMENT:



		return_value = 0
		index = JOBS_WITH_ENERGY_REQUIREMENT.index(JOBS[each])



		return_value=job_with_energy_requirement(each,index)



		if return_value == 1:
			with open('THE SCRIPT HAS TERMINATED DUE TO ERRORS IN THE JOB.txt', 'w') as myfile:
				myfile.write('THE SCRIPT HAS TERMINATED DUE TO ERRORS IN JOB' +'\n')
				myfile.close
			break
		#Sleep for some time between job submissions to allow Abaqus to completely close current job
		time.sleep(wait_time_between_jobs)







	else:


		return_value = 0
		return_value=job_without_energy_requirement(each)



		if return_value == 1:
			with open('THE SCRIPT HAS TERMINATED DUE TO ERRORS IN THE JOB.txt', 'w') as myfile:
				myfile.write('THE SCRIPT HAS TERMINATED DUE TO ERRORS IN JOB' +'\n')
				myfile.close
			break
		#Sleep for some time between job submissions to allow Abaqus to completely close current job
		time.sleep(wait_time_between_jobs)



