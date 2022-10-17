#!/usr/bin/env python3
import concurrent.futures
from concurrent.futures import TimeoutError
import datetime
import requests
import general_functions as gf


ZIP_CODES_WEBSITE = "https://api.prod.bs-aws-stage.com/zip_codes"
HOUSINGS_SITE = "https://api.prod.bs-aws-stage.com/search/cases?ZIPCODES" \
						 		"addressTypes=villa%2Ccondo%2Cterraced+house%2Choliday+house" \
								"%2Ccooperative%2Cfarm%2Chobby+farm%2Cfull+year+plot" \
								"%2Cvilla+apartment%2Choliday+plot&per_page=HOUSINGS_NUMBER" \
								"&page=PAGE_NUMBER&sortAscending=true&sortBy=zipCode"
HOUSING_TYPES = {"terraced house": "Rækkehus", "condo": "Ejerlejlighed",
								 "villa apartment": "Villalejlighed", "villa": "Villa",
								 "cooperative": "Andelsbolig", "holiday plot": "Fritidsgrund",
								 "farm": "Landejendom", "full year plot": "Helårsgrund",
								 "hobby farm": "Lystejendomme", "holiday house": "Fritidshus",
								 "allotment": "Fritidshus"}

def getZipCodes(postalMin = 0, postalMax = 9999):
		# Return a list of postal codes used to request sites for boligsiden.dk
		# Argument:
		#		- postalMin: Minimum postal number (int)
		# 	- postalMax: Maximum postal number (int)
		# Returns:
		#		- List of postal codes (list)

		# Get website
		resp = gf.getSiteData(ZIP_CODES_WEBSITE)
		if resp.status_code != 200:
				return []

		# Get data as dict
		content = resp.json()

		# Get zipcodes within limits
		zipcodes = []
		for item in content["zipCodes"]:
				if "group" in item:
						zipcode = item["group"]
				else:
						zipcode = item["zipCode"]
				if (zipcode not in zipcodes and
						zipcode >= postalMin and
						zipcode <= postalMax):
						zipcodes.append(zipcode)

		return zipcodes

def getHousingZipcodeData(zipcode):
		# Return a list of housing data from boligsiden.dk for the
		# specified zipcode
		# Argument:
		#		- zipcode: Zipcode to search for (int)
		# Returns:
		#		- List of housing data (list)

		# Set the zipcode in the correct format
		zipcodeStr = "zipCodes={}&".format(zipcode)

		# Get the proper website name
		websiteName = HOUSINGS_SITE.replace(
			"ZIPCODES", zipcodeStr).replace(
			"HOUSINGS_NUMBER", "1000").replace(
			"PAGE_NUMBER", str(1))

		# Get website
		resp = gf.getSiteData(websiteName)
		if resp.status_code != 200:
				return []
		
		# Get data as dict
		content = resp.json()
		if content["cases"] is None:
				return []

		# Get the data for each housing
		data = []
		for item in content["cases"]:
				status = item["status"]
				roadName = item["address"]["roadName"]
				houseNumber = ""
				if "houseNumber" in item["address"]:
						houseNumber = item["address"]["houseNumber"]
				addr = "{} {}".format(roadName, houseNumber).strip()
				floor = None
				if "floor" in item["address"]:
						floor = gf.toInt(item["address"]["floor"], returnValue=None)
				door = None
				if "door" in item["address"]:
						door = item["address"]["door"]
				cityName = item["address"]["cityName"]
				postalNo = gf.toInt(item["address"]["zipCode"])
				region = gf.postalCodeRegionDk(postalNo)
				daysOnMarket = None
				if "daysOnMarket" in item:
						daysOnMarket = item["daysOnMarket"]
				postal = "{} {}".format(postalNo, cityName)
				coordinatesLat = gf.toFloat(item["coordinates"]["lat"], 6)
				coordinatesLon = gf.toFloat(item["coordinates"]["lon"], 6)
				link = "https://www.boligsiden.dk" + \
							 item["address"]["_links"]["self"]["href"]
				if "caseUrl" in item:
						link = item["caseUrl"]
				housingArea = 0
				if "housingArea" in item:
						housingArea = gf.toInt(item["housingArea"])
				energyLabel = None
				if "energyLabel" in item:
						energyLabel = item["energyLabel"].upper()
				monthlyExpense = gf.toInt(item["monthlyExpense"])
				numberOfRooms = 0
				if "numberOfRooms" in item:
						numberOfRooms = gf.toInt(item["numberOfRooms"])
				priceCash = gf.toInt(item["priceCash"])
				perAreaPrice = 0
				if "perAreaPrice" in item:
						perAreaPrice = gf.toInt(item["perAreaPrice"])
				yearBuilt = None
				if "yearBuilt" in item:
						yearBuilt = gf.toInt(item["yearBuilt"], returnValue=None)
				heatingInstallation = None
				if "buildings" in item["address"]:
						if "yearRenovated" in item["address"]["buildings"][0]:
								yearBuilt = gf.toInt(
									item["address"]["buildings"][0]["yearRenovated"])
						if "heatingInstallation" in item["address"]["buildings"][0]:
								heatingInstallation = item["address"]["buildings"][0]["heatingInstallation"]
				downPayment = None
				grossMortgage = None
				if "realEstate" in item:
						if "downPayment" in item["realEstate"]:
								downPayment = item["realEstate"]["downPayment"]
						if "grossMortgage" in item["realEstate"]:
								grossMortgage = item["realEstate"]["grossMortgage"]
				addressType = item["addressType"]
				if addressType in HOUSING_TYPES:
						addressType = HOUSING_TYPES[addressType]
				else:
						print(addressType, link)
				lotArea = 0
				if "lotArea" in item:
						lotArea = gf.toInt(item["lotArea"])
				if status != "open":
						print(status, addr, postalNo, link)

				# Set update time
				updateTime = datetime.datetime.now()

				# Set website and favorite
				website = "Boligsiden"
				favorite = False

				# Set data
				datapoint = [addr, floor, door, postal, postalNo, cityName, region,
										 priceCash, energyLabel, addressType, link, coordinatesLon,
										 coordinatesLat, housingArea, lotArea, numberOfRooms,
										 yearBuilt, perAreaPrice, monthlyExpense, updateTime,
										 website, favorite, daysOnMarket, heatingInstallation,
										 downPayment, grossMortgage]
				data.append(datapoint)
		return data

def getHousingData(zipcodes):
		data = []
		if not zipcodes:
				return data

		maxWorkers = min(30, len(zipcodes))
		with concurrent.futures.ThreadPoolExecutor(max_workers=maxWorkers) as executor:
				try:
						for result in executor.map(
							lambda zipcode: getHousingZipcodeData(zipcode), zipcodes):
								data += result
				except TimeoutError:
						print("Process fik en timeout fejl.")
		return data

def printFunction(item, spaces = 0):
		if isinstance(item, dict):
				for key, val in item.items():
						if key in ["images", "defaultImage",
											 "descriptionBody"]:
								continue
						print(" " * spaces * 2, key, "(dict with {} key(s))".format(len(item.keys())))
						printFunction(val, spaces + 1)
		elif isinstance(item, list):
				for val in item:
						print(" " * spaces * 2, "(list of len {})".format(len(val)))
						printFunction(val, spaces + 1)
		else:
				print(" " * spaces * 2, item, "(val)")