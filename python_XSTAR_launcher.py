#-----------------------------------------------------
#  Version 0.04: implimentation of feedback, to make
# the code adhere to more python styling standards,
# use of different process handlers, and to implement
# a new parameter file stander.
# 
#  Questions, comments, or concerns, please email
# Randall Dannen at dannenr@unlv.nevada.edu.
# 
# Usage: python [name].py [parameter file]
#---------------------------------------------------
import sys
import os
import subprocess
import ConfigParser
import time
import numpy as np
from Queue import Queue
from threading import Thread

#---------------------------------------------------
#  Declare some sets that contain all the parameters
# that we'll be looking for.  As well as declaring
# some global system parameters to be over written
# should they be passed in the parameter file.
#---------------------------------------------------

const_params = ("cfrac","density","pressure",
				"column","spectrum","spectrum_file",
				"spectun","trad","rlrad38","lcpres",
				"modelname")

abunds       = ("habund","heabund","liabund","beabund",
				"babund","cabund","nabund","oabund",
				"fabund","neabund","naabund", "mgabund",
				"alabund","siabund","pabund","sabund",
				"clabund","arabund","kabund","caabund",
				"scabund","tiabund","vabund","crabund",
				"mnabund","feabund","coabund","niabund",
				"cuabund","znabund")

hidden_params = ("niter","nsteps","lprint","lwrite","critf",
				 "emult","taumax","xeemin","vturbi","radexp",
				 "npass","ncn2")

interp_params = ("temperatureMin", "temperatureMax",
				 "numberOfTempSteps","rlogxiMin",
				 "rlogxiMax","numXiSteps")

sys_params    = ("base_dir","num_threads")

#------------------------------------------------
#  Function to do the calling of XSTAR in the
# specified directory.
#------------------------------------------------
def run_XSTAR(command,base_dir,model,index):
	directory = base_dir+model+str(index).zfill(7)
	with open(os.devnull,'w') as f:
		if not os.path.exists(directory): os.makedirs(directory)
		print "{}:  executing XSTAR with the following commang:\n{}\n".format(index,command)
		full_command = "( cd "+directory+" ; "+command+" )"
		t1 = time.time()
		subprocess.call(full_command,shell=True,stdout=f)
		t2 = time.time()
		print "{}: finish in {} seconds.\n".format(index,(t2-t1))


#------------------------------------------------
#  Function to read the parameter file and check
# if all parameters are passed.  Should return a
# list of all XSTAR models to be executed.
#------------------------------------------------
def read_parameter_file(fname):
	config = ConfigParser.ConfigParser()
	config.read(fname)
	xstar_models = []
	com_base     = "xstar"
	for s in ["const_params","abunds","hidden_params"]:
		for o in config.options(s):
			if o == "modelname":
				m_name = config.get(s,o)
			com_base += " "+o+"="+config.get(s,o)
	s  = "interp_params"
	o  =  config.options(s)
	v  = []
	for oo in o:
		v.append(float(config.get(s,oo)))
	t_arr  = np.logspace(np.log10(v[0]),np.log10(v[1]),num=v[2])
	xi_arr = np.linspace(v[3],v[4],v[5])
	v  = []
	for t in t_arr:
		for xi in xi_arr:
			v.append("{} temperature={} rlogxi={}".format(com_base,t,xi))
	s  = "sys_params"
	nt = int(config.get(s,"num_threads"))
	bd = config.get(s,"base_dir")
	return v,m_name,nt,bd

#------------------------------------------------
#      This should begin the main block.
#------------------------------------------------
if __name__ == "__main__":
	if   len(sys.argv) < 2:
		print "Too few arguments passed."
		sys.exit()
	elif len(sys.argv) > 2:
		print "Too many arguments passed."
		sys.exit()
	
	fname = sys.argv[1]
	if not os.path.isfile(fname):
		print "Parameter file, {}, does not exist.".format(fname)
		sys.exit()

	com_list,model_name,num_threads,base_dir = read_parameter_file(fname)

	command_queue = Queue()
	
	def worker():
		while True:
			command = command_queue.get()
			run_XSTAR(command[0],base_dir,model_name,command[1])
			command_queue.task_done()

	for i in range(num_threads):
		t = Thread(target=worker)
		t.daemon = True
		t.start()
	
	count = 0
	for c in com_list:
		command_queue.put([c,count])
		count += 1
	
	command_queue.join()