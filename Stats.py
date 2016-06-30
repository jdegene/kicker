# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd 

season = '2015'
league = '1'

dbName = 'D:/Test/kicker_DB/kicker_main.sqlite'


league1Teams = ['FC Augsburg', 'Hamburger SV', 'Bor. Mönchengladbach', 'Borussia Dortmund', 'Werder Bremen', 
       'TSG Hoffenheim', 'Bayern München', '1. FC Köln', 'Hannover 96', 'Eintracht Frankfurt', 'SV Darmstadt 98',
       'VfL Wolfsburg', 'FC Schalke 04',  'Bayer 04 Leverkusen', 'VfB Stuttgart', 'Hertha BSC',
       'FC Ingolstadt 04',  '1. FSV Mainz 05']

league2Teams = [ '1. FC Nürnberg', 'Fortuna Düsseldorf', 'Arminia Bielefeld', '1. FC Union Berlin',
 'SV Sandhausen', 'MSV Duisburg', 'SC Paderborn 07', '1860 München', 'SC Freiburg',
 'FC St. Pauli', 'VfL Bochum', 'Eintracht Braunschweig', 'FSV Frankfurt', 'Karlsruher SC',
 'SpVgg Greuther Fürth', '1. FC Heidenheim', 'RasenBallsport Leipzig', '1. FC Kaiserslautern']
 
 
 
##########################################################################################
# DB/Pandas data extraction, creates a list of player cost,points
##########################################################################################

# Load Player and PLayerStats table into a dataframe 
conDB = sqlite3.connect(dbName)
c = conDB.cursor()
dfPlayer = pd.read_sql_query("SELECT * from Player", conDB)
dfPlyStats = pd.read_sql_query("SELECT * from PlayerStats", conDB)

# Load Points into dataframe
dfBL = pd.read_sql_query("SELECT * from BL1_15", conDB)

# Load Tactics into dataframe THIS TAKES TOO LONG, DATAFRAME WILL BE HUGE, RATHER USE SQLITE FOR THIS
#dfTactics = pd.read_sql_query("SELECT * from Tactics1_15", conDB)

# calculate the sums of columns 1:35 (i.e. all gamedays) add it to new column 'Sum', sort by 'Sum' descending
dfBL['Sum'] = dfBL.iloc[:,1:35].sum(axis=1).sort("Sums", ascending=False)


# points per player by grouping and summing, as_index prevents using ID as index (needed for join)
pSums = dfPlyStats.groupby('Player_ID', as_index=False)['Points'].sum()

# join pSums to dfPlyStats
pSmerge = pd.merge(dfPlayer, pSums, on='Player_ID', how='inner')

# filter df to just contain players from first or second league
pL1 = pSmerge[pSmerge['Team'].isin(league1Teams)]
pL2 = pSmerge[pSmerge['Team'].isin(league2Teams)]

# create a dataframe with total points of each Manager
dfPoints = pd.read_sql_query("SELECT * from BL{}_{}".format(league,season[2:]), conDB)
col_list= list(dfPoints)[1:] # list of column names, without ID column
dfPoints['Total'] = dfPoints[col_list].sum(axis=1) 


# drop all columns not needed for knapsack and convert df to list
pL1list = pL1.drop(["Player_ID", "FirstName", "LastName", "Team", "POS", "BackNum", "Born", "Height", "Weight", "Nationality"], axis=1).values.tolist()
pL2list = pL2.drop(["Player_ID", "FirstName", "LastName", "Team", "POS", "BackNum", "Born", "Height", "Weight", "Nationality"], axis=1).values.tolist()

# switch value/points pair to fit knpasack() correct order, convert to tuples, convert points to integer
pL1list = [tuple([int(x[1]),x[0]]) for x in pL1list]
pL2list = [tuple([int(x[1]),x[0]]) for x in pL2list]

# Remove all points/value combinations that exist more than once
uniquePlayers1 = list(set(pL1list))
uniquePlayers2 = list(set(pL2list))




def managerSlice(upperBound, lowerBound):
    """
    returns a df slice of Managers depending on their total points
    upperBound/lowerBound are the bounds in percent
    100, 90 would return the top 10% of alle Managers, 50,0 the lower half...
    the values of upperBound and lowerBound are included
    """    
    
    # because best values will be on bottom of the  list, change upperBpund to bottomrow
    bottomrow = int(upperBound * len(dfPoints) / 100)
    toprow = int(lowerBound * len(dfPoints) / 100)

    # sort by total points, most points are on bottom of dataframe
    returndf = dfPoints.sort_values(by="Total")._slice(slice(toprow,bottomrow))
    
    return returndf
    


class Stats:
    
    # returns a list of points for 1% slices of Managers
    def slicePoints():
        pointsList = []    
        for x in range(1,101):
            myDf = managerSlice(x,x-1)
            pointsList.append(myDf["Total"].mean())    
        return pointsList
    
    # check how often a tactical ID is used for slices of Managers (10% slices)
    # returns a list with 10 lists (first are worst 10%, last are best 10%)
    def sliceTactics():
        returnList = []
        for x in range(1,101,10):
            # get the df only containing the players from this slice
            myDf = managerSlice(x+10,x)
            # convert ManagerID column into a list
            IDlist = myDf["Manager_ID"].values.tolist()
            # for each ID, get the tactical ID from the database 
            DBOutput = [c.execute('SELECT TacID FROM Tactics1_15 WHERE Manager_ID={}'.format(x)).fetchall() for x in IDlist]
            # flatten this list of tuples so only 1 long list of tactical IDs exitst
            flatList = [item[0] for sublist in DBOutput for item in sublist]
            sliceList = [flatList.count(x) for x in range(5)]
            returnList.append(sliceList)
        
        return returnList 
    
    # returns the average points for each tactical lineup
    def pointsPerTactic():
        for x in range(5):
            returnList = []
            DBOutput = c.execute('SELECT Manager_ID, GameDay FROM Tactics1_15 WHERE TacID={}'.format(x)).fetchall()
            pointsList = []
            for y in DBOutput:
                points = dfBL[dfBL["Manager_ID"]==y[0]]["GD"+str(y[1])].values[0]
                pointsList.append(int(points))
            avgPoints = sum(pointsList)/len(pointsList)
            returnList.append(avgPoints)
            
        return returnList
            

            
    