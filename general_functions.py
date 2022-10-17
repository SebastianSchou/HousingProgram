#!/usr/bin/env python3
import math
import sys
import os
from time import sleep
import numpy as np
import tkinter as tk
from tkinter import ttk
import requests
import re

def toInt(string, returnValue = 0):
		# Removes danish dots and converts to int.
		# Argument:
		#		- string: Number to be convereted (string)
		# Returns:
		#		- Number as int (int)
		if isinstance(string, int):
				return string
		number = string.replace(".", "")
		if number.isdigit():
				return int(number)
		return returnValue

def toFloat(string, decimals = "All"):
		# Replaces danish commas with dots and converts to float.
		# Argument:
		#		- string: Number to be convereted (string)
		# Returns:
		#		- Number as float (float)
		if isinstance(string, float):
				return string
		if isinstance(string, int):
				return float(string)
		number = string.replace(",", ".")
		try:
				if decimals != "All" and isinstance(decimals, int):
						return round(float(number), decimals)
				else:
						return float(number)
		except:
				return 0.0

def addDecimalSeparator(number):
		return '{0:,}'.format(number)

def removeDecimalSeperator(string):
		if isinstance(string, int):
				return string
		try:
				s = string.replace(",", "")
				if "." in s:
						return round(float(s))
				else:
						return int(s)
		except:
				return string

def roundToValue(value, roundValue, rounding = "round"):
		if rounding == "ceil":
				val = math.ceil(float(value) / roundValue)
		elif rounding == "floor":
				val = math.floor(float(value) / roundValue)
		else:
				val = round(float(value) / roundValue)
		if isinstance(value, int):
				return int(val) * roundValue
		return float(int(val)) * roundValue

def haversine(lon1, lat1, lon2, lat2):
		# Get distances between coordinates
		# arguments:
		#		- lon1: Longitude 1 (Pandas series or float)
		#		- lat1: Latitude 1 (Pandas series or float)
		#		- lon2: Longitude 2 (Pandas series or float)
		#		- lat2: Latitude 2 (Pandas series or float)
		# returns:
		#		- Series of distances or distance as float

		# Map coordinates
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # Get differences
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Get angles
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    # Calculate distance
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    
    return km

def createScrollableCanvas(container, color, width = None, name = None):
		# Create canvas
		canvas = tk.Canvas(container,
											 highlightthickness=0,
											 bg=color)

		# Create frame
		frame = tk.Frame(canvas, bg=color)

		# Set width is specified
		hasStaticWidth = width is not None
		if hasStaticWidth:
				frame.config(width=width)
				canvas.config(width=width)

		# Function to scroll, while avoiding being able to scroll above canvas
		def _yview(*args):
				if canvas.yview() == (0.0, 1.0):
						return
				canvas.yview(*args)

		def _onCanvasConfigure(event):
				if hasStaticWidth or frame.winfo_width() == event.width:
						return
				frame.config(width=event.width)
				canvas.yview_moveto(0)

		canvas.bind("<Configure>", _onCanvasConfigure)

		# Create scrollbar
		scrollbar = ttk.Scrollbar(container, 
														  orient="vertical",
														  command=_yview)
		scrollbar.grid(column=1, row=0, sticky="ns")
		
		if hasStaticWidth:
				container.update()
				label = tk.Label(container, image=tk.PhotoImage(width=1, height=1),
												 text="", width=scrollbar.winfo_width() - 4, compound="c",
												 background=color, highlightthickness=0)
				label.grid(column=1, row=0, sticky="ns")

		scrollbar.grid_forget()

		def _onConfigure(event):
				canvas.itemconfig(canvasFrame, width=canvas.winfo_width())
				canvas.configure(scrollregion=canvas.bbox("all"))
				if event.width <= 1 or canvas.winfo_height() == 1:
						return
				if frame.winfo_height() <= canvas.winfo_height():
						scrollbar.grid_forget()
						if hasStaticWidth:
								label.grid(column=1, row=0, sticky="ns")
				elif scrollbar.winfo_viewable() == 0:
						scrollbar.grid(column=1, row=0, sticky="ns")
						if hasStaticWidth:
								label.grid_forget()

		# Configure scroll region
		frame.bind("<Configure>", _onConfigure)

		# Binding function to activate or deactivate scrolling on entering
		# and leaving canvas
		def _bindMouseWheel(event):
				canvas.bind_all("<MouseWheel>", _onMouseWheel)

		def _unbindMouseWheel(event):
				canvas.unbind_all("<MouseWheel>")

		def _onMouseWheel(event):
				if frame.winfo_height() > canvas.winfo_height():
						canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

		# Bind enter and leave
		canvas.bind("<Enter>", _bindMouseWheel)
		canvas.bind("<Leave>", _unbindMouseWheel)

		# Set window
		canvasFrame = canvas.create_window((0, 0), window=frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)

		# Insert filter canvas
		canvas.grid(column=0, row=0, sticky="nsew")
		container.grid_columnconfigure(0, weight=1)
		container.grid_rowconfigure(0, weight=1)

		return frame

def getGridRow(frame):
		return frame.grid_size()[1]

def bindAfterEntry(root, entry, afterId, function, time = 500, default = 0):
		def wait(event):
				if afterId[0] is not None:
						root.after_cancel(afterId[0])
				if entry.get() != "":
						afterId[0] = root.after(time, function)
				
		def lostFocus(event):
				if entry.get() == "":
						entry.insert(0, str(default))
						afterId[0] = root.after(0, function)

		entry.bind("<KeyRelease>", wait)
		entry.bind("<FocusOut>", lostFocus)

def bindAfter(root, widget, afterId, function, bindKey, time = 500):
		def wait(event):
				if afterId[0] is not None:
						root.after_cancel(afterId[0])
				afterId[0] = root.after(time, lambda: function(event))

		widget.bind(bindKey, wait)

def validateFloat(P):
		try:
				float(P)
				return True
		except:
				return str.isdigit(P) or P == ""

def validateInt(P):
		return str.isdigit(P) or P == ""

def getCurrentDirectory():
		if hasattr(sys, "_MEIPASS"):
				return sys._MEIPASS
		return os.path.dirname(os.path.realpath(__file__))

def getAppDirectory():
		if hasattr(sys, "_MEIPASS"):
				homePath = os.path.abspath(os.path.expanduser("~"))
				appDir = os.path.join(homePath, f".housing_app")
				if not os.path.exists(appDir):
						os.mkdir(appDir)
				return appDir
		return os.path.dirname(os.path.realpath(__file__))

def postalCodeRegionDk(postalCode):
		if not isinstance(postalCode, (int, float)):
				return "Ukendt"
		if postalCode < 3000:
				return "København"
		elif postalCode < 3700:
				return "Nordsjælland"
		elif postalCode < 3800:
				return "Bornholm"
		elif postalCode < 4000:
				return "Færøerne/Grønland"
		elif postalCode < 5000:
				return "Sjælland"
		elif postalCode < 6000:
				return "Fyn"
		elif postalCode < 7000:
				return "Sønderjylland"
		elif postalCode < 8000:
				return "Midtjylland"
		elif postalCode < 9000:
				return "Østjylland"
		elif postalCode < 10000:
				return "Nordjylland"
		else:
				return "Ukendt"

def getSiteData(website):
		# Return website response. If request fails, the function tries three
		# times more
		# Argument:
		#		- website: Name of website (string)
		# Returns:
		#		- Request response (requests class)

		# Get website response
		resp = requests.get(website)

		# If request failed, try three more times
		tries = 0
		while resp.status_code != 200 and tries < 3:
				resp = requests.get(website)
				tries += 1

		return resp

def getAddressSplit(name):
		floor = None
		floorNo = None
		try:
				numberIdx = re.search(r"[0-9]+", name).start()
		except:
				return name, floor, floorNo

		nameSplit = name[numberIdx:].split(" ")
		name = name[:numberIdx] + nameSplit[0]
		if name[-1] in [".", ","]:
				name = name[:-1]
		nameSplit = nameSplit[1:]
		if len(nameSplit) > 0:
				floorTemp = nameSplit[0].lower().replace(".", "")
				if floorTemp == "st":
						floor = 0
				elif floorTemp.isdigit():
						floor = int(floorTemp)
				if len(nameSplit) > 1:
						floorNo = nameSplit[1].lower().replace(".", "").replace(",", "")
						if len(nameSplit) > 2 and nameSplit[2].replace(".", "").isdigit():
								floorNo += " " + nameSplit[2]

		return name, floor, floorNo
