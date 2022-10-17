#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from tkinter import font
import os
import csv
import colors
import general_functions as gf

IDX_GENERAL = 0
IDX_INCOME = 1
IDX_EXPENSES = 2
IDX_ELECTRICITY = 0
IDX_WATER = 1
FRAME_NAMES = ["Generelt", "Indtægter", "Udgifter"]
PRICES_VALUES = [["Elektricitet kr/kWh:", 1.84],
								 ["Vand kr/m\u00b3:", 82],
								 ["Gas kr/kWh:", 2.71],
								 ["Fjernvarme kr/kWh:", 0.71],
								 ["Elvarme kr/kWh:", 1.9]]
HEATING_TYPES = ["Naturgas", "Fjernvarme", "El"]
CONSUMPTION_VALUES = [["Elektricitet kWh:", 1600],
											["Vand m\u00b3:", 52]]
NAME_TEMP_TEXT = "Skriv unikt navn her..."
NAME_NOT_UNIQUE = "Navnet skal være unikt!"
PR_MONTH, PR_QUARTER, PR_HALFYEAR, PR_YEAR = \
	"Pr. måned", "Pr. kvartal", "Pr. halvår", "Pr. år"
MONTH_VALUES = {PR_MONTH: 1, PR_QUARTER: 3, PR_HALFYEAR: 6, PR_YEAR: 12}
ENERGY_LABELS = {"A2020": [20, 0], "A2015": [30, 1000], "A2010": [52.5, 1650],
								 "A2": [35, 1100], "A1": [50, 1600], "A": [50, 1600],
								 "B": [70, 2200], "C": [110, 3200], "D": [150, 4200],
								 "E": [190, 5200], "F": [240, 6500], "G": [240, 6500],
								 "Udefineret": [240, 6500]}
NAME_ELECTRICITY = "Elektricitet"
NAME_WATER = "Vand"
NAME_HEAT = "Varme"
NAME_COST_OWNERSHIP = "Ejerudgifter"
NAME_GROSS_MORTGAGE = "Boliglån brutto"
CURRENT_DIRECTORY = gf.getCurrentDirectory()
APP_DIRECTORY = gf.getAppDirectory()
GENERAL_DATA_PATH = APP_DIRECTORY + "/generel_data.csv"
INCOME_DATA_PATH = APP_DIRECTORY + "/income_data.csv"
EXPENSES_DATA_PATH = APP_DIRECTORY + "/expenses_data.csv"

def getTotalPriceString(value):
		return "Månedlig udgift: {} kr".format(round(value))

def getTotalLeftString(value):
		return "Månedligt fribeløb: {} kr".format(round(value))

class ExpensesWidget:
		class CustomEntry:
				class CustomEntryContent:
						def __init__(self, customEntry, row):
								self.parent = customEntry.parent
								self.customEntry = customEntry
								self.frame = customEntry.frame
								self.noOfPeople = customEntry.noOfPeople
								self.row = row
								self.afterId = [None]
								self.updateEntryAll = True
								self._createEntryContent()

						def _createEntryContent(self):								
								self.combo = ttk.Combobox(
									self.frame, value=list(MONTH_VALUES.keys()),
									background=colors.TAB_BG_COLOR, state="readonly",
									takefocus=0, width=100, height=20)

								self.combo.set(PR_MONTH)
								self.combo.grid(column=0, row=self.row, sticky="nsew", padx=(4, 2))
								
								if self.customEntry.isCategory:
										self.combo.bind("<<ComboboxSelected>>",
																		self.customEntry.sumSubcategories)
								else:
										self.combo.bind("<<ComboboxSelected>>", self.parent.updateSum)
								self.combo.unbind_class("TCombobox", "<MouseWheel>")

								self.name = tk.Entry(
									self.frame, background=colors.ENTRY_INSIDE_COLOR, takefocus=0)
								self.name.insert(0, NAME_TEMP_TEXT)
								self.name.bind("<Enter>", self.removeTempText)
								self.name.bind("<Leave>", self.insertTempText)
								self.name.bind("<FocusOut>", self._validateName)
								self.name.grid(column=1, row=self.row, sticky="ew", padx=(2, 2))

								self.entryOne = tk.Entry(
									self.frame, background=colors.ENTRY_INSIDE_COLOR, validate='all',
									validatecommand=(self.frame.register(gf.validateFloat), '%P'),
									width=7)
								self.entryOne.insert(0, "0")
								self.entryOne.grid(column=2, row=self.row, sticky="ew", padx=(2, 2))
								gf.bindAfterEntry(self.parent.root, self.entryOne,
																	self.afterId, self.updateAll, time=1000)

								self.entryAll = tk.Entry(
									self.frame, background=colors.ENTRY_INSIDE_COLOR, validate='all',
									validatecommand=(self.frame.register(gf.validateFloat), '%P'),
									width=7)
								self.entryAll.insert(0, "0")
								self.entryAll.grid(column=3, row=self.row, sticky="ew", padx=(2, 4))
								gf.bindAfterEntry(self.parent.root, self.entryAll,
																	self.afterId, self.updateOne, time=1000)

						def _validateName(self, event):
								name = self.getName()
								if (name not in [NAME_TEMP_TEXT, NAME_NOT_UNIQUE, ""] and
										self.parent.isValidName(self.customEntry, name)):
										self.parent.saveIncomeAndExpenses()
								else:
										self.name.delete(0, tk.END)
										self.name.insert(0, NAME_NOT_UNIQUE)
										self.name.config(fg="red")

						def removeTempText(self, event):
								if self.getName() in [NAME_TEMP_TEXT, NAME_NOT_UNIQUE]:
										self.name.delete(0, tk.END)
										self.name.config(fg="black")

						def insertTempText(self, event):
								if self.frame.focus_get() == self.name:
										return
								if self.getName() in ["", NAME_TEMP_TEXT]:
										self.name.delete(0, tk.END)
										self.name.insert(0, NAME_NOT_UNIQUE)
										self.name.config(fg="red")

						def getName(self):
								return self.name.get()

						def getNoOfPeople(self):
								return int(self.noOfPeople.get())

						def setEntryOne(self, value):
								if value == int(value):
										value = int(value)
								self.entryOne.delete(0, tk.END)
								self.entryOne.insert(0, str(value))

						def setEntryAll(self, value):
								if value == int(value):
										value = int(value)
								self.entryAll.delete(0, tk.END)
								self.entryAll.insert(0, str(value))

						def getEntryOne(self):
								value = self.entryOne.get()
								if value == "":
										value = 0
								return float(value)

						def getEntryAll(self):
								value = self.entryAll.get()
								if value == "":
										value = 0
								return float(value)

						def updateOne(self):
								self.updateEntryAll = False
								noOfPeople = self.getNoOfPeople()
								if noOfPeople == 0:
										return

								self.setEntryOne(round(self.getEntryAll() / noOfPeople, 1))
								if self.customEntry.isCategory:
										self.customEntry.sumSubcategories()
								else:
										self.parent.updateSum()

						def updateAll(self):
								self.updateEntryAll = True
								noOfPeople = self.getNoOfPeople()
								if noOfPeople == 0:
										return

								self.setEntryAll(self.getEntryOne() * noOfPeople)
								if self.customEntry.isCategory:
										self.customEntry.sumSubcategories()
								else:
										self.parent.updateSum()

						def getMonths(self):
								return MONTH_VALUES[self.combo.get()]

						def setUneditable(self):
								self.name.config(state=tk.DISABLED)
								self.entryOne.config(state=tk.DISABLED)
								self.entryAll.config(state=tk.DISABLED)
								self.combo.config(state=tk.DISABLED)

						def setWidgetData(self, name, months, valueOne, valueAll,
															updateEntryAll):
								self.name.delete(0, tk.END)
								self.name.insert(0, name)
								self.setEntryOne(valueOne)
								self.setEntryAll(valueAll)
								self.combo.set(months)
								self.updateEntryAll = updateEntryAll

				def __init__(self, parent, frame, noOfPeople):
						self.parent = parent
						self.parentFrame = frame
						self.frame = tk.Frame(frame, bg=colors.TAB_BG_COLOR)
						self.mainFields = None
						self.separator = None
						self.noOfPeople = noOfPeople
						self.frame.columnconfigure(0, weight=4, uniform=1)
						self.frame.columnconfigure(1, weight=5, uniform=1)
						self.frame.columnconfigure(2, weight=2, uniform=1)
						self.frame.columnconfigure(3, weight=2, uniform=1)
						self.updateEntryAll = True
						self.isDisabled = False
						self.isIncome = False
						self.isCategory = False
						self.subcategoryFields = []
						self.row = 0
						self.imageMinus = tk.PhotoImage(file = CURRENT_DIRECTORY + "/minus.png")
						ratio = int(self.imageMinus.width() / 21)
						self.imageMinus = self.imageMinus.subsample(ratio, ratio)
						self.imagePlus = tk.PhotoImage(file = CURRENT_DIRECTORY + "/plus.png")
						self.imagePlus = self.imagePlus.subsample(ratio, ratio)
						self.createEntry()

				def createEntry(self):
						self.mainFields = self.CustomEntryContent(self, 0)
						
						self.removeButton = tk.Button(
							self.frame,
							image=self.imageMinus,
							relief=tk.FLAT,
							background=colors.TAB_BG_COLOR,
							command=self.removeWidget)
						self.removeButton.grid(column=2, row=1, sticky="e", padx=(0, 2))
						
						self.addButton = tk.Button(
							self.frame,
							image=self.imagePlus,
							relief=tk.FLAT,
							background=colors.TAB_BG_COLOR,
							command=self.addNewWidget)
						self.addAddButton()

						def _bindRightClick(event):
								self.frame.bind_all("<Button-3>", self._onRightClick)

						def _unbindRightClick(event):
								self.frame.unbind_all("<Button-3>")

						# Bind enter and leave
						self.frame.bind("<Enter>", _bindRightClick)
						self.frame.bind("<Leave>", _unbindRightClick)

				def addNewWidget(self):
						entry = self.parent.CustomEntry(self.parent, self.parentFrame, self.noOfPeople)
						entry.grid(self.parentFrame, column=0, row=self.row + 2, columnspan=4, sticky="ew")
						entryIdx = int((self.row) / 2)
						if self.isIncome:
								self.parent.customWidgetsIncomes.insert(entryIdx, entry)
								entry.isIncome = True
								widgetArr = self.parent.customWidgetsIncomes
						else:
								self.parent.customWidgetsExpenses.insert(entryIdx, entry)
								widgetArr = self.parent.customWidgetsExpenses
						for idx in range(entryIdx + 1, len(widgetArr)):
								widgetArr[idx].updateRow(2)

				def removeWidget(self):
						for child in self.frame.winfo_children():
								child.destroy()
						entryIdx = int((self.row) / 2) -1
						self.frame.grid_forget()
						self.frame.destroy()
						self.separator.grid_forget()
						self.separator.destroy()
						if self.isIncome:
								self.parent.customWidgetsIncomes.remove(self)
								widgetArr = self.parent.customWidgetsIncomes
						else:
								self.parent.customWidgetsExpenses.remove(self)
								widgetArr = self.parent.customWidgetsExpenses
						for idx in range(entryIdx, len(widgetArr)):
								w = widgetArr[idx]
								widgetArr[idx].updateRow(-2)
						self.parent.updateSum()

				def _makeCategory(self, addFields = True):
						self.mainFields.name["font"] = (font.BOLD, 8, "bold")
						self.mainFields.combo.set(PR_MONTH)
						self.mainFields.combo.config(state=tk.DISABLED)
						self.mainFields.setEntryOne(0)
						self.mainFields.setEntryAll(0)
						if addFields:
								self.addCategoryField(0)
						self.isCategory = True
						
				def _removeCategory(self):
						self.mainFields.name["font"] = (font.NORMAL, 8, "")
						self.mainFields.combo.config(state=tk.NORMAL)
						self.isCategory = False
						for widget in self.subcategoryFields:
								for field in [widget.combo, widget.name,
															widget.entryOne, widget.entryAll]:
										field.grid_forget()
										field.destroy()
						increment = -len(self.subcategoryFields)
						self.subcategoryFields = []
						self._updateCategoryRows(increment, 0)

				def addCategoryField(self, row):
						if row < gf.getGridRow(self.frame) - 1:
								row += 1
						content = self.CustomEntryContent(self, row)
						self.subcategoryFields.insert(row - 1, content)
						self._updateCategoryRows(1, row)

				def _removeCategoryField(self, row):
						widget = self.subcategoryFields.pop(row - 1)
						for field in [widget.combo, widget.name,
													widget.entryOne, widget.entryAll]:
								field.grid_forget()
								field.destroy()

						self._updateCategoryRows(-1, row - 1)
						self.parent.sumSubcategories()

				def _updateCategoryRows(self, increment, index):
						for widget in self.subcategoryFields[index:]:
								for field in [widget.combo, widget.name,
														  widget.entryOne, widget.entryAll]:
										args = field.grid_info()
										field.grid_forget()
										args["row"] += increment
										widget.row += increment
										field.grid(args)
						self._updateButtonPlacement(increment)

				def _updateButtonPlacement(self, increment):
						for widget in [self.addButton, self.removeButton]:
								args = widget.grid_info()
								widget.grid_forget()
								args["row"] += increment
								widget.grid(args)

				def updateRow(self, increment):
						args = self.frame.grid_info()
						self.frame.grid_forget()
						self.separator.grid_forget()
						args["row"] += increment
						self.row += increment
						self.frame.grid(args)
						args["row"] += 1
						self.separator.grid(args, pady=(5, 5))

				def getName(self):
						return self.mainFields.name.get()

				def getSubcategoryNames(self):
						return [field.getName() for field in self.subcategoryFields]

				def getNoOfPeople(self):
						return int(self.noOfPeople.get())

				def grid(self, frame, **kwargs):
						self.frame.grid(kwargs)
						self.row = kwargs["row"]
						kwargs["row"] += 1
						self.separator = ttk.Separator(frame, orient="horizontal")
						self.separator.grid(kwargs, pady=(5, 5))

				def updateValues(self):
						for fields in [self.mainFields] + self.subcategoryFields:
								if fields.updateEntryAll:
										fields.updateAll()
								else:
										fields.updateOne()

				def sumSubcategories(self, event = None):
						total = 0
						for fields in self.subcategoryFields:
								total += round(fields.getEntryAll() / fields.getMonths(), 1)
						self.setValueAll(total)
						self.parent.updateSum()

				def getTotal(self):
						return self.mainFields.getEntryAll()

				def getMonths(self):
						return self.mainFields.getMonths()

				def setUneditable(self):
						self.isDisabled = True
						self.mainFields.setUneditable()
						self.addButton.grid_forget()
						self.removeButton.grid_forget()

				def addAddButton(self):
						self.addButton.grid(column=3, row=1, sticky="w", padx=(2, 0))

				def removeRemoveButton(self):
						self.removeButton.grid_forget()

				def setName(self, name):
						self.mainFields.name.config(state=tk.NORMAL)
						self.mainFields.name.delete(0, tk.END)
						self.mainFields.name.insert(0, name)
						self.mainFields.name.config(state=tk.DISABLED)

				def setMonth(self, months):
						self.mainFields.combo.config(state=tk.NORMAL)
						self.mainFields.combo.set(months)
						self.mainFields.combo.config(state=tk.DISABLED)

				def setValueOne(self, value):
						self.mainFields.updateEntryAll = True
						self.mainFields.entryOne.config(state=tk.NORMAL)
						self.mainFields.setEntryOne(value)
						self.mainFields.entryOne.config(state=tk.DISABLED)
						self.mainFields.entryAll.config(state=tk.NORMAL)
						self.mainFields.setEntryAll(value * self.getNoOfPeople())
						self.mainFields.entryAll.config(state=tk.DISABLED)

				def setValueAll(self, value):
						self.mainFields.updateEntryAll = False
						self.mainFields.entryAll.config(state=tk.NORMAL)
						self.mainFields.setEntryAll(value)
						self.mainFields.entryAll.config(state=tk.DISABLED)
						self.mainFields.entryOne.config(state=tk.NORMAL)
						self.mainFields.setEntryOne(round(value / self.getNoOfPeople(), 1))
						self.mainFields.entryOne.config(state=tk.DISABLED)

				def _onRightClick(self, event):
						menu = tk.Menu(self.frame, tearoff=0)

						# Get clicked row from mouse position
						frameX, frameY = self.frame.winfo_rootx(), self.frame.winfo_rooty()
						xDiff, yDiff = event.x_root - frameX, event.y_root - frameY
						column, row = self.frame.grid_location(xDiff, yDiff)
						if self.isCategory:
								menu.add_command(label="Fjern kategori",
																 command=self._removeCategory)
								menu.add_command(label="Tilføj underemne",
																 command=lambda: self.addCategoryField(row))
								if (row > 0 and row < self.frame.grid_size()[1] - 1 and
										len(self.subcategoryFields) > 1):
											menu.add_command(label="Fjern underemne",
																			 command=lambda: self._removeCategoryField(row))
						elif self.mainFields.name["state"] != tk.DISABLED:
								menu.add_command(label="Lav til kategori",
																 command=self._makeCategory)
						else:
								return

						try:
								menu.tk_popup(event.x_root, event.y_root)
						finally:
								menu.grab_release()

		def __init__(self, frame, root):
				self.root = root
				self.frame = tk.Frame(frame)
				self.frame.config(bg=colors.TAB_BG_COLOR)
				for i in range(len(FRAME_NAMES)):
						self.frame.columnconfigure(i * 2, weight=1, uniform=1)
				self.frame.grid_rowconfigure(4, weight=1)
				self.totalPriceVar = tk.StringVar()
				self.totalLeftVar = tk.StringVar()
				self.scrollableFrames = []
				self.afterId = [None]
				self.entryPeople = None
				self.customWidgetsExpenses = []
				self.customWidgetsIncomes = []
				self.area = 0
				self._createWidget()

		def _createWidget(self):
				# Create labels for total monthly price and total monthly
				# free cash
				self.totalPriceVar.set(getTotalPriceString(0))
				labelTotalPrice = tk.Label(
					self.frame, textvariable=self.totalPriceVar,
					background=colors.TAB_BG_COLOR)
				labelTotalPrice.grid(column=0, row=0, sticky="w")
				self.totalLeftVar.set(getTotalLeftString(0))
				labelTotalLeft = tk.Label(
					self.frame, textvariable=self.totalLeftVar,
					background=colors.TAB_BG_COLOR)
				labelTotalLeft.grid(column=0, row=1, sticky="w")

				# Make seperator
				separator = ttk.Separator(self.frame, orient="horizontal")
				separator.grid(column=0, row=2, columnspan=5, sticky="ew", pady=(5, 10))

				# Create scrollable frames
				for i, name in enumerate(FRAME_NAMES):
						label = tk.Label(
							self.frame, text=name, borderwidth=3, relief=tk.GROOVE,
							background=colors.FILTER_BUTTON_COLOR, height=2)
						label.grid(column=i * 2, row=3, sticky="ew", pady=(0, 5))

						container = tk.Frame(self.frame)
						container.config(bg=colors.WINDOW_BG_COLOR)
						container.grid(column=i * 2, row=4, sticky="nsew")
						container.columnconfigure(0, weight=1)
						container.rowconfigure(0, weight=1)
						
						frame = gf.createScrollableCanvas(container, colors.TAB_BG_COLOR, name=name)
						self.scrollableFrames.append(frame)

						if i != len(FRAME_NAMES) - 1:
								separator = ttk.Separator(self.frame, orient="vertical")
								separator.grid(column=i * 2 + 1, row=3, rowspan=2, sticky="ns",
															 padx=(5, 5))

				self._makeGeneralFrame()
				self._makeIncomeFrame()
				self._makeExpensesFrame()

				# Update
				self.update()

		def place(self, **kwargs):
				self.frame.place(kwargs)

		def grid(self, **kwargs):
				self.frame.grid(kwargs)

		def getCustomWidget(self, name):
				for widget in self.customWidgetsExpenses + self.customWidgetsIncomes:
						if widget.getName() == name:
								return widget
				return None

		def isValidName(self, widgetUnique, name):
				for widget in self.customWidgetsExpenses + self.customWidgetsIncomes:
						count = ([widget.getName()] +
										 widget.getSubcategoryNames()).count(name)
						if ((count > 0 and widget != widgetUnique) or count > 1):
								return False
				return True

		def _makeFrameIntro(self, frame):
				frame.columnconfigure(0, weight=4, uniform=1)
				frame.columnconfigure(1, weight=5, uniform=1)
				frame.columnconfigure(2, weight=2, uniform=1)
				frame.columnconfigure(3, weight=2, uniform=1)

				# Labels
				row = gf.getGridRow(frame)
				label = tk.Label(frame, text="",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=0, row=row, sticky="ew")

				label = tk.Label(frame, text="",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=1, row=row, sticky="ew")

				label = tk.Label(frame, text="Pr. pers.",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=2, row=row, sticky="w")

				label = tk.Label(frame, text="For alle",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=3, row=row, sticky="w")

				separator = ttk.Separator(frame, orient="horizontal")
				separator.grid(column=0, row=row+1, columnspan=4, sticky="ew",
											 pady=(5, 5))

		def _makeIncomeFrame(self):
				# Make content for "general" frame
				frame = self.scrollableFrames[IDX_INCOME]
				self._makeFrameIntro(frame)

				entry = self.addSemiStaticCustomWidget(
					frame, "Løn efter skat", PR_MONTH, self.customWidgetsIncomes)
				entry.removeRemoveButton()
				entry.isIncome = True

				# Read data
				if os.path.exists(INCOME_DATA_PATH):
						self.loadData(INCOME_DATA_PATH, frame, self.customWidgetsIncomes,
													isIncome=True)

		def _makeExpensesFrame(self):
				# Make content for "general" frame
				frame = self.scrollableFrames[IDX_EXPENSES]
				self._makeFrameIntro(frame)

				self.addStaticCustomWidget(
					frame, NAME_ELECTRICITY, PR_YEAR, self.customWidgetsExpenses)
				self.addStaticCustomWidget(
					frame, NAME_WATER, PR_YEAR, self.customWidgetsExpenses)
				self.addStaticCustomWidget(
					frame, NAME_HEAT, PR_YEAR, self.customWidgetsExpenses)
				self.addStaticCustomWidget(
					frame, NAME_COST_OWNERSHIP, PR_MONTH, self.customWidgetsExpenses)
				entry = self.addSemiStaticCustomWidget(
					frame, NAME_GROSS_MORTGAGE, PR_MONTH, self.customWidgetsExpenses)
				entry.removeRemoveButton()

				# Read data
				if os.path.exists(EXPENSES_DATA_PATH):
						self.loadData(EXPENSES_DATA_PATH, frame, self.customWidgetsExpenses)

		def addSemiStaticCustomWidget(self, frame, name, months, widgetArr):
				entry = self.CustomEntry(self, frame, self.entryPeople)
				row = gf.getGridRow(frame)
				entry.grid(frame, column=0, row=row, columnspan=4, sticky="ew")
				entry.setName(name)
				entry.setMonth(months)
				widgetArr.append(entry)
				return entry

		def addStaticCustomWidget(self, frame, name, months, widgetArr):
				entry = self.CustomEntry(self, frame, self.entryPeople)
				entry.setUneditable()
				entry.setName(name)
				entry.setMonth(months)
				row = gf.getGridRow(frame)
				entry.grid(frame, column=0, row=row, columnspan=4, sticky="ew")
				widgetArr.append(entry)
				return entry

		def _makeGeneralFrame(self):
				# Make content for "general" frame
				frame = self.scrollableFrames[IDX_GENERAL]
				frame.columnconfigure(1, weight=1)

				# No. of people
				row = gf.getGridRow(frame)

				label = tk.Label(frame, text="Antal personer:",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=0, row=row, sticky="w")
				self.entryPeople = tk.Entry(
					frame, background=colors.ENTRY_INSIDE_COLOR,
					validate='all', validatecommand=(frame.register(gf.validateInt), '%P'),
					takefocus=0)
				self.entryPeople.insert(0, "1")
				self.entryPeople.grid(column=1, row=row, sticky="ew")
				gf.bindAfterEntry(self.root, self.entryPeople, self.afterId,
													self.update, default=1)

				# Make seperator
				separator = ttk.Separator(frame, orient="horizontal")
				separator.grid(column=0, row=gf.getGridRow(frame), columnspan=2,
											 sticky="ew", pady=(5, 5))

				# Set entries for prices
				self.prices = []
				for values in PRICES_VALUES:
						# Get row
						row = gf.getGridRow(frame)

						# Make label
						label = tk.Label(frame, text=values[0],
														 background=colors.TAB_BG_COLOR)
						label.grid(column=0, row=row, sticky="w")

						# Make entry
						entry = tk.Entry(
							frame, background=colors.ENTRY_INSIDE_COLOR,
							validate='all', validatecommand=(frame.register(gf.validateFloat), '%P'),
							takefocus=0)
						entry.insert(0, str(values[1]))
						entry.grid(column=1, row=row, sticky="ew")
						gf.bindAfterEntry(self.root, entry, self.afterId, self.update)
						self.prices.append(entry)

				# Make seperator
				separator = ttk.Separator(frame, orient="horizontal")
				separator.grid(column=0, row=gf.getGridRow(frame), columnspan=2,
											 sticky="ew", pady=(5, 5))

				# Choose heating method
				self.heatingVar = tk.IntVar()
				self.heatingVar.set(1)
				for idx, heatingMethod in enumerate(HEATING_TYPES):
						rb = tk.Radiobutton(frame,
																text=heatingMethod,
																variable=self.heatingVar,
																value=idx,
																background=colors.TAB_BG_COLOR,
																activebackground=colors.TAB_BG_COLOR,
																command=self.update)
						if idx == 0:
								rb.select()
						else:
								rb.deselect()
						row = gf.getGridRow(frame)
						
						rb.grid(column=1, row=row, sticky="w")

				# Make label
				label = tk.Label(frame, text="Opvarmnings metode",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=0, row=row - 1, sticky="w")

				# Make seperator
				separator = ttk.Separator(frame, orient="horizontal")
				separator.grid(column=0, row=gf.getGridRow(frame), columnspan=2,
											 sticky="ew", pady=(5, 5))

				# Choose average consumption
				# Get row
				row = gf.getGridRow(frame)

				# Make column labels
				label = tk.Label(frame, text="Forbrug per person per år",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=0, row=row, sticky="w")

				# Make row values
				self.consumption = []
				for values in CONSUMPTION_VALUES:
						# Get row
						row = gf.getGridRow(frame)

						# Make label
						label = tk.Label(frame, text=values[0],
														 background=colors.TAB_BG_COLOR)
						label.grid(column=0, row=row, sticky="w")

						# Make entry
						entry = tk.Entry(
							frame, background=colors.ENTRY_INSIDE_COLOR,
							validate='all', validatecommand=(frame.register(gf.validateInt), '%P'),
							takefocus=0)
						entry.insert(0, str(values[1]))
						entry.grid(column=1, row=row, sticky="ew")

						# Bind keys
						gf.bindAfterEntry(self.root, entry, self.afterId, self.update)

						self.consumption.append(entry)

				# Make seperator
				separator = ttk.Separator(frame, orient="horizontal")
				separator.grid(column=0, row=gf.getGridRow(frame), columnspan=2,
											 sticky="ew", pady=(5, 5))

				# Energy label
				# Get row
				row = gf.getGridRow(frame)

				# Make labels
				label = tk.Label(frame, text="Energimærkat",
												 background=colors.TAB_BG_COLOR)
				label.grid(column=0, row=row, sticky="w")

				# Make combobox
				self.energyLabel = ttk.Combobox(frame, value=list(ENERGY_LABELS.keys()),
																				background=colors.TAB_BG_COLOR, state="readonly")
				self.energyLabel.grid(column=1, row=row, sticky="ew")
				self.energyLabel.bind("<<ComboboxSelected>>", self.update)
				self.energyLabel.set("C")

				# Read data
				if os.path.exists(GENERAL_DATA_PATH):
						self.loadGeneralData()

		def setEnergyLabel(self, label):
				if label in self.energyLabel["values"]:
					 self.energyLabel.set(label)
				else:
						self.energyLabel.set("Udefineret")

		def setMonthlyCostOfOwnership(self, value):
				widget = self.getCustomWidget(NAME_COST_OWNERSHIP)
				if widget == None:
						return
				widget.setValueAll(value)

		def setGrossMortgage(self, value):
				widget = self.getCustomWidget(NAME_GROSS_MORTGAGE)
				if widget == None:
						return
				widget.mainFields.setEntryAll(value)
				widget.mainFields.updateOne()

		def setHouseArea(self, area):
				self.area = area

		def setHeatingType(self, heatingType):
				if heatingType.lower() in ["udefineret", "blandet",
																	 "ingen varmeinstallation",
																	 "ovn til fast og flydende brændsel"]:
						return
				elif heatingType.lower() in ["fjernvarme/blokvarme",
																		 "centralvarme med én fyringsenhed",
																		 "centralvarme med to fyringsenheder",
																		 "varmepumpe"]:
						self.heatingVar.set(1)
				elif heatingType.lower() == "elvarme":
						self.heatingVar.set(2)
				elif heatingType.lower() == "gasradiator":
						self.heatingVar.set(0)
				else:
						print(heatingType)

		def update(self, event = None):
				try:
						persons = int(self.entryPeople.get())
						if persons == 0:
								return

						widget = self.getCustomWidget(NAME_ELECTRICITY)
						if widget == None:
								return
						electricityPrice = float(self.prices[IDX_ELECTRICITY].get())
						electricityUsage = float(self.consumption[IDX_ELECTRICITY].get())
						widget.setValueOne(electricityPrice * electricityUsage)

						widget = self.getCustomWidget(NAME_WATER)
						if widget == None:
								return
						waterPrice = float(self.prices[IDX_WATER].get())
						waterUsage = float(self.consumption[IDX_WATER].get())
						widget.setValueOne(waterPrice * waterUsage)

						widget = self.getCustomWidget(NAME_HEAT)
						if widget == None:
								return
						heatingType = self.heatingVar.get()
						heatingPrice = float(self.prices[heatingType + 2].get())
						energyLabel = self.energyLabel.get()
						if energyLabel in list(ENERGY_LABELS.keys()) and self.area != 0:
								values = ENERGY_LABELS[energyLabel]
								heatingUsage = values[0] * self.area + values[1]
								widget.setValueAll(round(heatingPrice * heatingUsage, 1))

						for widget in self.customWidgetsIncomes + self.customWidgetsExpenses:
								if widget.isDisabled:
										continue
								widget.updateValues()

						self.saveGeneralData()
						self.updateSum()

				except Exception as e:
						print(e)
						return

		def updateSum(self, event = None):
				sumIncome = 0
				sumExpenses = 0
				for widget in self.customWidgetsIncomes:
						sumIncome += (widget.getTotal() / widget.getMonths())
				for widget in self.customWidgetsExpenses:
						sumExpenses += (widget.getTotal() / widget.getMonths())
				self.totalPriceVar.set(getTotalPriceString(sumExpenses))
				self.totalLeftVar.set(getTotalLeftString(sumIncome - sumExpenses))
				self.saveIncomeAndExpenses()

		def saveGeneralData(self):
				data = []
				data.append(["People", int(self.entryPeople.get())])
				dataLine = []
				for entry in self.prices:
						dataLine.append(float(entry.get()))
				data.append(["Prices", dataLine])
				data.append(["Heating", self.heatingVar.get()])
				dataLine = []
				for entry in self.consumption:
						dataLine.append(int(entry.get()))
				data.append(["Consumption", dataLine])
				data.append(["Label", self.energyLabel.get()])
				data.append(["Area", self.area])

				with open(GENERAL_DATA_PATH, "w", encoding="UTF8", newline="") as file:
						writer = csv.writer(file, delimiter="\t")
						writer.writerows(data)

		def saveData(self, path, widgetArr):
				# Initialize values
				data = []

				# Loop over widgets
				for widget in widgetArr:
						dataLine = []
						for fields in [widget.mainFields] + widget.subcategoryFields:
								name = fields.getName()
								if name in ["", NAME_TEMP_TEXT, NAME_NOT_UNIQUE]:
										continue
								valueOne = fields.getEntryOne()
								valueAll = fields.getEntryAll()
								months = fields.combo.get()
								updateEntryAll = fields.updateEntryAll
								dataLine.extend([name, valueOne, valueAll, months, updateEntryAll])
						data.append(dataLine)

				# Write values to csv file
				with open(path, "w", encoding="UTF8", newline="") as file:
						writer = csv.writer(file, delimiter="\t")
						writer.writerows(data)

		def saveIncomeAndExpenses(self):
				self.saveData(INCOME_DATA_PATH, self.customWidgetsIncomes)
				self.saveData(EXPENSES_DATA_PATH, self.customWidgetsExpenses)

		def loadGeneralData(self):
				with open(GENERAL_DATA_PATH, "r", encoding="UTF8", newline="") as file:
						reader = csv.reader(file, delimiter="\t")

						for row in reader:
								name = row[0]
								data = row[1]
								if name == "People":
										self.entryPeople.delete(0, tk.END)
										self.entryPeople.insert(0, data)
								elif name == "Prices":
										data = data[1:-1].split(", ")
										for i, value in enumerate(data):
												self.prices[i].delete(0, tk.END)
												self.prices[i].insert(0, value)
								elif name == "Heating":
										self.heatingVar.set(data)
								elif name == "Consumption":
										data = data[1:-1].split(", ")
										for i, value in enumerate(data):
												self.consumption[i].delete(0, tk.END)
												self.consumption[i].insert(0, value)
								elif name == "Label":
										self.energyLabel.set(data)
								elif name == "Area":
										self.area = int(data)

		def loadData(self, path, frame, widgetArr, isIncome = False):
				with open(path, "r", encoding="UTF8", newline="") as file:
						reader = csv.reader(file, delimiter="\t")

						for row in reader:
								if not row:
										continue
								name = row[0]
								valueOne = float(row[1])
								valueAll = float(row[2])
								months = row[3]
								updateEntryAll = row[4] == "True"
								widget = self.getCustomWidget(name)
								if widget == None:
										widget = self.CustomEntry(self, frame, self.entryPeople)
										widget.mainFields.setWidgetData(
											name, months, valueOne, valueAll, updateEntryAll)
										widget.isIncome = isIncome
										widget.grid(frame, column=0, row=gf.getGridRow(frame),
																columnspan=4, sticky="ew")
										widgetArr.append(widget)
								else:
										widget.updateEntryAll = updateEntryAll
										if widget.isDisabled:
												if updateEntryAll:
														widget.setValueOne(valueOne)
												else:
														widget.setValueAll(valueAll)
										else:							
												widget.mainFields.setEntryOne(valueOne)
												widget.mainFields.setEntryAll(valueAll)

								subcategoryFields = []
								if len(row) > 5:
										subcategoryFields = row[5:]
										widget._makeCategory(addFields=False)

								while len(subcategoryFields) > 0:
										name = subcategoryFields[0]
										valueOne = float(subcategoryFields[1])
										valueAll = float(subcategoryFields[2])
										months = subcategoryFields[3]
										updateEntryAll = subcategoryFields[4] == "True"
										subcategoryFields = subcategoryFields[5:]
										widget.addCategoryField(len(widget.subcategoryFields))
										widget.subcategoryFields[-1].setWidgetData(
											name, months, valueOne, valueAll, updateEntryAll)



