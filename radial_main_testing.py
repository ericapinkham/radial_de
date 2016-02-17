##### 0-11
#TO DO:
	#0: NEEDS
		#way to shutdown computer, logout, etc
		#some way for this program to be restarted in case of crash
		#modify $XDG_DATA_DIRS to find a default icon theme
	#1: PROBABLY NEEDS
		#figure out the problem with clearing layouts, what i have now works, but its weird
	#2: WANTS
		#window management
			#launch applications in full screen mode
			#maximize applications when launched
		#menu
			#"remove from favorites" does not work in favorites menu.
			#right click event on buttons
			#mouseover is taken over by joystick, making it look funny
			#add more info in status menu, like cpu and memory usage, open applications memory usage etc
		#other
			#write your own keyboard
			#make things prettier
			#write your own filemanager
			#a system tray
	#3: SHOULD PROBABLY DO
		#cleanup and minimize dependencies
import sys
from PyQt4 import QtGui, QtCore
import numpy as np
import subprocess
from lxml import etree
import os
import time
from menu_layouts import *
from xbox_controller import *
import pwd
import platform
import pyamixer

class launch_application(QtCore.QThread):
	# this class launches applications in a thread
	def __init__(self,application, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.parent=parent
		self.application=application
		self.exiting = False
		self.start()
		self.finished.connect(self.app_finished)
	def run(self):
		#clean up workspaces
		#shouldn't need to do this but doing it anyway
		pywmctrl.cleanup()
		#create new workspace
		pywmctrl.create_and_switch()
		#launch application
		process=subprocess.Popen(self.application,shell=True)
		process.wait()
		#app_finished runs after process is done
		
	def app_finished(self):
		#if the program was launched by this application, the following code is executed after the program finishes
		#cleanup up unused workspaces
		pywmctrl.cleanup()
		#switch back to applications mode, this should be more sophisticated
		print(self.application+ " is done")
		self.parent.applications_mode() #return to controller application mode
		
#class launch_application():
	## this class launches applications in a thread
	#def __init__(self,application, parent=None):
		#self.parent=parent
		#self.application=application
		#out=subprocess.Popen(self.application+" & echo $!",shell=True,stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n") 
		#print(out)
		
		
class open_file(QtCore.QThread):
	# this class launches applications in a thread
	def __init__(self,file_name, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.parent=parent
		self.file_name=file_name
		self.exiting = False
		self.start()
	def run(self):
		subprocess.call(['xdg-open',self.file_name])
		
class button(QtGui.QPushButton):
	#this class creates and assigns action to buttons
	def __init__(self,xml_node,parent,group):
		self.node=xml_node
		QtGui.QPushButton.__init__(self,self.node.attrib['name'],parent) #innitialize button
		self.group=group #this says it belongs to the class radial menu, but not as a child
		self.parent=parent #parent is the main ui
		self.clicked.connect(self.act)
		font=QtGui.QFont()
		self.setMouseTracking(True)

		try:
			if self.node.attrib['subtype']=="font":
				font.setFamily(self.node.attrib['value'])
				self.node.attrib['tool_tip']=self.node.attrib['name']
				self.setText('ABC\nxyz')
			else:
				pass
		except:
			font.setFamily(self.group.settings['Font'])
		parent_node=self.node.getparent()
		try:
			parent_name=parent_node.attrib['name']
		except:
			parent_name=None
		if parent_name=="Button Size":
			btn_size=int(self.node.attrib['value'])
		else:
			btn_size=int(self.group.settings['Button Size'])
		font.setPointSize(btn_size/2)
		self.setFont(font)
		if self.node.attrib['icon']!="none": #for some reasone this is not working correctly, some weird applications don't have icons in the theme
			self.setStyleSheet("QPushButton {color: black; border: none}")
			self.setIcon(QtGui.QIcon.fromTheme(self.node.attrib['icon'],QtGui.QIcon.fromTheme("applications-other")))
			self.setIconSize(QtCore.QSize(btn_size,btn_size))
			self.resize(self.sizeHint())
			self.setText("")
		else:
			self.setStyleSheet("QPushButton {color: black}")
			self.resize(self.sizeHint())
	def act(self):
		print(self.node.attrib['name'])
		btn_type=self.node.attrib['type']
		if btn_type=='exit':
			root = self.parent.layouts.tree.find('.//button[@name="Cancel Logout"]')
			print(root)
			self.group.change_menu(root)
		elif btn_type=="leave":
			if self.node.attrib['subtype']=="cancel_logout":
				self.group.change_menu()
			else:
				self.parent.leave(self.node.attrib['subtype'])
		elif btn_type=='status':
			self.parent.status_mode()
		elif btn_type=='search':
			self.parent.search_mode()
		elif btn_type=='files':
			self.parent.files_mode()
		elif btn_type=='desktop':
			self.parent.applications_mode()
		elif btn_type=='menu': #main navigation btn_type
			if self.node.attrib['name']=="Favorites":
				#remove favorites
				children=self.node.getchildren() 
				for child in children:
					self.node.remove(child)
				#add favorites
				children=self.parent.layouts.tree.findall('.//button[@is_favorite="1"]')
				for child in children:
					child = etree.SubElement(self.node, "button",attrib=child.attrib)
			self.group.change_menu(self.node)
		elif btn_type=='application':
			app=launch_application(self.node.attrib['exec'],self.parent)
			if self.node.attrib['use_controller']=="0":
				self.parent.applications_mode_no_controller()
			else:
				self.parent.applications_mode()
		elif btn_type=='setting':
			print(self.node.attrib['name'])
			parent_node = self.node.getparent()
			
			if self.node.attrib['name']=="Raise Volume":
				pyamixer.increase('Master',5)
				parent_node.attrib['value']=str(pyamixer.get_level('Master'))
			elif self.node.attrib['name']=="Lower Volume":
				pyamixer.decrease('Master',5)
				parent_node.attrib['value']=str(pyamixer.get_level('Master'))
				
			else:
				parent_node.attrib['value']=self.node.attrib['value']
			self.group.change_menu(parent_node)
		elif btn_type=='a_r_favorites': #ADD OR REMOVE FAVORITES
			parent_node = self.node.getparent()
			parent_node.attrib['is_favorite']=str(1-int(parent_node.attrib['is_favorite']))
			print(parent_node.attrib)
			if parent_node.attrib['is_favorite']=="1":
				self.node.attrib['name']="remove from favorites"
				self.node.attrib['icon']="list-remove"
			else:
				self.node.attrib['name']="add to favorites"
				self.node.attrib['icon']="tab-new"
			self.group.change_menu(parent_node)
		elif btn_type=='set_controller_scheme': #set controller scheme
			parent_node = self.node.getparent()
			parent_node.attrib['use_controller']=str(1-int(parent_node.attrib['use_controller']))
			print(parent_node.attrib)
			if parent_node.attrib['use_controller']=="1":
				self.node.attrib['name']="disable controller"
				self.node.attrib['icon']="input-gaming"
			else:
				self.node.attrib['name']="enable controller"
				self.node.attrib['icon']="applications-games"
			self.group.change_menu(parent_node)
		elif btn_type=='running_apps': #CURRENTLY RUNNING APPLICATIONS
			#previous running applications
			children=self.node.getchildren()
			for child in children:
				self.node.remove(child)
			running_apps=pywmctrl.get_running_applications()
			for app in running_apps:
				child=etree.SubElement(self.node, "button")
				child.attrib['wmctrl_id']=app[0]
				child.attrib['wmctrl_desktop']=app[1]
				child.attrib['pid']=app[2]
				
				output = subprocess.Popen("ps -q "+str(app[2])+" -o comm=", shell=True, stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")
				pid_name=output[0]#[1].split()[-1]
				child.attrib['name']=pid_name
				print(pid_name)
				try:
					child.attrib['icon']=self.parent.layouts.icon_dict[pid_name]
				except(KeyError):
					child.attrib['icon']="other"
				child.attrib['type']='running_app'
			self.group.change_menu(self.node)
		elif btn_type=='running_app': #SWITCH TO RUNNING APPP
			pywmctrl.switch_to_running_app(self.node.attrib['wmctrl_id'])
			self.parent.applications_mode()
		elif btn_type=="close_running_app":
			pywmctrl.close_running_app(self.node.attrib['wmctrl_id'])
			self.group.change_menu()
		else:
			print("undefined action")
	def act_x(self):
		print("x at " + self.node.attrib['name'])
		btn_type=self.node.attrib['type']
		if btn_type=='application': #opens add to favorites menu
			root=self.node
			# add or remove favorite button
			children=root.getchildren()
			if children==[]: #check to see if child has already been created
				#if not, create child
				child_fav = etree.SubElement(root, "button")
				child_control = etree.SubElement(root, "button")
				if root.attrib['is_favorite']=="0":
					child_fav.attrib['icon']="tab-new"
				else:
					child_fav.attrib['icon']="list-remove"
				if root.attrib['use_controller']=="0":
					child_control.attrib['icon']="applications-games"
				else:
					child_control.attrib['icon']="input-gaming"
			else:
				#children already present, use existing child node
				for child in children:
					if "favorites" in child.attrib['name'].lower():
						child_fav=child #choose favorite child
					if "controller" in child.attrib['name'].lower():
						child_control=child
			if root.attrib['is_favorite']=="1":
				child_fav.attrib['name']="remove from favorites"
			else:
				child_fav.attrib['name']="add to favorites"
			if root.attrib['use_controller']=="1":
				child_control.attrib['name']="disable controller"
			else:
				child_control.attrib['name']="enable controller"
			child_fav.attrib['type']="a_r_favorites"
			child_control.attrib['type']="set_controller_scheme"

			
			#done with children, change mode
			self.group.change_menu(self.node)
		elif btn_type=='running_app': #SWITCH TO RUNNING APPP
			root=self.node
			children=root.getchildren()
			for child in children: #this is inefficient maybe?
				self.node.remove(child)
			#add close application button
			child = etree.SubElement(root, "button")
			#child.attrib=self.node.attrib
			child.attrib['name']="close"
			child.attrib['wmctrl_id']=self.node.attrib['wmctrl_id']
			child.attrib['icon']="process-stop"
			child.attrib['type']="close_running_app"
			self.group.change_menu(self.node)
			
		else:
			print("undefined action")
	def enterEvent(self,event):
		self.hovered(1)
	def leaveEvent(self,event):
		self.hovered(0)
	def hovered(self,is_hovered):
		if is_hovered==1:
			if self.node.attrib['icon']!="none":
				self.setStyleSheet("QPushButton {color: gray; border: none}") 
				self.setText(self.node.attrib['name'])
			else:
				self.setStyleSheet("QPushButton {color: gray}")
			try: 
				if self.node.attrib['subtype']=='font':
					font=self.node.attrib['value']
				else:
					font=None
			except:
				font = None
			try:
				self.group.set_lower_label(self.node.attrib['tool_tip'],font)
			except(KeyError):
				self.group.set_lower_label('')
			except(AttributeError):
				pass
		else:
			if self.node.attrib['icon']!="none":
				self.setStyleSheet("QPushButton {color: black; border: none}")
				self.setText("")
			else:
				self.setStyleSheet("QPushButton {color: black}")
		
class radial_menu(QtCore.QObject):
	#this class creates buttons in a radial way
	def __init__(self,parent):
		super(radial_menu, self).__init__()
		self.init_radial_menu(parent)
	def init_radial_menu(self,parent):
		#self.layouts =layouts #contains directory information but also settings
		self.parent=parent
		self.resolution = QtGui.QDesktopWidget().screenGeometry()
		self.center=[self.resolution.width()/2,self.resolution.height()/2]
		self.radius=self.resolution.height()/2-64
		self.change_menu()
	def change_menu(self,node=None): # change menu program
		#to do: make settings persistant
		#also, it would probably save some cpu time to only do this sometimes, like when in a settings sub directory
		#load some settings
		setting_nodes=self.parent.layouts.tree.findall('.//button[@name="Settings"]/button') #finds all children of node "settings"
		self.settings={}
		for setting in setting_nodes:
			self.settings[setting.attrib['name']]=setting.attrib['value']
		self.parent.clear() #remove all buttons
		if node==None:
			node=self.parent.layouts.tree.find('.//button[@name="Home"]')
		self.btns=[]
		#font
		font=QtGui.QFont()
		font.setFamily(self.settings['Font'])
		font.setPointSize(48)
		#title label
		label_text=node.attrib['name']
		try:
			label_text+=": " +node.attrib['value']
		except:
			pass
		title_label=QtGui.QLabel(label_text,self.parent)
		title_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		title_label.setFont(font)
		title_label.resize(title_label.sizeHint())
		title_label.setStyleSheet("QLabel {color: gray}")
		title_label.move(32,16)
		title_label.show()
		#lower_label
		self.lower_label=QtGui.QLabel("info",self.parent)
		self.lower_font=font
		self.lower_font.setPointSize(28)
		self.lower_label.setFont(self.lower_font)
		self.lower_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.lower_label.setStyleSheet("QLabel {color: gray}")
		self.lower_label.show()
		#center button
		if node.attrib['name'].lower() not in ['exit','cancel logout']:
			center_node=node.getparent()
		else:
			center_node=node
		center_node.attrib['vector_x']="0"
		center_node.attrib['vector_y']="0"
		btn=button(center_node,self.parent,self)
		self.max_btn=btn
		btn.move(self.center[0]-0.5*btn.width(),self.center[1]-0.5*btn.height())
		btn.show()
		self.btns.append(btn)
		#radial buttons
		children=node.getchildren()
		num_btns=len(children)
		j=0
		for child in children:
			x_loc=self.center[0]+self.radius*np.cos(2*j*np.pi/num_btns-np.pi/2)
			y_loc=self.center[1]+self.radius*np.sin(2*j*np.pi/num_btns-np.pi/2)
			self.thresh=abs(np.cos(np.pi/num_btns)+np.sin(np.pi/num_btns))
			child.attrib['vector_x']=str((x_loc-self.center[0])/np.sqrt((x_loc-self.center[0])**2+(y_loc-self.center[1])**2))
			child.attrib['vector_y']=str((y_loc-self.center[1])/np.sqrt((x_loc-self.center[0])**2+(y_loc-self.center[1])**2))
			btn=button(child,self.parent,self)
			btn.move(x_loc-0.5*btn.width(),y_loc-0.5*btn.height())
			btn.show()
			self.btns.append(btn)
			j=j+1
		self.set_lower_label()
		# Xbox interface stuff
		self.parent.xbox_actions_master=xbox_actions_in_radial(self.btns) #class which controls xbox inpput, each time it is recreated, the actions get reassigned
		self.parent.thread.button_signal_up.connect(self.parent.xbox_actions_master.btn_action)
		self.parent.thread.lstick_signal_continuous.connect(self.parent.xbox_actions_master.lstick_action)
	def set_lower_label(self,text="info",font_name=None):
		if font_name!=None:
			font = self.lower_font
			font.setFamily(font_name)
		else:
			font = self.lower_font
		self.lower_label.setFont(font)
		self.lower_label.setText(text)
		self.lower_label.resize(self.lower_label.sizeHint())
		self.lower_label.move(32,self.resolution.height()-self.lower_label.height()-16)
		
class status(QtCore.QObject):
	# this class displays some system information
	def __init__(self,parent):
		super(status,self).__init__()
		self.init_status(parent)
	def init_status(self,parent):
		self.parent=parent
		resolution = QtGui.QDesktopWidget().screenGeometry()
		#load some settings
		#to do: make settings persistant
		#also, it would probably save some cpu time to only do this sometimes, like when in a settings sub directory
		#removing objects
		setting_nodes=self.parent.layouts.tree.findall('.//button[@name="Settings"]/button') #finds all children of node "settings"
		self.settings={}
		for setting in setting_nodes:
			self.settings[setting.attrib['name']]=setting.attrib['value']
		self.parent.clear() #remove all buttons
		#adding objects 
		font=QtGui.QFont()
		font.setFamily(self.settings['Font'])
		font.setPointSize(48)
		title_label=QtGui.QLabel(' Status',self.parent) 
		title_label.resize(title_label.sizeHint())
		title_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		title_label.setFont(font)
		title_label.move(32,16)
		home_node=self.parent.layouts.tree.find('.//button[@name="Home"]')
		btn = button(home_node,self.parent,self)
		self.btns=[btn]
		vbox=QtGui.QVBoxLayout()
		hbox=QtGui.QHBoxLayout()
		#add status items
		status_items=QtGui.QListWidget()
		#add some platform info
		uname=platform.uname()
		for n in uname:
			status_items.addItem(QtGui.QListWidgetItem(n))
		#add status specific to ui
		root=self.parent.layouts.tree.find('.//button[@name="Settings"]')
		children=root.getchildren()
		for child in children:
			status_items.addItem(QtGui.QListWidgetItem(child.attrib['name']+": "+child.attrib['value']))
		for stat in list(self.parent.status_list.keys()):
			status_items.addItem(QtGui.QListWidgetItem(stat+": "+str(self.parent.status_list[stat])))
		#add window manager name
		status_items.addItem(QtGui.QListWidgetItem("Window Manager: "+pywmctrl.window_manager_name()))
		## ADD MORE STATUS ITEMS HERE
		vbox.addWidget(title_label)
		vbox.addWidget(status_items)
		hbox.addWidget(btn)
		vbox.addLayout(hbox) #for some reason having this fucking button in a layout in a layout made it work
		self.parent.setLayout(vbox)
		#xbox signals
		self.parent.xbox_actions_master=xbox_actions_in_status(self.btns) #these are linked to top level qobject widget
		self.parent.thread.button_signal_up.connect(self.parent.xbox_actions_master.btn_action)
	def change_menu(self,ignore_this):
		self.parent.radial_mode()


class files(QtGui.QFileDialog):
	#this is supposed to be a basic file manager
	def __init__(self,parent):
		super(files,self).__init__()
		self.init_files(parent)
	def init_files(self,parent):
		QtGui.QFileDialog.__init__(self)
		self.parent=parent
		self.cursor_speed=20
		resolution = QtGui.QDesktopWidget().screenGeometry()
		#load some settings
		#to do: make settings persistant
		#also, it would probably save some cpu time to only do this sometimes, like when in a settings sub directory
		#removing objects
		setting_nodes=self.parent.layouts.tree.findall('.//button[@name="Settings"]/button') #finds all children of node "settings"
		self.settings={}
		for setting in setting_nodes:
			self.settings[setting.attrib['name']]=setting.attrib['value']
		#adding objects 
		font=QtGui.QFont()
		font.setFamily(self.settings['Font'])
		font.setPointSize(int(self.settings['Font Size']))
		self.showFullScreen()
		#xbox signals
		self.parent.xbox_actions_master=xbox_actions_in_applications(self) #these are linked to top level qobject widget
		self.parent.thread.lstick_signal_continuous.connect(self.parent.xbox_actions_master.lstick_action)
		self.parent.thread.button_signal_down.connect(self.parent.xbox_actions_master.btn_action_down)
		self.parent.thread.button_signal_up.connect(self.parent.xbox_actions_master.btn_action_up)
		if self.exec_():
			self.file_names = self.selectedFiles()
	def reject(self):
		print("reject")
		self.parent.radial_mode()
		self.done(1)
	def accept(self):
		self.file_names = self.selectedFiles()
		print("open" + self.file_names[0])
		try:
			app=open_file(self.file_names[0],self) #for some reason this doesn't fucking work!
			self.parent.applications_mode()
		except:
			print("something went wrong...")
		self.done(0)
		
		
class applications(QtCore.QObject):
	#this class controls behavior for applications
	def __init__(self,parent):
		super(applications,self).__init__()
		self.init_applications(parent)
	def init_applications(self,parent):
		self.parent=parent
		#load some settings
		setting_nodes=self.parent.layouts.tree.findall('.//button[@name="Settings"]/button') #finds all children of node "settings"
		self.settings={}
		for setting in setting_nodes:
			self.settings[setting.attrib['name']]=setting.attrib['value']
		#xbox signals
		self.parent.xbox_actions_master=xbox_actions_in_applications(self) #these are linked to top level qobject widget
		self.parent.thread.lstick_signal_continuous.connect(self.parent.xbox_actions_master.lstick_action) #lstick
		self.parent.thread.rstick_signal_continuous.connect(self.parent.xbox_actions_master.rstick_action) #rstick
		self.parent.thread.button_signal_down.connect(self.parent.xbox_actions_master.btn_action_down)
		self.parent.thread.button_signal_up.connect(self.parent.xbox_actions_master.btn_action_up)
		
class applications_no_controller(QtCore.QObject):
	#this class controls behavior for applications which have their own xbox controller interface
	def __init__(self,parent):
		super(applications_no_controller,self).__init__()
		self.init_applications_no_controller(parent)
	def init_applications_no_controller(self,parent):
		self.parent=parent
		#xbox signals
		self.parent.xbox_actions_master=xbox_actions_none() #these are linked to top level qobject widget
		
class main_ui(QtGui.QWidget):
	########## MAIN UI ##########
	def __init__(self):
		super(main_ui, self).__init__()
		self.init_ui()
	def init_ui(self):
		QtGui.QMainWindow.__init__(self, None)
		# add background image
		#try:
			#desktop_background=QtGui.QPixmap("/home/eric/Dropbox/gui_programming/radial/pluto.png")
			#palette	= QtGui.QPalette()
			#palette.setBrush(QtGui.QPalette.Background,QtGui.QBrush(desktop_background))
			#self.setPalette(palette)
		#except:
			#pass
		self.showFullScreen()
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.status_list={}
		self.thread=xbox_controller(self) #start the xbox controller thread
		self.layouts = menu_layouts() # generate list of applications
		self.radial_mode() #innitialize radial menu
		QtGui.QIcon.setThemeName("Numix-Circle-Light")
		self.installEventFilter(self)
		# connect panic combo, a universal combination which will return you to main menu
		self.thread.panic.connect(self.panic)
	#functions for changing modes
	def clear(self): #clears al QPushButtons
		children=self.findChildren(QtGui.QWidget)
		for child in children: #clear child widgets
			child.setParent(None)
		if self.layout(): #i think this clears layouts
			a=QtGui.QWidget()
			a.setLayout(self.layout())
			a.deleteLater()
	
	def radial_mode(self): #radial menu mode
		self.clear()
		self.menu=radial_menu(self)
		self.mode='radial'
		self.showFullScreen() #full screen main interface
	def status_mode(self): #status mode
		self.clear()
		self.menu=status(self)
		self.mode='status'
		self.showFullScreen() #full screen main interface
	def search_mode(self): #search mode
		self.clear()
		self.menu=search(self)
		self.mode='search'
		self.showFullScreen() #full screen main interface
	def files_mode(self): #files mode
		self.clear()
		self.menu=files(self)
		self.mode='files'
	def applications_mode(self): #applications mode
		self.clear()
		self.menu=applications(self)
		self.mode='applications'
		self.hide()
	def applications_mode_no_controller(self): #applications mode
		self.clear()
		self.menu=applications_no_controller(self)
		self.mode='applications_no_controller'
		self.hide()
	def panic(self): #a panic function, this is accessible through all modes
		#os.execv("/home/eric/Dropbox/gui_programming/radial/radial_main_02_07.py",sys.argv) this is supposed to restart the whole program
		#self.hide() #get to fallout shelter
		#pywmctrl.close_all() #the nuclear option
		self.radial_mode()
		########################
	#def paintEvent(self,e): #this draws a fucking blue line
		#qp = QtGui.QPainter()
		#qp.begin(self)
		#self.drawLines(qp)
		#qp.end()
	#def drawLines(self, qp):
		#pen = QtGui.QPen(QtCore.Qt.blue, 2, QtCore.Qt.SolidLine)
		#qp.setPen(pen)
		#qp.drawLine(20, 40, 250, 40)
	def leave(self,exit_mode):
		#get settings path: default $HOME/.config/radial_de
		settings_path = subprocess.Popen("echo $HOME",shell=True, stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")[0]
		#save favorites
		children=self.layouts.tree.findall('.//button[@is_favorite="1"]')
		with open(settings_path+'/.config/radial_de/'+'favorites.txt', 'w') as favorites:
			favorites.writelines("%s\n" % child.attrib['name'] for child in children)
		#save controller settings
		children=self.layouts.tree.findall('.//button[@use_controller="0"]')
		with open(settings_path+'/.config/radial_de/'+'no_controller.txt', 'w') as no_controller:
			no_controller.writelines("%s\n" % child.attrib['name'] for child in children)
		#save settings 
		root=self.layouts.tree.find('.//button[@name="Settings"]')
		children=root.getchildren()
		with open(settings_path+'/.config/radial_de/'+'settings.txt', 'w') as settings_file:
			settings_file.writelines(child.attrib['name'] +" "+ child.attrib['value']+"\n" for child in children)
		#close
		if exit_mode=='shutdown':
			sys.exit(253)
		elif exit_mode=='reboot':
			sys.exit(254)
		elif exit_mode=='logout':
			sys.exit(255)
		self.close()
	def eventFilter(self, object, event):
		if event.type()== QtCore.QEvent.WindowDeactivate:
			print("main window has lost focus")
			if 'applications' not in self.mode:
				self.activateWindow()
		return(False)
if __name__=='__main__':
	app=QtGui.QApplication(sys.argv) 	#Create application object
	main_application_window=main_ui()#innitialize main window
	sys.exit(app.exec_())

