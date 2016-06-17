# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd 

import collections
import functools

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
# Find players by their value/points combination
# xTup is a tuple (points, value), df the dataframe to look in for player data
# reutrns a list of player ID's fitting the search
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
    
    
def knapsack2(capacity, value, weight, maxitems):
    """
    Originally from: https://gist.github.com/Phovox/127e5923660d60fb7924
    
    solve the 3d-knapsack problem specified in its parameters: capacity is the
    overall capacity of the knapsack and the ith position of the arrays value
    and weight specify the value and weight of the ith item. This is called the
    3d-knapsack not because it refers to a cuboid but because it also considers
    a maximum number of items to insert which is given in the last parameter
    """


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
                    
    # return the table computed so far
    return table
    


    
    
    
    