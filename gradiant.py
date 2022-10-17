#!/usr/bin/env python3
import tkinter as tk
import general_functions as gf
import numpy as np
import math

class Gradiant:
		def __init__(self, root, frame, width, height,
								 bgColor = "white", rightOrTop = True):
				self.root = root
				self.frame = tk.Frame(frame)
				self.frame.config(bg=bgColor)
				self.size = (width, height)
				self.wide = width > height
				self.labelVarH = tk.StringVar()
				self.labelVarL = tk.StringVar()
				self.labelVarM = tk.StringVar()
				self.values = (0, 1)
				self.preciseValue = None
				self.afterId = [None]
				self.suffix = ""
				self.title = ""
				self.labelM =tk.Label(self.frame, textvariable=self.labelVarM,
															anchor="w", background=bgColor)
				labelH = tk.Label(self.frame, textvariable=self.labelVarH,
													anchor="w", background=bgColor)
				labelL = tk.Label(self.frame, textvariable=self.labelVarL,
													anchor="e", background=bgColor)
				if self.wide:
						self.canvas = tk.Canvas(self.frame, width=width,
																		height=height, bg=bgColor,
																		highlightthickness=0)
						self.canvas.grid(column=0, row=rightOrTop==True,
														 columnspan=2, sticky="nsew")
						self.frame.grid_columnconfigure(0, weight=0)
						labelH.grid(column=1, row=rightOrTop==False, sticky="e")
						labelL.grid(column=0, row=rightOrTop==False, sticky="w")
						self.labelM.place(x=width / 2, y=height - 20)
						self.labelM.config(anchor="ew")
				else:
						self.canvas = tk.Canvas(self.frame, width=width,
																		height=height, bg="red",#bgColor,
																		highlightthickness=0)
						self.canvas.grid(column=rightOrTop==False, row=0,
														 rowspan=2, sticky="nsew")
						self.frame.grid_rowconfigure(1, weight=0)
						labelH.config(anchor="sw")
						labelL.config(anchor="nw")
						labelH.grid(column=rightOrTop==True, row=1, sticky="sw")
						labelL.grid(column=rightOrTop==True, row=0, sticky="nw")
						self.labelM.place(x=width, y=(height / 2) - 10)
				gf.bindAfter(root, self.frame, self.afterId,
										 self._onConfigure, "<Configure>")
				self.fill()

		def grid(self, **kwargs):
				self.frame.grid(kwargs)

		def _onConfigure(self, event):
				if self.wide and event.width != self.size[0]:
						pass
				elif not self.wide and event.height != self.size[1]:
						self.size = (self.size[0], event.height)
						self.canvas.config(height=event.height)
						self.fill()
						value = self.preciseValue
						self.removePreciseLabel()
						self.setPreciseLabel(value)

		def rgb(self, r, g, b):
				return "#%s%s%s" % tuple([hex(c)[2:].rjust(2, "0") for c in (r, g, b)])

		def fill(self):
				size = self.size[0] if self.wide else self.size[1]
				mult = size / 255
				for x in range(0, 256):
						color = self.getColor(x)
						if self.wide:
								x0, y0, x1, y1 = (round(x * mult),
																	0,
																	round((x + 1) * mult),
																	self.size[1])
						else:
								x0, y0, x1, y1 = (0,
																	round(x * mult),
																	self.size[0],
																	round((x + 1) * mult))
						self.canvas.create_rectangle(x0, y0, x1, y1,
																				 fill=color,
																				 outline=color)

		def getColor(self, value):
				value = max(min(255, value), 0)
				r = value * 2 if value < 128 else 255
				g = 255 if value < 128 else 255 - (value - 128) * 2
				return self.rgb(r, g, 0)

		def _getValueCorrected(self, value):
				if isinstance(value, str):
						value = gf.removeDecimalSeperator(value)

				if isinstance(value, float):
						return round(value, 1)
				elif isinstance(value, (int, np.int64)) or value.isdigit():
						return int(value)
				else:
						return None

		def getValueColor(self, value):
				value = self._getValueCorrected(value)
				if value is None:
						return "#FFFFFF"
				val = 1
				if self.values[1] - self.values[0] != 0:
						val = (value - self.values[0]) / (self.values[1] - self.values[0])
				val = round(val * 255)
				return self.getColor(val)

		def getValuePosition(self, value):
				value = self._getValueCorrected(value)
				if value is None:
						return 0
				pos = 0
				if self.values[1] - self.values[0] != 0:
						pos = (value - self.values[0]) / (self.values[1] - self.values[0])

				if self.wide:
						pos = round(pos * self.size[0])
				else:
						pos = round(pos * self.size[1])

				return pos

		def setLabels(self, labelL, labelH):
				self.labelVarL.set(labelL)
				self.labelVarH.set(labelH)

		def isPreciseLabelOverlapping(self, pos, label):
				if not self.wide:
						posMin = 20
						posMax = self.size[1] - 35
						return pos < posMin or pos > posMax

				return False

		def setPreciseLabel(self, value):
				# Create label text
				if value is None:
						return

				if isinstance(value, float) and value % 1 == 0.0:
						value = int(value)
				self.preciseValue = value
				label = str(value) + " " + self.suffix

				# Get position
				pos = self.getValuePosition(value)

				# Place label
				if self.wide:
						self.labelM.place(x=pos, y=self.size[1] - 20)
				else:
						self.labelM.place(x=self.size[0], y=pos - 10)
				
				# Check label is not overlapping
				if self.isPreciseLabelOverlapping(pos, label):
						self.removePreciseLabel()
						return

				# Set label
				self.labelVarM.set(label)

		def removePreciseLabel(self):
				self.labelVarM.set("")
				self.preciseValue = None

		def setValues(self, title, values, loft, floor, suffix, minmax):
				valL = values[0]
				valH = values[1]

				self.suffix = suffix
				self.title = title
				if minmax[0] != None:
						if valL < minmax[0]:
								floor = False
						if valH > minmax[1]:
								loft = False
						valL = max(valL, minmax[0])
						valH = min(valH, minmax[1])

				valL = int(valL) if valL % 1 == 0.0 else valL
				valH = int(valH) if valH % 1 == 0.0 else valH

				if self.title not in ["År bygget"]:
						labelL = gf.addDecimalSeparator(valL)
						labelH = gf.addDecimalSeparator(valH)
				else:
						labelL = str(valL)
						labelH = str(valH)

				if floor:
						labelL = "<" + labelL
				
				if loft:
						labelH += "+"

				labelL += " " + self.suffix
				labelH += " " + self.suffix
				self.values = (valL, valH)

				self.setLabels(labelL, labelH)