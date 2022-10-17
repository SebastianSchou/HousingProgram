#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import tkintermapview
import pandas as pd
import public_transport as pt
import general_functions as gf
import boligsiden
import edc
import boliga
import gradiant
import treeview_list as tl
import expenses
from filters import Filters, SORT_ALPHABETICALLY, SORT_NONE, TYPE_RANGE, \
										TYPE_CHECKBOX, TYPE_ADDED_RANGE, TYPE_SLIDER
import os
import sys
import time
import math
import numpy as np
import RangeSlider.RangeSlider as rs
import webbrowser
import threading
import csv
import colors
import sklearn
import sklearn.neighbors
from sklearn.neighbors import KDTree, BallTree

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
PADDING = 5
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30
TAB_WIDTH = 950
TAB_HEIGHT = 550
COLUMN_WIDTH_MINIMIZED = 20
FILTER_WIDTH = WINDOW_WIDTH - (3 * PADDING + TAB_WIDTH)
GIF_PLACE = [WINDOW_WIDTH - (PADDING * 3 + BUTTON_WIDTH * 2),
						 PADDING,
						 BUTTON_HEIGHT,
						 BUTTON_HEIGHT]
LOWER_POSTAL = 1000
UPPER_POSTAL = 4999
LIST_FONT = "Cambria"
LIST_FONT_NAME = "cambria.ttc"
DATA_COLUMNS = ["address", "floor level", "floor door no.", "postal code",
								"postal no.", "postal name", "region", "price", "energy level",
								"type", "link", "coord. x", "coord. y", "m2 house", "m2 ground",
								"rooms", "year built", "price per m2", "monthly expenses",
								"updated", "website", "favorite", "days on market",
								"heating installation", "down payment", "gross mortgage"]
LIST_COLUMNS = ["id", "adresse", "pris", "energimærkat", "type", "m2 hus",
								"m2 grund", "rum", "år bygget", "pris per m2",
								"ejerudgifter", "bruttolån", "liggetid", "boligside"]
FILTER_NAMES_CHECKBOX = ["Boligside", "Region", "Type", "Energi mærkat"]
FILTER_NAMES_RANGE = ["Pris", "Kvadratmeter hus", "Rum", "Etage", "År bygget",
											"Pris per kvadratmeter", "Ejerudgifter",
											"Bruttolån", "Liggetid"]
FILTER_NAMES_SLIDER = ["Sidst opdateret"]
FILTER_NAMES_ADDED_RANGE = ["Offentlig transport", "Distance", "Steder"]
FILTER_NAMES = FILTER_NAMES_CHECKBOX + FILTER_NAMES_RANGE + \
							 FILTER_NAMES_ADDED_RANGE + FILTER_NAMES_SLIDER
COLUMNS_TO_SORT = [["Pris", "pris"],
									 ["Kvadratmeter hus", "m2 hus"],
									 ["Rum", "rum"],
									 ["Etage", None],
									 ["År bygget", "år bygget"],
									 ["Pris per kvadratmeter", "pris per m2"],
									 ["Ejerudgifter", "ejerudgifter"],
									 ["Bruttolån", "bruttolån"],
									 ["Liggetid", "liggetid"],
									 ["Offentlig transport", None],
									 ["Distance", None],
									 ["Steder", None],
									 ["Boligside", "boligside"],
									 ["Region", None],
									 ["Type", "type"],
									 ["Energi mærkat", "energimærkat"],
									 ["Sidst opdateret", None]]
COLUMNS_WITH_DECIMAL_SEPERATOR = ["pris", "pris per m2", "ejerudgifter",
																	"bruttolån"]
COLUMNS_TREE_IGNORE = ["floor level", "postal name", "updated", "address",
											 "postal code", "floor door no.", "region"]
UNDEFINED = "Udefineret"
CURRENT_DIRECTORY = gf.getCurrentDirectory()
APP_DIRECTORY = gf.getAppDirectory()

def setDataframe(df1, df2):
		# Copies the values from df2 to df1 inplace
		for column in df1:
				df1.drop(column, axis=1, inplace=True)
		df1.index = df2.index
		for column in df2.columns:
				df1[column] = df2[column]

def getIndex(name):
		if name in FILTER_NAMES:
				return FILTER_NAMES.index(name) * 2 + 1

class GUI:
		def __init__(self):
				self.window = tk.Tk()
				self.blacklistPath = APP_DIRECTORY + "/blacklist.csv"
				self.csvPath = APP_DIRECTORY + "/housing_data.csv"
				self.filterCsvPath = APP_DIRECTORY + "/last_search.csv"
				self.gifPath = CURRENT_DIRECTORY + "/Loading.gif"
				self.iconPath = CURRENT_DIRECTORY + "/house_icon.png"
				self.mapDbPath = CURRENT_DIRECTORY + "/map.db"
				self.placesPath = CURRENT_DIRECTORY + "/krak.csv"
				self.pixel = tk.PhotoImage(width=1, height=1)
				self.loadGif = None
				self.df = pd.DataFrame()
				self.blacklist = pd.DataFrame()
				self.threadPtData = pd.DataFrame()
				self.listDf = pd.DataFrame()
				self.placesDf = pd.DataFrame()
				self.loadButton = None
				self.threadPt = None
				self.threadLoad = None
				self.threadLoadData = None
				self.noOfResultsText = None
				self.treeMain = None
				self.treeFavorite = None
				self.filters = None
				self.dkMap = None
				self.mapMarkers = []
				self.ptQueue = []
				if os.path.exists(self.placesPath):
						self.placesDf = pd.read_csv(self.placesPath, sep="\t", index_col=0)
						self.placesDf.columns = self.placesDf.columns.str.lower()
				self._createWindow()
				if os.path.exists(self.blacklistPath):
						self._getCsvData(self.blacklistPath, self.blacklist)

				if os.path.exists(self.csvPath):
						self._initData()
				else:
						self._loadDataInBackground()
				self.window.update()
				for frame in self.expenseWidget.scrollableFrames:
						frame.event_generate("<Configure>")
				self.filters.frame.event_generate("<Configure>")

		def run(self):
				# Run window
				self.window.mainloop()

		def _quit(self):
				# Close window
				self.window.quit()
				self.window.destroy()
				print("Waiting for threads.")
				if self.threadLoad is not None:
						self.threadLoad.join()
				if self.threadPt is not None:
						self.threadPt.join()
				print("Shutting down.")

		def _createWindow(self):
				# Set behaviour on close
				self.window.protocol("WM_DELETE_WINDOW", self._quit)

				# Set title
				self.window.title("Bolig program")

				# Set window size
				geometryStr = "{}x{}".format(WINDOW_WIDTH, WINDOW_HEIGHT)
				self.window.geometry(geometryStr)

				# Set background color
				self.window.configure(bg=colors.WINDOW_BG_COLOR)

				# Set icon
				self.window.iconphoto(False, tk.PhotoImage(file=self.iconPath))

				# Make load button
				self.loadButton = tk.Button(
						self.window,
						text="Indhent data",
						background=colors.LOAD_BUTTON_COLOR,
						command=self._loadDataInBackground)
				self.loadButton.grid(column=2, row=0, sticky="ew", padx=5, pady=5)

				# Make sorting button
				buttonSort = tk.Button(
						self.window,
						text="Sorter data",
						background=colors.SORT_BUTTON_COLOR,
						command=lambda: self._updateList(self.df))
				buttonSort.grid(column=1, row=0, sticky="ew", padx=5, pady=5)

				# Loading gif
				gifPath = os.path.dirname(os.path.realpath(__file__)) + "/Loading.gif"
				gifFrames = []
				i = 0
				while True:
						try:
								gifFrames.append(tk.PhotoImage(
										file=gifPath, format = "gif -index %i" % i))
								i += 1
						except:
								break

				# Set update function for gif
				def gifUpdate(ind):
						try:
								frame = gifFrames[ind]
						except:
								frame = gifFrames[0]
								ind = 0
						ind += 1
						self.loadGif.configure(image=frame)
						self.window.after(100, gifUpdate, ind)

				# Start loading gif animation
				self.loadGif = tk.Label(self.window, bg=colors.WINDOW_BG_COLOR)
				self.window.after(0, gifUpdate, 0)

				# Continually check if threads are done
				self.window.after(1000, self._checkThread)

				# Create tkinter style
				style = ttk.Style()
				style.theme_use("clam")

				# Set style for tabs
				style.configure("TNotebook", background=colors.WINDOW_BG_COLOR)
				style.configure("TNotebook.Tab", background=colors.FILTER_BUTTON_COLOR)
				style.map("TNotebook.Tab", background=[("selected", colors.TAB_BG_COLOR)])

				# Set font type for treeview (Used to calculate width of columns)
				style.configure("Treeview", font=("Cambria", 9))
				style.configure("Treeview.Heading", font=("Cambria", 9),
												background=colors.LIST_HEADING_COLOR, height=40,
												foreground="black")

				# Set tab column and row to have weight
				self.window.grid_columnconfigure(0, weight=1)
				self.window.grid_columnconfigure(1, weight=0)
				self.window.grid_columnconfigure(2, weight=0)
				self.window.grid_rowconfigure(2, weight=1)

				# Make tabs
				tabsystem = ttk.Notebook(self.window)
				tabsystem.grid(column=0, row=1, rowspan=2, sticky="nsew", padx=5, pady=5)
				tab1 = tk.Frame(tabsystem)
				tab2 = tk.Frame(tabsystem)
				tab3 = tk.Frame(tabsystem)
				tab4 = tk.Frame(tabsystem)
				tab1.config(bg=colors.TAB_BG_COLOR)
				tab2.config(bg=colors.TAB_BG_COLOR)
				tab3.config(bg=colors.TAB_BG_COLOR)
				tab4.config(bg=colors.TAB_BG_COLOR)
				tabsystem.add(tab1, text="Bolig liste")
				tabsystem.add(tab2, text="Bolig kort")
				tabsystem.add(tab3, text="Favoritter")
				tabsystem.add(tab4, text="Månedlige omkostninger")

				self.treeMain = self._createTree(tab1, "Main")	

				# Create label for number of results
				self.noOfResultsText = tk.StringVar()
				label = tk.Label(self.window,
												 textvariable=self.noOfResultsText,
												 anchor="w")
				label.grid(column=1, row=1, sticky="ew", padx=5, pady=5)
				label.config(bg=colors.WINDOW_BG_COLOR)
				self.noOfResultsText.set("0 boliger")

				buttonReset = tk.Button(
						self.window,
						text="Nulstil filtre",
						background=colors.SORT_BUTTON_COLOR,
						command=lambda: self._resetFilters())
				buttonReset.grid(column=2, row=1, sticky="ew", padx=5, pady=5)
				
				# Add filters
				self._setFilters()

				# Tab 2 - Map
				# Make container for map
				containerMap = tk.Frame(tab2, bg=colors.TAB_BG_COLOR)
				tab2.grid_columnconfigure(0, weight=1)
				tab2.grid_rowconfigure(0, weight=1)
				containerMap.grid(column=0, row=0, sticky="nsew", padx=5, pady=5)

				# Load offline map if not existing. This takes way too
				# long for the moment
				#if not os.path.exists(self.mapDbPath):
				#		loader = tkintermapview.OfflineLoader(path=self.mapDbPath)
				#		pos1 = (57.7565757, 5.4753103)
				#		pos2 = (54.7939603, 15.5387869)
				#		loader.save_offline_tiles(pos1, pos2, 0, 12)

				# Create map
				self.dkMap = tkintermapview.TkinterMapView(
					containerMap, width=TAB_WIDTH - 3 * PADDING - 100,
					corner_radius=0, bg=colors.TAB_BG_COLOR)#, database_path=self.mapDbPath)
				self.dkMap.grid(column=0, row=0, rowspan=2, sticky="nsew")
				self.gradiantCombo = ttk.Combobox(containerMap, value=[], background=colors.TAB_BG_COLOR)
				self.gradiantCombo.grid(column=0, row=0, columnspan=2, sticky="ne", padx=(0, PADDING))

				self.gradiant = gradiant.Gradiant(
					self.window, containerMap, width=25,
					height=TAB_HEIGHT - (41 + 20 + PADDING),
					bgColor=colors.TAB_BG_COLOR)
				self.gradiant.grid(column=1, row=1, sticky="nsew", padx=(0, PADDING), pady=5)
				containerMap.grid_columnconfigure(0, weight=1)
				containerMap.grid_rowconfigure(1, weight=1)
				self.gradiantCombo.bind("<<ComboboxSelected>>", self._setGradiant)

				# Make function for when map is clicked
				def onMapClick(coords):
						if self.dkMap.canvas["cursor"] == "hand2":
								return
						self.gradiant.removePreciseLabel()
						for marker in self.mapMarkers:
								marker.set_text("")

				# Bind function to map
				self.dkMap.add_left_click_map_command(onMapClick)

				# Set position and zoom level
				self.dkMap.set_position(56.0773287, 10.8582637)
				self.dkMap.set_zoom(7)

				# Tab 3
				# Create treeview
				self.treeFavorite = self._createTree(tab3, "Favorite")

				# Tab 4
				self.expenseWidget = expenses.ExpensesWidget(tab4, self.window)
				tab4.grid_columnconfigure(0, weight=1)
				tab4.grid_rowconfigure(0, weight=1)
				self.expenseWidget.grid(column=0, row=0, sticky="nsew", padx=5, pady=5)

		def _checkThread(self):
				# Check on threads
				if ((self.threadLoad is None or not self.threadLoad.is_alive()) and
						self.threadLoadData is not None):

						# Set dataframe
						newData = pd.DataFrame(self.threadLoadData)
						newData.columns = DATA_COLUMNS
						self.threadLoadData = None
						self._updateData(newData)
						
						# Initialize rest of data
						self._updateApp()

				if self.threadPt is None or not self.threadPt.is_alive():
						if not self.threadPtData.empty:
								# Expand dataframe
								self.df.sort_index(inplace=True)
								if self.threadPtData.name in self.df.columns:
										self.df[self.threadPtData.name] = self.threadPtData
								else:
										setDataframe(self.df, self.df.join(self.threadPtData))
								self.threadPtData = pd.DataFrame()
								self.df.to_csv(self.csvPath, sep="\t")
								
								# Make filter
								self.filters.get("Offentlig transport").makeFilter(self.df)

								# Hide load gif
								self.loadGif.grid_forget()

								# Insert into tree
								self._updateList(self.df)
						elif len(self.ptQueue) != 0:
								# Get first element in list
								elem = self.ptQueue.pop()

								# Get address
								text = elem[len("time to "):]
								text = text.split(" (")
								address = text[0]

								# Get day and time of day
								text = text[1].split(", ")
								day = text[0].title()
								timeOfDay = text[1].split(")")[0].title()

								# Get stop
								stop = pt.getLocation(address)

								# If text gotten correctly, load public transport times
								if (day in pt.DAYS and timeOfDay in pt.TIMES and
										stop is not None):
										limit = 90
										self._loadPtInBackground(stop, day, timeOfDay, limit)

				# Check again after a second
				self.window.after(1000, self._checkThread)

		def _setFilters(self):
				self.filters = Filters(self.window, width=FILTER_WIDTH)
				self.filters.grid(column=1, row=2, columnspan=2, sticky="ns", padx=5, pady=5)
				self.filters.setCheckboxNames(FILTER_NAMES_CHECKBOX)
				self.filters.setRangeNames(FILTER_NAMES_RANGE)
				self.filters.setAddedRangeNames(FILTER_NAMES_ADDED_RANGE)
				self.filters.setSliderNames(FILTER_NAMES_SLIDER)
				self.filters.initalizeFilters()
				self.filters.get("Offentlig transport").initializePublicTransport()
				self.filters.get("Offentlig transport").setCommand(self._loadPtInBackground)
				self.filters.get("Distance").initializeDistance()
				self.filters.get("Distance").setCommand(self._getDistances)
				self.filters.get("Steder").initializeChoices(self.placesDf["query"])
				self.filters.get("Steder").setCommand(self._getDistanceToPlaces)
				self.filters.setArguments(
					"Boligside", column="website", sortType=SORT_ALPHABETICALLY)
				self.filters.setArguments(
					"Region", column="region", sortType=SORT_NONE)
				self.filters.setArguments("Type", column="type")
				self.filters.setArguments(
					"Energi mærkat", column="energy level", sortType=SORT_ALPHABETICALLY)
				self.filters.setArguments(
					"Pris", column="price", suffix="kr", loft=6000000, floor=1000000,
					roundTo=100000)
				self.filters.setArguments(
					"Kvadratmeter hus", column="m2 house", suffix="m2", loft=200, roundTo=5)
				self.filters.setArguments(
					"Rum", column="rooms", suffix="rum", loft=10, roundTo=1)
				self.filters.setArguments(
					"Etage", column="floor level", suffix="etage", roundTo=1,
					nanReplaceValue=0, loft=20)
				self.filters.setArguments(
					"År bygget", column="year built", addSeperator=False,
					roundTo=10, floor=1900)
				self.filters.setArguments(
					"Pris per kvadratmeter", column="price per m2", suffix="kr",
					loft=50000, roundTo=1000)
				self.filters.setArguments(
					"Ejerudgifter", column="monthly expenses", suffix="kr",
					loft=10000, roundTo=500)
				self.filters.setArguments(
					"Bruttolån", column="gross mortgage", suffix="kr",
					loft=20000, floor=5000, roundTo=1000)
				self.filters.setArguments(
					"Liggetid", column="days on market", suffix="dage", loft=30, roundTo=1)
				self.filters.setArguments(
					"Offentlig transport", replaceEng="time to", replaceDk="tid til",
					suffix="minutter", loft=90, roundTo=5)
				self.filters.setArguments(
					"Distance", replaceEng="distance to", replaceDk="distance til",
					suffix="km", loft=100, roundTo=5)
				self.filters.setArguments(
					"Steder", replaceEng="shortest distance to",
					replaceDk="korteste distance til", suffix="km",
					loft=5, roundTo=0.5)
				self.filters.setArguments(
					"Sidst opdateret", column="updated", isDate=True)

		def _resetFilters(self):
				self.filters.reset()
				self._updateList(self.df)

		def _createTree(self, frame, name):
				tree = tl.TreeviewList(frame, name)
				frame.grid_columnconfigure(0, weight=1)
				frame.grid_rowconfigure(0, weight=1)
				tree.grid(column=0, row=0, sticky="nsew", padx=5, pady=5)
				#tree.place(x=PADDING, y=PADDING,
				#					 width=TAB_WIDTH - 2 * PADDING, height=TAB_HEIGHT - 39)
				tree.setDataframe(self.df)
				tree.setDoubleClickCommand(
					lambda event: self._onDoubleClick(event, tree))
				tree.setRightClickCommand(
					lambda event: self._onRightClick(event, tree))
				tree.setLeftClickCommand(
					lambda event: self._onLeftClick(event, tree))
				tree.setListColumns(LIST_COLUMNS)
				tree.setColumnsWithDecimalSeperator(COLUMNS_WITH_DECIMAL_SEPERATOR)
				tree.setColumnsToIgnore(COLUMNS_TREE_IGNORE)

				return tree

		def _onLeftClick(self, event, treeview):
				# Set energy label and update expenses
				item = treeview.tree.identify("item", event.x, event.y)
				if not item:
						return
				idx = int(treeview.tree.item(item, "values")[0])
				row = self.df.loc[idx]
				self._setExpenses(row)
				self.gradiant.removePreciseLabel()
				column = self._getGradiantColumn()[1]
				for marker in self.mapMarkers:
						markerId = int(marker.data.split("id:")[1])
						if idx == markerId:
								marker.set_text(marker.data.split("id:")[0])
								row = self.listDf.loc[self.listDf["id"] == idx]
								value = row[column].values[0]
								self.gradiant.setPreciseLabel(value)
						else:
								marker.set_text("")

		def _setExpenses(self, row):
				self.expenseWidget.setEnergyLabel(row["energy level"])
				self.expenseWidget.setMonthlyCostOfOwnership(row["monthly expenses"])
				self.expenseWidget.setHouseArea(row["m2 house"])
				grossMortgage = 0 if pd.isnull(row["gross mortgage"]) else row["gross mortgage"]
				self.expenseWidget.setGrossMortgage(grossMortgage)
				self.expenseWidget.setHeatingType(row["heating installation"])
				self.expenseWidget.update()

		def _onDoubleClick(self, event, treeview):
				# Open link for double clicked list item
				item = treeview.tree.identify("item", event.x, event.y)
				if not item:
						return
				values = treeview.tree.item(item, "values")
				webbrowser.open(self.df.loc[int(values[0]), "link"])

		def _onRightClick(self, event, treeview):
				# Create a popup menu on right clicking the list
				menu = tk.Menu(self.window, tearoff=0)
				region = treeview.tree.identify_region(event.x, event.y)
				if region == "heading":
						# If the column headings are clicked, display menu options
						# related to them (minimize/maximize, remove column)

						# Identify column and set menu title
						colId = treeview.tree.identify_column(event.x)
						title = treeview.tree.heading(colId)["text"].lower().replace("\n", " ")
						width = treeview.tree.column(colId, "width")
						menu.add_command(label=title.title(), state=tk.DISABLED)
						menu.add_separator()

						# If column is minimized, set option for maximizing, else
						# set option to minimize
						if width <= COLUMN_WIDTH_MINIMIZED:
								menu.add_command(
									label="Maksimer kolonne",
									command=lambda: treeview.setColumnWidth(self.listDf, title))
						else:
								menu.add_command(
									label="Minimer kolonne",
									command=lambda: treeview.tree.column(
										colId, width=COLUMN_WIDTH_MINIMIZED))

						# If the column is for public transport or distances, set option
						# to remove column
						if any(self.filters.get(name).replaceDk in title \
									 for name in FILTER_NAMES_ADDED_RANGE):
								f = self.filters.getAddedRange(title)
								columnName = title.replace(f.replaceDk, f.replaceEng)

								menu.add_command(label="Fjern kolonne",
																 command=lambda: self._removeColumn(columnName))
						
				elif region == "cell":
						# If a cell is clicked, set options to remove row or add to favorites
						values = treeview.tree.item(
							treeview.tree.identify("item", event.x, event.y), "values")
						if treeview.name == "Favorite":
								menu.add_command(label="Fjern fra favoritter",
																 command=lambda: self._removeFromFavorites(values))
						else:
								menu.add_command(label="Tilføj til favoritter",
																 command=lambda: self._addToFavorites(values))
								menu.add_command(label="Fjern bolig",
																 command=lambda: self._removeRow(values))
				try:
						menu.tk_popup(event.x_root, event.y_root)
				finally:
						menu.grab_release()

		def _updateData(self, df):
				# Specify columns to index by
				keyColumns = ["address", "floor level", "floor door no.", "postal code"]

				# Correct new data
				self._fixDataframe(df)

				# Remove duplicates
				df.drop_duplicates(subset=keyColumns, keep="first", inplace=True)
				self.df.drop_duplicates(subset=keyColumns, keep="first", inplace=True)

				if self.df.empty:
						# If there is no previous data, set data
						setDataframe(self.df, df)

						# Get distance to places
						self._initPlaces(self.df)

				else:
						# If there is previous data, update and insert
						# Set address as index and update dataframe
						self.df.set_index(keyColumns, inplace=True)
						df.set_index(keyColumns, inplace=True)
						self.df.update(df.loc[:, df.columns != "favorite"])

						# Reset index
						self.df.reset_index(inplace=True)
						df.reset_index(inplace=True)

						# Remove blacklisted housings
						self._removeBlacklistings(df)

						# Get only the newest housings from the new data
						dfNew = pd.merge(df, self.df, on=keyColumns,  how='left', indicator=True)
						dfNew.index = df.index
						dfNew = df[dfNew["_merge"] == "left_only"]

						# Set index for new data to be from end of existing data to
						# length of new data, such that indexes doesn't overlap
						dfNew.index = range(self.df.index.max() + 1,
																self.df.index.max() + 1 + len(dfNew))

						# Get distance to places for new data
						self._initPlaces(dfNew)

						# Append new data and remove duplicates
						setDataframe(self.df, pd.concat([self.df, dfNew]))
						self.df.drop_duplicates(subset=keyColumns, keep="first", inplace=True)

						# Find distances for new data
						f = self.filters.get("Distance")
						for col in f.getRangeNamesEng():
								address = col[len(f.replaceEng + " "):]
								stop = pt.getLocation(address)
								pt.getDistances(self.df, stop)

						# Find distances to places for new data
						f = self.filters.get("Steder")
						for col in f.getRangeNamesEng():
								choices = col[len(f.replaceEng + " "):].split(", ")
								choices = [choice.title() for choice in choices]
								self._getDistanceToPlaces(choices=choices)

						# Set public transport queue
						f = self.filters.get("Offentlig transport")
						self.ptQueue = f.getRangeNamesEng()

				# Fix data
				self._fixDataframe(self.df)

		def _removeBlacklistings(self, df):
			keyColumns = ["address", "floor level", "floor door no.", "postal code"]
			if not self.blacklist.empty:
					cond = df[keyColumns[0]].isin(self.blacklist[keyColumns[0]])
					for col in keyColumns[1:]:
							cond &= df[col].isin(self.blacklist[col])
					df.drop(df[cond].index, inplace=True)

		def _removeColumn(self, columnName):
				# Drop column and reinitialize dataframe
				self.df.drop(columnName, axis=1, inplace=True)
				self._updateApp()

		def _removeRow(self, values):
				# Find corresponding row, transforming it into a dataframe
				row = self.df.loc[int(values[0])].to_frame().T

				if self.blacklist.empty:
						# If blacklist is empty, assign row as blacklist
						setDataframe(self.blacklist, row)
				else:
						# If blacklist is not empty, append and remove duplicates
						setDataframe(self.blacklist, pd.concat([self.blacklist, row]))
						self.blacklist.drop_duplicates(
							subset=["address", "floor level",
											"floor door no.", "postal code"],
							keep="first", inplace=True)

				# Fix dataframe
				self._fixDataframe(self.blacklist)

				# Write to csv
				self.blacklist.to_csv(self.blacklistPath, sep="\t")

				# Remove row from original dataframe and reinitialize dataframe
				self.df.drop(int(values[0]), axis=0, inplace=True)
				self._updateApp()

		def _addToFavorites(self, values):
				# Find corresponding row, transforming it into a dataframe
				self.df.loc[int(values[0]), "favorite"] = True

				# Write to csv
				self.df.to_csv(self.csvPath, sep="\t")

				# Set tree
				self.treeFavorite.setListValues(self._getFavoritesList())

		def _removeFromFavorites(self, values):
				# Find corresponding row, transforming it into a dataframe
				self.df.loc[int(values[0]), "favorite"] = False			

				# Write to csv
				self.df.to_csv(self.csvPath, sep="\t")

				# Set tree
				self.treeFavorite.setListValues(self._getFavoritesList())

		def _getFavoritesList(self):
				# Get all rows where favorite is true
				df = self.df[self.df["favorite"] == True]

				if df.empty:
						return df

				# Make the dataframe into a proper list format
				df = self._createListDataframe(df)

				# Set address names
				self._setAddress(df)

				# Add decimal seperators
				self._addDecimalSeperatorToColumn(df, COLUMNS_WITH_DECIMAL_SEPERATOR)

				return df

		def _setComboboxValues(self):
				comboboxValues = []
				for idx, f in enumerate(self.filters.filters):
						name = f.name
						if name in FILTER_NAMES_RANGE:
								comboboxValues.append(name)
						elif name in FILTER_NAMES_ADDED_RANGE:
								for rs in f.filter.ranges:
										comboboxValues.append(rs.name.title())
												
				length = len(max(comboboxValues, key=len))
				self.gradiantCombo.config(width=length)
				self.gradiantCombo["values"] = comboboxValues

		def _getGradiantColumn(self):
				text = self.gradiantCombo.get()

				if text == "Kvadratmeter hus":
						return text, "m2 hus"
				elif text == "Pris per kvadratmeter":
						return text, "pris per m2"
				elif text == "Etage":
						return text, "floor level"
				return text, text.lower()

		def _setGradiant(self, event):
				text, col = self._getGradiantColumn()

				mm = (None, None)
				if not self.listDf.empty:
						df2 = self.listDf[col].apply(gf.removeDecimalSeperator)
						df2 = df2[~df2.isin(["<NA>"])]
						df2 = df2.astype("Float64")
						mm = (min(df2), max(df2))

				if text not in FILTER_NAMES:
						filtersAddedRange = [self.filters.get(name) for name in \
																 FILTER_NAMES_ADDED_RANGE]
						for f in filtersAddedRange:
								for rs in f.ranges:
										if text.lower() == rs.name.lower():
												self.gradiant.setValues(
													rs.name,
													rs.getRangeValues(),
													rs.hasReachedLoft(),
													rs.hasReachedFloor(),
													rs.getSuffix(),
													mm)
				else:
						rs = self.filters.get(text)
						self.gradiant.setValues(
							rs.parent.name,
							rs.getRangeValues(),
							rs.hasReachedLoft(),
							rs.hasReachedFloor(),
							rs.getSuffix(),
							mm)

				for marker in self.mapMarkers:
						idx = int(marker.data.split("id:")[1])
						row = self.listDf[self.listDf["id"] == idx]
						if row[col].empty:
								marker.delete()
								self.mapMarkers.remove(marker)
								continue

						val = row[col].values[0]
						color = self.gradiant.getValueColor(val)
						if marker.text != "":
								self.gradiant.setPreciseLabel(val)
						marker.marker_color_circle = color
						marker.map_widget.canvas.delete(marker.big_circle)
						marker.big_circle = None
						marker.draw()
				self.dkMap.update_canvas_tile_images()

		def _placeLoadGif(self):
				self.loadGif.grid(column=0, row=0, sticky="ne")

		def _loadDataInBackground(self):
				if self.threadLoad is None or not self.threadLoad.is_alive():
						self._placeLoadGif()
						self.threadLoad = threading.Thread(target=self._getNewData, daemon=True)
						self.threadLoad.start()

		def _loadPtInBackground(self, stop = None, day = None,
														timeOfDay = None, limit = None):
				# Set stop values
				ptFilter = self.filters.get("Offentlig transport")
				if stop is None:
						stop = ptFilter.getStation()

				# Return if stop is none
				if stop is None:
						return

				# Start thread
				if self.threadPt is None or not self.threadPt.is_alive():
						self._placeLoadGif()
						self.threadLoad = threading.Thread(target=self._getTimesToStation,
																							 args=(stop, day,
																										 timeOfDay, limit,),
																							 daemon=True)
						self.threadLoad.start()

		def _getDistances(self):
				# Return if no stop specified
				station = self.filters.get("Distance").getStation()
				if station is None:
						return

				# Get distances and reinitialize data
				columnName = pt.getDistances(self.df, station)
				self._updateApp()

		def _getDistanceToPlaces(self, choices = None):
				# Get filter
				f = self.filters.get("Steder")

				# Get filter choices
				if choices is None:
						choices = f.getChoices()

				# Return if no choices
				if not choices:
						return

				# Reset choices
				f.resetChoices()

				# Set and reinitialize data
				choices = [choice.lower() for choice in choices]
				columnName = f.replaceEng + " " + ", ".join(choices)
				choicesColumns = ["closest {}:distance".format(choice) for choice in choices]
				self.df[columnName] = self.df[choicesColumns].min(axis=1)
				self._updateApp()

		def _fixDataframe(self, df):
				# Set some of the columns to int instead of float
				for col in ["price", "m2 house", "m2 ground", "rooms", "year built",
										"floor level", "price per m2", "monthly expenses",
										"days on market", "postal no.", "down payment",
										"gross mortgage"]:
						df[col] = pd.to_numeric(df[col], errors="coerce")
						df[col] = df[col].astype("Int64")

				# Set nan values in "days on market" to 0
				df["days on market"] = df["days on market"].replace(np.NaN, 0)

				# Set door no. as string
				for col in ["floor door no.", "heating installation"]:
						df[col] = df[col].astype("string")

				# Replace nan values in "website" to "EDC" (first website implemented)
				df["website"] = df["website"].str.title().replace(np.NaN, "EDC")

				# Replace nan values to "Udefineret"
				for col in ["energy level", "heating installation"]:
						df[col] = df[col].str.upper().replace(np.NaN, UNDEFINED)
						df[col] = df[col].replace(UNDEFINED.upper(), UNDEFINED)

				# Set "favorite" to bool
				df["favorite"] = df["favorite"] == True

				# Correct added range values
				for name in FILTER_NAMES_ADDED_RANGE:
						f = self.filters.get(name)
						if any([column not in df.columns for column in f.getRangeNamesEng()]):
								continue
						df[f.getRangeNamesDk()] = df[f.getRangeNamesEng()].astype("Float64")

				# Correct datetime values
				df["updated"] = pd.to_datetime(df["updated"], errors="coerce")

				# Remove rows with empty street names
				df["address"].replace("", np.nan, inplace=True)
				df.dropna(subset=["address"], inplace=True)

				# Remove duplicated indexes
				setDataframe(df, df[~df.index.duplicated(keep="first")])
				df.sort_index(inplace=True)

				# Remove invalid rows
				df.dropna(subset=["postal code"], inplace=True)
				
				# Remove duplicate rows
				df.drop(columns=df.columns[df.columns.duplicated()], inplace=True)

		def _getNewData(self):
				# Set state of search and load button
				ptButton = self.filters.get("Offentlig transport").button
				ptButton["state"] = tk.DISABLED
				self.loadButton["state"] = tk.DISABLED

				# Start timer
				timeStart = time.time()

				# Get subsites on edc site with postal codes within the range
				subsitesEdc = edc.getIndexSubsites(LOWER_POSTAL, UPPER_POSTAL)
				zipcodesBoligsiden = boligsiden.getZipCodes(LOWER_POSTAL, UPPER_POSTAL)
				
				# Get data from subsites
				dataBoligsiden = boligsiden.getHousingData(zipcodesBoligsiden)
				dataEdc = edc.getHousings(subsitesEdc)
				dataBoliga = boliga.getHousingData([1, 2, 3, 4, 5, 6])
				self.threadLoadData = dataBoligsiden + dataEdc + dataBoliga

				print("Getting data took %.2f seconds." % float(time.time() - timeStart))
				
				# Enable buttons again
				ptButton["state"] = tk.NORMAL
				self.loadButton["state"] = tk.NORMAL

				# Hide load gif
				self.loadGif.grid_forget()

		def _getCsvData(self, path, df = pd.DataFrame()):
				# Read csv file
				setDataframe(df, pd.read_csv(path, sep="\t", index_col=0))

				# Set all columns to lower
				df.columns = df.columns.str.lower()

				# Add new columns (if any)
				newColumns = list(set(DATA_COLUMNS).difference(df.columns))
				if newColumns != []:
						df[newColumns] = ""
						df.to_csv(path, sep="\t")

				# Fix data
				self._fixDataframe(df)

		def _initPlaces(self, df):
				if self.placesDf.empty:
						return

				for value in self.placesDf["query"].unique():
						name = "closest {}".format(value.lower())
						if name + ":distance" in df.columns:
								continue

						# Get chosen place
						places = self.placesDf[self.placesDf["query"] == value]
						# Reindexing
						index = [i for i in range(len(places))]
						places.index = index
						places.sort_index(inplace=True)

						# Convert places to numpy coordinates
						placesCoords = places[["coord. y", "coord. x"]].to_numpy()

						# Create BallTree using places coordinates and specify distance metric
						tree = BallTree(placesCoords, metric="haversine")

						def distance(row):
								coords = row[["coord. y", "coord. x"]].to_numpy()
								dist, ind = tree.query(coords.reshape(1, -1), k=1)
								ind = ind[0][0]
								return (dist[0][0] * 100,
												places.loc[ind, "name"],
												places.loc[ind, "coord. x"],
												places.loc[ind, "coord. y"])

						# Set smallest distance
						cDist = name + ":distance"
						cName = name + ":name"
						cX = name + ":coord. x"
						cY = name + ":coord. y"
						df[[cDist, cName, cX, cY]] = df.apply(distance, axis=1,
																									result_type="expand")

		def _initData(self):
				# Get data and remove blacklistings
				self._getCsvData(self.csvPath, self.df)
				self._removeBlacklistings(self.df)

				# If distances to places are not found, find them
				self._initPlaces(self.df)

				# Remove danish columns in dataframe, as this is unintened
				for name in FILTER_NAMES_ADDED_RANGE:
						f = self.filters.get(name)
						for fName in f.getMatchingDk(self.df.columns.tolist()):
								self.df.drop(fName, axis=1, inplace=True)

				# Update checkboxes and range sliders
				self.filters.makeFilters(self.df)

				# Load filter settings
				self.filters.loadFilterSettings(self.filterCsvPath,
																				filtersToIgnore=["Sidst opdateret"])

				# Set combobox values
				self._setComboboxValues()
				self.gradiantCombo.set("Pris")
				self._setGradiant(0)

				# Set favorites
				self.treeFavorite.setListValues(self._getFavoritesList())

				self._updateApp()

		def _updateApp(self):
				self.df.to_csv(self.csvPath, sep="\t")
				
				# Update checkboxes and range sliders
				self.filters.makeFilters(self.df)

				# Update list
				self._updateList(self.df)

		def _getTimesToStation(self, stop = None, day = None,
													 timeOfDay = None, limit = None):
				# Set state of search and load button
				ptFilter = self.filters.get("Offentlig transport")
				ptFilter.button["state"] = tk.DISABLED
				self.loadButton["state"] = tk.DISABLED

				# Get day and time of day
				if day is None:
						day = ptFilter.getDay()
				if timeOfDay is None:
						timeOfDay = ptFilter.getTime()
				departureTime = pt.getDepartureTime(day, timeOfDay)

				# Calculate distances
				if stop is None:
						stop = ptFilter.getStation()
				df = self.df.copy()
				columnNameDist = pt.getDistances(df, stop)
				df.sort_values(columnNameDist, axis=0, inplace=True)

				# Set name
				columnName = "time to {} ({}, {})".format(
					stop["name"].split(",")[0], day, timeOfDay).lower()

				# Get values
				if limit is None:
						limit = ptFilter.getLimit()
				df[columnName] = pt.getStationsWithinLimit(df, stop, limit, columnName,
																									 time=departureTime,
																									 includeWalking=True)
				df[columnName] = df[columnName].astype("Int64")
				self.threadPtData = df[columnName]

				# Sort by index
				df.sort_index(inplace=True)

				# Enable buttons again
				ptFilter.button["state"] = tk.NORMAL
				self.loadButton["state"] = tk.NORMAL

				# Hide load gif
				self.loadGif.grid_forget()

		def _getAddress(self, row):
				addr = row["address"]
				postal = row["postal code"]
				floorLevel = row["floor level"]
				floorNo = row["floor door no."]
				hasFloorLevel = not pd.isna(floorLevel)
				hasFloorNo = not pd.isna(floorNo)
				if not hasFloorLevel and not hasFloorNo:
						return "{}, {}".format(addr, postal)
				
				if not hasFloorLevel or floorLevel == 0:
						floorLevel = "st. etage"
				else:
						floorLevel = str(floorLevel) + ". etage"

				if not hasFloorNo:
						return "{}, {}, {}".format(addr, floorLevel, postal)
				else:
						return "{}, {} {}, {}".format(addr, floorLevel, floorNo, postal)

		def _addDecimalSeperatorToColumn(self, df, columns):
				if not df.empty:
						for col in columns:
								df[col] = df.apply(
									lambda row: gf.addDecimalSeparator(row[col]), axis=1)

		def _updateList(self, df):
				# Create list dataframe
				setDataframe(self.listDf, self._createListDataframe(df))
				if self.listDf.empty:
						return

				# Set index
				self.listDf.set_index("id", inplace=True)

				# Filter values except checkboxes
				self.filters.sort(self.listDf, sortValues=COLUMNS_TO_SORT,
													avoid=[TYPE_CHECKBOX])

				# Update checkboxes
				self.filters.update(self.listDf, sortValues=COLUMNS_TO_SORT,
														types=[TYPE_CHECKBOX])

				# Filter checkboxes
				self.filters.sort(self.listDf, sortValues=COLUMNS_TO_SORT,
													avoid=[TYPE_RANGE, TYPE_ADDED_RANGE,
																 TYPE_SLIDER])

				# Update range checkboxes
				self.filters.update(self.listDf, sortValues=COLUMNS_TO_SORT,
														types=[TYPE_RANGE, TYPE_ADDED_RANGE])

				# Save search options
				self.filters.saveFiltersSettings(self.filterCsvPath)

				# Add decimal seperator
				self._addDecimalSeperatorToColumn(
					self.listDf, COLUMNS_WITH_DECIMAL_SEPERATOR)

				# Set address names
				self._setAddress(self.listDf)

				def getMarkerData(row):
						return "{}\n{}kr, {} rum, {}m\u00b2".format(row["adresse"].title(),
																												row["pris"],
																												row["rum"],
																												row["m2 hus"])

				# Insert new markers and update old markers if there are less than
				# 1000 listings (avoids lag)
				if len(self.listDf) < 1000 and not self.listDf.empty:
						# Get list of current markers' data
						markerList = [getMarkerData(row) for idx, row in self.listDf.iterrows()]

						# Keep existing markers and remove the nonexisting
						existingMarkers = []
						for marker in list(self.mapMarkers):
								if (marker.data.split("id:")[0] in markerList):
										existingMarkers.append(marker.data.split("id:")[0])
								else:
										self.mapMarkers.remove(marker)
										marker.delete()

						# Skip the housings which have markers and add the new ones
						for idx, row in self.listDf.iterrows():
								data = getMarkerData(row)
								if data in existingMarkers:
										continue
								data += "id:" + str(idx)
								marker = self.dkMap.set_marker(self.df.loc[idx, "coord. y"],
																							 self.df.loc[idx, "coord. x"],
																							 text="",
																							 data=data,
																							 command=self._clickMarker,
																							 command2=self._doubleClickMarker)
								self.mapMarkers.append(marker)
				else:
						# If more than 500 listings or no data, remove all markers
						for marker in list(self.mapMarkers):
								self.mapMarkers.remove(marker)
								marker.delete()

				# Reset index
				self.listDf.reset_index(inplace=True)

				# Make list
				self.treeMain.setListValues(self.listDf)

				# Set gradiant on map
				if len(self.listDf) < 1000 and not self.listDf.empty:
						self._setGradiant(0)

				# Sort if previously sorted
				self.treeMain.sortList()

				# Display number of housings
				self.noOfResultsText.set("{} boliger".format(len(self.listDf)))

		def _clickMarker(self, marker):
				self.gradiant.removePreciseLabel()
				for mark in self.mapMarkers:
						mark.set_text("")
				if marker.text == "":
						marker.set_text(marker.data.split("id:")[0])
						column = self._getGradiantColumn()[1]
						idx = int(marker.data.split("id:")[1])
						row = self.listDf.loc[self.listDf["id"] == idx]
						self.treeMain.tree.selection_set(idx)
						self.treeMain.tree.focus(idx)
						self.treeMain.tree.see(idx)
						self._setExpenses(self.df.loc[idx])
						value = row[column].values[0]
						self.gradiant.setPreciseLabel(value)

		def _doubleClickMarker(self, marker):
				idx = int(marker.data.split("id:")[1])
				link = self.df["link"].loc[idx]
				webbrowser.open(link)

		def _createListDataframe(self, df):
				# Create the new dataframe
				df2 = pd.DataFrame()

				# Return if df is emoty
				if df.empty:
						return df2

				# Insert columns and values
				df2["id"] = list(df.index)
				df2.set_index("id", inplace=True)
				df2["adresse"] = ""
				df2[COLUMNS_TREE_IGNORE] = df[COLUMNS_TREE_IGNORE]
				df2[["pris", "energimærkat", "type", "m2 hus", "m2 grund", "rum",
						 "år bygget", "pris per m2", "ejerudgifter", "bruttolån",
						 "liggetid"]] = df[[
						 "price", "energy level", "type", "m2 house", "m2 ground", "rooms",
						 "year built", "price per m2", "monthly expenses", "gross mortgage",
						 "days on market"]]
				for name in FILTER_NAMES_ADDED_RANGE:
						f = self.filters.get(name)
						df2[f.getRangeNamesDk()] = df[f.getRangeNamesEng()].round(1).astype("Float64")
				df2["boligside"] = df["website"]

				# Reset index
				df2.reset_index(inplace=True)

				return df2

		def _setAddress(self, df):
				if df.empty:
						return

				# Set addresses
				df["adresse"] = df.apply(self._getAddress, axis=1)

				# Remove non valid entries
				df.dropna(subset=["adresse"], inplace=True)