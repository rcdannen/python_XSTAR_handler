"""
Version 0.3:  Hopefully to add multithreading properly

Python scrlessipt to read a parameter file and launch 
XSTAR with those parameters or restart a given grid of
models.

Usage: python [name].py [file]
"""
import sys
import os
from Queue import Queue
from threading import Thread
import numpy as np

num_threads = 1
base_dir    = "./"

def runXSTAR(command,base_dir,model,index):
	directory = base_dir+model+str(index).zfill(7)
	if not os.path.exists(directory): os.makedirs(directory)
	print "%i: python XSTAR launcher running using the following command:" % index
	os.system("( cd %s ; %s )" % (directory,command))

#-------------------------------------------------------
#  Begin main block
#-------------------------------------------------------
if   len(sys.argv) < 2:
	print "Too few arguments passed."
	sys.exit()
elif len(sys.argv) > 3:
	print "Too many arguments passed."
	sys.exit()
elif sys.argv[1] == "-i":
	f = open(sys.argv[2],'r')
else: 
	print "Incorrect arguemnts passed."
	sys.exit()

command = "xstar"

"""
List all of the constant parameter names so that we
can search the file for them and retrieve values from
the given parameter file.
"""
paramNames   = ("cfrac","density","pressure","column","spectrum","spectrum_file","spectun","trad","rlrad38","lcpres","habund","heabund","liabund","beabund","babund","cabund","nabund","oabund","fabund","neabund","naabund", "mgabund","alabund","siabund","pabund","sabund","clabund","arabund","kabund","caabund","scabund","tiabund","vabund","crabund","mnabund","feabund","coabund","niabund","cuabund","znabund","niter","nsteps","lprint","lwrite","critf","emult","taumax","xeemin","vturbi","radexp","npass","ncn2","modelname")
param        = []
for line in f:
	if line[0] != "#" and line[0] != "\n":
		for word in line.split():
			param.append(word)

#---------------------------------------------------
#  Grab our new system parameters.
#---------------------------------------------------
index     = param.index("base_dir")
base_dir  = param[index+1]

index     = param.index("num_threads")
num_threads = int(param[index+1])

for name in paramNames:
	index   = param.index(name)
	command = '%s %s=%s' % (command,param[index],param[index+1])
	if name == "modelname":
		model_name = param[index+1]

index     = param.index("temperatureMin")
tempMin   = float(param[index+1])
index     = param.index("temperatureMax")
tempMax   = float(param[index+1])
index     = param.index("numberOfTempSteps")
tempSteps = float(param[index+1])
tempArr   = np.logspace(np.log10(tempMin),np.log10(tempMax),num=tempSteps)

index     = param.index("rlogxiMin")
xiMin     = float(param[index+1])
index     = param.index("rlogxiMax")
xiMax     = float(param[index+1])
index     = param.index("numXiSteps")
xiSteps   = float(param[index+1])
xiArr     = np.linspace(xiMin,xiMax,num=xiSteps)

f.close()

command_queue = Queue()

def worker():
	while True:
		command = command_queue.get()
		runXSTAR(command[0],command[1],model_name,command[2])
		command_queue.task_done()

for i in range(num_threads):
	t = Thread(target=worker)
	t.daemon = True
	t.start()

count = 0
for temp in tempArr:
	for xi in xiArr:
		command_queue.put(["%s temperature=%s rlogxi=%s"%(command,temp,xi),base_dir,count])
		count+=1

command_queue.join()
