#!/usr/bin/env python3
##### 0-13
#TO DO:
	#0: NEEDS
		#way to shutdown computer, logout, etc
		#some way for this program to be restarted in case of crash
		#modify $XDG_DATA_DIRS to find a default icon theme
		#a more universal way to get menus and icons in different distros
		#a system tray and notification interface
		#if no joystick plugged in, pygame raises invalid device number error
		#cancel logout does not work
	#1: PROBABLY NEEDS
		#figure out the problem with clearing layouts, what i have now works, but its weird
		#applications, such as terminal emulators, have their working directory the same as this program, not optimal
	#2: WANTS
		#window manager
			#launch applications in full screen mode
			#maximize applications when launched
			#doesn't cleanup properly when launching xdg-open <file>
		#menu
			#add a function for main_ui to change title label and lower label maybe?
			#"remove from favorites" does not work in favorites menu. neither does set controller scheme.
			#right click event on buttons
			#mouseover is taken over by joystick, making it look funny
			#add more info in status menu, like cpu and memory usage, open applications memory usage etc
		#other
			#write your own keyboard
			#make things prettier
		#file manager
			#make icon change to go back
			#x button options:
				#cut
				#copy
				#paste
				#delete
				#open with
				#properties
				#open file manager here...
			#.. button loops forever on /
			#cache thumbnails
	#3: SHOULD PROBABLY DO
		#cleanup and minimize dependencies
			#use pyflakes to do this 
#DEBIAN DEPENDENCIES
#pyqt4-dev-tools
#python-lxml
#python-matplotlib
#python-pygame
#python-xlib
#wmctrl
#xdg stuff

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
from button import *
import warnings
	
class image_viewer(QtCore.QObject):
	def __init__(self,parent):
		super(image_viewer, self).__init__()
		self.init_image_viewer(parent)
	def init_image_viewer(self,parent):
		self.parent=parent
		
class radial_menu(QtCore.QObject):
	#this class creates buttons in a radial way
	def __init__(self,parent,node=None):
		super(radial_menu, self).__init__()
		self.init_radial_menu(parent)
	def init_radial_menu(self,parent,node=None):
		#self.layouts =layouts #contains directory information but also settings
		self.parent=parent
		self.resolution = QtGui.QDesktopWidget().screenGeometry()
		self.center=[self.resolution.width()/2,self.resolution.height()/2]
		self.radius=self.resolution.height()/2-64
		self.change_menu(node)
	def change_menu(self,node=None,btn_set=0): # change menu program
		#to do: make settings persistant
		#also, it would probably save some cpu time to only do this sometimes, like when in a settings sub directory
		#load some settings
		setting_nodes=self.parent.layouts.tree.findall('.//button[@name="Settings"]/button') #finds all children of node "settings"
		self.settings={}
		for setting in setting_nodes:
			self.settings[setting.attrib['name']]=setting.attrib['value']
		self.parent.clear() #remove all buttons
		if node==None: #try to go back to previous node
			try:
				node=self.parent.last_node
			except:
				node=self.parent.layouts.tree.find('.//button[@name="Home"]')
		elif node=='home':
			node=self.parent.layouts.tree.find('.//button[@name="Home"]')
		self.parent.last_node=node
		self.btns=[]
		#font
		font=QtGui.QFont()
		font.setFamily(self.settings['Font'])
		font.setPointSize(48)
		self.current_node=node
		#empty list of buttons to thumbnail
		self.to_thumbnail=[]
		self.parent
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
		#checking if we need to break this up into smaller groups
		self.btn_set=btn_set
		self.max_num_btns=20
		if num_btns>self.max_num_btns:
			#break into chunks of buttons
			btn_sets=[children[x:x+self.max_num_btns] for x in range(0, len(children), self.max_num_btns)]
			self.num_sets=len(btn_sets)
			children=btn_sets[self.btn_set]
			num_btns=len(children)
			#add left-right more buttons
			btn_left_more=button_more(-1,self.parent,self)
			btn_left_more.move(128-0.5*btn_left_more.width(),self.center[1]-0.5*btn_left_more.height())
			btn_left_more.show()
			btn_right_more=button_more(1,self.parent,self)
			btn_right_more.move(self.resolution.width()-128-0.5*btn_right_more.width(),self.center[1]-0.5*btn_right_more.height())
			btn_right_more.show()
			lr_more_btns=[btn_left_more,btn_right_more]
		else:
			lr_more_btns=[None,None]
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
			
		#title label
		label_text=node.attrib['name']
		try:
			if node.attrib['value']!="":
				label_text+=": " +node.attrib['value']
		except:
			pass
		try:
			label_text+=": "+str(self.btn_set+1)+" of "+str(len(btn_sets))
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
		
		#volume bar
		if node.attrib['name']=="Volume":
			volume_bar=QtGui.QProgressBar(self.parent)
			volume_bar.setValue(int(node.attrib['value']))
			volume_bar.setOrientation(2)
			volume_bar.move(32,title_label.height()+32)
			volume_bar.resize(title_label.height(),self.resolution.height()-title_label.height()-64-self.lower_label.height())
			volume_bar.setTextVisible(False)
			volume_bar.show()
		
		self.set_lower_label()
		# Xbox interface stuff
		self.parent.xbox_actions_master=xbox_actions_in_radial(self.btns,self.parent,lr_more_btns) #class which controls xbox inpput, each time it is recreated, the actions get reassigned
		self.parent.thread.button_signal_up.connect(self.parent.xbox_actions_master.btn_action)
		self.parent.thread.lstick_signal_continuous.connect(self.parent.xbox_actions_master.lstick_action)
		#generate thumbnails
		if len(self.to_thumbnail)>0:
			self.parent.thumb_thread=generate_thumbnails(self)
			self.parent.thumb_thread.thumbnail_signal.connect(self.parent.make_thumbnail)
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
	def help():
		pass
class generate_thumbnails(QtCore.QThread):
	thumbnail_signal=QtCore.pyqtSignal(button,QtGui.QImage)
	def __init__(self, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.parent=parent
		self.exiting = False
		self.start()
	def __del__(self):
		self.exiting = True
		self.wait()
	def run(self):
		for btn in self.parent.to_thumbnail:
			image_file=btn.get_thumbnail()
			image = QtGui.QImage(image_file)
			self.thumbnail_signal.emit(btn, image)
	
	
class status(QtCore.QObject):
	#TODO: get title label to be consistent with every other title label, maybe make a function for main ui to handle this
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
		title_label=QtGui.QLabel('Status',self.parent) 
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
	def change_menu(self,ignore_this): #what the fuck is this?
		self.parent.radial_mode()
	

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

class configure_controller(QtCore.QObject):
	#this class creates buttons in a radial way
	def __init__(self,parent):
		super(configure_controller, self).__init__()
		self.init_configure_controller(parent)
	def init_configure_controller(self,parent):
		#self.layouts =layouts #contains directory information but also settings
		self.parent=parent
		self.resolution = QtGui.QDesktopWidget().screenGeometry()
		self.center=[self.resolution.width()/2,self.resolution.height()/2]
		#controller label
		background=QtGui.QPixmap(os.environ['HOME'] +'/.config/radial_de/controller_diagram_minimal.png')
		controller_label=QtGui.QLabel("",self.parent)
		controller_label.setPixmap(background)
		controller_label.resize(controller_label.sizeHint())
		controller_label.move(self.center[0]-controller_label.width()/2,self.center[1]-controller_label.height()/2)
		controller_label.show()
		#add combo boxes
		b_combo_box=QtGui.QComboBox(self.parent)
		b_combo_box.move(self.center[0]-controller_label.width()/2+795,self.center[1]-controller_label.height()/2+140)
		b_combo_box.addItem(QtGui.QIcon.fromTheme('go-previous'),"")
		b_combo_box.show()
		#i'll do this for each button, make my own icons for xbox buttons, and try and figure that shit out
class main_ui(QtGui.QWidget):
	########## MAIN UI ##########
	def __init__(self):
		super(main_ui, self).__init__()
		self.init_ui()
	def init_ui(self):
		QtGui.QMainWindow.__init__(self, None)
		#load a file icon dict, since using xdg lookup is painfully slow
		try:
			with open(os.environ['HOME']+'/.config/radial_de/'+"file_icons.INI") as file_icons_file:
				file_icons_file=[setting.rstrip("\n") for setting in settings_file.readlines()]
		except:
			file_icons_file=[]
		self.file_icons_dict={}
		for line in file_icons_file:
			line=line.rsplit(" ",1)
			self.file_icons_dict[line[0]]=line[1]
		#show main window
		self.showFullScreen()
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.status_list={}
		self.thread=xbox_controller(self) #start the xbox controller thread
		self.layouts = menu_layouts() # generate list of applications
		self.radial_mode("home") #innitialize radial menu
		#QIcon.setThemeSearchPaths <------------------ use this to avoid weird icon problem
		QtGui.QIcon.setThemeName("Numix-Circle-Light")
		#set a list of supported image formats
		self.supported_image_formats = [str(fmt).split("'")[1] for fmt in QtGui.QImageReader.supportedImageFormats()]
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
	
	def radial_mode(self,node=None): #radial menu mode
		self.clear()
		self.menu=radial_menu(self,node)
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
	def image_viewer_mode(self):
		self.clear()
		self.menu=image_viewer(self)
		self.mode='image_viewer'
		self.showFullScreen()
	def configure_controller_mode(self):
		self.clear()
		self.menu=configure_controller(self)
		self.mode='configure_controller'
		self.showFullScreen()
		
	def panic(self): #a panic function, this is accessible through all modes
		#self.hide()
		#pywmctrl.close_all() #the nuclear option
		self.close()
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
	def leave(self,exit_mode): #saves settings in various .INI files, which are loaded by menu layouts
		
		
		#get settings path: default $HOME/.config/radial_de
		settings_path = subprocess.Popen("echo $HOME",shell=True, stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")[0]
		#check to see if /.config/radial_de/ is made
		if '.config' not in os.listdir(settings_path):
			os.mkdir(settings_path +'/.config')
		if 'radial_de' not in os.listdir(settings_path+'/.config'):
			os.mkdir(settings_path+'/.config/radial_de')
		#save favorites
		children=self.layouts.tree.findall('.//button[@is_favorite="1"]')
		with open(settings_path+'/.config/radial_de/'+'favorites.INI', 'w') as favorites:
			favorites.writelines("%s\n" % child.attrib['name'] for child in children)
		#save controller settings
		children=self.layouts.tree.findall('.//button[@use_controller="0"]')
		with open(settings_path+'/.config/radial_de/'+'no_controller.INI', 'w') as no_controller:
			no_controller.writelines("%s\n" % child.attrib['name'] for child in children)
		#save settings 
		root=self.layouts.tree.find('.//button[@name="Settings"]')
		children=root.getchildren()
		with open(settings_path+'/.config/radial_de/'+'settings.INI', 'w') as settings_file:
			settings_file.writelines(child.attrib['name'] +" "+ child.attrib['value']+"\n" for child in children)
		#save settings 
		with open(settings_path+'/.config/radial_de/'+'file_icons.INI', 'w') as settings_file:
			settings_file.writelines(key +" "+ self.file_icons_dict[key]+"\n" for key in self.file_icons_dict.keys())
		#close
		self.close()
		#if exit_mode=='shutdown':
			#sys.exit(253)
		#elif exit_mode=='reboot':
			#sys.exit(254)
		#elif exit_mode=='logout':
			#sys.exit(255)
		#self.close()
	def eventFilter(self, object, event):
		if event.type()== QtCore.QEvent.WindowDeactivate:
			print("main window has lost focus")
			if 'applications' not in self.mode:
				self.activateWindow()
		return(False)
	def make_thumbnail(self,btn,image):
		pixmap = QtGui.QPixmap(72, 72)
		pixmap.convertFromImage(image) #   <-- This is the magic function!
		icon = QtGui.QIcon(pixmap)
		btn.setIcon(icon)
		print('making thumbnail')
		#found the solution here
		#http://stackoverflow.com/questions/4611239/pyqt-how-do-i-handle-qpixmaps-from-a-qthread

if __name__=='__main__':
	app=QtGui.QApplication(sys.argv) 	#Create application object
	main_application_window=main_ui()#innitialize main window
	sys.exit(app.exec_())

