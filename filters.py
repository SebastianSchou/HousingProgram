#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
import general_functions as gf
import public_transport as pt
import RangeSlider.RangeSlider as rs
import colors
import csv
import math

SORT_VALUE = "Value"
SORT_ALPHABETICALLY = "Alphabetically"
SORT_NONE = "None"
TYPE_CHECKBOX = 0
TYPE_RANGE = 1
TYPE_ADDED_RANGE = 2
TYPE_SLIDER = 3

class Filters:
		class Filter():
				class Checkbox():
						def __init__(self, parent, frame = None):
								self.type = TYPE_CHECKBOX
								self.parent = parent
								self.frame = parent.frame if frame is None else frame
								self.column = ""
								self.sortType = SORT_VALUE
								self.currentFilter = []

						def getName(self, cb):
								return cb.cget("text").split("(")[0].strip()

						def setArguments(self, column = "", sortType = SORT_VALUE):
								self.column = column
								self.sortType = sortType
								if sortType not in [SORT_VALUE, SORT_ALPHABETICALLY, SORT_NONE]:
										self.sortType = SORT_VALUE

						def getCheckboxes(self):
								return self.frame.winfo_children()

						def makeFilter(self, df):
								# Make filter checkboxes based on values in columnName of df
								series = df[self.column]
								values = {}

								# Get values from each checkbox and remove them
								for cb in self.getCheckboxes():
										values[self.getName(cb)] = cb.var.get()
										cb.destroy()

								# Get unique values and their counts
								counts = series.value_counts(sort=self.sortType == SORT_VALUE,
																						 dropna=False)

								# If alphabetically is true, sort counts alphabetically
								if self.sortType == SORT_ALPHABETICALLY:
										counts = counts.sort_index()

								# For each item in counts, insert and set checkbox
								for name, val in counts.iteritems():
										# Checkbox variable
										var = tk.IntVar()

										# Set checkbox
										cb = tk.Checkbutton(self.frame,
																				text="{} ({})".format(name, val),
																				variable=var,
																				anchor="nw",
																				background=colors.FILTER_BG_COLOR)
										cb.var = var

										# Set right click command
										cb.bind("<Button-3>", lambda event: self._onRightClick(event))

										# Insert into grid
										cb.grid(column=0, row=gf.getGridRow(self.frame), sticky="w")

										# Set value based on previous checkbox values
										if name in values and values[name] == 0:
												cb.deselect()
										else:
												cb.select()

						def _onRightClick(self, event):
								menu = tk.Menu(self.parent.parent.window, tearoff=0)
								menu.add_command(label="Fravælg alle",
																 command=lambda: self._uncheckAll())
								menu.add_command(label="Vælg alle",
																 command=lambda: self._checkAll())
								try:
										menu.tk_popup(event.x_root, event.y_root)
								finally:
										menu.grab_release()

						def _uncheckAll(self):
								for cb in self.getCheckboxes():
										if cb["state"] == tk.NORMAL:
												cb.deselect()

						def _checkAll(self):
								for cb in self.getCheckboxes():
										if cb["state"] == tk.NORMAL:
												cb.select()

						def sort(self, df, column = None):
								if column is None:
										column = self.column

								# Get unchecked boxes
								self.currentFilter = self.getUncheckedBoxes()

								# Drop corresponding values
								if self.currentFilter != []:
										df.drop(df[df[column].str.contains(
											"|".join(self.currentFilter))].index, inplace=True)

						def isChecked(self, cb):
								return cb.var.get() == 1

						def getUncheckedBoxes(self):
								# Get a list of unchecked values
								fields = []

								for cb in self.getCheckboxes():
										name = self.getName(cb)
										if not self.isChecked(cb):
												fields.append(name)
								return fields

						def update(self, df, column = None):
								# Update checkbox values
								if column is None:
										column = self.column
								counts = df[column].value_counts(dropna=False)
								for cb in self.getCheckboxes():
										name = self.getName(cb)

										# Get new count for value. If 0, deselect checkbox
										if name in counts:
												val = counts[name]
												cb.config(state=tk.NORMAL)
										else:
												val = 0
												cb.config(state=tk.DISABLED)

										# Set new name
										cb.config(text = "{} ({})".format(name, val))

						def uncheckBoxes(self, uncheckedBoxes):
								# Update checkbox values
								for cb in self.getCheckboxes():
										# Get checkbox name
										name = self.getName(cb)

										# Get new count for value. If 0, deselect checkbox
										if name in uncheckedBoxes:
												cb.deselect()

						def reset(self):
								for checkbox in self.getCheckboxes():
										checkbox.select()

						def getSaveSettings(self):
								return self.getUncheckedBoxes()

				class Range():
						def __init__(self, parent, frame = None):
								self.type = TYPE_RANGE
								self.parent = parent
								self.frame = parent.frame if frame is None else frame
								self.width = self.parent.width
								self.column = ""
								self.suffix = ""
								self.loft = None
								self.floor = None
								self.roundTo = None
								self.name = None
								self.addSeperator = True
								self.nanReplaceValue = None
								self.minValue = 0
								self.maxValue = 0
								self.checkbox = None
								self.checkboxGridRow = 0
								self.range = None
								self.labelText = None
								self.currentFilter = [None, None, None]

						def setArguments(self, column = "", suffix = "", loft = None,
														 floor = None, roundTo = None, name = None,
														 addSeperator = True, nanReplaceValue = None):
								self.column = column
								self.suffix = suffix
								self.loft = loft
								if loft is None or floor is None or floor < loft:
										self.floor = floor
								self.roundTo = roundTo
								self.name = name
								self.addSeperator = addSeperator
								self.nanReplaceValue = nanReplaceValue

						def setLabelText(self, val1, val2):
								# Add a '<' to label if floor is reached
								labelText = ""
								if self.floor != None and self.minValue >= val1:
										labelText += "<"

								# Add a '+' to label if loft is reached
								loftStr = ""
								if self.loft != None and self.maxValue <= val2:
										loftStr = "+"

								# Add decimal separators to values if specified
								if self.addSeperator:
										val1 = gf.addDecimalSeparator(val1)
										val2 = gf.addDecimalSeparator(val2)

								labelText += "{} {}...{}{} {}".format(val1, self.suffix, val2,
																											loftStr, self.suffix)

								self.labelText.set(labelText)

						def makeFilter(self, df):
								# Get previous values
								values = self.getRangeValues()
								for idx in range(len(values)):
										values[idx] = gf.roundToValue(values[idx], self.roundTo)
								checkboxVal = self.getCheckboxValue()

								# Remove widgets
								for child in self.frame.winfo_children():
										child.destroy()

								dfColumn = df[self.column].copy()
								if self.nanReplaceValue is not None:
										dfColumn.fillna(self.nanReplaceValue, inplace=True)

								#try:
								#		quantiles = dfColumn.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
								#		print(quantiles)
								#		print(self.floor, self.loft, self.roundTo)
								#except Exception as e:
								#		print("{} error: {}".format(self.name, e))

								# Set min and max values
								if dfColumn.isnull().values.all():
										self.minValue = 0
										self.maxValue = 1
								else:
										self.minValue = dfColumn.min()
										self.maxValue = dfColumn.max()

								# If a loft is specified, set max to loft
								if self.loft != None:
										self.maxValue = min(self.loft, self.maxValue)

								# If a floor is specified, set min to floor
								if self.floor != None:
										self.minValue = max(self.floor, self.minValue)

								# If a rounding values is specified, round min and max values
								if self.roundTo != None:
										self.minValue = gf.roundToValue(
											self.minValue, self.roundTo, rounding="floor")
										self.maxValue = gf.roundToValue(
											self.maxValue, self.roundTo, rounding="ceil")

								# If no previous value exist, set values to min and max value
								if values == []:
										values = [self.minValue, self.maxValue]

								# Limit values
								if isinstance(self.roundTo, int):
										values[0] = max(int(values[0]), self.minValue)
										values[1] = min(int(values[1]), self.maxValue)
								else:
										values[0] = max(values[0], self.minValue)
										values[1] = min(values[1], self.maxValue)

								# Initialize range variables
								var1 = tk.DoubleVar(self.frame, values[0])
								var2 = tk.DoubleVar(self.frame, values[1])
								
								# Initalize label variable
								self.labelText = tk.StringVar()

								# Create label name if specified
								if self.name != None:
										name = self.name
										labelName = ttk.Label(self.frame, padding=(5, 5, 0, 0),
																					text=self.name.title(), anchor="w",
																					wraplength=self.width - 10, justify=tk.LEFT,
																					background=colors.FILTER_BG_COLOR)
										labelName.grid(column=0, row=gf.getGridRow(self.frame), sticky="w")

								# Create label
								label = ttk.Label(self.frame, padding=(5, 5, 0, 0),
																	textvariable=self.labelText, anchor="w",
																	background=colors.FILTER_BG_COLOR)

								# Create checkbox if any undefined values
								self.checkbox = None
								if dfColumn.isnull().values.any():
										cbVar = tk.IntVar()
										self.checkbox = tk.Checkbutton(
											self.frame, text="Inkluder udefinerede værdier",
											variable=cbVar, anchor="w",
											background=colors.FILTER_BG_COLOR)
										self.checkbox.var = cbVar
										if checkboxVal:
												self.checkbox.select()

								# Create range slider
								self.range = rs.RangeSliderH(
									self.frame, variables=[var1, var2], Width=self.width - 10,
									Height=60, padX = 5, min_val=self.minValue, max_val=self.maxValue,
									bar_radius=7, line_width=6, show_value=False,
									bgColor=colors.FILTER_BG_COLOR)

								# Set label text
								self.setLabelText(values[0], values[1])

								# Call function when value changed
								var1.trace_variable("w", self.updateLabel)
								var2.trace_variable("w", self.updateLabel)

								# Insert into grid
								label.grid(column=0, row=gf.getGridRow(self.frame), sticky="w")
								if self.checkbox is not None:
										self.checkboxGridRow = gf.getGridRow(self.frame)
										self.checkbox.grid(column=0, row=self.checkboxGridRow, sticky="w")
								self.range.grid(column=0, row=gf.getGridRow(self.frame), sticky="w")

						def updateLabel(self, var, index, mode):
								# Function called each time range slider change value
								# Updates the label text to represent values
								values = self.getRangeValues()
								val1 = values[0]
								val2 = values[1]
								if isinstance(self.roundTo, int):
										val1 = int(values[0])
										val2 = int(values[1])

								# Round and set values if specified
								if self.roundTo is not None:
										val1 = gf.roundToValue(val1, self.roundTo)
										val2 = gf.roundToValue(val2, self.roundTo)
										if val2 == self.minValue:
												val2 += self.roundTo
										elif val1 == self.maxValue:
												val1 -= self.roundTo
										if val1 == val2:
												val1 = gf.roundToValue(values[0], self.roundTo, "floor")
												val2 = gf.roundToValue(values[1], self.roundTo, "ceil")
										self.range.setValues([val1, val2])

								# Update label text
								self.setLabelText(val1, val2)

						def getRangeValues(self):
								if self.range is not None:
										return self.range.getValues()
								return []

						def hasReachedLoft(self):
								return (self.loft is not None and
												self.getRangeValues()[1] == self.maxValue)

						def hasReachedFloor(self):
								return (self.floor is not None and
												self.getRangeValues()[0] == self.minValue)

						def getCheckboxValue(self):
								return (self.checkbox is None or
												self.checkbox.var.get() == 1)

						def getSuffix(self):
								return self.suffix

						def setRangeValues(self, values, cb = None):
								self.range.setValues(values)
								if self.checkbox is not None and cb is not None:
										if cb:
												self.checkbox.select()
										else:
												self.checkbox.deselect()

						def sort(self, df, column = None):
								if column is None:
										column = self.column

								# Get range values
								values = self.getRangeValues()
								checkbox = self.getCheckboxValue()

								# Set current values
								self.currentFilter = [values[0], values[1], checkbox]

								# Get NaN values
								dfColumn = df[column]
								if self.nanReplaceValue is not None:
										dfColumn.fillna(self.nanReplaceValue, inplace=True)
								notNa = df[column].notna()

								# Get values above and below limits. Set to a series of false values
								# if floor or loft is reached
								seriesFalse = pd.Series(False, index=df.index)
								below = dfColumn < values[0] if not self.hasReachedFloor() else seriesFalse
								above = dfColumn > values[1] if not self.hasReachedLoft() else seriesFalse

								# Drop values
								df.drop(df[(above | below) & notNa].index, inplace=True)

								# Drop NaNs if specified
								if not checkbox:
										df.dropna(subset=[column], inplace=True)

						def update(self, df, column = None):
								if column is None:
										column = self.column
								if self.checkbox is None or self.checkbox.var.get() == 0:
										return
								
								if df[column].isnull().values.any():
										self.checkbox.grid(column=0, row=self.checkboxGridRow, sticky="w")
								else:
										self.checkbox.grid_forget()

						def reset(self):
								self.setRangeValues([self.minValue, self.maxValue], True)

						def getSaveSettings(self):
								values = self.getRangeValues()
								return [self.getCheckboxValue(), values[0], values[1]]

				class AddedRange():
						def __init__(self, parent, frame = None):
								self.type = TYPE_ADDED_RANGE
								self.parent = parent
								self.frame = parent.frame if frame is None else frame
								self.width = self.parent.width
								self.ranges = []
								self.suffix = ""
								self.loft = None
								self.roundTo = None
								self.floor = None
								self.replaceEng = ""
								self.replaceDk = ""
								self.nanReplaceValue = None
								self.station = None
								self.daysVar = tk.IntVar()
								self.timeVar = tk.IntVar()
								self.checkboxes = []
								self.slider = None
								self.button = None
								self.command = None

						def setArguments(self, suffix = "", loft = None,
														 floor = None, roundTo = None,
														 replaceEng = "", replaceDk = "",
														 nanReplaceValue = None):
								self.suffix = suffix
								self.loft = loft
								self.floor = floor
								self.roundTo = roundTo
								self.replaceEng = replaceEng
								self.replaceDk = replaceDk
								self.nanReplaceValue = nanReplaceValue

						def destroy(self, rangeslider):
								for child in rangeslider.frame.winfo_children():
										child.destroy()
								rangeslider.frame.destroy()
								self.ranges.remove(rangeslider)

						def getMatchingDk(self, listOfNames):
								return [c for c in listOfNames if \
												(self.replaceDk in c and c.index(self.replaceDk) == 0)]

						def makeFilter(self, df):
								# Ignore filters which exists
								existingRanges = []
								for rangeslider in list(self.ranges):
										name = rangeslider.name
										nameEng = name.replace(self.replaceDk, self.replaceEng)
										if nameEng in df.columns:
												existingRanges.append(nameEng)
										else:
												self.destroy(rangeslider)

								# Get new columns
								columns = [col for col in df.columns.tolist() \
													 if (self.replaceEng in col and
													 		 col.index(self.replaceEng) == 0 and
															 col not in existingRanges)]

								# Create new ranges
								for idx, column in enumerate(columns):
										# Create frame
										rangeFrame = tk.Frame(self.frame, bg=colors.FILTER_BG_COLOR)
										rangeFrame.grid(column=0, row=gf.getGridRow(self.frame),
																		columnspan=2, sticky="nsew")

										# Get name
										name = column.replace(self.replaceEng, self.replaceDk)

										# Create and set range
										rangeslider = self.parent.Range(self, rangeFrame)
										rangeslider.setArguments(column=column, suffix=self.suffix,
																						 loft=self.loft, roundTo=self.roundTo,
																						 floor=self.floor, name=name)
										rangeslider.makeFilter(df)

										# Append to ranges
										self.ranges.append(rangeslider)

						def _createSearchField(self, typeName):
								# Get row number
								row = gf.getGridRow(self.frame)
								# Create label and entry for search input
								label1 = tk.Label(self.frame,
																	text="{} navn:".format(typeName),
																	background=colors.FILTER_BG_COLOR)
								entryField = tk.Entry(self.frame, background=colors.ENTRY_INSIDE_COLOR)
								label1.grid(column=0, row=row, sticky="w")
								entryField.grid(column=1, row=row, sticky="w")

								# Create labels for station/address found
								label2 = tk.Label(self.frame,
																	text="{} fundet:".format(typeName),
																	background=colors.FILTER_BG_COLOR)
								label2.grid(column=0, row=row + 1, sticky="w")
								stopVar = tk.StringVar()
								stopVar.set("Ingen")
								stationLabel = tk.Label(self.frame,
																				textvariable=stopVar,
																				background=colors.FILTER_BG_COLOR)
								stationLabel.grid(column=1, row=row + 1, sticky="w")

								# Make variable for previous entry input
								textVarPrev = tk.StringVar()
								textVarPrev.set("")

								def checkEntry(event):
										# Check if station entry is empty if it hasn't changed
										entryText = entryField.get()
										if entryText == "" or entryText == textVarPrev.get():
												return

										# Set the new previous value
										textVarPrev.set(entryText)

										# Clean entry text
										entryText = entryText.lower().replace(".", "").strip()

										# Get the station
										self.station = pt.getLocation(entryText)

										# Set station name if possible
										name = "Ingen"
										if self.station != None:
												name = self.station["name"]
												if len(name) > 24:
														name = name[:20] + "..."
										stopVar.set(name)
										self.parent.parent.window.update()

										# If name is too long, shorten it
										label2Width = label2.winfo_width()
										while label2Width + stationLabel.winfo_width() > self.width:
												name = name[:-5]
												name += "..."
												stopVar.set(name)
												self.parent.parent.window.update()

								# Bind function to mouse leave and enter pressed
								entryField.bind("<Leave>", checkEntry)
								entryField.bind("<Return>", checkEntry)

						def initializePublicTransport(self):
								# Make filter for public transport time
								# Create search field
								self._createSearchField("Stop")
								row = gf.getGridRow(self.frame)

								# Create radio buttons for day choice
								label3 = tk.Label(self.frame, text="Dag:", background=colors.FILTER_BG_COLOR)
								label3.grid(column=0, row=row, sticky="w")
								self.daysVar.set(1)
								rowInit = row + 1
								for idx, day in enumerate(pt.DAYS):
										rb = tk.Radiobutton(self.frame,
																				text=day,
																				variable=self.daysVar,
																				value=idx,
																				background=colors.FILTER_BG_COLOR,
																				activebackground=colors.FILTER_BG_COLOR)
										if idx == 0:
												rb.select()
										else:
												rb.deselect()
										row = rowInit + math.floor(idx / 2)
										rb.grid(column=idx % 2, row=row, sticky="w")

								# Create radio buttons for time choice
								label4 = tk.Label(self.frame, text="Tidspunkt:", background=colors.FILTER_BG_COLOR)
								rowInit = row + 1
								label4.grid(column=0, row=rowInit, sticky="w")
								self.timeVar.set(1)
								for idx, time in enumerate(pt.TIMES):
										rb = tk.Radiobutton(self.frame,
																				text=time,
																				variable=self.timeVar,
																				value=idx,
																				background=colors.FILTER_BG_COLOR,
																				activebackground=colors.FILTER_BG_COLOR)
										if idx == 0:
												rb.select()
										else:
												rb.deselect()
										row = rowInit + 1 + math.floor(idx / 2)
										rb.grid(column=idx % 2, row=row, sticky="w")

								# Create slider
								label5 = tk.Label(self.frame,
																	text="Max. rejsetid\ni minutter:",
																	background=colors.FILTER_BG_COLOR)
								label5.grid(column=0, row=row + 1, sticky="w")
								self.slider = tk.Scale(self.frame,
																			 from_=0,
																			 to=120,
																			 orient=tk.HORIZONTAL,
																			 background=colors.FILTER_BG_COLOR,
																			 troughcolor="white",
																			 highlightthickness=0,
																			 resolution=5)
								self.slider.grid(column=0, row=row + 2, columnspan=2, sticky="ew")

								# Create search button
								self._createButton("Find rejsetid", row + 3)

						def initializeDistance(self):
								# Make filter for distance to location
								# Create search field
								self._createSearchField("Adresse")

								# Create search button
								self._createButton("Find distancer", gf.getGridRow(self.frame))

						def initializeChoices(self, dfColumn):
								for idx, value in enumerate(dfColumn.unique()):
										# Checkbox variable
										var = tk.IntVar()

										# Set checkbox
										cb = tk.Checkbutton(self.frame,
																				text=str(value),
																				variable=var,
																				anchor="nw",
																				background=colors.FILTER_BG_COLOR)
										cb.var = var

										# Append checkboxes
										self.checkboxes.append(cb)

										# Insert into grid
										cb.grid(column=idx % 2, row=math.floor(idx / 2), sticky="w")

								self._createButton("Find distancer", gf.getGridRow(self.frame))

						def getChoices(self):
								choices = []
								for checkbox in self.checkboxes:
										if checkbox.var.get() == 1:
												choices.append(checkbox.cget("text"))
								return choices

						def resetChoices(self):
								for checkbox in self.checkboxes:
										checkbox.deselect()

						def _createButton(self, text, row):
								self.button = tk.Button(self.frame,
																				text=text,
																				image=self.parent.parent.pixel,
																				width=self.width - 100,
																				height=15,
																				compound="c",
																				background=colors.FILTER_BUTTON_COLOR,
																				command=self._executeCommand)
								self.button.grid(column=0, row=row, columnspan=2, sticky="n")

						def _executeCommand(self):
								if self.command is not None:
										self.command()

						def setCommand(self, command):
								self.command = command

						def sort(self, df, column = None):
								# Get frame and loop over children which are frames themselves
								for rs in self.ranges:
										# If the column name is in the dataframe, sort ranges,
										# else destroy the child frame
										if rs.name in df.columns:
												rs.sort(df, column=rs.name)
										else:
												self.destroy(rs)

						def update(self, df, column = None):
								for rs in self.ranges:
										rs.update(df, column = rs.name.replace(self.replaceEng, self.replaceDk))

						def getRangeNamesDk(self):
								return [rs.name for rs in self.ranges]

						def getRangeNamesEng(self):
								return [rs.name.replace(self.replaceDk, self.replaceEng) for \
												rs in self.ranges]

						def getDay(self):
								return pt.DAYS[self.daysVar.get()]

						def getTime(self):
								return pt.TIMES[self.timeVar.get()]

						def getStation(self):
								return self.station

						def getLimit(self):
								return self.slider.get()

						def reset(self):
								for rs in self.ranges:
										rs.reset()

						def getSaveSettings(self):
								data = []
								for rs in self.ranges:
										data.extend([rs.name] + (rs.getSaveSettings()))
								return data

				class Slider():
						def __init__(self, parent, frame = None):
								self.type = TYPE_SLIDER
								self.parent = parent
								self.frame = parent.frame if frame is None else frame
								self.width = self.parent.width
								self.column = ""
								self.isDate = False
								self.useTicks = True
								self.maxValue = 1
								self.minValue = 0
								self.slider = None
								self.textVar = tk.StringVar()
								self.value = None
								self.values = None
								self.valuesIndexes = None
								self.indexValue = None
								self.currentFilter = None

						def setArguments(self, column = "", isDate = False,
														 useTicks = True):
								self.column = column
								self.isDate = isDate
								self.useTicks = useTicks

						def makeFilter(self, df):
								# Get uniue values
								if self.isDate:
										uniqueValues = df[self.column].dt.date.value_counts()
								else:
										uniqueValues = df[self.column].value_counts()

								# Remove previous child widgets
								for child in self.frame.winfo_children():
										child.destroy()

								# List of unique values with max and min
								uniqueList = list(uniqueValues.index)
								self.minValue = min(uniqueList)
								self.maxValue = max(uniqueList)
								self.value = self.maxValue

								# Get value indexes. If isDate, index by number of
								# days since first date
								self.valuesIndexes = {}
								for value in uniqueList:
										diff = value - self.minValue
										if self.isDate:
												diff = diff.days
										idx = int(diff)
										self.valuesIndexes[idx] = value
								self.values = list(self.valuesIndexes.keys())
								self.indexValue = max(self.values)
								
								# Create label
								label = ttk.Label(self.frame, padding=(5, 5, 0, 0),
																	textvariable=self.textVar, anchor="w",
																	background=colors.FILTER_BG_COLOR)
								self.textVar.set(self.maxValue)

								# Create slider
								toValue = self.maxValue - self.minValue
								if self.isDate:
										toValue = toValue.days
								self.slider = tk.Scale(self.frame,
																			from_=0,
																			to=(self.maxValue - self.minValue).days,
																			orient=tk.HORIZONTAL,
																			background=colors.FILTER_BG_COLOR,
																			troughcolor="white",
																			highlightthickness=0,
																			command=self.updateSlider,
																			showvalue=False,
																			length=self.width - 10)
								self.slider.set(toValue)

								# Insert widgets
								label.grid(column=0, row=0, columnspan=2, sticky="ew")
								self.slider.grid(column=0, row=1, columnspan=2, sticky="ew")

						def updateSlider(self, value):
								# Get difference
								diff = [abs(x - int(value)) for x in self.valuesIndexes.keys()]
								
								# Get difference in days between values and slider value
								idx = diff.index(min(diff))

								# Set value and label to value closest to slider value
								self.slider.set(self.values[idx])
								self.textVar.set(self.valuesIndexes[self.values[idx]])
								self.value = self.valuesIndexes[self.values[idx]]
								self.indexValue = self.values[idx]

						def sort(self, df, column = None):
								if column is None:
										column = self.column

								if column not in df.columns:
										return

								val = self.getValue()
								if self.isDate:
										df.drop(df[df[column].dt.date != val].index, inplace=True)
								else:
										df.drop(df[df[column] != val].index, inplace=True)

						def update(self, df):
								pass

						def getValue(self):
								self.currentFilter = self.value
								return self.value

						def reset(self):
								self.updateSlider(max(self.values))

						def getSaveSettings(self):
								return [self.indexValue]

				def __init__(self, parent, name):
						self.parent = parent
						self.name = name
						self.width = self.parent.width
						self._createFilterButton()
						self._createFilterFrame()
						self.filter = None

				def _createFilterButton(self):
						# Create filter buttons
						self.button = tk.Button(
								self.parent.frame,
								image=self.parent.pixel,
								width=self.width - 10,
								height=15,
								text=self.name,
								compound="c",
								relief=tk.GROOVE,
								background=colors.FILTER_BUTTON_COLOR,
								command=lambda: self._showWidget())
						row = gf.getGridRow(self.parent.frame)
						row += row % 2
						self.button.grid(column=0, row=row, sticky="ew")

				def _createFilterFrame(self):
						# Initialize filter frame
						self.frame = tk.Frame(self.parent.frame)
						self.frame.config(bg=colors.FILTER_BG_COLOR)

				def _showWidget(self):
						# Show filter
						self.button.configure(command=lambda: self._hideWidget())
						row = self.parent._getIndex(self.name) * 2 + 1
						self.frame.grid(column=0, row=row, sticky="ew")

				def _hideWidget(self):
						# Hide filter
						self.button.configure(command=lambda: self._showWidget())
						self.frame.grid_forget()

		def __init__(self, window, width):
				self.window = window
				self.checkboxNames = []
				self.rangeNames = []
				self.addedRangeNames = []
				self.sliderNames = []
				self.filterNames = []
				self.width = width
				self.filters = []
				self.container = tk.Frame(window, width=width)
				self.pixel = tk.PhotoImage(width=1, height=1)
				self.container.config(bg=colors.WINDOW_BG_COLOR)
				self.frame = gf.createScrollableCanvas(
					self.container, colors.WINDOW_BG_COLOR, width=width)

		def grid(self, **kwargs):
				self.container.grid(kwargs)

		def setCheckboxNames(self, names):
				self.checkboxNames = names

		def setRangeNames(self, names):
				self.rangeNames = names

		def setAddedRangeNames(self, names):
				self.addedRangeNames = names

		def setSliderNames(self, names):
				self.sliderNames = names

		def _getIndex(self, name):
				return self.filterNames.index(name)

		def initalizeFilters(self):
				self.filterNames = self.checkboxNames + self.rangeNames + \
													 self.addedRangeNames + self.sliderNames
				widgetIdx = 0
				for name in self.filterNames:
						f = self.Filter(self, name)
						self.filters.append(f)
						if name in self.checkboxNames:
								f.filter = f.Checkbox(f)
						elif name in self.rangeNames:
								f.filter = f.Range(f)
						elif name in self.addedRangeNames:
								f.filter = f.AddedRange(f)
						else:
								f.filter = f.Slider(f)

		def setArguments(self, name, **kwargs):
				self.get(name).setArguments(**kwargs)

		def reset(self):
				for f in self.filters:
						f.filter.reset()

		def get(self, name):
				return self.filters[self._getIndex(name)].filter

		def getAddedRange(self, name):
				for title in self.addedRangeNames:
						f = self.get(title)
						if any(name == rs.name for rs in f.ranges):
								return f
				return None

		def sort(self, df, sortValues = [], avoid = []):
				if sortValues:
						for values in sortValues:
								name = values[0]
								column = values[1]
								f = self.get(name)
								if f.type not in avoid:
										f.sort(df, column)
				else:
						for f in self.filters:
								if f.filter.type not in avoid:
										f.filter.sort(df)

		def update(self, df, sortValues = [], types = []):
				if sortValues:
						for values in sortValues:
								name = values[0]
								column = values[1]
								f = self.get(name)
								if f.type in types:
										f.update(df, column)
				else:
						for f in self.filters:
								if f.filter.type in types:
										f.filter.update(df)

		def makeFilters(self, df):
				for f in self.filters:
						f.filter.makeFilter(df)

		def saveFiltersSettings(self, path):
				# Initialize values
				data = []
				dataLine = []

				# Loop over filter widgets
				for f in self.filters:
						dataLine = []
						dataLine.append(f.name)
						dataLine.extend(f.filter.getSaveSettings())
						data.append(dataLine)

				# Write values to csv file
				with open(path, "w", encoding="UTF8", newline="") as file:
						writer = csv.writer(file, delimiter="\t")
						writer.writerows(data)

		def loadFilterSettings(self, path, filtersToIgnore = []):
				# Read csv file and set filter parameters
				with open(path, "r", encoding="UTF8", newline="") as file:
						reader = csv.reader(file, delimiter="\t")

						# For each row, get filter index and set values
						for row in reader:
								try:
										# Get index
										name = row[0]
										if name in filtersToIgnore:
												continue
										f = self.get(name)

										if name in self.checkboxNames:
												# Set checkbox values
												uncheckedBoxes = row[1:]
												f.uncheckBoxes(uncheckedBoxes)

										elif name in self.rangeNames:
												# Set range values
												values = [float(row[2]), float(row[3])]
												checkbox = row[1] == "True"
												f.setRangeValues(values, checkbox)

										elif name in self.addedRangeNames:
												# Set added range values for each added range existing
												for rs in f.ranges:
														nameIdx = row.index(rs.name)
														values = [float(row[nameIdx + 2]), float(row[nameIdx + 3])]
														checkbox = row[nameIdx + 1] == "True"
														rs.setRangeValues(values, checkbox)

										elif name in self.sliderNames:
												# Set slider values
												if len(row) == 1:
														continue
												value = row[1]
												f.updateSlider(value)

										else:
												continue

								except Exception as e:
										print(e)
										continue