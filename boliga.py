#!/usr/bin/env python3
import concurrent.futures
from concurrent.futures import TimeoutError
import datetime
import requests
import general_functions as gf
import re

WEBSITE = "https://api.boliga.dk/api/v2/search/results?pageSize=999&" + \
					"sort=daysForSale-d&area=AREA&page=PAGE&includeds=1"
PROPERTY_TYPES = {3: "Ejerlejlighed", 1: "Villa", 4: "Fritidshus",
									2: "Rækkehus", 6: "Landejendom", 9: "Villalejlighed",
									5: "Andelsbolig", 7: "Helårsgrund", 8: "Fritidsgrund",
									10: "Udefineret", 12: "Udefineret", 11: "Udefineret"}

ignore = ["propertyType", "price", "energyClass", "city", "zipCode", "street",
					"size", "rooms", "lotSize", "floor", "buildYear", "squaremeterPrice",
					"daysForSale", "exp", "downPayment", "latitude", "longitude", "id"]

def getHousingAreaData(area, page = 1):
		# Return a list of housing data from boligsiden.dk for the
		# specified area
		# Argument:
		#		- area: Area to search for (int)
		# Returns:
		#		- List of housing data (list)

		# Get the proper website name
		websiteName = WEBSITE.replace("AREA", str(area)).replace("PAGE", str(page))

		# Get website
		resp = gf.getSiteData(websiteName)
		if resp.status_code != 200:
				return []
		
		# Get data as dict
		content = resp.json()
		if content["results"] is None:
				return []

		# Get the data for each housing
		data = []
		for item in content["results"]:
				link = "https://www.boliga.dk/bolig/" + str(item["id"])
				propertyType = item["propertyType"]
				if propertyType in PROPERTY_TYPES:
						propertyType = PROPERTY_TYPES[propertyType]
				else:
						print(link, propertyType)
						continue

				price = item["price"]
				energyClass = item["energyClass"]
				if isinstance(energyClass, str) and energyClass.lower() in ["-", "j", "k"]:
							energyClass = "Udefineret"
				city = item["city"]
				zipCode = item["zipCode"]
				postal = "{} {}".format(zipCode, city)
				region = gf.postalCodeRegionDk(zipCode)
				street = item["street"]
				if street == "":
						print("Empty street, link:", link)
						continue
				size = item["size"]
				rooms = item["rooms"]
				lotSize = item["lotSize"]
				floor = item["floor"]
				floorNo = None
				streetCopy = street
				street, floor, door = gf.getAddressSplit(street)
				buildYear = item["buildYear"]
				squaremeterPrice = item["squaremeterPrice"]
				daysForSale = item["daysForSale"]
				exp = item["exp"]
				downPayment = item["downPayment"]
				latitude = item["latitude"]
				longitude = item["longitude"]

				# Set update time
				updateTime = datetime.datetime.now()

				# Set website and favorite
				website = "Boliga"
				favorite = False
				heatingInstallation = None
				grossMortgage = None

				# Set data
				datapoint = [street, floor, door, postal, zipCode, city, region,
										 price, energyClass, propertyType, link, longitude,
										 latitude, size, lotSize, rooms,
										 buildYear, squaremeterPrice, exp, updateTime,
										 website, favorite, daysForSale, heatingInstallation,
										 downPayment, grossMortgage]
				data.append(datapoint)

		if len(content["results"]) == 500:
				data.extend(getHousingAreaData(area, page + 1))

		return data

def getHousingData(areas):
		data = []
		if not areas:
				return data

		maxWorkers = min(10, len(areas))
		with concurrent.futures.ThreadPoolExecutor(max_workers=maxWorkers) as executor:
				try:
						for result in executor.map(
							lambda area: getHousingAreaData(area), areas):
								data += result
				except TimeoutError:
						print("Process fik en timeout fejl.")
		return data