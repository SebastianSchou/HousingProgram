#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import general_functions as gf
import numpy as np
import pandas as pd
from PIL import ImageFont
import colors
import math
import time

def wrap(string, length=15):
		if len(string) > length:
				half = int(len(string) / 2)
				split = string[half:].split(" ")
				s1 = string[:half] + split[0]
				if len(split) == 1:
						return s1
				s2 = " ".join(split[1:])
				return s1 + "\n" + s2
		return string

class TreeviewList():
		"""docstring for TreeviewList"""
		def __init__(self, frame, name):
				self.container = tk.Frame(frame)
				self.tree = ttk.Treeview()
				self.name = name
				self.df = pd.DataFrame()
				self.listDf = pd.DataFrame()
				self.sortingValues = (None, None)
				self.listColumns = []
				self.columnsWithDecimalSeperator = []
				self.columnsToIgnore = []
				self._createTreeview()

		def _createTreeview(self):
				# Create and attatch scrollbars
				vsby = ttk.Scrollbar(orient="vertical", command=self.tree.yview)
				vsbx = ttk.Scrollbar(orient="horizontal", command=self.tree.xview)
				self.tree.configure(yscrollcommand=vsby.set)
				self.tree.configure(xscrollcommand=vsbx.set)

				# Insert tree and scrollbars into grid
				self.tree.grid(column=0, row=0, sticky="nsew", in_=self.container)
				vsby.grid(column=1, row=0, sticky="ns", rowspan=2, in_=self.container)
				vsbx.grid(column=0, row=1, sticky="nsew", in_=self.container)
				self.container.grid_columnconfigure(0, weight=1)
				self.container.grid_rowconfigure(0, weight=1)

		def place(self, **kwargs):
				self.container.place(kwargs)

		def grid(self, **kwargs):
				self.container.grid(kwargs)

		def setDataframe(self, df):
				self.df = df

		def setListDataframe(self, df):
				self.listDf = df

		def setDoubleClickCommand(self, command):
				self.tree.bind("<Double-Button-1>", command)

		def setRightClickCommand(self, command):
				self.tree.bind("<Button-3>", command)

		def setLeftClickCommand(self, command):
				self.tree.bind("<Button-1>", command)

		def setColumnsWithDecimalSeperator(self, columns):
				self.columnsWithDecimalSeperator = columns

		def setColumnsToIgnore(self, columns):
				self.columnsToIgnore = columns

		def setListColumns(self, columns):
				self.listColumns = columns

		def sortList(self):
				if self.sortingValues[0] != None:
						self._sortList(self.sortingValues[0], self.sortingValues[1])

		def setListValues(self, df):
				# Remove all data in list
				indexes = []
				indexColumn = list(df.iloc[:, 0])
				for child in self.tree.get_children():
						idx = self.tree.item(child)["values"][0]
						if idx in indexColumn:
								indexes.append(idx)
						else:
								self.tree.delete(child)

				# Initialize column names
				columnList = df.columns.tolist()
				if not columnList:
						columnList = self.listColumns

				for column in self.columnsToIgnore:
						if column in columnList:
								columnList.remove(column)

				# Set header height to two lines
				self.tree.heading("#0", text="\n\n")

				self.tree["columns"] = columnList
				self.tree["show"] = "headings"

				for name in self.tree["columns"]:
						# Set column names
						self.tree.heading(name,
														  text=wrap(name.title()),
														  command=lambda col=name: self._sortList(col, False))

						# Set header width
						self.setColumnWidth(df, name)

				# Insert data
				for rowId, row in df[~df.iloc[:, 0].isin(indexes)].iterrows():
						row = row.drop(self.columnsToIgnore)
						item = self.tree.insert("", "end", iid=row["id"], values=row.tolist())

				# Set tags
				for idx, child in enumerate(self.tree.get_children()):
						tag = "Evenrow" if idx % 2 == 0 else "Oddrow"
						self.tree.item(child, tags=(tag,))

				# Set color of even and odd rows
				self.tree.tag_configure("Evenrow", background=colors.LIST_COLOR_1)
				self.tree.tag_configure("Oddrow", background=colors.LIST_COLOR_2)

				# Set list dataframe
				self.listDf = df

		def setColumnWidth(self, df, name):
				# Get length of the longest word in column, incl. header name
				header = wrap(name)
				if "\n" in header:
						header = max(header.split("\n"), key=len)
				longestWord = header.title()
				if not df.empty:
						strings = df[name].astype("string").str.len()
						strMax = strings.max()
						if not str(strMax).isdigit():
								strMax = len(str(strMax))
						if len(longestWord) < strMax:
								argmax = np.where(strings == strMax)[0]
								longestWord = df[name].iloc[argmax].tolist()[-1]
						
				# Adjust the column's width to the header string
				font = ImageFont.truetype("cambria.ttc", 9, encoding="unic")
				size = font.getsize(str(longestWord))[0]
				self.tree.column(name, width=round(size*1.35)+15, stretch=False)

		def _sortList(self, col, reverse):
				# Sort treeview list
				if col not in self.tree["columns"]:
						self.sortingValues = (None, None)
						return

				# Remember sorting
				self.sortingValues = (col, reverse)

				# Get column index
				colIndex = self.tree["columns"].index(col)

				# Get list items
				children = self.tree.get_children()

				# Get column values
				l = [(self.tree.item(k)["values"][colIndex], k) for k in children]

				# Remove decimal seperator
				if col in self.columnsWithDecimalSeperator:
						l = [(gf.removeDecimalSeperator(v), k) for (v, k) in l]

				# The sorting method for Int64 type columns. This method sorts <NA>
				# values last
				def sortMethod(e):
						if isinstance(e[0], str):
								try:
										return float(e[0])
								except:
										return math.inf
						else:
								return e[0]

				# Sort NaN values last if column is of type "Int64"
				if (self.listDf.dtypes[col] == "Int64" or
						self.listDf.dtypes[col] == "Float64" or
						col in self.columnsWithDecimalSeperator):
						l.sort(key=sortMethod, reverse=reverse)
				else:
						l.sort(key=lambda e: e[0], reverse=reverse)

				# Move items and change tags
				for idx, (val, k) in enumerate(l):
						tag = "Evenrow" if idx % 2 == 0 else "Oddrow"
						self.tree.item(k, tags=(tag,))
						self.tree.move(k, "", idx)

				# Set color of even and odd rows
				self.tree.tag_configure("Evenrow", background=colors.LIST_COLOR_1)
				self.tree.tag_configure("Oddrow", background=colors.LIST_COLOR_2)

				# Reverse sorting if column heading is pressed again
				self.tree.heading(col, text=wrap(col.title()),
													command=lambda: self._sortList(col, not reverse))