# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd 

import collections
import functools

import datetime

import sys
sys.setrecursionlimit(10000)

season = '2015'
league = '1'

dbName = 'D:/Test/kicker_DB/kicker_main.sqlite'


##########################################################################################
# DB/Pandas data extraction, creates a list of player cost,points
##########################################################################################

league1Teams = ['FC Augsburg', 'Hamburger SV', 'Bor. Mönchengladbach', 'Borussia Dortmund', 'Werder Bremen', 
       'TSG Hoffenheim', 'Bayern München', '1. FC Köln', 'Hannover 96', 'Eintracht Frankfurt', 'SV Darmstadt 98',
       'VfL Wolfsburg', 'FC Schalke 04',  'Bayer 04 Leverkusen', 'VfB Stuttgart', 'Hertha BSC',
       'FC Ingolstadt 04',  '1. FSV Mainz 05']

league2Teams = [ '1. FC Nürnberg', 'Fortuna Düsseldorf', 'Arminia Bielefeld', '1. FC Union Berlin',
 'SV Sandhausen', 'MSV Duisburg', 'SC Paderborn 07', '1860 München', 'SC Freiburg',
 'FC St. Pauli', 'VfL Bochum', 'Eintracht Braunschweig', 'FSV Frankfurt', 'Karlsruher SC',
 'SpVgg Greuther Fürth', '1. FC Heidenheim', 'RasenBallsport Leipzig', '1. FC Kaiserslautern', ]


# Load Player and PLayerStats table into a dataframe 
conDB = sqlite3.connect(dbName)
dfPlayer = pd.read_sql_query("SELECT * from Player", conDB)
dfPlyStats = pd.read_sql_query("SELECT * from PlayerStats", conDB)

# Load Points into dataframe
dfBL = pd.read_sql_query("SELECT * from BL1_15", conDB)

# calculate the sums of columns 1:35 (i.e. all gamedays) add it to new column 'Sum', sort by 'Sum' descending
dfBL['Sum'] = dfBL.iloc[:,1:35].sum(axis=1).sort("Sums", ascending=False)


# points per player by grouping and summing, as_index prevents using ID as index (needed for join)
pSums = dfPlyStats.groupby('Player_ID', as_index=False)['Points'].sum()

# join pSums to dfPlyStats
pSmerge = pd.merge(dfPlayer, pSums, on='Player_ID', how='inner')

# filter df to just contain players from first or second league
pL1 = pSmerge[pSmerge['Team'].isin(league1Teams)]
pL2 = pSmerge[pSmerge['Team'].isin(league2Teams)]

# drop all columns not needed for knapsack and convert df to list
pL1list = pL1.drop(["Player_ID", "FirstName", "LastName", "Team", "POS", "BackNum", "Born", "Height", "Weight", "Nationality"], axis=1).values.tolist()
pL2list = pL2.drop(["Player_ID", "FirstName", "LastName", "Team", "POS", "BackNum", "Born", "Height", "Weight", "Nationality"], axis=1).values.tolist()

# switch value/points pair to fit knpasack() correct order, convert to tuples, convert points to integer
pL1list = [tuple([int(x[1]),x[0]]) for x in pL1list]
pL2list = [tuple([int(x[1]),x[0]]) for x in pL2list]

# Remove all points/value combinations that exist more than once
uniquePlayers1 = list(set(pL1list))
uniquePlayers2 = list(set(pL2list))



##########################################################################################

# Convert a list of tuples with the second element a float into int by multiplying 2nd element by 10
def forwConv(tupList):
    returnList = [tuple([x[0], int(x[1]*10) ]) for x in tupList]
    return returnList

# Convert a list of tuples with the second element *10 higher than original back to original value
def backConv(tupList):
    returnList = [tuple([x[0], round( float(x[1]/10), 1)]) for x in tupList]
    return returnList

# converts only 1 tuple
def backConv1(tup):
    returnTup = tuple([tup[0], round( float(tup[1]/10), 1) ])
    return returnTup

##########################################################################################



# convert floating point weights/worth into integer by multiplying them with 100
pL1listInt = forwConv(pL1list)
pL2listInt = forwConv(pL2list)
uniquePlayers1Int = forwConv(uniquePlayers1)
uniquePlayers2Int = forwConv(uniquePlayers2)



##########################################################################################
# ID is a player ID, it returns a (value,weight) tuple for that player
##########################################################################################

def buildTups(ID):
    
    mio = pSmerge[pSmerge["Player_ID"] == ID]["Mio"].values
    points = pSums[pSums["Player_ID"] == ID]["Points"].values
    
    return tuple([points.item(), mio.item()])




##########################################################################################
# Find players by their value/points combination
# xTup is a tuple (points, value), df the dataframe to look in for player data (pSmerge)
# returns a list of player ID's fitting the search
##########################################################################################

def plyrFind(xTup, df):
    
    # filter by Points and Value
    filtered = df[df["Points"] == xTup[0]][df["Mio"] == xTup[1]]
    
    #remove all colums except the Player_ID and convert it to list
    outIDList = filtered["Player_ID"].values.tolist()
    
    #remove all colums except the First and Lastname and convert it to list
    nameList = filtered[["FirstName", "LastName"]].values.tolist()
    outNameList = [x[0] + " " + x[1] for x in nameList]
    
    return outIDList, outNameList




##########################################################################################
# Knapsack Algrithm for determining best possible team
##########################################################################################

class memoized(object):
   '''Decorator. Caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned
   (not reevaluated).
   '''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      if not isinstance(args, collections.Hashable):
         # uncacheable. a list, for instance.
         # better to not cache than blow up.
         return self.func(*args)
      if args in self.cache:
         return self.cache[args]
      else:
         value = self.func(*args)
         self.cache[args] = value
         return value
   def __repr__(self):
      '''Return the function's docstring.'''
      return self.func.__doc__
   def __get__(self, obj, objtype):
      '''Support instance methods.'''
      return functools.partial(self.__call__, obj)


def knapsack(items, maxweight):
    """
    http://codereview.stackexchange.com/questions/20569/dynamic-programming-solution-to-knapsack-problem
    
    Solve the knapsack problem by finding the most valuable
    subsequence of `items` subject that weighs no more than
    `maxweight`.

    `items` is a sequence of pairs `(value, weight)`, where `value` is
    a number and `weight` is a non-negative integer.

    `maxweight` is a non-negative integer.

    Return a pair whose first element is the sum of values in the most
    valuable subsequence, and whose second element is the subsequence.

    >>> items = [(4, 12), (2, 1), (6, 4), (1, 1), (2, 2)]
    >>> knapsack(items, 15)
    (11, [(2, 1), (6, 4), (1, 1), (2, 2)])
    """

    # Return the value of the most valuable subsequence of the first i
    # elements in items whose weights sum to no more than j.
    @memoized
    def bestvalue(i, j):
        if i == 0: return 0
        value, weight = items[i - 1]
        if weight > j:
            return bestvalue(i - 1, j)
        else:
            return max(bestvalue(i - 1, j),
                       bestvalue(i - 1, j - weight) + value)
            

    j = maxweight
    result = []
    for i in range(len(items), 0, -1):
        if bestvalue(i, j) != bestvalue(i - 1, j):
            result.append(items[i - 1])
            j -= items[i - 1][1]
    result.reverse()
    return bestvalue(len(items), maxweight), result
    
    
def knapsack2(capacity, plList, maxitems):
    """
    Originally from: https://gist.github.com/Phovox/127e5923660d60fb7924
    
    plList is a list of (value, weight) tuples representing each player
    
    solve the 3d-knapsack problem specified in its parameters: capacity is the
    overall capacity of the knapsack and the ith position of the arrays value
    and weight specify the value and weight of the ith item. This is called the
    3d-knapsack not because it refers to a cuboid but because it also considers
    a maximum number of items to insert which is given in the last parameter
    """
    
    startTime = datetime.datetime.now()
    
    # the original function was changed to accept 1 list of player (value weight) tuples
    # to conform with the original script, it is split up into 2 lists again
    value = []
    weight = []
    for item in plList:
        value.append(item[0])
        weight.append(item[1])
    

    # initialization - the number of items is taken from the length of any array
    # which shall have the same length
    nbitems = len (value)

    # we use dynamic programming to solve this problem. Thus, we'll need a table
    # that contains (N, M) cells where 0<=N<=capacity and 0<=M<=nbitems
    table=dict ()
    
    # initialize the contents of the dictionary for all capacities and number of
    # items to another dictionary which returns 0 by default
    for icapacity in range (0, 1+capacity):
        table [icapacity]=dict ()
        for items in range (0, 1+nbitems):
            table [icapacity][items] = collections.defaultdict (int)

    # now we are ready to start, ... for the first j items
    for j in range (0, nbitems):

        # for all capacities ranging from 1 to the maximum overall capacity
        for i in range (1, 1+capacity):

            # and for all cardinalities of items from 1 until the maximum
            # allowed
            for k in range (1, 1+maxitems):

                # if this item can not be inserted
                if (weight [j] > i):
                    table [i][1+j][k] = table [i][j][k]   # just do not add it
                    
                # otherwise, consider inserting it
                else:
                    
                    # if this is item is known to fit the knapsack (because its
                    # weight does not exceed the current capacity and adding it
                    # creates a set with a cardinality less or equal than the
                    # cardinality currently considered), then compute the
                    # optimal value as usual but considering sets of the same
                    # cardinality (k)
                    if (j<k):
                        table [i][1+j][k] = max (table[i][j][k],
                                                 table[i-weight[j]][j][k]+value[j])

                    else:
                        prev = []

                        # retrieve the optimal solution for all values of
                        # (i-weight[j], kappa [0 .. j-1], k-1)
                        for kappa in range (0, 1+j):
                            prev.append (table[i-weight[j]][kappa][k-1])

                        # and consider inserting this item taking into account
                        # the optimal solution from the preceding cardinality
                        # considering all sets of items
                        table [i][1+j][k] = max (table[i][j][k],
                                                 max (prev) + value[j])
    
    timeSpent = datetime.datetime.now() - startTime
    print("Process took ", timeSpent.seconds,"s to finish a list of ", len(plList), " items and item limit of ", maxitems)               
    # return the table computed so far
    return table
    


def backtrace(table, plList):
    """
    uses the return table from knapsack2(), and traces backwards to determine the involved players
    plList is the same list that is fed to knapsack2()
    
    returns maximum possible points/value, the weight of the optimal combination, of how many items
    the solution exists and a list of all used (value, weight) items
    """
    
    yLen = len(table)           # length of y-axis, = budget or weight levels
    xLen = len(table[0])        # length of x-axis, = amount of total players to choose from
    zLen = len(table[0][0])     # length of z-axis, = max number of items
    
    maxAbsVal = table[yLen-1][xLen-1][zLen-1] # maximum possible value
    
    if maxAbsVal == 0:
        return([0,0,[]])
    
    optList = []    # list that will store the 
    
    # check if the maximum number of players is exactly hit, or if the optimal solutio consists
    # of a smaller number of players.
    # if for max y and max x axis the value for max-allowed player is the same as for max-1
    # the full number of players/items is not necessary
    # This loop determines for how many players the optimal soultion was found
    # returns 2 if the optimal solution consists of 2 players
    for i in range(zLen-1,0,-1):
        if table[yLen-1][xLen-1][i] != table[yLen-1][xLen-1][i-1]:
            optNum = i
            break
    
    # now check where the value for this optimal number of players came from
    # option a) from the same table but from the player before (the standard way with unlimited number of items allowed)
    # or b) the current player/item was included because its the best solution for 
    for curItem in range(optNum,0,-1):
         
        #find the player in the current table/z-level that first introduced the value
        # returns 5 if the player is the 5th player in the original list
        for j in range(xLen-1,0,-1):
            xLen -= 1
            if table[yLen-1][j][curItem] != table[yLen-1][j-1][curItem]:
                #addItem = j  
                break

        optList.append(plList[j-1]) #add player to list of optimal players
        
        yLen = yLen - plList[j-1][1] # new max value is old p minus the weight of added player
      
    
    totWeight = sum([x[1] for x in optList])
    
    return(maxAbsVal, totWeight, len(optList) ,optList)
    


def backtrace2(table, plList, weight, maxItems):
    """
    similar to backtrace(), but it won't start at the maximum points, but at a specified 
    location. This is useful when you're not interested in the best value, but if you have
    to consider other tables as well (see posTable() and tracePos())
    """
    
    yLen = weight+1          # length of y-axis, = maximum weight to consider
    xLen = len(table[0])        # length of x-axis, = amount of total players to choose from
    zLen = maxItems+1     # length of z-axis, = max number of items to consider
    
    maxAbsVal = table[yLen-1][xLen-1][zLen-1] # maximum possible value
    
    if maxAbsVal == 0:
        return([0,0,[]])
    
    optList = []    # list that will store the 
    
    # check if the maximum number of players is exactly hit, or if the optimal solution consists
    # of a smaller number of players.
    # if for max y and max x axis the value for max-allowed player is the same as for max-1
    # the full number of players/items is not necessary
    # This loop determines for how many players the optimal soultion was found
    # returns 2 if the optimal solution consists of 2 players
    for i in range(zLen-1,0,-1):
        if table[yLen-1][xLen-1][i] != table[yLen-1][xLen-1][i-1]:
            optNum = i
            break
    
    # now check where the value for this optimal number of players came from
    # option a) from the same table but from the player before (the standard way with unlimited number of items allowed)
    # or b) the current player/item was included because its the best solution for 
    for curItem in range(optNum,0,-1):
         
        #find the player in the current table/z-level that first introduced the value
        # returns 5 if the player is the 5th player in the original list
        for j in range(xLen-1,0,-1):
            xLen -= 1
            if table[yLen-1][j][curItem] != table[yLen-1][j-1][curItem]:
                #addItem = j  
                break

        optList.append(plList[j-1]) #add player to list of optimal players
        
        yLen = yLen - plList[j-1][1] # new max value is old p minus the weight of added player
      
    
    totWeight = sum([x[1] for x in optList])
    
    return(maxAbsVal, totWeight, len(optList) ,optList)

##########################################################################################
# Returns a knapsack2() table only for players of a certain position
# position can be one of the following: 'Torwart', 'Abwehr', 'Mittelfeld', 'Sturm'
# league can be 1 or 2 (integer)
# capacity, maxItems are the same as for knapsack()
##########################################################################################    

def posTable(position, league, capacity, maxItems):
    
    # return a list of player ID's on that position
    if league == 1:
        posList = pL1[pL1.POS == position]["Player_ID"].values.tolist()
    else:
        posList = pL2[pL2.POS == position]["Player_ID"].values.tolist()
    
    # create a list of value,weight tuples
    valList = [buildTups(x) for x in posList]
    
    # get rid of floats in valList
    feedList = forwConv(valList)
    
    t = knapsack2(capacity, feedList, maxItems)
    
    return(t, feedList)
    


##########################################################################################
# examines the best possible combination from the 4 tables from posTable() and returns it
# This works for exactly 11 players and regards all tactical combinations
##########################################################################################    
    
def tracePos11(torTable, abwTable, mitTable, stuTable):
    
    maxPoints = 0
    

    tactics = [(3,4,3), (3,5,2), (4,5,1), (4,4,2), (4,3,3)]
    
    # determine minimum and maximum goalie cost, so not the full budget span is iterated over
    for torLen in range(len(torTable)-1,-1,-1):
        if torTable[torLen][len(torTable[1])-1][1] != torTable[torLen-1][len(torTable[1])-1][1]:
            torMax = torLen
            break
    for torLen in range(len(torTable)-1):
        if torTable[torLen][len(torTable[1])-1][1] != 0:
            torMin = torLen
            break
        
    
    for tactic in tactics:
    
        # iterate over all budget levels possible for goalie
        for wg in range(torMin,torMax+1):
            
            # maximum points possible for current budget, torPoints will store the maximum points
            # for goalies
            torPoints = torTable[wg][len(torTable[1])-1][1]
            
            # iterate over the remaining budget for the defenders
            for wd in range(len(torTable)-wg):
                defPoints = abwTable[wd][len(abwTable[1])-1][tactic[0]]
            
                # iterate over the remaining budget for the midfielders
                for wm in range(len(torTable)-wd-wg):
                    midPoints = mitTable[wm][len(mitTable[1])-1][tactic[1]]
                        
                    # don't iterate through all possible, only the one remaining is enough
                    restBudget = len(torTable)-wm-wd-wg
                    scoPoints = stuTable[restBudget-1][len(stuTable[1])-1][tactic[2]]
                    
                    sumPoints = torPoints + defPoints  + midPoints + scoPoints 
                        
                    if sumPoints > maxPoints:
                        maxPoints = sumPoints
                        maxList = tuple([wg,wd,wm,restBudget-1])
                        theTactic = tactic
    
    return [maxPoints, maxList, theTactic]
        
    
##########################################################################################
# examines the best possible combination from the 4 tables from posTable() and returns it
# This works for exactly 22 players, this doesn't account for any tactical lineup
##########################################################################################   
def tracePos22(torTable, abwTable, mitTable, stuTable):   
    
    maxPoints = 0
    
    # determine minimum and maximum goalie cost, so not the full budget span is iterated over
    for torLen in range(len(torTable)-1,-1,-1):
        if torTable[torLen][len(torTable[1])-1][3] != torTable[torLen-1][len(torTable[1])-1][3]:
            torMax = torLen
            break
    for torLen in range(len(torTable)-1):
        if torTable[torLen][len(torTable[1])-1][3] != 0:
            torMin = torLen
            break
    

    # iterate over all budget levels possible for goalie
    for wg in range(torMin,torMax+1):
        torPoints = torTable[wg][len(torTable[1])-1][3]
        
        # iterate over the remaining budget for the defenders
        for wd in range(len(torTable)-wg):
            defPoints = abwTable[wd][len(abwTable[1])-1][6]
            
            # iterate over the remaining budget for the midfielders
            for wm in range(len(torTable)-wd-wg):
                midPoints = mitTable[wm][len(mitTable[1])-1][8]
                    
                # don't iterate through all possible, only the one remaining is enough
                restBudget = len(torTable)-wm-wd-wg
                scoPoints = stuTable[restBudget-1][len(stuTable[1])-1][5]
                
                sumPoints = torPoints + defPoints  + midPoints + scoPoints 
                    
                if sumPoints > maxPoints:
                    maxPoints = sumPoints
                    maxList = tuple([wg,wd,wm,restBudget-1])
                    theTactic = (3,6,8,5)
                    
    return [maxPoints, maxList, theTactic]        
    
 
   
##########################################################################################
# Returns the maximum points that can be achieved by the player lists fed into
#  input lists should contain player ID's as integer [2546871,2158484,124478...]
########################################################################################## 
def optimal22(goaList, defList, midList, scoList):
        
    # Function will return the position of the largest value in a list
    def index_max(values):
        return max(range(len(values)),key=values.__getitem__)
        
    # checks for a list of player ID's, if more than 3 players are from the same team
    # returns 0 if more than 3 players from same team
    def checkMax3(IDs):
        teamList = []
        for ID in IDs:
            curTeam = dfPlayer["Team"][dfPlayer["Player_ID"] == ID].item()
            if teamList.count(curTeam) > 2:
                return 0
            else:
                teamList.append(dfPlayer["Team"][dfPlayer["Player_ID"] == ID].item())
        return 1
    
    # takes the list of 11 player ID's, finds those that are part of a group with more than
    # 3 players of one team, determines the worst of these players and returns their ID's
    # i.e. it ignores the 3 best players from this team
    def checkMax3Player(IDlist, pointsList):
        badList = []
        teamList = []
        for ID in IDlist:            
            curTeam = dfPlayer["Team"][dfPlayer["Player_ID"] == ID].item()
            teamList.append(curTeam)
        teamSet = set(teamList)
        
        for uqTeam in teamSet:
            chooseList = []
            for player in range(11):
                if teamList[player] == uqTeam:
                    chooseList.append( [pointsList[player], IDlist[player]])
            
            while len(chooseList) > 3:
                badList.append(min(chooseList)[1])
                chooseList.remove(min(chooseList))
        return(badList)

    
    # calculates the best 
    def bestCombo(gameDay, playerIDlist, playerPointslist):
              
        tactics = [(3,4,3), (3,5,2), (4,5,1), (4,4,2), (4,3,3)]
        
        goaList, defList, midList, scoList = [x for x in playerIDlist]
        goaPlist, defPlist, midPlist, scoPlist = [x for x in playerPointslist]
                            
        # list will be returned, contains a list of gamedays with each conataining 
        #  maximum points, tactical lineup, points per player and player ID's
        returnList = []       
        dayPlayerList = []  # stores best player ID's per gameDay
        dayPointsList = []  # stores the best points per player for each DG
        dayPoints = 0       # stores max possible points per gameDay
        
        for tactic in tactics:
            dayTacList = [] # fill list for each tactic and only use best tactic
            dayTacPointList = []
            
            # position of best point value of this gd for goalies
            goaMaxPos = index_max([x[gameDay-1] for x in goaPlist])
            dayTacPointList.append(goaPlist[goaMaxPos][gameDay-1])
            dayTacList.append(goaList[goaMaxPos])
            
            # for defenders, create a list of all values and subtract each best after iteration
            defDayList = [x[gameDay-1] for x in defPlist]
            curdefIDlist = [x for x in defList]
            for i in range(tactic[0]):
                defMaxPos = index_max(defDayList)
                dayTacPointList.append(defDayList[defMaxPos])
                dayTacList.append(curdefIDlist[defMaxPos])
                defDayList.remove(defDayList[defMaxPos])
                curdefIDlist.remove(curdefIDlist[defMaxPos])
                            
            # for midfielders, create a list of all values and subtract each best after iteration
            midDayList = [x[gameDay-1] for x in midPlist] 
            curmidIDlist = [x for x in midList]
            for i in range(tactic[1]):
                midMaxPos = index_max(midDayList)
                dayTacPointList.append(midDayList[midMaxPos])
                dayTacList.append(curmidIDlist[midMaxPos])
                midDayList.remove(midDayList[midMaxPos])
                curmidIDlist.remove(curmidIDlist[midMaxPos])
            
            # for scorers, create a list of all values and subtract each best after iteration
            scoDayList = [x[gameDay-1] for x in scoPlist]  
            curscoIDlist = [x for x in scoList]
            for i in range(tactic[2]):
                scoMaxPos = index_max(scoDayList)
                dayTacPointList.append(scoDayList[scoMaxPos])
                dayTacList.append(curscoIDlist[scoMaxPos])
                scoDayList.remove(scoDayList[scoMaxPos])
                curscoIDlist.remove(curscoIDlist[scoMaxPos])
            
            
            #check that no more than 3 players of one team are in the list, else skip
            if checkMax3(dayTacList) == 0:
                                
                badList = checkMax3Player(dayTacList, dayTacPointList)
                
                newPlayerIDlist = [x for x in playerIDlist]  
                newPlayerPointslist = [x for x in playerPointslist]
                 
                for badValue in badList:
                    for listIndex in range(len(newPlayerIDlist)):
                        if badValue in newPlayerIDlist[listIndex]:
                            badIndex = newPlayerIDlist[listIndex].index(badValue)
                            del newPlayerIDlist[listIndex][badIndex]
                            del newPlayerPointslist[listIndex][badIndex]
                             
                 
                returnList = bestCombo(gameDay, newPlayerIDlist, newPlayerPointslist)
                dayPoints, returnTactic, dayPointsList, dayPlayerList = [x for x in returnList]
                 
            else:            
                if sum(dayTacPointList) > dayPoints:
                    dayPlayerList = [x for x in dayTacList]
                    dayPointsList = [x for x in dayTacPointList]
                    dayPoints = sum(dayTacPointList)
                    returnTactic = tactic
    
                    returnList = [dayPoints, returnTactic, dayPointsList, dayPlayerList] 
        
        return(returnList)
    
 
    
    # These lists will store a list per ID with points per GD
    goaPlist, defPlist, midPlist, scoPlist = ([] for i in range(4))
    
    # get for every player ID a list of of points for each GameDay
    for curList, writeList in zip([goaList, defList, midList, scoList],[goaPlist, defPlist, midPlist, scoPlist]):
        for curID in curList:
            
            # returns a list where each item consists of [GameDay, Points]
            gdPoints = dfPlyStats[dfPlyStats["Player_ID"]==curID][['GameDay','Points']].values.tolist()
            plyList = []
            
            for i in range(1, 35):
                if i in [x[0] for x in gdPoints]: # check if gameday was played
                    for j in gdPoints:            # then find gd and add it to list
                        if j[0] == i:
                            plyList.append(j[1])
                else:                              # if not played insert 0
                    plyList.append(0)
                          
            # this would be a much more efficient solution, but it fails with an IndexError in Python 3.4
            # if run in code, but succeeds if run standlone in console
            #j = 1
            #for i in range(1,35):
            #    if gdPoints[i-j][0] == i:
            #        plyList.append(gdPoints[i-j][1])
            #    else:
            #        plyList.append(0)
            #        j += 1
                
            writeList.append(plyList)
            
    
    finalList = []
    #find max posible points of supplied lists for each gameday
    for gD in range(1,35):        
        finalList.append(bestCombo(gD, [goaList, defList, midList, scoList], [goaPlist, defPlist, midPlist, scoPlist]))

    return finalList 


#goaList=[43627, 51437, 46371]
#defList=[77168, 66525, 54252, 48721, 48335, 30898]
#midList=[81437,39228, 79036,57894,51516,48905,42063,31656]
#scoList= [79543, 65936, 63878,40133,33715]






