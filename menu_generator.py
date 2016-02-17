#menu generator
import os

desktop_files=os.listdir('/usr/share/applications') #getting a list of desktop files
desktop_files=[df for df in desktop_files if df[0]!='.' and '.desktop' in df] #removing hidden and non .desktop files
categories_dict={}
for df in desktop_files:
	with open('/usr/share/applications/'+df) as desktop:
		desktop=[line.rstrip("\n") for line in desktop.readlines()]
		name=''
		generic_name=''
		categories=''
		execute=''
		try_execute=''
		icon=''
		terminal=''
		add_to_file=1
		for line in desktop:
			if line[0:5]=='Name=' and name=='':
				name=line[5:]
			elif line[0:12] =='GenericName=' and generic_name=='':
				generic_name=line[12:]
			elif line[0:11]=='Categories=' and categories=='':
				categories=line[11:]
				if categories=='':
					categories='Other;'
				categories_list=categories.split(";")[:-1]
				for category in categories_list:
					try:
						categories_dict[category]+=1
					except:
						categories_dict[category]=1
				print(categories_list)
			elif line[0:5]=='Exec=' and execute=='':
				execute=line[5:]
			elif line[0:8]=='TryExec=' and try_execute=='':
				try_execute=line[8:]
			elif line[0:5]=='Icon=' and icon=='':
				icon=line[5:]
			elif line[0:9]=='Terminal=' and terminal=='':
				terminal=line[9:]
				if terminal=='True':
					terminal=1
				else:
					terminal=0
			elif line[0:15]=='[Desktop Action':
				break
			elif line[0:5]=='Type=':
				if 'Application' not in line:
					add_to_file=0
					break
		if generic_name=='':
			generic_name==name
print(categories_dict)
