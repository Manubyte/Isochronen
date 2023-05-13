###########################################################
#                   Bachelor's Thesis                   ###
# Author:  Manuel Fischer	                            ###
# Supervisor: Dr. Sebastian Feick                       ###
# Friedrich-Alexander-Universität Erlangen-Nürnberg     ###
###########################################################


###################################################################################################
# Methods:
#
# createIsochrone (module):
#                       creates isochrones and saves them in new directory in projPath folder. runs entire analysis
#                       by calling filterStopTimes, reachableStopTimes, prepResultsForOrs, requestOrsIsochrones
#
# filterStopTimes (module):
#                       returns filtered stop times. stop times are read from the GTFS file and filtered
#                       by date and time.
#
# reachableStopTimes (module):
#                        returns all stop times that can be reached within a given period of time and maximum amount
#                        of transfers from a given starting point.
#
# startTimeToTimedelta (module):
#                       converts input value to datetime type.
#
# readOrsTransfers (module):
#                       reads orsTransfers.csv to a Pandas Dataframe. Columns are renamed according to
#                       gtfs standards. all values in column from_id_values are set to "startingPoint".
#
# readGtfsTransfers (module):
#                       reads the gtfs file transfers.txt as DataFrame.
#                       Converts "min_transfer_time" column values to timedelta.
#                       keeps only rows with "min_transfer_time" values.
#
# findReachableStopTimesRecursion (module):
#                       recursively finds all reachable stop times by:
#                           (1) calls findReachedStops() to find all stops reached in the previous recursion step.
#                           (2) calls takeEveryTrip() to find all reachable stop times for this recursion step.
#                           (3) if maximum amount of transfers is reached return empty DataFrame, else go to step (1).
#                           (4) concat results from step (2) and step (3).
#                           (5) return results
#
# findReachedStops (module):
#                       finds stops from a DataFrame of stop times and finds stops reachable by
#                       transfer from those stops. Adds the earliest arrival time for all those stops.
#                       returns DataFrame of stops.
#
# takeEveryTrip (module):
#                       Takes all Trips departing from a given DataFrame of stops.
#                       Returns DataFrame of reachable stop times.
#
# prepResultsForOrs (module):
#                       prepares a DataFrame of reachable stop times for ors api querries. Also takes
#                       different maximum catchment areas for different types of transport into account.
#                       returns DataFrame with georeferenced (epsg 4326) stops and according catchment areas.
#
# requestOrsIsochrones (module):
#                       creates and sends querries for the open routing service application programming interface.
#                       receives and saves Isochrones as *.geojson.
#
###################################################################################################

###################################################################################################
# INPUTS:
#
# date:             String in the format "yyyymmdd". Sets date and weekday of the investigation.
# startTime:        String in the format "hh_mm_ss". Sets the time the investigation starts.
# duration:         Int sets the maximum travel time in seconds.
# maxTransfers:     Int sets the maximum amount of transfers between start and end.
# catchmentStreet:  Integer sets maximum walking distance from stops reached by bus or tram.
# catchmentRail:    Integer sets maximum walking distance from stops reached by train or subway.
# gtfsPath:         Path to the gtfs folder for the investigated region.
# projectPath:      Path to the project for saving Isochrones and accessing the orsTransfers.csv file.
# dfReachedStopTimes: Dataframe used recursive function, wich stop times were reached in the previous step.
# leftTransfers:    Int tells the recursive function how many transfers are left until termination.
# filteredStopTimes:DataFrame containing all stop times, that are left after filtering by date, weekday and time.
# dfTransfers:      DataFrame transfers from starting point to starting stops and inbetween stops
# dfReachedStops:   DataFrame used in recursive function. contains all stop, that were reached in the previous step.
###################################################################################################

# Import required packages
import json
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from pathlib import Path


###################################################################################################
# [run step 1 - 4: "starte Analyse"]

def createIsochrone(date, startTime, duration, maxTransfers, catchmentStreet,
                    catchmentRail, gtfsPath, projectPath):
    

    # set path to save results. is located in project path.
    savePath = projectPath + 'date_' + str(date) + '_time_' + str(startTime) + \
               '_dur_' + str(duration) + '_transfers_' + str(maxTransfers) + \
               '_cmStreet_' + str(catchmentStreet) + '_cmRail_' + str(catchmentRail)

    # print savePath for User
    print(savePath)
    
    # create directory.
    Path(savePath).mkdir(parents=True, exist_ok=True)

    # filter stop times by time and by date.
    stopTimes = filterStopTimes(date, startTime, duration, gtfsPath)

    # compute all reachable stop times.
    dfReachableStopTimes = reachableStopTimes(startTime, duration, maxTransfers, stopTimes,
                                              gtfsPath, projectPath)

    # save reachable stop times (raw data) in savePath directory
    dfReachableStopTimes.to_csv(savePath + '/rohdaten_' + str(dfReachableStopTimes.shape))

    # prepare results for ors api requests, by transforming stop times to stops.
    dfReachableStops = prepResultsForOrs(dfReachableStopTimes, gtfsPath, catchmentStreet, catchmentRail)

    # save reachable stops (prepared data) in savePath directory.
    dfReachableStops.to_csv(savePath + '/aufbereitet_' + str(dfReachableStops.shape))

    # request and save isochrones for every reachable stop
    requestOrsIsochrones(dfReachableStops, savePath)


###################################################################################################

###################################################################################################
# [Analysis step 2: "Filtere Haltezeiten"]


def filterStopTimes(date, startTime, duration, gtfsPath):
    startTime = startTimeToTimedelta(startTime)  # convert datatype of startTime to timedelta.
    duration = timedelta(seconds=duration)  # convert datatype of duration to timedelta.

    # compute end of the investigation period from start time and duration. Result type is timedelta.
    endTime = startTime + duration

    # read stop_times.txt from gtfs file as DataFrame, all columns are Strings.
    # Only reads columns 'trip_id', 'arrival_time', 'departure_time', 'stop_id' and 'stop_sequence'.
    dfStopTimesUnfiltered = pd.read_csv(gtfsPath + 'stop_times.txt', dtype=str, usecols=['trip_id', 'arrival_time',
                                                                                         'departure_time', 'stop_id',
                                                                                         'stop_sequence'])

    # change type of 'arrival_time' column to timedelta.
    dfStopTimesUnfiltered['arrival_time'] = pd.to_timedelta(dfStopTimesUnfiltered['arrival_time'])

    # change type of 'departure_time' column to timedelta.
    dfStopTimesUnfiltered['departure_time'] = pd.to_timedelta(dfStopTimesUnfiltered['departure_time'])

    # keep stop times, departing after start time and arriving before end time.
    dfFilteredStopTimes = dfStopTimesUnfiltered.loc[
        (dfStopTimesUnfiltered['departure_time'] >= startTime) & (dfStopTimesUnfiltered['arrival_time'] <= endTime)]

    # read calendar.txt from gtfs file as DataFrame, all columns are strings.
    dfCalendar = pd.read_csv(gtfsPath + 'calendar.txt', dtype=str)

    # convert 'start_date' column to datetime. Read Format as "YYYYMMDD".
    dfCalendar['start_date'] = pd.to_datetime(dfCalendar['start_date'], format='%Y%m%d')

    # convert 'end_date' column to datetime. Read Format as "YYYYMMDD".
    dfCalendar['end_date'] = pd.to_datetime(dfCalendar['end_date'], format='%Y%m%d')

    # convert user input 'date' to datetime. Read Format as "YYYYMMDD".
    date = pd.to_datetime(date, format='%Y%m%d')

    day = date.day_name().lower()  # get the name of the weekday and make it lower case.

    # keep services (=service_ids) that operate on the selected day
    dfCalendarOnSelectedDay = dfCalendar.loc[
        dfCalendar[day] == "1"]

    # keep services that start operating before the given date and end operating after the given date.
    dfCalendarOnSelectedDay = dfCalendarOnSelectedDay.loc[
        (dfCalendarOnSelectedDay['start_date'] <= date) & (date <= dfCalendarOnSelectedDay['end_date'])]

    # read trips.txt from gtfs file as DataFrame, all columns are strings. Only read columns 'trip_id' and 'service_id'.
    dfTrips = pd.read_csv(gtfsPath + 'trips.txt', dtype=str, usecols=['trip_id', 'service_id'])

    # keep trips (=trip_ids) with service_ids operating on the selected day of the week.
    dfTripsOnSelectedDay = dfTrips.loc[
        dfTrips['service_id'].isin(dfCalendarOnSelectedDay['service_id'])]

    # keep stop times with trip_ids operating on the selected day of the week.
    dfStopTimesOnSelectedDay = dfFilteredStopTimes.loc[
        dfFilteredStopTimes['trip_id'].isin(dfTripsOnSelectedDay['trip_id'])]

    return dfStopTimesOnSelectedDay  # return filtered stop times


###################################################################################################


###################################################################################################
# [Analysis step 3: "Ermittle alle erreichbaren Haltezeiten"]


def reachableStopTimes(startTime, duration, maxTransfers, filteredStopTimes, gtfsPath, projectPath):
    startTime = startTimeToTimedelta(startTime)  # convert datatype of start time to timedelta.
    duration = timedelta(seconds=duration)  # convert datatype of duration to timedelta.

    dfOrsTransfers = readOrsTransfers(projectPath)  # read orsTransfers.csv from projectPath directory as dataframe.
    dfGtfsTransfers = readGtfsTransfers(gtfsPath)  # read transfers.txt from gtfs directory as dataframe.

    # concatenate ors and gtfs transfers. results in one DataFrame containing all Transfers.
    dfTransfers = pd.concat([dfOrsTransfers, dfGtfsTransfers], axis=0)

    # define a starting point (DataFrame) for the recursive method.
    # 'stop_id' must be equal to 'from_stop_id' in orsTransfers.
    # must have 'departure_time' column.
    # must have 'trip_id' column.
    # 'arrival_time' sets actual start of the investigation.
    recursionStartingPoint = pd.DataFrame({
        'stop_id': ['startingPoint'],
        'departure_time': [None],
        'trip_id': [None],
        'arrival_time': [startTime]})

    # recursive method to calculate all reachable stop times. recursionStartingPoint is passed as reachedStopTimes.
    # maxTransfers are passed as transfersLeft.
    dfAllReachableStopTimes = findReachableStopTimesRecursion(
        filteredStopTimes, recursionStartingPoint, dfTransfers, maxTransfers)

    # add column for time left until end of investigation. calculated by start time + duration - arrival time.
    dfAllReachableStopTimes['time_left'] = (startTime + duration) - dfAllReachableStopTimes['arrival_time']

    # change the datatype of the 'time_left' column from timedelta to int.
    dfAllReachableStopTimes['time_left'] = dfAllReachableStopTimes['time_left'].apply([lambda x: int(x.seconds)])

    # reset indices of reachable stop times. Drop old indices.
    dfAllReachableStopTimes.reset_index(drop=True, inplace=True)

    # return all reachable stop times.
    return dfAllReachableStopTimes


def startTimeToTimedelta(startTime):
    t = datetime.strptime(startTime, "%H_%M_%S")  # Parse string to datetime objekt.

    # create timedelta object from datetime object.
    timedeltaStartTime = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

    return timedeltaStartTime  # return start time as timedelta.


def readOrsTransfers(projectPath):
    # read (in QGIS created) orsTransfers.csv as dataframe, all values are string.
    orsTransfers = pd.read_csv(projectPath + 'ors_transfers.csv', dtype=str)

    # change column names according to official GTFS convention.
    orsTransfers.rename({'FROM_ID': 'from_stop_id', 'TO_ID': 'to_stop_id', 'DURATION_H': 'min_transfer_time'},
                        axis='columns', inplace=True)

    # change type of 'min_transfer_time' column to timedelta. Value is interpreted as float in hours.
    orsTransfers['min_transfer_time'] = pd.to_timedelta(orsTransfers['min_transfer_time'].astype(float), unit='h')

    # set all values in 'from_stop_id' to String 'startingPoint'.
    orsTransfers = orsTransfers.assign(from_stop_id="startingPoint")

    return orsTransfers  # return Dataframe.


def readGtfsTransfers(gtfsPath):
    # read gtfs file transfers.txt as dataframe, all values are strings.
    dfTransfers = pd.read_csv(gtfsPath + 'transfers.txt', dtype=str)

    # change type of 'min_transfer_time' column to timedelta. Value is interpreted as float in seconds.
    dfTransfers['min_transfer_time'] = pd.to_timedelta(dfTransfers['min_transfer_time'].astype(float), unit='sec')

    # only keep rows, that have a 'min_transfer_time'.
    dfTransfers = dfTransfers.loc[dfTransfers['min_transfer_time'].notnull()]

    return dfTransfers  # return Dataframe.


def findReachableStopTimesRecursion(filteredStopTimes, dfReachedStopTimes, dfTransfers, leftTransfers):
    if leftTransfers < 1:  # end condition: no more transfers left.
        return pd.DataFrame()  # if end condition is met return an empty DataFrame.
    else:  # base case: still transfers left.
        leftTransfers = leftTransfers - 1  # if end condition is not met decrement leftTransfers!

        # step one: find all stops reached so far.
        dfReachedStops = findReachedStops(dfReachedStopTimes, dfTransfers)

        # step two: take all trips from the stops reached so far and get all associated stop times.
        dfReachableStopTimesThisStep = takeEveryTrip(dfReachedStops, filteredStopTimes,leftTransfers)

        # add column 'transfers_left' with number of transfers left to reachable stop times DataFrame.
        dfReachableStopTimesThisStep['transfers_left'] = leftTransfers

        # call the method, we are currently in --> do a recursion step
        dfReachableStopTimesNextSteps = findReachableStopTimesRecursion(filteredStopTimes,
                                                                        dfReachableStopTimesThisStep.copy(),
                                                                        dfTransfers,
                                                                        leftTransfers)

        # create a list with stop times reached at this recursion level and stop times reached at deeper levels.
        resultList = [dfReachableStopTimesThisStep, dfReachableStopTimesNextSteps]

        dfReachableStopTimes = pd.concat(resultList)  # concatenate results from result list

        return dfReachableStopTimes  # return all reachable stop times


def findReachedStops(dfReachedStopTimes, dfTransfers):
    # There are two ways to reach a stop.
    # 1) Direct: You arrive directly at a stop (=dfReachedStopTimes).
    # 2) Indirect: You arrive at a stop and go to one of the surrounding stops (=transfer).

    # group reached stop times by 'stop_id', keep rows with lowest 'arrival_time' values. Convert result to DataFrame.
    dfDirectReachedStops = dfReachedStopTimes.groupby('stop_id')['arrival_time'].min().to_frame()

    # reset index and make stop_id a column again (stop_id was index).
    dfDirectReachedStops.reset_index(inplace=True)

    # keep transfers departing from ('from_stop_id') a directly reached stop ('stop_id').
    dfIndirektReachedStops = dfTransfers.loc[
        dfTransfers['from_stop_id'].isin(dfDirectReachedStops['stop_id'])]

    # merge indirect reached stops and the earliest arrival time at stops on the 'from_stop_id/stop_id' column.
    # --> indirekt reached now have an 'arrival_time' column, describing the arrival time at 'from_stop_id'
    dfIndirektReachedStops = pd.merge(dfIndirektReachedStops, dfDirectReachedStops, left_on='from_stop_id',
                                      right_on='stop_id')

    # calculate arrival time after transfer for indirectly reached stops (= arrival time at 'to_stop_id'),
    # by adding the min transfer time to the arrival time.
    dfIndirektReachedStops['arrival_time_at_to_stop_id'] = dfIndirektReachedStops['arrival_time'] + \
                                                           dfIndirektReachedStops['min_transfer_time']

    # rename column (= axis 1) 'arrival_time' to 'arrival_time_at_to_stop_id'. rename column 'stop_id' to 'to_stop_id'
    dfDirectReachedStops = dfDirectReachedStops.rename(
        {'arrival_time': 'arrival_time_at_to_stop_id', 'stop_id': 'to_stop_id'}, axis=1)

    # concatenate rows (=axis 0) of direkt and indirekt reached stops.
    dfAllReachedStops = pd.concat([dfDirectReachedStops, dfIndirektReachedStops], axis=0)

    # group all reached stops by 'to_stop_id' column, keep rows with minimum 'arrival_time_at_to_stop_id' value.
    serAllReachedStops = dfAllReachedStops.groupby('to_stop_id')['arrival_time_at_to_stop_id'].min()

    # convert serAllReachedStops to a DataFrame.
    dfAllReachedStops = serAllReachedStops.to_frame()

    # reset index of reached stop times, so 'to_stop_id' becomes column again.
    dfAllReachedStops.reset_index(inplace=True)

    return dfAllReachedStops  # return all reached stops.


def takeEveryTrip(dfReachedStops, filteredStopTimes, leftTransfers):
    # merge filtered stop times and reached stops on 'stop_id/to_stop_id' column.
    # --> only stop times at reached stops are left. every stop time has column with arrival time at stop id.
    dfStopTimesFromReachableStops = pd.merge(
        left=filteredStopTimes, right=dfReachedStops, left_on='stop_id', right_on='to_stop_id')

    # Keep only stop times departing after arrival at the stop.
    dfStopTimesFromReachableStops = dfStopTimesFromReachableStops.loc[
        dfStopTimesFromReachableStops['departure_time'] >= dfStopTimesFromReachableStops['arrival_time_at_to_stop_id']]

    # converte stop_sequence column to Integer
    dfStopTimesFromReachableStops['stop_sequence'] = dfStopTimesFromReachableStops['stop_sequence'].astype(int)

    # group all stop times from reachable stops by 'trip_id' column, keep rows with minimum 'stop_sequence' value.
    serEarliestReachableStopSequencesOfReachableTrips = dfStopTimesFromReachableStops.groupby('trip_id')[
        'stop_sequence'].min()

    # merge stop times and earliest reachable stop sequence of reachable trips on 'trip_id' column.
    # --> only stop times on a reachable trip are left. stop times now have two 'stop_sequence' columns:
    # stop_sequence_x = stop sequence of stop time,
    # stop_sequence_y = the earliest reachable stop sequence.
    dfReachableStopTimes = pd.merge(left=filteredStopTimes, right=serEarliestReachableStopSequencesOfReachableTrips,
                                    on='trip_id')

    # keep stop times with a higher stop sequence, than the earliest reachable stop sequence.
    dfReachableStopTimes = dfReachableStopTimes.loc[
        dfReachableStopTimes['stop_sequence_x'].astype(int) >= dfReachableStopTimes['stop_sequence_y'].astype(int)]

    return dfReachableStopTimes  # return all reachable stop times


###################################################################################################

###################################################################################################
# [Analysis step 4: "Bereite erreichbare Haltezeiten für ORS API Abfragen auf"]


def prepResultsForOrs(dfReachedStopTimes, gtfsPath, catchmentStreet=288, catchmentRail=504):

    # if no stop times were reached
    if dfReachedStopTimes.empty:
        # print, that no stop times were reached
        print('no stops were found!')
        # and exit the script
        exit()

    # read stops.txt from gtfs file as DataFrame, all columns are strings.
    dfStops = pd.read_csv(gtfsPath + 'stops.txt', dtype=str)

    # read trips.txt from gtfs file as DataFrame, all columns are strings.
    dfTrips = pd.read_csv(gtfsPath + 'trips.txt', dtype=str)

    # read routes.txt from gtfs file as DataFrame, all columns are strings.
    # only read columns 'route_id' and 'route_type'
    dfRoutes = pd.read_csv(gtfsPath + 'routes.txt', dtype=str, usecols=['route_id', 'route_type'])

    # dictionary with vehicle type code and associated catchment are. 0: Tram, 1: Subway, 2: Rail, 3: Bus
    # ORS Walking speed is 5 km/h. catchment area of 400(700) meter is equal to walking 288(504) seconds.
    # maxCatchmentAreas = {"0": catchmentStreet, "1": catchmentRail, "2": catchmentRail, "3": catchmentStreet}

    # this dictionary has some route_type values of the gtfs route type extension (can handle vbb dataset).
    # --> see gtfs extension https://developers.google.com/transit/gtfs/reference/extended-route-types.
    maxCatchmentAreas = {"0": catchmentStreet, "1": catchmentRail, "2": catchmentRail, "3": catchmentStreet, "100": catchmentRail,
                        "109": catchmentRail, "400": catchmentRail, "700": catchmentStreet, "900": catchmentStreet, "1000": catchmentStreet}

    # create DataFrame from catchment area dictionary. Column names are 'route_type' and 'max_catchment_area'.
    dfMaxCatchmentAreas = pd.DataFrame(maxCatchmentAreas.items(), columns=['route_type', 'max_catchment_area'])

    # ensure time_left column is int
    dfReachedStopTimes['time_left'] = dfReachedStopTimes['time_left'].astype(int)

    # group dfReachedStopTimes by 'stop_id', keep rows with maximum 'time_left' values.
    dfFastestStopTimesAtStops = dfReachedStopTimes.loc[
        dfReachedStopTimes.groupby('stop_id')['time_left'].idxmax()]

    # merge stops and fastest Stop times at stops by 'stop_id' column.
    # --> stops now also have 'trip_id' and 'time_left' columns
    dfStops = pd.merge(dfStops, dfFastestStopTimesAtStops, on='stop_id')

    # merge trips and routs by 'route_id' column --> trips now also have 'route_type' column.
    dfTripsWithRouteType = pd.merge(left=dfTrips, right=dfRoutes, on='route_id')

    # merge stops and trips with route id by trip_id --> stops now also have 'route_type' column.
    dfStops = pd.merge(dfStops, dfTripsWithRouteType, on='trip_id')

    # merge stops and catchment areas by route_id --> stops now also have 'max_catchment_area' column
    dfStops = pd.merge(dfStops, dfMaxCatchmentAreas, on='route_type')


    # clip (=set a min and max value for) 'time_left' column of stops.
    # min value is 1; max value is max_catchment_area.
    dfStops['time_left'] = dfStops['time_left'].clip(lower=1, upper=dfStops['max_catchment_area'])

    return dfStops  # return all reachable stops.


###################################################################################################

###################################################################################################
# [Analysis step 5: "Erstelle Isochronen"]

def requestOrsIsochrones(dfOrsPrepedResults, savePath):
    # create a list of api keys. with every key 500 requests can be made.
    # Key '5b3ce3597851110001cf624842a188fa1398429c8964718870a35b5f' is on collaboration plan, 2500 requests per day.
    keys = [
        '5b3ce3597851110001cf624842a188fa1398429c8964718870a35b5f',
        '5b3ce3597851110001cf6248a50ab05356c34bfcbcaddb9b6aefa36c',
        '5b3ce3597851110001cf6248278ec1fa56ae4ec0a121115f5b5374df',
        '5b3ce3597851110001cf62489ece2cbe18ff460ea59efed06f0d1f8d', ]

    # create directory for savePath. If it already exists nothing will happen.
    Path(savePath).mkdir(parents=True, exist_ok=True)

    # change column types of 'stop_lon', 'stop_lat' and 'time_left' to string. ORS Request needs strings.
    dfOrsPrepedResults[['stop_lon', 'stop_lat', 'time_left']] = dfOrsPrepedResults[
        ['stop_lon', 'stop_lat', 'time_left']].astype(str)

    # reset index to make sure index matches with rows.
    dfOrsPrepedResults = dfOrsPrepedResults.reset_index()

    # for each row in ors prepared results Dataframe.
    for index, row in dfOrsPrepedResults.iterrows():

        # create a request body for current row containing the longitude, latitude and the isochrone range.
        body = {"locations": [[row['stop_lon'], row['stop_lat']]], "range": [row['time_left']]}

        # create a header for the request. This is the default header. can be generated with an online tool:
        # https://openrouteservice.org/dev/#/api-docs/v2/isochrones/{profile}/post
        header = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': keys[2],
            'Content-Type': 'application/json; charset=utf-8'
        }

        # request the Isochron for current row.
        call = requests.post('https://api.openrouteservice.org/v2/isochrones/foot-walking', json=body, headers=header)

        # save the result in the save path directory as geojson.
        json.dump(call.json(), open(savePath + '/Isochrone_' + str(index) + '.geojson', 'w+'))

        # print information about progress.
        print('Isochrone number: ' + str(index + 1) + ' von ' + str(len(dfOrsPrepedResults.index) + 1))

        # estimate the time until all isochrones are requested.
        estimation = timedelta(seconds=(len(dfOrsPrepedResults.index) - index) * 3)
        print(call.json())
        print('Geschätzte Restdauer: ' + str(estimation))  # print estimation
        time.sleep(3)  # wait 3 seconds until sending the next request


if __name__ == '__main__':
    # In den folgen 5 zeilen kann die Untersuchung weiter spezifiziert werden
    analysisDate = '20220314'  # format 'yyyymmdd'
    analysisStartTime = '17_35_00'  # Trennzeichen kann in der Funktion "startzeit_zu_timedelta()" festgelegt werden.
    analysisDuration = 1800  # in Sekunden
    analysisMaxTransfers = 4  # amount of allowed transfers. Transfer from the starting point to the first stops also counts as transfer.
    analysisCatchementStreet = 300  # catchment area in seconds, to convert in meter: x * (5000/3600)
    analysisCatchmentTrain = 600  # catchment area in seconds, to convert in meter: x * (5000/3600)
    analysisGtfsPath = 'gtfs/vbb/'  # Path to the gtfs files
    analysisProjectPath = 'untersuchungsgebiete/Adlershof/'  # Path to ors_transfers.csv

    createIsochrone(analysisDate, analysisStartTime, analysisDuration, analysisMaxTransfers, analysisCatchementStreet,
                    analysisCatchmentTrain, analysisGtfsPath, analysisProjectPath)


