#!/usr/bin/env python3
import concurrent.futures
from concurrent.futures import TimeoutError
import datetime
import requests
import general_functions as gf
import pandas as pd
import numpy as np
import os

KRAK_SITE = "https://www.krak.dk/api/cs?device=desktop&query=QUERY" \
						"&sortOrder=default&profile=krak&page=PAGE"
HEADER = ["name", "query", "labels", "address", "postal no.", "postal name", "coord. x", "coord. y"]
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
QUERIES  = [["Metrostationer", "Metrostationer"],
						["Togstationer", "Togstationer"],
						["S-togsstationer", "S-togsstationer"],
						["Supermarked", ["Supermarked", "Discountsupermarkeder",
						 								 "Købmænd", "Shoppingcenter"]],
						["Fitnesscenter", ["Fitnesscenter"]],
						["Restaurant", ["Restaurant", "Kroer", "Kinesisk restaurant",
														"Cafeterier", "Café", "Italienske restauranter",
														"Pizzeria", "Grillbar", "Græske restauranter",
														"Frokostrestauranter", "Danske restauranter",
														"Take away", "Fastfood-spisesteder",
														"Sushirestaurant", "Thailandske restauranter",
														"Mexicanske restauranter", "Steakrestauranter"]]]


def getKrakData(query, queryLabels):
		site = KRAK_SITE.replace("QUERY", query + " sjælland")
		queryHits = 1
		querySum = 0
		data = []
		page = 0
		while True:
				try:
						resp = gf.getSiteData(site.replace("PAGE", str(page)))
						content = resp.json()
						if len(content["items"]) == 0:
								break

						queryHits = content["count"]
						querySum += len(content["items"])
						print("Progress: %i/%i" % (querySum, queryHits))

						for item in content["items"]:
								try:
										if not "location" in item:
												continue
										name = item["name"]
										labels = [x["label"] for x in item["headings"] if "label" in x]
										if queryLabels is not None:
												if ((isinstance(queryLabels, str) and
														 queryLabels not in labels) or
														(isinstance(queryLabels, list) and
														 not any(queryLabel in labels for queryLabel in queryLabels))):
														continue
										streetName = item["address"][0]["streetName"]
										streetNumber = item["address"][0]["streetNumber"]
										addr = "{} {}".format(streetName, streetNumber)
										postCode = item["address"][0]["postCode"]
										postArea = item["address"][0]["postArea"]
										lon = item["location"][0]["xCoord"]
										lat = item["location"][0]["yCoord"]
										#print(name, labels)
										data.append([name, query, labels, addr, postCode, postArea, lon, lat])
								except Exception as e:
										print(e)
										print(item)
										continue
						page += 1
				except Exception as e:
						print(e)
						break

		# Append missing data manually
		if query == "S-togsstationer":
				name = "Albertslund St."
				labels = [query]
				addr = "Vognporten 9"
				postCode = 2620
				postArea = "Albertslund"
				lon = 12.353710920565227
				lat = 55.658132065557965
				data.append([name, query, labels, addr, postCode, postArea, lon, lat])

		# Set as dataframe
		places = pd.DataFrame(data)
		if places.empty:
				return places
		places.columns = HEADER

		# Remove duplicates
		places.drop_duplicates(subset=["name", "coord. x", "coord. y"],
													 keep="first", inplace=True)
		return places

if __name__ == "__main__" :
		places = pd.DataFrame()
		for query in QUERIES:
				print("Querying for '%s'" % query[0])
				places = pd.concat([places, getKrakData(query[0], query[1])])

		# Remove duplicates
		places.drop_duplicates(subset=["name", "coord. x", "coord. y"],
													 keep="first", inplace=True)
		
		# Reindexing
		index = [i for i in range(len(places))]
		places.index = index
		places.sort_index(inplace=True)

		# Write to csv
		places.to_csv(CURRENT_DIRECTORY + "/krak.csv", sep="\t")