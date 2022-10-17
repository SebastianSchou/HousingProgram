#!/usr/bin/env python3
import rjpl
from datetime import datetime, timedelta
import general_functions as gf
import concurrent.futures
from concurrent.futures import TimeoutError
import requests
import numpy as np

TIME_FORMAT = "%d.%m.%y %H:%M"
COORDINATE_MULTIPLIER = 1000000
DAYS = ["Hverdag", "Fredag", "Lørdag", "Søndag"]
TIMES = ["Morgen", "Middag", "Aften", "Nat"]

def toMinutes(time):
		# Converts datetime object to minutes
		# arguments:
		#		- time: datetime object
		# returns:
		#		- minutes (int)
		return int(time.total_seconds() / 60)

def getLegStartTime(leg):
		# Get leg start time
		# arguments:
		#		- leg: leg of journey, recieved from rjpl trip function
		# returns:
		#		- leg start time (datetime)
		return datetime.strptime("{} {}".format(leg["Origin"]["date"],
																						leg["Origin"]["time"]),
																						TIME_FORMAT)

def getLegEndTime(leg):
		# Get leg end time
		# arguments:
		#		- leg: leg of journey, recieved from rjpl trip function
		# returns:
		#		- leg end time (datetime)
		return datetime.strptime("{} {}".format(leg["Destination"]["date"],
																						leg["Destination"]["time"]),
																						TIME_FORMAT)

def getJourneyTime(legs, includeWalking = True):
		# Get entire journey time
		# arguments:
		#		- legs: List of legs of journey, recieved from rjpl trip function
		# returns:
		#		- journey time (datetime)
		if isinstance(legs, list):
				if not includeWalking:
						if legs[0]["type"] == "WALK":
								legs = legs[1:]
						if legs[-1]["type"] == "WALK":
								legs = legs[:-1]
				return getLegEndTime(legs[-1]) - getLegStartTime(legs[0])
		else:
				return getLegEndTime(legs) - getLegStartTime(legs)

def getLegTime(leg):
		# Get leg time
		# arguments:
		#		- leg: leg of journey, recieved from rjpl trip function
		# returns:
		#		- Leg time (datetime)
		return getLegEndTime(leg) - getLegStartTime(leg)

def printJourney(legs):
		# Print journey
		# arguments:
		#		- legs: List of legs of journey, recieved from rjpl trip function
		# returns:
		#		- Nothing
		journey = ""
		for i in range(len(legs)):
				journey += legs[i]["type"]
				if i != len(legs) - 1:
						journey += " -> "
		print(journey)

def getLocation(station):
		# Finds the location of the station in the rjpl database
		# arguments:
		#		- station: Name of station (str)
		# returns:
		#		- Station name with coordinates (dict) if found, else None
		try:
				results = rjpl.location(station)
		except:
				return None
		# Make a list of stops and coordinates, if both available
		stopList = []
		if "StopLocation" in results:
				if isinstance(results["StopLocation"], dict):
						stopList += [results["StopLocation"]]
				else:
						stopList += results["StopLocation"]
		if "CoordLocation" in results:
				if isinstance(results["CoordLocation"], dict):
						stopList += [results["CoordLocation"]]
				else:
						stopList += results["CoordLocation"]

		# Find first match. Remove anything after a comma to match
		stationSplit = station.lower().split(",")
		for stop in stopList:
				if station.lower().split(",")[0] in stop["name"].lower():
						stop["x"] = float(stop["x"])/COORDINATE_MULTIPLIER
						stop["y"] = float(stop["y"])/COORDINATE_MULTIPLIER
						return stop
		return None

def toTripClass(stop):
		# Converts location dict to Stop() or Coord() class, to be used with the trip
		# arguments:
		#		- station: Name of station (str)
		# returns:
		#		- Station name with coordinates (dict) if found, else None
		if stop == None:
				return None
		elif "id" in stop:
				return rjpl.Stop(int(stop["id"]))
		else:
				return rjpl.Coord(float(stop["x"]),
													float(stop["y"]),
													stop["name"])

def getDistance(start, end):
		# Get distance between two stations
		# arguments:
		#		- start: Station (dict from getLocation)
		#		- end: Station (dict from getLocation)
		# returns:
		#		- Distance between the two stations (float)
		x = start["x"] - end["x"]
		y = start["y"] - end["y"]
		return (x**2 + y**2) / 2.

def getDistances(df, station):
		# Get distances between coordinates in a dataframe and a station
		# arguments:
		#		- df: dataframe (Pandas dataframe)
		#		- stationName: Station name (string)
		# returns:
		#		- Name of column
		stationName = station["name"].split(",")[0]
		columnName = "distance to %s" % stationName.lower()
		df[columnName] = gf.haversine(df["coord. x"], df["coord. y"],
																	station["x"], station["y"])
		return columnName

def calcDay(weekday, now, day):
		if weekday == day:
				return now + timedelta(days=7)
		else:
				return now + timedelta(days=(day - (weekday)) % 7)

def getDay(day):
		now = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
		weekday = now.weekday()
		if day == DAYS[0]:
				if weekday in [3, 4, 5]:
						return now + timedelta(days=7 - weekday)
				else:
						return now + timedelta(days=1)
		elif day == DAYS[1]:
				return calcDay(weekday, now, 4)
		elif day == DAYS[2]:
				return calcDay(weekday, now, 5)
		else:
				return calcDay(weekday, now, 6)

def getTime(time):
		if time == TIMES[0]:
				return timedelta(hours=8)
		elif time == TIMES[1]:
				return timedelta(hours=13)
		elif time == TIMES[2]:
				return timedelta(hours=18)
		else:
				return timedelta(hours=23, minutes=45)

def getDepartureTime(day, time):
		if day not in DAYS:
				day = DAYS[0]
		if time not in TIMES:
				time = TIMES[0]
		
		return (getDay(day) + getTime(time))
		
def getShortestTrip(start, end, includeWalking = True):
		# Get the shortest trip between two stations
		# arguments:
		#		- start: Station (dict from getLocation)
		#		- end: Station (dict from getLocation)
		# returns:
		#		- Shortest time between the stations (datetime)
		if not isinstance(end, (rjpl.Stop, rjpl.Coord)):
				end = toTripClass(end)

		if not isinstance(start, (rjpl.Stop, rjpl.Coord)):
				start = toTripClass(start)

		results = rjpl.trip(start, end, timeout=60)
		time = []
		for result in results:
				time.append(getJourneyTime(result["Leg"], includeWalking))
		return min(time)

def getShortestTripDf(row, end, columnName, includeWalking = True,
											time = None, attempts = 0):
		# Get the shortest trip between two stations
		# arguments:
		#		- row: Dataframe row (Pandas dataframe)
		#		- end: Station (Coord() or Stop() class)
		#		- includeWalking: Include walking time from first and last leg (bool)
		#		- time: Day and time of day for the trip (datetime)
		#		- attempts: Number of times the function has tried getting the trip
		# returns:
		#		- Shortest time between the stations (minutes)
		if (columnName in row[1] and
				isinstance(row[1][columnName], int) and
				row[1][columnName] != 0):
				return row[1][columnName]
		name = row[1]["address"]
		if not isinstance(name, str):
				print(row)
				return None
		x = row[1]["coord. x"]
		y = row[1]["coord. y"]
		start = rjpl.Coord(x, y, name)
		try:
				results = rjpl.trip(start, end, time=time, timeout=15)
				time = []
				if isinstance(results, dict):
						time.append(getJourneyTime(results["Leg"], includeWalking))
				elif isinstance(results, list):
						for result in results:
								time.append(getJourneyTime(result["Leg"], includeWalking))
				return toMinutes(min(time))
		except rjpl.rjplAPIError as e:
				# Raised when the API returned an error
				if attempts < 3:
						return getShortestTripDf(row, end, columnName, includeWalking,
																		 time, attempts + 1)
				return 0
		except rjpl.rjplConnectionError as e:
				# Raised in the event of a network problem
				if attempts < 3:
						return getShortestTripDf(row, end, columnName, includeWalking,
																		 time, attempts + 1)
				return None
		except rjpl.rjplHTTPError as e:
				# Raised when the HTTP response code is not 200
				if attempts < 3:
						return getShortestTripDf(row, end, columnName, includeWalking,
																		 time, attempts + 1)
				return None
		except Exception as e:
				print("Error in public_transport, function getShortestTripDf.\n" +
							"Exception type {}, arguments:\n{}".format(type(e).__name__,
																														 e.args))
				return None

def getStationsWithinLimit(df,
													 endStation,
													 timeLimit,
													 columnName,
													 time = None,
													 includeWalking = True):
		timeList = []
		maxConcurrent = 15
		tally = 0
		endLocationClass = toTripClass(endStation)
		with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
				try:
						for result in executor.map(
							lambda row: getShortestTripDf(row,
																						endLocationClass,
																						columnName,
																						includeWalking=includeWalking,
																						time=time),
							df.iterrows()):
								if result != None and result <= timeLimit:
										tally = 0
								else:
										tally += 1
								if tally >= maxConcurrent:
										executor.shutdown(wait=False)
										break
								timeList.append(result)
				except TimeoutError:
						print("Process fik en timeout fejl.")
		if columnName in df.columns:
				timeList += df[columnName].iloc[len(timeList):].tolist()
		else:
				timeList += [None for i in range(len(df) - len(timeList))]
		return timeList