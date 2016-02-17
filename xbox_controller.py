#from PyQt4.QtCore import *
from PyQt4 import QtCore
from PyQt4 import QtGui
import pygame
import os
import time
import sys
import numpy as np
import subprocess
from lxml import etree
#sys.path.insert(0, os.environ['HOME']+'/.config/radial_de/PyUserInput-master') #Pyuserinput finally seems to get everything to work!
sys.path.insert(0, os.environ['HOME']+'/Dropbox/gui_programming/PyUserInput-master') #Pyuserinput finally seems to get everything to work!

from pymouse import PyMouse
from pykeyboard import PyKeyboard
import pywmctrl
class xbox_controller(QtCore.QThread):
	# this class monitors the xbox controller for values
	# the actions assigned to each button are in xbox_actions class
	#rstick_signal=pyqtSignal(list)
	panic=QtCore.pyqtSignal()
	lstick_signal=QtCore.pyqtSignal(list) #signal for left stick
	lstick_signal_continuous=QtCore.pyqtSignal(list) #continuouus monitoring version
	rstick_signal=QtCore.pyqtSignal(list) #signal for right stick
	rstick_signal_continuous=QtCore.pyqtSignal(list) #continuouus monitoring version
	button_signal_up=QtCore.pyqtSignal(list) #signal for button press event
	button_signal_down=QtCore.pyqtSignal(list) #signal for button press event
	def __init__(self, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.parent=parent
		self.exiting = False
		self.start()
	def __del__(self):
		self.exiting = True
		self.wait()
	def run(self):
		#setup
		os.environ["SDL_VIDEODRIVER"] = "dummy" #this line allows usage of pygame without window	
		pygame.init() #innitialize pygame
		pygame.joystick.init() # Initialize the joysticks
		done = False
		#lpress=False
		while done==False:
			#innitialize joystick
			joystick_count = pygame.joystick.get_count()
			self.parent.status_list['joysticks']=joystick_count
			joystick = pygame.joystick.Joystick(0)
			joystick.init()
			name = joystick.get_name()
			xbox_axes = joystick.get_numaxes()
			xbox_btns = joystick.get_numbuttons()
			# EVENT PROCESSING STEP
			xbox_joystick_values=[joystick.get_axis(i) for i in range(xbox_axes)]
			
			self.lstick_signal_continuous.emit([xbox_joystick_values[0],xbox_joystick_values[1]])
			self.rstick_signal_continuous.emit([xbox_joystick_values[3],xbox_joystick_values[4]])
			for event in pygame.event.get(): # User did something
				#if event.type == pygame.QUIT: # If user clicked close
					#done=True # Flag that we are done so we exit this loop
				# Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
				if event.type == pygame.JOYBUTTONDOWN:
					xbox_btn_values=[joystick.get_button(i) for i in range(xbox_btns)]
					
					if xbox_btn_values==[0,0,0,0,1,1,1,1,0,0,0,0,0,0,0]: #panic combo
						self.panic.emit()
					self.button_signal_down.emit(xbox_btn_values)
				if event.type == pygame.JOYBUTTONUP:
					self.button_signal_up.emit(xbox_btn_values)
				if event.type== pygame.JOYAXISMOTION:
					self.lstick_signal.emit([xbox_joystick_values[0],xbox_joystick_values[1]])#these only emit if change in axis detected
					self.rstick_signal.emit([xbox_joystick_values[3],xbox_joystick_values[4]])
				#these emit every loop
			
			#axes value update
			###### axes: #####
			#axis 0: left stick left(-1) right(+1)
			#axis 1: left stick up(-1) down(+1)
			#axis 2: left trigger released(-1) pressed(1)
			#axis 3: right stick left(-1) right(+1)
			#axis 4: right stick up(-1) down(+1)
			#axis 5: right trigger released(-1) pressed(1)
				#emit(SIGNAL("output(QObject,QObject)"),rs_x,rs_y)
			##### buttons: #####
			#button 0: A
			#button 1: B
			#button 2: X
			#button 3: Y
			#button 4: LB
			#button 5: RB
			#button 6: BACK
			#button 7: START
			#button 8: CENTER BUTTON
			#button 9: LS
			#button 10: RS
			#button 11: Dpad left
			#button 12: Dpad right
			#button 13: Dpad up
			#button 14: Dpad down
			#button value update
			time.sleep(0.02)
			
class xbox_actions_in_radial():
	#defines actions for xbox controller in radial menu
	def __init__(self,buttons=[],parent=None,lr_more_btns=[]): #innitialize
		self.btns=buttons
		self.parent=parent
		self.max_btn=self.btns[0]
		self.max_btn.hovered(1)
		self.lr_more_btns=lr_more_btns
		#self.max_btn.raise()
	def lstick_action(self,v): #left stick action
		j=0
		max_ip=0
		for btn in self.btns:
			btn_node=btn.node
			btn_ip=v[0]*float(btn_node.attrib['vector_x'])+v[1]*float(btn_node.attrib['vector_y'])
			if btn_ip>max_ip:
				self.max_btn=btn
				max_ip=btn_ip
			j+=1
		if max_ip<0.5:
			self.max_btn=self.btns[0]
		for btn in self.btns:
			if btn==self.max_btn:
				self.max_btn.hovered(1) 
			else:
				btn.hovered(0)	
	def btn_action(self,button_values):
		if button_values[0]==1: #A
			self.max_btn.act()
		elif button_values[1]==1: #B
			self.btns[0].act() 
		elif button_values[2]: #X
			self.max_btn.act_x()
		elif button_values[3]: #Y
			pass
		elif button_values[4]: #LB
			if self.lr_more_btns[0]!=None:
				self.lr_more_btns[0].act()
		elif button_values[5]: #RB
			if self.lr_more_btns[1]!=None:
				self.lr_more_btns[1].act()
		elif button_values[6]: #BACK
			pass
		elif button_values[7]: #START
			pass
		elif button_values[8]: #CENTER
			self.parent.radial_mode(node="home")
			print('going home')
		elif button_values[9]: #LS
			pass
		elif button_values[10]: #RS
			pass
		elif button_values[11]: #DL
			pass
		elif button_values[12]: #DR
			pass
		elif button_values[13]: #DU
			pass
		elif button_values[14]: #DD
			pass

class xbox_actions_in_status():
	#defines actions for xbox controller in status menu
	def __init__(self,buttons=[]): #innitialize
		self.btns=buttons
		self.max_btn=self.btns[0]
		self.max_btn.hovered(1)
	
	def btn_action(self,button_values):
		if button_values[0]==1: #A
			self.max_btn.act()
		elif button_values[1]==1: #B
			self.btns[0].act()
		elif button_values[2]: #X
			pass
		elif button_values[3]: #Y
			pass
		elif button_values[4]: #LB
			pass
		elif button_values[5]: #RB
			pass
		elif button_values[6]: #BACK
			pass
		elif button_values[7]: #START
			pass
		elif button_values[8]: #CENTER
			pass
		elif button_values[9]: #LS
			pass
		elif button_values[10]: #RS
			pass
		elif button_values[11]: #DL
			pass
		elif button_values[12]: #DR
			pass
		elif button_values[13]: #DU
			pass
		elif button_values[14]: #DD
			pass

class xbox_actions_in_applications(): 
	#defines actions for xbox controller in status menu
	def __init__(self,parent): #innitialize
		self.parent=parent
		self.cursor_speed=int(parent.settings['Cursor Speed'])
		self.mouse=PyMouse()
		self.keyboard=PyKeyboard()
	def lstick_action(self,lstick_values): #left stick action
		v=[np.sign(a)*a**2*(abs(a**2)>0.05) for a in lstick_values] #this is a temporary fix, later, ill implement something so that it compares joystick values to previous values in loop
		self.mouse_pos=self.mouse.position()
		self.mouse.move(int(self.mouse_pos[0]+self.cursor_speed*v[0]),int(self.mouse_pos[1]+self.cursor_speed*v[1]))
	def rstick_action(self,rstick_values): #left stick action
		#It would be nice to slow this down a lot
		v=[np.ceil(2*a*(abs(a)>0.33)) for a in rstick_values] #this is a temporary fix, later, ill implement something so that it compares joystick values to previous values in loop
		self.mouse.scroll(vertical=-v[1],horizontal=v[0])
	def btn_action_down(self,button_values):
		if button_values[0]==1: #A
			self.mouse.press(self.mouse_pos[0], self.mouse_pos[1], 1)
		elif button_values[1]==1: #B
			self.keyboard.press_key("BackSpace")
		elif button_values[2]: #X
			self.mouse.press(self.mouse_pos[0], self.mouse_pos[1], 2)
		elif button_values[3]: #Y
			pass
		elif button_values[4]: #LB
			pass #move to desktop left on up
		elif button_values[5]: #RB
			pass #move to desktop right on up
		elif button_values[6]: #BACK
			pass #open keyboard on up
		elif button_values[7]: #START
			pass
		elif button_values[8]: #CENTER
			self.parent.parent.radial_mode()
		elif button_values[9]: #LS
			pass
		elif button_values[10]: #RS
			pass
		elif button_values[11]: #DL
			self.keyboard.press_key("Left")
		elif button_values[12]: #DR
			self.keyboard.press_key("Right")
		elif button_values[13]: #DU
			self.keyboard.press_key("Up")
		elif button_values[14]: #DD
			self.keyboard.press_key("Down")
	def btn_action_up(self,button_values):
		if button_values[0]==1: #A
			self.mouse.release(self.mouse_pos[0], self.mouse_pos[1], 1)
			self.a_down=0
		elif button_values[1]==1: #B
			self.keyboard.release_key("BackSpace")
		elif button_values[2]: #X
			self.mouse.release(self.mouse_pos[0], self.mouse_pos[1], 2)
			self.x_down=0
		elif button_values[3]: #Y
			pass
		elif button_values[4]: #LB
			pywmctrl.move_to_desktop_left()
		elif button_values[5]: #RB
			pywmctrl.move_to_desktop_right()
		elif button_values[6]: #BACK
			keyboard_thread=launch_keyboard(self.parent)
			#widget = my_keyboard(self.parent.parent) 
		elif button_values[7]: #START
			pass
		elif button_values[8]: #CENTER
			self.parent.parent.radial_mode()
		elif button_values[9]: #LS
			pass
		elif button_values[10]: #RS
			pass
		elif button_values[11]: #DL
			self.keyboard.release_key("Left")
		elif button_values[12]: #DR
			self.keyboard.release_key("Right")
		elif button_values[13]: #DU
			self.keyboard.release_key("Up")
		elif button_values[14]: #DD
			self.keyboard.release_key("Down")
class launch_keyboard(QtCore.QThread):
	def __init__(self, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.parent=parent
		self.exiting = False
		self.start()
	def run(self):
		subprocess.call("onboard") #find a good keyboard for this
		#subprocess.call("kvkbd") #find a good keyboard for this
		#subprocess.call("matchbox-keyboard")
		#or get yours to work
class xbox_actions_none():
	#this class is really a dummy to destroy connections used in other modes
	def __init__(self): #innitialize
		pass


#### THIS IS SOME BULL SHIT TO MAKE YOUR OWN STUPID KEYBOARD WORK
class keyboard_button(QtGui.QPushButton):
	def __init__(self,parent,xml_node):
		super(keyboard_button, self).__init__()
		self.init_keyboard_button(parent,xml_node)
	def init_keyboard_button(self,parent,xml_node):
		self.parent=parent
		self.xml_node=xml_node
		
		size=[48,48]
		if xml_node.attrib['subtype']=="symbol":
			self.name=self.xml_node.attrib['name']
			self.shift_name=self.xml_node.attrib['shift_name']
			if self.name=="7":
				self.shift_name="&"
			elif self.name==",":
				self.shift_name="<"
			elif self.name==".":
				self.shift_name=">"
			elif self.name=="apostrophe":
				self.name="'"
				self.shift_name='"'
			QtGui.QPushButton.__init__(self,self.shift_name+'\n'+self.name ,self.parent)
		else:
			self.name=self.xml_node.attrib['name']
			QtGui.QPushButton.__init__(self,self.name,self.parent)
		self.setMinimumSize(int(float(self.xml_node.attrib['size'])*size[0]),size[1])
		#self.setFocusPolicy(QtCore.Qt.NoFocus)
		self.setFocusProxy(self.parent.focusProxy())
		#self.setMaximumSize(int(float(xml_node.attrib['size'])*size[0]),size[1])
		self.clicked.connect(self.act_press)
		self.released.connect(self.act_release)
	def act_press(self):
		self.subtype=self.xml_node.attrib['subtype']
		if self.subtype=="close":
			self.close()
		elif self.subtype=="special":
			#special key bindings go here
			pass
		elif self.subtype=="letter":
			self.parent.keyboard.press_key(self.name)
		elif self.subtype=="symbol":
			pass
	def act_release(self):
		self.subtype=self.xml_node.attrib['subtype']
		if self.subtype=="close":
			self.close()
		elif self.subtype=="special":
			#special key bindings go here  
			pass
		elif self.subtype=="letter":
			self.parent.keyboard.release_key(self.name)
		elif self.subtype=="symbol":
			pass
	def shift(self):
		pass
class my_keyboard(QtGui.QWidget):
	def __init__(self,parent):
		super(my_keyboard, self).__init__()
		self.init_keyboard(parent)
	def init_keyboard(self,parent):
		self.parent=parent
		self.setFocusProxy(self.parent)
		QtGui.QWidget.__init__(self,None,QtCore.Qt.WindowStaysOnTopHint)
		vbox=QtGui.QVBoxLayout()
		self.tree = etree.parse('keyboard.xml')
		self.keyboard=PyKeyboard()
		self.root = self.tree.getroot()
		self.button_list=[]
		self.shift=0
		self.capslock=0
		for child in self.root.getchildren(): #row loop
			row_box=QtGui.QHBoxLayout()
			row_list=[]
			for grandchild in child.getchildren(): #button loop
				button=keyboard_button(self,grandchild)
				row_box.addWidget(button)
				row_list.append(button)
			vbox.addLayout(row_box)
			self.button_list.append(row_list) #i'll use this for controlling keyboard with joystick
		self.setLayout(vbox)
		self.resize(self.minimumSizeHint())
		self.setFixedSize(self.width(),self.height())
		#self.setFocusPolicy(QtCore.Qt.NoFocus)
		
		self.show()
