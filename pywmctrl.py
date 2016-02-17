import subprocess
import pipes
#this is broken
def get_current_desktop():
	process = subprocess.Popen(["wmctrl", "-d"], stdout=subprocess.PIPE)
	process.wait()
	output=process.communicate()[0].decode('UTF-8').split("\n") #split adds a '' to the end
	num_desktops=len(output)-1
	desktop=0
	for l in output:
		if "*" in l:
			break
		desktop+=1
	return(desktop,num_desktops)
	
def move_to_desktop_left():
	[cur_desktop,num_desktops]=get_current_desktop()
	new_desktop=cur_desktop-1
	if new_desktop<0:
		new_desktop=num_desktops-1
	subprocess.Popen(["wmctrl","-s",str(new_desktop)])

def move_to_desktop_right():
	[cur_desktop,num_desktops]=get_current_desktop()
	new_desktop=cur_desktop+1
	if new_desktop>num_desktops-1:
		new_desktop=0
	subprocess.Popen(["wmctrl","-s",str(new_desktop)])
	
def get_running_applications():
	output = subprocess.Popen(["wmctrl", "-l","-p"], stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').split("\n") 
	running_list=[]
	for l in output:
		l=l.split(maxsplit=4)
		if l!=[]:
			if l[2]!='-1':
				running_list.append(l)
	try:
		running_list.remove([])
	except:
		pass
	return(running_list)

def get_running_pids():
	#returns a list of only running pids
	running_apps=get_running_applications()
	pids=[]
	for app in running_apps:
		pids.append(app[2])
	return(pids)

def switch_to_running_app(wmctrl_id):
	subprocess.Popen(["wmctrl","-i","-a",wmctrl_id])
	#the command for switching to an application by its weird code is
	#wmctrl -i -a 0x02e002d5

def close_running_app(wmctrl_id):
	subprocess.Popen(["wmctrl","-i","-c",wmctrl_id])
	
def close_all():
	running_apps=get_running_applications()
	for app in running_apps:
		close_running_app(app[0])

def close_all():
	running_apps=get_running_applications()
	for app in running_apps:
		if "Terminal" not in app[4]: #temporary to keep main application running
			close_running_app(app[0])

def get_active_window():
	#returns active window id
	output = subprocess.Popen("wmctrl -lp | grep $(xprop -root | grep _NET_ACTIVE_WINDOW | head -1 | awk '{print $5}' | sed 's/,//' | sed 's/^0x/0x0/')",
		shell=True, stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
	return(output.split()[0])

def window_manager_name():
	#returns active window id
	output = str(subprocess.Popen("wmctrl -m",shell=True, stdout=subprocess.PIPE).communicate()[0]).split('\n')
	return(output[0].split()[1])

def get_used_desktops():
	running_apps=get_running_applications()
	used_desktops=[]
	for app in running_apps:
		if app[1] not in used_desktops and app[1]!='-1':
			used_desktops.append(app[1])
	return(used_desktops)

def cleanup():
	#this is supposed to check if there are unused desktops, then move all desktops left and remove a desktop
	used_desktops=get_used_desktops()
	num_desktops=get_current_desktop()[1]
	while len(used_desktops)<num_desktops:
		running_apps=get_running_applications()
		for app in running_apps:
			if str(int(app[2])-1) not in used_desktops and int(app[2])-1>=0:
				process=subprocess.Popen("wmctrl -ri "+app[0]+" -t "+str(int(app[2])-1),shell=True)
				process.wait()
		if num_desktops>1:
			process=subprocess.Popen("wmctrl -n "+str(num_desktops-1),shell=True)
			process.wait()
		used_desktops=get_used_desktops()
		num_desktops=get_current_desktop()[1]
def create_and_switch():
	num_desktops=get_current_desktop()[1]
	process=subprocess.Popen("wmctrl -n "+str(num_desktops+1),shell=True)
	process.wait()
	process=subprocess.Popen("wmctrl -s "+str(num_desktops),shell=True)
	process.wait()
