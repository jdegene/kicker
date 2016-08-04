# -*- coding: utf-8 -*-

import sqlite3


import matplotlib.pyplot as plt  
import matplotlib.ticker as plticker

from scipy import stats
import pandas as pd 

import numpy as np

import datetime, statistics, os

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 


season = '2015'
league = '1'

dbName = 'D:/Test/kicker_DB/kicker_main.sqlite'

ligaDict = {5138700 : "Flávia", 4540209 : "Jan Degener", 4385248 : "Stefan Hohnwald",
            4233249 : "Stefan Erasmi", 4406058 : "Heiko Faust", 4549411 : "Alex Wunz",
            4539630 : "Julie Scholz", 4230283 : "Thomas Duwe", 4201334 : "Steffen Möller", 
            4984316 : "Christine Gehrig-Downie", 4392277 : "Hannah Erasmi", 
            4624644 : "Michael Fink", 151575 : "Thomas Jarmer", 4748965 : "Niklas Rehkopp",
            3449995 : "Johannes Winter", 4979914 : "Helga Grenzebach", 
            3770837 : "Sebastian Goihl", 4985870 : "Bryan Downie"}

league1Teams = ['FC Augsburg', 'Hamburger SV', 'Bor. Mönchengladbach', 'Borussia Dortmund', 'Werder Bremen', 
       'TSG Hoffenheim', 'Bayern München', '1. FC Köln', 'Hannover 96', 'Eintracht Frankfurt', 'SV Darmstadt 98',
       'VfL Wolfsburg', 'FC Schalke 04',  'Bayer 04 Leverkusen', 'VfB Stuttgart', 'Hertha BSC',
       'FC Ingolstadt 04',  '1. FSV Mainz 05']

league2Teams = [ '1. FC Nürnberg', 'Fortuna Düsseldorf', 'Arminia Bielefeld', '1. FC Union Berlin',
 'SV Sandhausen', 'MSV Duisburg', 'SC Paderborn 07', '1860 München', 'SC Freiburg',
 'FC St. Pauli', 'VfL Bochum', 'Eintracht Braunschweig', 'FSV Frankfurt', 'Karlsruher SC',
 'SpVgg Greuther Fürth', '1. FC Heidenheim', 'RasenBallsport Leipzig', '1. FC Kaiserslautern', ]

# List of distinct colors http://stackoverflow.com/questions/2328339/how-to-generate-n-different-colors-for-any-natural-number-n
distColors = ("#000000", "#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059",
        "#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", "#8FB0FF", "#997D87",
        "#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", "#FF2F80",
        "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
        "#DDEFFF", "#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F",
        "#372101", "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09",
        "#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
        "#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",

        "#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81",
        "#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
        "#7900D7", "#A77500", "#6367A9", "#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700",
        "#549E79", "#FFF69F", "#201625", "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329",
        "#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
        "#83AB58", "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
        "#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200", "#5B4E51",
        "#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379", "#012C58")


def teamStats(manID, gameDay, season, league):
    """
    returns a list of the value, height/weight/Backnumber, nationality of a team at specific gameDay
        :manId:     Manager ID (int) 
    """    
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    # Get a tuple of all player ID for specified gameDay
    plIDs = c.execute('SELECT * FROM Tactics{}_{} WHERE Manager_ID={} AND GameDay={}'.format(league,season[2:], manID, gameDay) ).fetchall()[0]
    
    # create a list for each parameter, will store each value of every player
    valList, heightList, weightList, backnumList, nationList = ([] for i in range(5))    
    print(plIDs)
    # iterate over all player IDs and extract info, save to relevant list
    for ID in plIDs[3:]:
        plStats = c.execute('SELECT * FROM Player{}_{} WHERE Player_ID={}'.format(league, season[2:], ID) ).fetchall()[0]
        valList.append(plStats[6])        
        heightList.append(plStats[8])
        weightList.append(plStats[9])
        backnumList.append(plStats[5])
        nationList.append(plStats[10])
        
    return (valList, heightList, weightList, backnumList, nationList)


def inOut(ManagerID):
    """
    returns the PlayerIDs that changed after half-time
    """
   
    #ManagerID = 4540209
    FirstGameDay = 2 
    SecGameDay = 19
    
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    try:
        plIDFirst = c.execute('SELECT * FROM Tactics{}_{} WHERE Manager_ID={} AND GameDay={}'.format(league,season[2:], ManagerID, FirstGameDay) ).fetchall()[0]
    except:
        plIDFirst =  []
    
    try:
        plIDSec = c.execute('SELECT * FROM Tactics{}_{} WHERE Manager_ID={} AND GameDay={}'.format(league,season[2:], ManagerID, SecGameDay) ).fetchall()[0]
    except:
        plIDSec = []
    
    # if managers only joined in the second half, fill out slots with default player 0
    if not plIDFirst:
        getOut = [0,0,0,0]
        getIn = plIDSec[-4:]
        changeList = list(getOut) + list(getIn)
        core = list(plIDSec[:-4])
    
    
    else:
        getOut = set(plIDFirst[3:]) - set(plIDSec[3:])
        getIn = set(plIDSec[3:]) - set(plIDFirst[3:])
        
        # Account for those who changed everyone
        if len(getOut) == 4:
            changeList = list(getOut) + list(getIn)
        
        # Account for those who didnt change anything
        elif len(getOut) == 0:
            getOutList = [0,0,0,0]
            getInList = list(plIDSec[-4:])
            changeList = getOutList + getInList
        
        # Account for Managers that changes less than 4 players
        else:
            for x in range(len(getOut)):
                getOutList = list(getOut)
                getOutList.append(0)
                getInList = list(getIn)
                getInList.append(0)
            
            changeList = getOutList + getInList
                
        core = [x for x in plIDFirst if x not in getOut]

    
    return core[3:], changeList





def drawTeamGrid(ligaDict, league, season,outFol):
    
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()

    picFol = "D:/WorkExchange/kicker/pics/"
    
    # Load Calibri as the font of choice for text
    font = ImageFont.truetype("C:\Windows\Fonts\Calibri\calibri.ttf", 35)
    font2 = ImageFont.truetype("C:\Windows\Fonts\Calibri\calibri.ttf", 50)
    font3 = ImageFont.truetype("C:\Windows\Fonts\Calibri\calibri.ttf", 80)
    font31 = ImageFont.truetype("C:\Windows\Fonts\Calibri\calibri.ttf", 70)
    font4 = ImageFont.truetype("C:\Windows\Fonts\Calibri\calibri.ttf", 25)
    font5 = ImageFont.truetype("C:\Windows\Fonts\Calibri\calibrib.ttf", 90)
    font51 = ImageFont.truetype("C:\Windows\Fonts\Calibri\calibrib.ttf", 70)
    
    # scaleFactor for output image, generalle increases space between Managers in pic
    scaleF = 600
    
    pointsDict = {}
    for keys in ligaDict:
        getPoints = c.execute('SELECT * FROM BL{}_{} WHERE Manager_ID={}'.format(league,season[2:], keys) ).fetchall()[0]
        totPoints = sum([x for x in getPoints[1:] if type(x)==int]) # allows running even with None values present
        pointsDict[keys] = totPoints 
        
    # create a list, with sorted ManagerIDs, first element is ID with most points, last element ID with least points
    sortKeys = list(reversed(sorted(pointsDict, key=pointsDict.__getitem__)))

    # create an empty image, that will contain all sub-images the will be created        
    #large_im = Image.new('RGBA', (4900, 510*len(sortKeys)), (255, 0, 0, 0))
    large_im = Image.new('RGBA', (4900, scaleF*len(sortKeys)), (255, 0, 0, 0))
    
    for place, ManagerID in enumerate(sortKeys):
    #ManagerID = 151575
    #place = 6

        ManagerName = ligaDict[ManagerID]
        getPoints = c.execute('SELECT * FROM BL{}_{} WHERE Manager_ID={}'.format(league,season[2:], ManagerID) ).fetchall()[0]
        totPoints = sum([x for x in getPoints[1:] if type(x)==int]) # Total Points
        
        
        # Get Player IDs, and those that went out and in
        allPlayers = inOut(ManagerID)
        allPlayers1L = allPlayers[0] + allPlayers[1] # make 1 list out of 2
        
        valList, heightList, weightList, backnumList, nationList, bdayList = ([] for i in range(6)) 
             
       
        # create a new empty image with transparent background
        new_im = Image.new('RGBA', (4900, 500), (255, 0, 0, 0))
        draw = ImageDraw.Draw(new_im)
        
        txtColor = "black"    
        counter = 0
        
        # Set all the right player images
        for j in range(0,500,250):
            for i in range(600,4800,237):    
                
                if j == 0:
                    curID = allPlayers[0][counter]
                    
                    plStats = c.execute('SELECT * FROM Player WHERE Player_ID={}'.format(curID) ).fetchall()[0]
                    valList.append(plStats[6]) 
                    bdayList.append(plStats[7])
                    heightList.append(plStats[8])
                    weightList.append(plStats[9])
                    backnumList.append(plStats[5])
                    nationList.append(plStats[10])
                    
                    # Get full filepath to pic
                    imString = [im for im in os.listdir(picFol) if im[:im.find("_")]==str(curID) ]
                    
                    # If player is not (anymore) in DB, no info exist, use default values instead            
                    if not imString:
                        im = Image.open(picFol+"Default.jpg")
                        plName1 = c.execute('SELECT FirstName FROM Player WHERE Player_ID={}'.format(curID) ).fetchall()[0][0]
                        plName2 = c.execute('SELECT LastName FROM Player WHERE Player_ID={}'.format(curID) ).fetchall()[0][0]
                    else:
                        im = Image.open(picFol + imString[0])                
                        # extract Player Name from Picture names
                        plName1 = imString[0][imString[0].rfind("_")+1 : imString[0].rfind(".") ][:14]
                        plName2 =  imString[0][ imString[0].find("_")+1 :  imString[0].rfind("_")][:14]
                    
                    #calculate player age in days
                    agesList = []
                    for bday in bdayList:
                        now = datetime.datetime.now()
                        bday = datetime.datetime.strptime(bday, '%d.%m.%Y')
                        timedelta = now-bday
                        agesList.append(timedelta.days)
                    avgAge = ( sum(agesList)/len(agesList) ) / 365.2425 #returns year age
                    
                    new_im.paste(im, (i,j))
                    draw.text((i, j+180),plName1,txtColor,font=font)
                    draw.text((i, j+210),plName2,txtColor,font=font)
                    draw.text((i+181, j),plStats[4][0],txtColor,font=font)                
                    draw.text((i+181, j+120),str(plStats[6]),txtColor,font=font)
                    draw.text((i+181, j+150),"Mio.",txtColor,font=font4)
                    
                    counter = counter + 1
                    #print(counter)
                    
                elif j == 250 and i > 2900:
        
                    curID = allPlayers[1][counter-18]
                    
                    
                    plStats = c.execute('SELECT * FROM Player WHERE Player_ID={}'.format(curID) ).fetchall()[0]
                    valList.append(plStats[6])        
                    heightList.append(plStats[8])
                    weightList.append(plStats[9])
                    backnumList.append(plStats[5])
                    nationList.append(plStats[10])
                    
                    imString = [im for im in os.listdir(picFol) if im[:im.find("_")]==str(curID) ]
                    if not imString:
                        im = Image.open(picFol+"Default.jpg")
                        plName1 = c.execute('SELECT FirstName FROM Player WHERE Player_ID={}'.format(curID) ).fetchall()[0][0]
                        plName2 = c.execute('SELECT LastName FROM Player WHERE Player_ID={}'.format(curID) ).fetchall()[0][0]
                    else:
                        im = Image.open(picFol + imString[0])                                
                        # extract Player Name from Picture names
                        plName1 = imString[0][imString[0].rfind("_")+1 : imString[0].rfind(".") ][:14]
                        plName2 =  imString[0][ imString[0].find("_")+1 :  imString[0].rfind("_")][:14]
                    
                    new_im.paste(im, (i,j))
                    draw.text((i, j+180),plName1,txtColor,font=font) 
                    draw.text((i, j+210),plName2,txtColor,font=font)
                    try:
                        draw.text((i+180, j),plStats[4][0],txtColor,font=font)
                    except:
                        draw.text((i+180, j),"x",txtColor,font=font)
                    if str(plStats[6]) == "None":
                        draw.text((i+181, j+120),"0",txtColor,font=font)
                    else:
                        draw.text((i+181, j+120),str(plStats[6]),txtColor,font=font)
                    draw.text((i+181, j+150),"Mio.",txtColor,font=font4)
                    
                    counter = counter + 1
        
        # remove empty elements from lists, sum() will throw error otherwise
        valList = [x for x in valList if x != " " and type(x)==float]
        heightList = [x for x in heightList if x != " " and type(x)==int]
        weightList = [x for x in weightList if x != " " and type(x)==int]
        backnumList = [x for x in backnumList if x != " " and type(x)==int]    
        
        
        # Write Manager Name
        if len(ManagerName) < 13:
            draw.text((25, 165), ManagerName,"gray",font=font3)
        else:
            splitMan = ManagerName.split()
            for x in range(len(splitMan)):
                draw.text((25, 90+x*75), splitMan[x],"gray",font=font3)
        
        draw.text((25, 300), "Platz: " + str(place+1) ,"gray",font=font3) 
        draw.text((25, 400), "Punkte: " + str(totPoints) ,"gray",font=font3) 
    
        draw.text((1850, 400), "Ø / Median €:","black",font=font3) 
        draw.text((2350, 395), str(sum(valList)/len(valList))[:4] + " / " + str(statistics.median(valList))[:4] ,"black",font=font5)
        draw.text((2760, 426), "Mio","black",font=font2)
       
        draw.text((1520, 300), "Ø Größe:","black",font=font31) 
        draw.text((1840, 290), str(sum(heightList)/len(heightList))[:5],"black",font=font5)
        draw.text((2060, 322), "cm","black",font=font2)
        
        draw.text((680, 300), "Ø Gewicht:","black",font=font31)     
        draw.text((1040, 290), str(sum(weightList)/len(weightList))[:5],"black",font=font5)    
        draw.text((1260, 320), "kg","black",font=font2)
        
        draw.text((2300, 300), "Ø Alter:","black",font=font31)   
        draw.text((2600, 290), str(avgAge)[:4] ,"black",font=font5)    
        draw.text((2780, 320), "Jahre","black",font=font2)
    
        draw.text((680, 400), "Anzahl Nationalitäten:","black",font=font31)     
        draw.text((1340, 395), str(len(set(nationList))),"black",font=font5)  
        draw.text((1440, 410), str( (1 - nationList.count("Deutschland")/25)*100 )[:2] + " %"    ,"black",font=font)  
        draw.text((1440, 440), "Nicht-Deutsche","black",font=font)
    
        
        # Draw rectangels around the in, out players and stats, several for linewidth effect
        for x in range(2):
            #draw.rectangle([ 600-x, 246-x, 2915+x, 497+x], outline = "black")
            draw.rectangle([ 2925-x, 246-x, 3909+x, 497+x], outline = "red")
            draw.rectangle([ 3915-x, 246-x, 4895+x, 497+x], outline = "green")
        # add text
        #draw.text((605, 250), "S","black",font=font2)
        #draw.text((605, 300), "T","black",font=font2)
        #draw.text((605, 350), "A","black",font=font2)
        #draw.text((605, 400), "T","black",font=font2)
        #draw.text((605, 450), "S","black",font=font2)
            
        draw.text((2930, 250), "O","red",font=font2)
        draw.text((2930, 300), "U","red",font=font2)
        draw.text((2935, 350), "T","red",font=font2)
        
        draw.text((4870, 250), "I","green",font=font2)
        draw.text((4862, 300), "N","green",font=font2)
        
        
        drawLarge = ImageDraw.Draw(large_im)
        drawLarge.line([ 10, (place*scaleF)-50, 4900, (place*scaleF)-50], "black", width=5)
        large_im.paste(new_im, (0,place*scaleF), new_im )
    
    large_im.save(outFol)




def returnSet(ManagerID, league, season):
    # create a set of unique players for each Manager, returns as list
    try:
        plIDFirst = c.execute('SELECT * FROM Tactics{}_{} WHERE Manager_ID={} AND GameDay={}'.format(league,season[2:], ManagerID, 2) ).fetchall()[0][3:]
    except:
        plIDFirst =  []
    
    try:
        plIDSec = c.execute('SELECT * FROM Tactics{}_{} WHERE Manager_ID={} AND GameDay={}'.format(league,season[2:], ManagerID, 19) ).fetchall()[0][3:]
    except:
        plIDSec = []
        
    combSet = list(set(list(plIDFirst) + list(plIDSec) ) )
    
    return combSet



def playerAge(bday):
    # returns the current age in DAYS, takes Birthday string (%d.%m.%Y) as input
    now = datetime.datetime.now()
    bday = datetime.datetime.strptime(bday, '%d.%m.%Y')
    timedelta = now-bday
    return timedelta.days
        
    #avgAge = ( sum(agesList)/len(agesList) ) / 365.2425 #returns year age
    


def playerStats(ManagerID, league, season):
    """
    returns several stats of a Managers players
    returns a stat tuple: (value, height, weight, backnum, age(days))
     each stat tuple consists of a list (sum, mean, median, stdev) 
    """

    players = returnSet(ManagerID, league, season)
    
    valList, heightList, weightList, backnumList, nationList, bdayList = ([] for i in range(6)) 
    
    for plID in players:
        try:
            plStats = c.execute('SELECT * FROM Player WHERE Player_ID={}'.format(plID) ).fetchall()[0]
            valList.append(plStats[6]) 
            bdayList.append(plStats[7])
            heightList.append(plStats[8])
            weightList.append(plStats[9])
            backnumList.append(plStats[5])
            nationList.append(plStats[10])
        except:
            continue
    
    valList = [x for x in valList if x != " " and type(x)==float]
    heightList = [x for x in heightList if x != " " and type(x)==int]
    weightList = [x for x in weightList if x != " " and type(x)==int]
    backnumList = [x for x in backnumList if x != " " and type(x)==int]
    
    ageList = [playerAge(x) for x in bdayList]
    
    # lists that will store the stats for each variable
    valList2, heightList2, weightList2, backnumList2, ageList2 = ([] for i in range(5)) 
    
    for curList, emptyList in zip([valList, heightList, weightList, backnumList, ageList],[valList2, heightList2, weightList2, backnumList2, ageList2]):
        try:
            emptyList.append(sum(curList))
            emptyList.append( statistics.mean(curList) )
            emptyList.append( statistics.median(curList) )
            emptyList.append( statistics.pstdev(curList) ) # standard deviation
        except:
            continue
    
    return(valList2, heightList2, weightList2, backnumList2, ageList2)




def fill_ManTeamStats(league, season):
    """
    calculates the stats for the ManTeamStats table and populates it
    """
    dbName = 'D:/WorkExchange/kicker/kicker_main_2.sqlite'
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    allIDlist = c.execute('SELECT Manager_ID FROM BL{}_{}'.format(league,season[2:]) ).fetchall()
    existList = c.execute('SELECT ManagerID FROM  ManTeamStats{}_{}'.format(league,season[2:]) ).fetchall()
    
    manIDlist = [x for x in allIDlist if x not in existList]
    
    for ManID in manIDlist:
        statsTuple = playerStats(ManID[0], league, season)
        
        #flatten tuple and add mangerID in front
        writeList = [league, season[2:], ManID[0]] + [item for sublist in statsTuple for item in sublist]
        
        #print(writeList)
             
        if len(writeList) == 23:
            #write tuple to DB
            c.execute('INSERT OR IGNORE INTO ManTeamStats{}_{} VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format( *writeList ) )
        
        if ManID[0] % 1000 == 0:
            conDB.commit()
        

    conDB.commit()
    #conDB.close()


def player_efficiency(position, league, outFile):
    """
    returns an Excel table of players by position, sorted by their points per million efficiency
        postion can be: 'Torwart', 'Abwehr', 'Mittelfeld', 'Sturm'
        league can be: '1' or '2'
        outFile is the path and name of the output file
    """
    
    if league == '1':
        leagueList = league1Teams
    else:
        leagueList = league2Teams
    
    conDB = sqlite3.connect(dbName)
    
    # Load the Player and PlayerStats table into a dataframe 
    dfPlayer = pd.read_sql_query("SELECT * from Player", conDB)
    dfPlyStats = pd.read_sql_query("SELECT * from PlayerStats", conDB)
    
    # points per player by grouping and summing, as_index prevents using ID as index (needed for join)
    pSums = dfPlyStats.groupby('Player_ID', as_index=False)['Points'].sum()
    
    # join pSums to dfPlyStats
    pSmerge = pd.merge(dfPlayer, pSums, on='Player_ID', how='inner')
    # create new column with Points per Million
    pSmerge["PPM"] = pSmerge["Points"] / pSmerge["Mio"]
    
    # Filter by position and players in respective league
    pSpos = pSmerge[( (pSmerge.POS == position) & (pSmerge['Team'].isin(leagueList)) )].sort("PPM", ascending=False)
    
    # drop unnecessary columns, combine First and Last name into one new column
    dfOut = pSpos.drop(["Player_ID", "POS", "BackNum", "Born", "Height", "Weight", "Nationality"], axis=1)
    dfOut["Name"] = dfOut["FirstName"].str.cat(dfOut["LastName"], sep = ' ')
    dfOut.drop(["FirstName", "LastName"], axis=1)
    
    # round the PPM column to 2 decimal places
    dfOut.round({"PPM":2})
    
    # rearrange columns
    dfOut = dfOut[ ["Name", "Team", "Mio", "Points", "PPM"] ]
    
    dfOut.to_excel(outFile)
    

    



def avgValue(ligaDict, league, season,outFol):
    
    outFol = 'D:/WorkExchange/kicker/Diags/'
    
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
  
    #dfPlayers = pd.read_sql_query("SELECT * from Player", conDB)
    # Load the Team Stats into a dataframe 
    dfStats = pd.read_sql_query("SELECT * from ManTeamStats{}_{}".format(league, season[2:]), conDB)
    
    # Load points in dataframe, add column for sum to sort by
    dfPoints = pd.read_sql_query("SELECT * from BL{}_{}".format(league,season[2:]), conDB)
    col_list= list(dfPoints)[1:] # list if column names, without ID column
    dfPoints['Total'] = dfPoints[col_list].sum(axis=1) # calc sum of all specified columns
    
    # New Dataframes with the Top and Bottom 10% of Managers
    topTenPerc = dfPoints.sort("Total", ascending=False).head(int(len(dfPoints)/10))
    botTenPerc = dfPoints.sort("Total", ascending=False).tail(int(len(dfPoints)/10))
    
    
    # create a new dataframe that holds the stats of the 10% best Managers
    topTenStats = dfStats[ dfStats['ManagerID'].isin(topTenPerc['Manager_ID']) ]
    
    # create a new dataframe that holds the stats of the 10% worst Managers
    botTenStats = dfStats[ dfStats['ManagerID'].isin(botTenPerc['Manager_ID']) ]
    
    
    # List of ManagerIDs from current ligaDict
    manList = [manID for manID in ligaDict]
    
    
    
    ############### Avg Heights ##############
    
    # DATA heightAVG
    topTenStats_meanHA = topTenStats['heightMean'].mean()
    botTenStats_meanHA = botTenStats['heightMean'].mean()
    all_meanHA = dfStats['heightMean'].mean()
    
    # Define y-axis min and max
    maxY = 187
    minY = 181    
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=2.0) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 1): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    heightQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    heightList = [x[6] for x in heightQ]
    curManIDs = [x[0] for x in heightQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanHA, botTenStats_meanHA], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanHA, all_meanHA], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanHA, topTenStats_meanHA], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), heightList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Average Team Height [cm]')
        
    fig.savefig(outFol + 'Heights_avg.png', dpi=300, transparent=True)
    
    
    
    ############### StdEv Heights ##############
    
    # DATA height StdDev 
    topTenStats_meanHS = topTenStats['heightStDev'].mean()
    botTenStats_meanHS = botTenStats['heightStDev'].mean()
    all_meanHS = dfStats['heightStDev'].mean()
    
    # Define y-axis min and max
    maxY = 7.5
    minY = 5.5 
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=0.5) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY +0.5, 0.5): 
        plt.plot(np.arange(len(manList)+1), [y] * len(np.arange(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    heightQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    heightList = [x[8] for x in heightQ]
    curManIDs = [x[0] for x in heightQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanHS, botTenStats_meanHS], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanHS, all_meanHS], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanHS, topTenStats_meanHS], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), heightList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Standard Deviation Team Height [cm]')
        
    fig.savefig(outFol + 'Heights_stDev.png', dpi=300, transparent=True)
    


    ############### Heights Histogram All Players ##############
      
    maxY = 80
    minY = 0
   
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
  
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    # Label intervals for x axis
    plt.xticks(np.arange(170,200,5))
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="on", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
  
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=25) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
        
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    plt.axis([165, 200, minY, maxY])
    
    #relative secure way to get values for unknown number of ManagerID inputs
    heightQ = c.execute("SELECT Height FROM Player").fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    heightList = [x[0] for x in heightQ if type(x[0]) == int]

    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    #plt.bar(range(len(curManNames)), heightList, width=0.75, color = barcol, zorder=2 )
    
    plt.xlabel("Height [cm]")
    plt.ylabel("Number of Players")
    
    plt.title('Player Height Distribution - All Players from 1. and 2. Bundesliga')
    
    n, bins, patches = plt.hist(heightList, 34, color = "white", zorder=2)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 25): 
        plt.plot(np.arange(200), [y] * len(np.arange(200)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
        
    fig.savefig(outFol + 'Heights_Histo.png', dpi=300, transparent=True)




    ############### Avg Weights ##############
    
    # DATA heightAVG
    topTenStats_meanWA = topTenStats['weightMean'].mean()
    botTenStats_meanWA = botTenStats['weightMean'].mean()
    all_meanWA = dfStats['weightMean'].mean()
    
    # Define y-axis min and max
    maxY = 82
    minY = 75    
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=2.0) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 1): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    weightQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    weightList = [x[10] for x in weightQ]
    curManIDs = [x[0] for x in weightQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanWA, botTenStats_meanWA], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanWA, all_meanWA], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanWA, topTenStats_meanWA], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), weightList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Average Team Weight [kg]')
        
    fig.savefig(outFol + 'Weightss_avg.png', dpi=300, transparent=True)




    ############### StDev Weights ##############
    
    # DATA heightAVG
    topTenStats_meanWS = topTenStats['weightStDev'].mean()
    botTenStats_meanWS = botTenStats['weightStDev'].mean()
    all_meanWS = dfStats['weightStDev'].mean()
    
    # Define y-axis min and max
    maxY = 9.5
    minY = 5.0    
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=1.0) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, 10, 1): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    weightQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    weightList = [x[12] for x in weightQ]
    curManIDs = [x[0] for x in weightQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanWS, botTenStats_meanWS], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanWS, all_meanWS], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanWS, topTenStats_meanWS], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), weightList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Standard Deviation Team Weight [kg]')
        
    fig.savefig(outFol + 'Weights_StDev.png', dpi=300, transparent=True)



     ############### Weights Histogram All Players ##############
      
    maxY = 120
    minY = 0
   
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
  
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    # Label intervals for x axis
    plt.xticks(np.arange(60,120,5))
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
  
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=25) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
        
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    plt.axis([55, 100, minY, maxY])
    
    #relative secure way to get values for unknown number of ManagerID inputs
    heightQ = c.execute("SELECT Weight FROM Player").fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    heightList = [x[0] for x in heightQ if type(x[0]) == int]

    
    plt.xlabel("Weight [kg]")
    plt.ylabel("Number of Players")
    
    plt.title('Player Weight Distribution - All Players from 1. and 2. Bundesliga')
    
    n, bins, patches = plt.hist(heightList, 34, color = "white", zorder=2)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 25): 
        plt.plot(np.arange(200), [y] * len(np.arange(200)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
        
    fig.savefig(outFol + 'Weights_Histo.png', dpi=300, transparent=True)





     ############### Avg BackNumber ##############
    
    # DATA heightAVG
    topTenStats_meanbA = topTenStats['backnumMean'].mean()
    botTenStats_meanbA = botTenStats['backnumMean'].mean()
    all_meanbA = dfStats['backnumMean'].mean()
    
    # Define y-axis min and max
    maxY = 26
    minY = 15    
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=2.0) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 1): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    backNumQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    backNumList = [x[14] for x in backNumQ]
    curManIDs = [x[0] for x in backNumQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanbA, botTenStats_meanbA], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanbA, all_meanbA], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanbA, topTenStats_meanbA], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), backNumList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Average Team Shirt Numbers')
        
    fig.savefig(outFol + 'BackNUm_avg.png', dpi=300, transparent=True)


    ############### StDev BackNumber ##############
    
    # DATA heightAVG
    topTenStats_meanbS = topTenStats['backnumStDev'].mean()
    botTenStats_meanbS = botTenStats['backnumStDev'].mean()
    all_meanbS = dfStats['backnumStDev'].mean()
    
    # Define y-axis min and max
    maxY = 14
    minY = 9    
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=1.0) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 1): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    backNumQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    backNumList = [x[16] for x in backNumQ]
    curManIDs = [x[0] for x in backNumQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanbS, botTenStats_meanbS], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanbS, all_meanbS], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanbS, topTenStats_meanbS], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), backNumList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Standard Deviation Team Shirt Numbers')
        
    fig.savefig(outFol + 'BackNUm_StDev.png', dpi=300, transparent=True)
    
    
    ############### Backnum Histogram All Players ##############
      
    maxY = 40
    minY = 0
   
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
  
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    # Label intervals for x axis
    plt.xticks(np.arange(5,50,5))
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
  
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=25) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
        
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    plt.axis([0,47, minY, maxY])
    
    #relative secure way to get values for unknown number of ManagerID inputs
    backNumQ = c.execute("SELECT BacKNum FROM Player").fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    backnumList = [x[0] for x in backNumQ if type(x[0]) == int]

    
    plt.xlabel("Shirt Number")
    plt.ylabel("Number of Players")
    
    plt.title('Player Shirt Number Distribution - All Players from 1. and 2. Bundesliga')
    
    n, bins, patches = plt.hist(backnumList, np.arange(1,48), color = "white", align="left", zorder=2)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 25): 
        plt.plot(np.arange(200), [y] * len(np.arange(200)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
        
    fig.savefig(outFol + 'BackNum_Histo.png', dpi=300, transparent=True)





    ############### Avg Ages ##############
    
    # DATA heightAVG
    topTenStats_meanAA = topTenStats['ageMean'].mean()/365.2445
    botTenStats_meanAA = botTenStats['ageMean'].mean()/365.2445
    all_meanAA = dfStats['ageMean'].mean()/365.2445
    
    # Define y-axis min and max
    maxY = 27
    minY =21  
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=2.0) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 1): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    ageQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    ageList = [x[18]/365.2445 for x in ageQ]
    curManIDs = [x[0] for x in ageQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanAA, botTenStats_meanAA], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanAA, all_meanAA], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanAA, topTenStats_meanAA], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), ageList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Average Age')
    fig.savefig(outFol + 'Age_avg.png', dpi=300, transparent=True)
    
    
    
    
    ############### StDev Ages ##############
    
    # DATA heightAVG
    topTenStats_meanAS = topTenStats['ageStDev'].mean()/365.2445
    botTenStats_meanAS = botTenStats['ageStDev'].mean()/365.2445
    all_meanAS = dfStats['ageStDev'].mean()/365.2445
    
    # Define y-axis min and max
    maxY = 6
    minY = 2  
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=2.0) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 1): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    ageQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    ageList = [x[20]/365.2445 for x in ageQ]
    curManIDs = [x[0] for x in ageQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanAS, botTenStats_meanAS], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanAS, all_meanAS], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanAS, topTenStats_meanAS], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), ageList, width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Standard Deviation Age')
        
    fig.savefig(outFol + 'Age_StDev.png', dpi=300, transparent=True)
    
    
    
    ############### Backnum Histogram All Players ##############
      
    maxY = 125
    minY = 0
   
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
  
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    # Label intervals for x axis
    plt.xticks(np.arange(5,50,5))
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
  
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=25) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
        
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    plt.axis([17,40, minY, maxY])
    
    #relative secure way to get values for unknown number of ManagerID inputs
    ageQ = c.execute("SELECT Born FROM Player").fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    ageList = [playerAge(x[0])/365.2445 for x in ageQ if type(x[0]) == str]

    
    plt.xlabel("Age")
    plt.ylabel("Number of Players")
    
    plt.title('Player Age Distribution - All Players from 1. and 2. Bundesliga')
    
    n, bins, patches = plt.hist(ageList, np.arange(15,40), color = "white", align="left", zorder=2)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 25): 
        plt.plot(np.arange(200), [y] * len(np.arange(200)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
        
    fig.savefig(outFol + 'Age_Histo.png', dpi=300, transparent=True)
    
    
    
    
    ############### Avg Value ##############
    
    # DATA heightAVG
    topTenStats_meanVA = topTenStats['ValueMean'].mean()
    botTenStats_meanVA = botTenStats['ValueMean'].mean()
    all_meanVA = dfStats['ValueMean'].mean()
    
    # Define y-axis min and max
    maxY = 2.5
    minY = 1.75
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=0.25) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 0.25): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    valueQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    valueList = [x[2] for x in valueQ]
    curManIDs = [x[0] for x in valueQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanVA, botTenStats_meanVA], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanVA, all_meanVA], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanVA, topTenStats_meanVA], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), valueList , width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Average Player Value [Mio. €]')
        
    fig.savefig(outFol + 'Value_avg.png', dpi=300, transparent=True)
    
    
    
    
    ############### StDev Value ##############
    
    # DATA heightAVG
    topTenStats_meanVS = topTenStats['ValueStDev'].mean()
    botTenStats_meanVS = botTenStats['ValueStDev'].mean()
    all_meanVS = dfStats['ValueStDev'].mean()
    
    # Define y-axis min and max
    maxY = 2.5
    minY = 0.5
    
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
    #fig, (ax1, ax2) = plt.subplots(2, 1)
    
    ## AXIS RELATED ##
    ax.set_ylim([minY,maxY]) # set the limits on the y axis
    
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
    # 
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=0.5) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 0.5): 
        plt.plot(range(len(manList)+1), [y] * len(range(len(manList)+1)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    #relative secure way to get values for unknown number of ManagerID inputs
    valueQ = c.execute("SELECT * FROM ManTeamStats" + str(league) + "_" + str(season[2:]) + "\
                WHERE ManagerID IN (" + ",".join("?"*len(manList)) + ")", manList).fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    valueList = [x[4] for x in valueQ]
    curManIDs = [x[0] for x in valueQ]
    
    # get ManagerNames from corresponding value ManagerIDs, shorten Names if too long
    curManNames = []
    for x in curManIDs:
        curName = ligaDict[x]
        if len(curName)<12:
            curManNames.append(ligaDict[x])
        else:
           curManNames.append(ligaDict[x].split()[0] + " " + ligaDict[x].split()[1][0] + ".")
            
    
    # set the locations and labels of the xticks
    plt.xticks(range(len(curManNames)), curManNames, ha='left' , rotation=70)   
    
    # define bar color, rgb values must be scaled between 0-1
    barcol = (31/255, 119/255, 180/255)
    
    # draw lines for all Manager mean, worst 10% mean, and top 10% mean
    plt.plot([0.1, len(curManNames)], [botTenStats_meanVS, botTenStats_meanVS], "-", lw=0.5, color="red", zorder=3, label="Worst 10%")
    plt.plot([0.1, len(curManNames)], [all_meanVS, all_meanVS], "-", lw=0.5, color="black", zorder=3, label="Avg All Managers" )
    plt.plot([0.1, len(curManNames)], [topTenStats_meanVS, topTenStats_meanVS], "-", lw=0.5, color="green", zorder=3, label="Best 10%")
    
    plt.bar(range(len(curManNames)), valueList , width=0.75, color = barcol, zorder=2 )
    
    plt.gcf().subplots_adjust(bottom=0.3) # extent to display full x-axis ticks
    
    plt.title('Standard Deviation Player Value [Mio. €]')
        
    fig.savefig(outFol + 'Value_StDev.png', dpi=300, transparent=True)
    
    
     ############### Backnum Histogram All Players ##############
      
    maxY = 425
    minY = 0
   
    fig, ax = plt.subplots(1, figsize=(10, 3.4))        
  
    # defining only bottom an left will remove top and right ticks
    ax.get_xaxis().tick_bottom ()
    ax.get_yaxis().tick_left()  
    
    # Label intervals for x axis
    plt.xticks(np.arange(0,10))
    
    #ax.tick_params(axis='x', colors="None")
    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.    
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
                labelbottom="on", left="off", right="off", labelleft="on")  
    
  
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    loc = plticker.MultipleLocator(base=100) # this locator puts ticks at regular intervals
    ax.yaxis.set_major_locator(loc)
        
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)    
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)   
    
    plt.axis([0,8.5, minY, maxY])
    
    #relative secure way to get values for unknown number of ManagerID inputs
    backNumQ = c.execute("SELECT Mio FROM Player").fetchall()
    
    # fill list with heights from Managers, create new correctly ordered Name list for x-ticks
    backnumList = [x[0] for x in backNumQ if type(x[0]) == float]

    
    plt.xlabel("Player Value [Mio. €]")
    plt.ylabel("Number of Players")
    
    plt.title('Player Value Distribution - All Players from 1. and 2. Bundesliga')
    
    n, bins, patches = plt.hist(backnumList, np.arange(0,9,0.5), color = "white", align="mid", zorder=2)
    
    # dotted horizontal indicator lines
    for y in np.arange(minY, maxY, 100): 
        plt.plot(np.arange(200), [y] * len(np.arange(200)) , "--", lw=0.5, color="black", alpha=0.3, zorder=1)
        
    fig.savefig(outFol + 'Value_Histo.png', dpi=300, transparent=True)







#drawTeamGrid(ligaDict, league, season, "D:\Test\kicker3\image2.png")
#fill_ManTeamStats('1', '2015')















