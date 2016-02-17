from PyQt4 import QtCore, QtGui
from lxml import etree
import sys
sys.path.insert(0, '/home/eric/Dropbox/gui_programming/PyUserInput-master')
from pykeyboard import PyKeyboard
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
		self.setFocusPolicy(QtCore.Qt.NoFocus)
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
class keyboard(QtGui.QWidget):
	def __init__(self):
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
		self.setFocusPolicy(QtCore.Qt.NoFocus)
		self.show()
app = QtGui.QApplication([]) 
widget = keyboard() 
widget.show()
app.exec_()
