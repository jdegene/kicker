# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd 
import collections

season = '2015'
league = '1'

dbName = 'D:/Test/kicker_DB/kicker_main.sqlite'


league1Teams = ['FC Augsburg', 'Hamburger SV', 'Bor. Mönchengladbach', 'Borussia Dortmund', 'Werder Bremen', 
       'TSG Hoffenheim', 'Bayern München', '1. FC Köln', 'Hannover 96', 'Eintracht Frankfurt', 'SV Darmstadt 98',
       'VfL Wolfsburg', 'FC Schalke 04',  'Bayer 04 Leverkusen', 'VfB Stuttgart', 'Hertha BSC',
       'FC Ingolstadt 04',  '1. FSV Mainz 05']
       
league1URLs= ['fc-Augsburg','hamburger-sv', 'borussia-mgladbach', 'borussia-dortmund', 'werder-bremen',
                '1899-hoffenheim', 'bayern-muenchen', 'fc-koeln', 'hannover-96', 'eintracht-frankfurt', 'sv-darmstadt',
                'vfl-wolfsburg', 'fc-schalke', 'leverkusen', 'vfb-stuttgart', 'hertha-bsc', 
                'fc-ingolstadt', 'fsv-mainz']

league2Teams = [ '1. FC Nürnberg', 'Fortuna Düsseldorf', 'Arminia Bielefeld', '1. FC Union Berlin',
 'SV Sandhausen', 'MSV Duisburg', 'SC Paderborn 07', '1860 München', 'SC Freiburg',
 'FC St. Pauli', 'VfL Bochum', 'Eintracht Braunschweig', 'FSV Frankfurt', 'Karlsruher SC',
 'SpVgg Greuther Fürth', '1. FC Heidenheim', 'RasenBallsport Leipzig', '1. FC Kaiserslautern']
 

##########################################################################################
# Small handy fucntions
##########################################################################################
    
# flatten any iterable into 1D
def flatten(myList):
    return [item for sublist in myList for item in sublist] 
 
##########################################################################################
# DB/Pandas data extraction, creates a list of player cost,points
##########################################################################################

# Load Player and PLayerStats table into a dataframe 
conDB = sqlite3.connect(dbName)
c = conDB.cursor()
dfPlayer = pd.read_sql_query("SELECT * from Player", conDB)
dfPlyStats = pd.read_sql_query("SELECT * from PlayerStats", conDB)

# Load Points into dataframe
#dfBL = pd.read_sql_query("SELECT * from BL1_15", conDB)

# calculate the sums of columns 1:35 (i.e. all gamedays) add it to new column 'Sum', sort by 'Sum' descending
#dfBL['Sums'] = dfBL.iloc[:,1:35].sum(axis=1)
#dfBLsorted = dfBL.sort_values("Sums", ascending=False)

# Load Tactics into dataframe THIS TAKES TOO LONG, DATAFRAME WILL BE HUGE, RATHER USE SQLITE FOR THIS
#dfTactics = pd.read_sql_query("SELECT * from Tactics1_15", conDB)



# points per player by grouping and summing, as_index prevents using ID as index (needed for join)
pSums = dfPlyStats.groupby('Player_ID', as_index=False)['Points'].sum()

# join pSums to dfPlyStats
pSmerge = pd.merge(dfPlayer, pSums, on='Player_ID', how='inner')

# filter df to just contain players from first or second league
pL1 = pSmerge[pSmerge['Team'].isin(league1Teams)]
pL2 = pSmerge[pSmerge['Team'].isin(league2Teams)]

# create a dataframe with total points of each Manager (oops, redundant, dfBL['Sums'] above does the same)
dfPoints = pd.read_sql_query("SELECT * from BL{}_{}".format(league,season[2:]), conDB)
col_list= list(dfPoints)[1:] # list of column names, without ID column
dfPoints['Total'] = dfPoints[col_list].sum(axis=1)


# add a column to dfBL with a collections.Counter of tactical lineup, and a column with the number of different lineups
# WAY TOO SLOW, ONLY RUN WHEN REALLY NEEDED. THE VERSION WITHOUT SQLite needs the dfTactics dataframe
#dfPoints["Counter"] = 0
#dfPoints["TacNum"] = 0
#for x in dfPoints["Manager_ID"]:
#    #DBoutput = c.execute('SELECT TacID FROM Tactics1_15 WHERE Manager_ID={}'.format(x)).fetchall()
#    DFoutput = dfTactics[dfTactics["Manager_ID"]==x]["TacID"]
#    #flatOutput = flatten(DBoutput)
#    dfPoints["Counter"].loc[dfPoints["Manager_ID"] == x] = dict(collections.Counter(DFoutput))
#    dfPoints["TacNum"].loc[dfPoints["Manager_ID"] == x] = len(collections.Counter(DFoutput))



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
    
    # returns average points of the teams playing against this one team
    # team must be in league1Teams
    def againstTeam(team):
        goaList, defList, midList, scoList = [[] for x in range(4)]
        
        # return team name as written in URL
        teamURLname = league1URLs[league1Teams.index(team)]
        
        for x in pL1["Player_ID"]:
            ownTeam = pL1["Team"][pL1["Player_ID"]==x].values[0]
            
            if ownTeam == team:
                continue
            
            position = pL1["POS"][pL1["Player_ID"]==x].values[0]
            playerpL1 = dfPlyStats[(dfPlyStats["Player_ID"]==x)]
            #gameIDlist = dfPlyStats[(dfPlyStats["Player_ID"]==x)]["GameID"].values.tolist()
            
            # iterate over each row
            for index, row in playerpL1.iterrows():
                gameURL = row["GameURL"]
                if teamURLname in gameURL:
                    
                    if position == "Torwart":
                        goaList.append(row["Points"])
                    elif position == "Abwehr":
                        defList.append(row["Points"])
                    elif position == "Mittelfeld":
                        midList.append(row["Points"])
                    elif position == "Sturm":
                        scoList.append(row["Points"])                    
                
                
        goaAvg = sum(goaList)/len(goaList)
        defAvg = sum(defList)/len(defList)
        midAvg = sum(midList)/len(midList)
        scoAvg = sum(scoList)/len(scoList)
            
        return [[goaAvg, defAvg, midAvg,scoAvg],[goaList,defList, midList, scoList]]
        
        
        
    
    # HoA can be "H" or "A" for Home or Away
    def homeaway(HoA):
        goaList, defList, midList, scoList = [[] for x in range(4)]
        for x in pL1["Player_ID"]:
            position = pL1["POS"][pL1["Player_ID"]==x].values[0] # get player position
            
            # get dataframe for player and home or away only
            newDF = dfPlyStats[(dfPlyStats["Player_ID"]==x) & (dfPlyStats["HA"]==HoA)]
            addList = newDF.Points.values.tolist() 
            
            if position == "Torwart":
                goaList.append(addList)
            elif position == "Abwehr":
                defList.append(addList)
            elif position == "Mittelfeld":
                midList.append(addList)
            elif position == "Sturm":
                scoList.append(addList)
        
        goaAvg = sum(flatten(goaList))/len(flatten(goaList))
        defAvg = sum(flatten(defList))/len(flatten(defList))
        midAvg = sum(flatten(midList))/len(flatten(midList))
        scoAvg = sum(flatten(scoList))/len(flatten(scoList))
            
        return [[goaAvg, defAvg, midAvg,scoAvg],[flatten(goaList),flatten(defList), flatten(midList), flatten(scoList)]]
                
            
    
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
    
    # returns the average points for each tactical lineup VERY VERY SLOW
    def pointsPerTactic():
        returnList = []
        for x in range(5):
            DBOutput = c.execute('SELECT Manager_ID, GameDay FROM Tactics1_15 WHERE TacID={}'.format(x)).fetchall()
            pointsList = []
            for y in DBOutput:
                points = dfPoints[dfPoints["Manager_ID"]==y[0]]["GD"+str(y[1])].values[0]
                pointsList.append(int(points))
            avgPoints = sum(pointsList)/len(pointsList)
            returnList.append(avgPoints)
            

    
    
    
        

            
    