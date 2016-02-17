
import subprocess
import warnings

def get_level(chanel="Master"):
	output = subprocess.Popen("amixer get "+chanel,shell=True, stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")
	for line in output:
		if '%' in line:
			level=line.split()[-2]
			level=level.rstrip('%]')
			level=level.lstrip('[')
			try: #a stopgap to figure out this bull shit
				level=int(level)
			except:
				warnings.warn("Couldn't get level from amixer. Setting volume will be impossible.") 
				level=0
			break #this is a little janky
	return(level)

def decrease(chanel,amt):
	level=get_level(chanel)
	new_level=level-amt
	subprocess.Popen("amixer sset Master "+str(new_level)+"%",shell=True)
	
def increase(chanel,amt):
	level=get_level(chanel)
	new_level=level+amt
	subprocess.Popen("amixer sset Master "+str(new_level)+"%",shell=True)

