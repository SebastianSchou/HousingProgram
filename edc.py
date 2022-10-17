#!/usr/bin/env python3
from bs4 import BeautifulSoup
import concurrent.futures
from concurrent.futures import TimeoutError
import re
from time import time, sleep
import datetime
import requests
import general_functions as gf


WEBSITE_NAME = "https://www.edc.dk"
WEBSITE_NAME_POSTAL_CODES = "https://www.edc.dk/bolig/postnumre-i-danmark/"

def getIndexSubsites(postalMin = 0, postalMax = 9999):
		# return a list of links for subsites with housings, split into postal
		# numbers, from the EDC housing site
		# Argument:
		#		- postalMin: Minimum postal number (int)
		# 	- postalMax: Maximum postal number (int)
		# Returns:
		#		- List of links (list)
		resp = gf.getSiteData(WEBSITE_NAME_POSTAL_CODES)
		if resp.status_code != 200:
				return []

		soup = BeautifulSoup(resp.content, "html.parser")
		subsites = []
		for a in soup.findAll("a"):
				try:
						link = a.get("href")
						if link == None:
								continue
						postal = re.findall(r"[0-9]{4}", link)
						if postal == []:
								continue
						postal = int(postal[0])
						if postal >= postalMin and postal <= postalMax:
								if re.match(r"/bolig/[0-9]{4}(?![0-9])", link):
										subsites.append(WEBSITE_NAME +
																		link +
																		"?antal=1000&side=1#lstsort")
				except:
						continue
		return subsites

def getHousingData(subsite):
		# Get subsite data
		resp = gf.getSiteData(subsite)
		if resp.status_code != 200:
				return []

		# Convert page content to readable format
		content = resp.content
		soup = BeautifulSoup(content, "html.parser")
		noOfHousings = soup.title.string.split(" ")[0].strip()
		if not noOfHousings.isdigit() or noOfHousings == 0:
				return []
		noOfTimes = 0
		timeAvg = 0
		data = []
		# Loop over each housing ad
		for a in soup.findAll(class_="col-12 propertyitem propertyitem--list"):
				timeA = time()
				try:
						# Get link to site
						link = a.find(class_="propertyitem__link").get("href")
						if link.split("/")[1] == "alle-boliger":
								link = "https://www.edc.dk" + link

						# Get coordinates
						coords = a.findAll("meta")
						x = gf.toFloat(coords[1].get("content"), 6)
						y = gf.toFloat(coords[0].get("content"), 6)

						# Breakdown html to get additional info
						b = a.find(class_="propertyitem__wrapper")
						firstText = b.find(class_="propertyitem__list--listview")

						# Get address, including level and number on floor
						addr = firstText.find("span").text.replace(",", "")
						level = None
						floorNo = None
						addr, level, floorNo = gf.getAddressSplit(addr)

						# Get postal and postal text
						postal = firstText.find("span", class_="propertyitem__zip--listview").text
						postalNo = gf.toInt(postal.split(" ")[0])
						region = gf.postalCodeRegionDk(postalNo)
						postalName = " ".join(postal.split(" ")[1:])

						# Get price
						price = firstText.find("div", class_="propertyitem__price").text
						price = gf.toInt(price.split(" ")[1])

						# Get energy level and housing type
						ownerInfo = firstText.find("div", class_="propertyitem__owner--listview")
						energy = ownerInfo.find('a')
						housingType = ownerInfo.text.split(" ")[0]
						if energy != None:
								energy = energy.text
								housingType = housingType[len(energy):]

						# Get squaremeters, rooms, year built, price per m2, and monthly expenses
						additionalInfo = b.findAll("td")
						m2House = gf.toInt(additionalInfo[0].text)
						m2Ground = gf.toInt(additionalInfo[1].text)
						rooms = gf.toInt(additionalInfo[2].text)
						year = gf.toInt(additionalInfo[3].text)
						daysOnMarket = gf.toInt(additionalInfo[4].text)
						if additionalInfo[4].findAll("br"):
								daysOnMarket = gf.toInt(
									re.findall(r'\d+', str(additionalInfo[4]))[0])
						pricePerM2 = None
						monthlyExpenses = None
						if len(additionalInfo) >= 8:
								pricePerM2 = gf.toInt(additionalInfo[6].text)
								monthlyExpenses = gf.toInt(additionalInfo[7].text)
						elif len(additionalInfo) == 7 and "/" in additionalInfo[6].text:
								n = additionalInfo[6].text.split(" / ")
								monthlyExpenses = gf.toInt(n[0]) + gf.toInt(n[1])

						# Set website and favorite
						website = "EDC"
						favorite = False

						# Set update time
						updateTime = datetime.datetime.now()

						# Unavailable data
						heatingInstallation = None
						downPayment = None
						grossMortgage = None

						# Append data
						datapoint = [addr, level, floorNo, postal, postalNo, postalName,
												 region, price, energy, housingType, link, x, y, m2House,
												 m2Ground, rooms, year, pricePerM2, monthlyExpenses,
												 updateTime, website, favorite, daysOnMarket,
												 heatingInstallation, downPayment, grossMortgage]
						data.append(datapoint)
				except Exception as e:
						print(e)
						continue
		return data

def getHousings(subsites):
		data = []
		threads = min(30, len(subsites))
		with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
				try:
						for result in executor.map(getHousingData, subsites, timeout=300):
								data = data + result
				except TimeoutError:
						print("Process fik en timeout fejl.")
		return data