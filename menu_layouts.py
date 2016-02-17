import xml.etree.ElementTree as ET
from lxml import etree
from PyQt4 import QtGui, QtCore
import os
import matplotlib.font_manager
import subprocess
import pyamixer
import platform
from xdg import *
class menu_layouts():
	def __init__(self):
		#self.tree = etree.parse(os.environ['HOME']+'/.config/radial_de/menu_tree.xml') #change this path
		self.tree = etree.parse(os.environ['HOME']+'/Dropbox/gui_programming/radial/menu_tree.xml') #change this path
		self.settings_path = subprocess.Popen("echo $HOME",shell=True, stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")[0]
		#put something here to detect if arch or debian maybe
		self.get_application_data()
		self.get_system_fonts() #listing system_fonts
		self.load_settings()
		self.root = self.tree.getroot()
	def load_settings(self):
		try:
			with open(os.environ['HOME']+'/.config/radial_de/'+"settings.INI") as settings_file:
				settings_file=[setting.rstrip("\n") for setting in settings_file.readlines()]
		except:
			settings_file=[]
		for setting in settings_file:
			setting=setting.rsplit(" ",1)
			root=self.tree.find('.//button[@name="'+setting[0]+'"]')
			if root!=None:
				root.attrib['value']=setting[1]
			volume_root=self.tree.find('.//button[@name="Volume"]')
			volume_root.attrib['value']=str(pyamixer.get_level('Master'))
			
	def get_system_fonts(self):
		font_root=self.tree.find('.//button[@name="Font"]')
		list_of_fonts=matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
		for font in list_of_fonts:
			font=font.split('/')[-1]
			font=font.split('.')
			font_type=font[1]
			font=font[0].split('-')
			font_name=font[0]
			if len(font)==2:
				font_style=font[1]
			else:
				font_style="Regular"
			if font_type=='ttf' and font_style=="Regular":
				child = etree.SubElement(font_root, "button")
				child.attrib['name']=font_name
				child.attrib['type']="setting"
				child.attrib['subtype']="font"
				child.attrib['icon']='none'
				child.attrib['tool_tip']=font_name
				child.attrib['setting']=font_name
				child.attrib['value']=font_name
	def get_application_data(self):
		dist=platform.dist()[0]
		if dist=='arch':
			self.get_application_data_arch()
		elif dist=='debian':
			self.get_application_data_debian()
	def get_application_data_debian(self):
		#debian function, uses python-xdg package
		try:
			with open(os.environ['HOME']+'/.config/radial_de/'+"favorites.INI") as favorites:
				favorites=[fav.rstrip("\n") for fav in favorites.readlines()]
		#except(FileNotFoundError):
		except:
			favorites=[]
		try:
			with open(os.environ['HOME']+'/.config/radial_de/'+"no_controller.INI") as no_controller:
				no_controller=[app.rstrip("\n") for app in no_controller.readlines()]
		#except(FileNotFoundError):
		except:
			no_controller=[]
		#using xdg to get menu
		home_root=self.tree.find('.//button[@name="Home"]')
		root_menu=Menu.parse("/etc/xdg/menus/debian-menu.menu")
		apps_menu=root_menu.getMenu("Applications")
		icon=str(apps_menu.getIcon())
		child=etree.SubElement(home_root,"button")
		child.attrib['name']="Applications"
		child.attrib['type']="menu"	
		child.attrib['icon']=str(apps_menu.getIcon())
		child.attrib['tool_tip']="Applications"
		apps_root=child
		for submenu in apps_menu.Entries:
			submenu_name=submenu.getName()
			child=etree.SubElement(apps_root,"button")
			child.attrib['name']=submenu_name
			child.attrib['icon']=str(submenu.getIcon())
			child.attrib['type']="menu"
			child.attrib['tool_tip']=submenu_name
			cat_root=child
			for app in submenu.Entries:
				try:
					name=str(app.DesktopEntry.getName())
					child=etree.SubElement(cat_root,"button")
					
					child.attrib['name']=name
					child.attrib['tool_tip']="a: launch "+name+"\nx: application options"
					child.attrib['icon']=str(app.DesktopEntry.getIcon())
					child.attrib['type']="application"
					if name in no_controller: #controler use
						child.attrib['use_controller']="0"
					else:
						child.attrib['use_controller']="1"
					if name in favorites: #favorites
						child.attrib['is_favorite']="1"
					else:
						child.attrib['is_favorite']="0"
					child.attrib['exec']=str(app.DesktopEntry.getExec())
				except(AttributeError):
					pass
	def get_application_data_arch(self):
		#this gets application data from both desktop files and xdg menu
		#modified to use xdg
		#getting icons from desktop files
		desktop_files=os.listdir('/usr/share/applications')
		self.icon_dict={"Accessibility": "preferences-desktop-accessibility", "Applications":"open-menu","Programming":"applications-development","Sound & Video":"applications-multimedia","System Tools":"applications-system"}
		for desktop_file in desktop_files:
			if '.desktop' in desktop_file and desktop_file[0]!='.':
				path='/usr/share/applications/' + desktop_file
				with open(path,encoding='utf-8', errors='ignore') as desktop:
					#desktop = open(path).readlines()
					desktop = [line.rstrip('\n').split(',') for line in desktop.readlines()]
				name=''
				icon=''
				for line in desktop:
					if line[0][0:5]=='Name=' and name=='':
						name=line[0][5:]
					elif line[0][0:5]=='Icon=':
						icon=line[0][5:]
				self.icon_dict[name.lower()]=icon
				self.icon_dict[desktop_file]=icon
		#create open list of favorites 
		try:
			with open(os.environ['HOME']+'/.config/radial_de/'+"favorites.INI") as favorites:
				favorites=[fav.rstrip("\n") for fav in favorites.readlines()]
		#except(FileNotFoundError):
		except:
			favorites=[]
		try:
			with open(os.environ['HOME']+'/.config/radial_de/'+"no_controller.INI") as no_controller:
				no_controller=[app.rstrip("\n") for app in no_controller.readlines()]
		#except(FileNotFoundError):
		except:
			no_controller=[]
		#using xdg to get menu
		try:
			output = subprocess.Popen(["xdg_menu", "--fullmenu"], stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")
		except:
			output = str(subprocess.Popen(["xdg_menu", "--fullmenu"], stdout=subprocess.PIPE).communicate()[0]).split("\n")
		home_root=self.tree.find('.//button[@name="Home"]')
		for line in output:
			line=line.strip("\n")
			if "MENU" in line:
				line=line.split('"')
				child=etree.SubElement(home_root,"button")
				child.attrib['name']=line[1]
				child.attrib['type']="menu"
				try:
					child.attrib['icon']=self.icon_dict[line[1]]
				except(KeyError):
					child.attrib['icon']="applications-"+line[1].lower()
				child.attrib['tool_tip']=line[1]
				if line[1]=="Applications":
					home_root=child
				root=child
			elif "EXEC" in line:
				line=line.split('EXEC')
				name=line[0]
				name=name.lstrip(" ")
				name=name.rstrip(" ")
				name=name.strip('"')
				execute=line[1]
				execute=execute.lstrip(" ")
				child = etree.SubElement(root, "button")
				child.attrib['name']=name
				try:
					child.attrib['icon']=self.icon_dict[name.lower()]
				except(KeyError):
					child.attrib['icon']="applications-accessories"
				child.attrib['tool_tip']="a: launch "+name+"\nx: application options"
				child.attrib['type']="application"
				if name in no_controller: #controler use
					child.attrib['use_controller']="0"
				else:
					child.attrib['use_controller']="1"
				if name in favorites: #favorites
					child.attrib['is_favorite']="1"
				else:
					child.attrib['is_favorite']="0"
				child.attrib['exec']=execute #execute command
				

