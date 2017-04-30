# -*- coding: utf-8 -*-

import os, sys, re

from bs4 import BeautifulSoup
import sqlite3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import datetime

import concurrent.futures as cf


# define used season (starting year), used for naming within database (no past season support)
season = '2016'
league = '1'

# Last played GameDay
maxGD = 30

# Database filepath
dbName = 'D:/Test/kicker/kicker_main.sqlite'



#############################
### ###  DB creation  ### ###
############################# 

# Test if db already exists, run inital table creation only if not
if os.path.isfile(dbName):
    dbExists = 1
else:
    dbExists = 0

# connect to SQLite3 DB
conDB = sqlite3.connect(dbName)
# conncect cursor to DB
c = conDB.cursor()

# The following steps are only necessary once, though running them again does no harm
if dbExists == 0:

    # create table to store Manager ID (as primary key) and Manager Name as Text
    c.execute('CREATE TABLE IF NOT EXISTS Manager(Manager_ID INTEGER PRIMARY KEY, Manager_Name TEXT)')
    
    # create table KeepTrack that keeps track of processed data using single digits
    # (0 = not processed, 1 = finished, 2 = started but not finished)
    # columns are League/Seasons and Manager League/season for each GD Manager team of choice
    # rows are Gamedays
    try:
        c.execute('CREATE TABLE KeepTrack (GameDay TEXT, BL1_{0} INTEGER, BL2_{0} INTEGER)'.format(season[2:]))
        for rowName in ['GD' + str(n) for n in range(1,35)]:
            c.execute('INSERT OR IGNORE INTO KeepTrack (GameDay, BL1_{0}, BL2_{0}, Man1_{0}, Man2_{0}) \
                        VALUES ("{1}","0","0","0","0")'.format(season[2:],rowName))
    except:
        pass
    
    # create a table for the current season and league
    for i in range(1,3):
        pointTblName = 'BL' + str(i) + "_" + season[2:]
        c.execute('CREATE TABLE IF NOT EXISTS ' + pointTblName + ' (Manager_ID INTEGER PRIMARY KEY)')
    
    # store the  points of each Manager for each day in a column, GD = GameDay
    # try/except used for already exisiting columns, as these would throw an error
    try:
        for i in range(1,3):
            pointTblName = 'BL' + str(i) + "_" + season[2:]
            for colName in ['GD' + str(n) for n in range(1,35)]:
                c.execute('ALTER TABLE {} ADD COLUMN {} INTEGER'.format(pointTblName, colName) )
    except:
        pass
    
    # store information for single games
    c.execute('CREATE TABLE IF NOT EXISTS Games (GameID INTEGER PRIMARY KEY, GameURL TEXT, Season INT, \
               League INT, EndResult TEXT, PlayerOfGame INT, Viewers INT, GameGrade REAL, ChancesRel TEXT, \
               CornersRel TEXT, RefreeName TEXT, RefreeGrade REAL)')
    
    # Table to store each game day, for each manager, with tactics and all players
    # populated by scrapeTactics()
    # Tactic IDs translate to: 0 =3-5-2,  1=4-5-1,  2 =4-4-2,  3 =4-3-3,  4 =3-4-3
    # First players in each group are actually playing
    # eg: Tactic ID = 3 -> Scorers have 3 Players -> SC1, SC2, SC3 were playing, 
    #  SC4 and SC5 are on the bench
    try:
        for i in range(1,3):
            tacTblName = 'Tactics' + str(i) + "_" + season[2:]
            c.execute('CREATE TABLE IF NOT EXISTS ' + tacTblName + ' (Manager_ID INT, GameDay INT, TacID INT, PRIMARY KEY (Manager_ID, GameDay))')
            for colName in ['Goal' + str(n) for n in range(1,4)]: # 3 Goalies
                c.execute('ALTER TABLE {} ADD COLUMN {} INTEGER'.format(tacTblName, colName) )
            for colName in ['Defn' + str(n) for n in range(1,7)]: # 6 Defenders
                c.execute('ALTER TABLE {} ADD COLUMN {} INTEGER'.format(tacTblName, colName) )
            for colName in ['Midf' + str(n) for n in range(1,9)]: # 8 Midfielders
                c.execute('ALTER TABLE {} ADD COLUMN {} INTEGER'.format(tacTblName, colName) )
            for colName in ['Scor' + str(n) for n in range(1,6)]: # 5 Scorer
                c.execute('ALTER TABLE {} ADD COLUMN {} INTEGER'.format(tacTblName, colName) )
                
    except:
        pass


conDB.commit()
conDB.close()


#############################
## ###  Website Login  ## ###
############################# 


#loginURL = "http://www.kicker.de/games/interactive/startseite/gamesstartseite.html" # OLD
loginURL = "https://secure.kicker.de/community/login"

# Username and PW read from separate file (first and second line)
uName = open('D:\Python\Info.txt', "r").readlines()[0].rstrip('\n')
uPass = open('D:\Python\Info.txt', "r").readlines()[1].rstrip('\n')

#driver = webdriver.Firefox()
#driver = webdriver.Chrome()
driver = webdriver.PhantomJS()

driver.get(loginURL)

# Get the Username and Password fields by their ID

login_name_form = driver.find_element_by_id('userTextBox')
login_pw_form = driver.find_element_by_id('passwortTextBox')
#login_name_form = driver.find_element_by_id('nicknameLoginBox') # OLD
#login_pw_form = driver.find_element_by_id('passwordLoginBox') # OLD


# Get the LOS Button by its name
LOS_Button = driver.find_element_by_name('loginButton')
#LOS_Button = driver.find_element_by_name('Submit') # OLD

# Check "Stay Logged in" Button
driver.find_element_by_name('loginPersistant').click()

# Fill in Username and Password and confirm with Enter
login_name_form.send_keys(uName)
login_pw_form.send_keys(uPass)
LOS_Button.send_keys(Keys.ENTER)



#############################
#### ###  Functions  ## #####
############################# 

#########################################################################################
################### Manager Points Scraping  ############################################
#########################################################################################

def scrapePoints(dbName,league,maxGD, minGD=1):
    """
    function that scrapes the points of every single gameday for each manager and stores them
    in the database
    
    The script will call the KeepTrack table in the DB to check which gamedays are already
    finished. Started but not finished days are still scraped from the beginning
    
        :dbName:    must be a sqlite3 DB connection
        :league:    takes 1 or 2, for Bundesliga 1 or 2
        :maxGD:     last played/available Gameday. Kicker would treat all non-played days
                    as the last played -> would not stop scraping + wrong values
        :minGD:     starting GameDay, default is 1. Useful when running mutliple clients for different
                    GameDays
        
    """
    # connect to SQLite3 DB
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    for Spieltag in range(minGD, maxGD+1):
        
        # check if gameday is already in DB by checking KeepTrack table, skip if existing
        x = c.execute('SELECT BL{}_{} FROM KeepTrack WHERE GameDay = "GD{}"'.format(league,season[2:],Spieltag)).fetchone()
        
        if not x:       #check if x exists at all (eg after fresh DB install)
            x = [0]
        
        if x[0] == 1:
            print("Skipping GameDay {}: already existing".format(Spieltag))
            continue        
        
        for counter in range(1,2000000,30):
            try:  
                if league == '1':                    
                    # switch URL between ...ive/bundesliga/mein... and ...ive/2bundesliga/mein... for resp. league
                    BLrankURL = "http://manager.kicker.de/interactive/bundesliga/meinteam/ranking/suchelfdnr/" \
                    + str(counter) + "/rankinglist/0/spieltag/" + str(Spieltag)
                elif league == '2': 
                    BLrankURL = "http://manager.kicker.de/interactive/2bundesliga/meinteam/ranking/suchelfdnr/" \
                    + str(counter) + "/rankinglist/0/spieltag/" + str(Spieltag)
                else:
                    "Only League 1 or 2 supported"
                
                # open URL that contains ranking points
                driver.get(BLrankURL)     
               
                BLrankHTLM = driver.page_source
                
                
                # As long as "Keine Daten vorhanden" is absent, it continues
                # if it appears, no more data is available, exception is raised and loop left
                assert "Keine Daten vorhanden" not in BLrankHTLM        
                
                
                # Define Parent element, use lxml parser
                soup = BeautifulSoup(BLrankHTLM, "lxml")              

                # Find the 'Ranking' table and move to child tbody
                entry = soup.find(summary='Ranking').tbody                
                               
                # iterate over all <tr> elements
                for tr_elem in entry("tr"):
                    
                    # find 'a' elements = links
                    a_elem = tr_elem('a')
                    
                    # iterate over the sub-elements and extract tag link and text
                    for elem in a_elem:
                        kickerURL = elem.get('href')
                        # extract the UserID from the URL
                        kickerID = kickerURL[kickerURL.find('manid')+6 : kickerURL.find('/', kickerURL.find('manid')+6)]
                        kickerName = elem.text
                    
                    # Define correct name of table to store data in
                    pointTblName = 'BL' + league + "_" + season[2:]
                
                    # find the points gained on every gameDay in the 'td' tag with attribute 'alignright last'
                    td_elem = tr_elem('td', class_="alignright last")
                    for elem in td_elem:
                        kickerPoints = elem.text
                     
                        # write Manager IDs and Names in table, ignore if already exists
                        c.execute('INSERT OR IGNORE INTO Manager VALUES (?,?)', (kickerID,kickerName))            
                        
                        # write Manager's ID in pointTblName if not yet exists
                        c.execute('INSERT OR IGNORE INTO ' + pointTblName + '(Manager_ID) VALUES (?)', (kickerID,))
                        
                        colName = 'GD' + str(Spieltag)
                        # write Manager's point of respective GameDay in pointTblName
                        c.execute('UPDATE ' + pointTblName + ' SET ' + colName + '=? WHERE Manager_ID = ?', (kickerPoints, kickerID))
            
                conDB.commit()
          
            except AssertionError:
                # Update KeepTrack table and exit loop
                c.execute('UPDATE KeepTrack SET BL{}_{}=1 WHERE GameDay = "GD{}"'.format(league,season[2:],Spieltag))
                break
            
            except Exception:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print(sys.exc_info()[0])
                continue
    
    driver.close()
    conDB.commit()
    conDB.close()




 
#########################################################################################
#################### Player Info Scraping  ##############################################
#########################################################################################


   
def scrapePlayers(dbName, season, league, update=1):
    """
    scrapes the information of all available players, one table per season
    First scrapes over the site containing all players, extracting Player ID's
     then uses the IDs to get all other data from the Player site
    
     :update: is a flag, that determines if all players should be scraped from scratch (0)
        or if only those with missing names but existing IDs are tried to be fetched (again) (1)
        (2) can be used if PlayerStats is empty and should be refilled
        1 = default
    """  

    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    # Table for basic player information
    c.execute('CREATE TABLE IF NOT EXISTS Player(Player_ID INTEGER PRIMARY KEY, \
                                                     FirstName TEXT, \
                                                     LastName TEXT, \
                                                     Team TEXT, \
                                                     POS TEXT, \
                                                     BackNum INT, \
                                                     Mio REAL, \
                                                     Born TEXT, \
                                                     Height INT, \
                                                     Weight INT, \
                                                     Nationality TEXT)')
    
    # Table for player performance per gameday
    c.execute('CREATE TABLE IF NOT EXISTS PlayerStats(UQID INT PRIMARY KEY, \
                                                     Player_ID INT, \
                                                     GameDay INT, \
                                                     Goals INT, \
                                                     Elfm TEXT, \
                                                     Assists INT, \
                                                     Scorer INT, \
                                                     Red INT, \
                                                     YelRed INT, \
                                                     Yellow INT, \
                                                     Change_In INT, \
                                                     Change_Out INT, \
                                                     Grade REAL, \
                                                     Points INT, \
                                                     GameID INT, \
                                                     GameURL TEXT, \
                                                     HA TEXT)'.format(league,season[2:]))
    
    
    
    # URL where a list of all players is found
    if league == '1':
        AllPlayersURL = 'http://manager.kicker.de/interactive/bundesliga/spielerliste/position/0/verein/0'
    elif league == '2':
        AllPlayersURL = 'http://manager.kicker.de/interactive/2bundesliga/spielerliste/position/0/verein/0'
    driver.get(AllPlayersURL)     
    BLrankHTLM = driver.page_source
    
    # Define Parent element, use lxml parser
    soup = BeautifulSoup(BLrankHTLM, "lxml")
     
    # Find the 'thead580' header 
    entry = soup.find(class_="thead580")
    
    # find all links after thead580. If they contain 'spielerid', extract the ID and save to list
    kickerIDlist = []
    if update == 0:
        for elem in entry.findAllNext('a', attrs={'class':"link"}):
            address = elem.get('href')
            if address.find('spielerid') != -1:
                kickerIDlist.append(address[address.find('spielerid')+10 : ])
        
        # write player_IDs from list into DB
        for ID in kickerIDlist:
            c.execute('INSERT OR IGNORE INTO Player (Player_ID) VALUES ({})'.format(league,season[2:], ID))       
        conDB.commit()  
    
    # for updates, Player Table is searched for missing FirstNames and exisiting IDs
    elif update == 1:
        for x in c.execute('SELECT Player_ID FROM Player WHERE FirstName IS NULL'.format(league,season[2:])).fetchall():
           kickerIDlist.append(str(x[0]))
    
    # Just use all exisiting PlayerIDs from "Player"
    elif update == 2:
            IDtuples = c.execute('SELECT Player_ID FROM Player'.format(league,season[2:])).fetchall()
            kickerIDlist = [x[0] for x in IDtuples if x[0]!=0]
    
    else:
        print('Update must be 0 or 1 or 2')
       
    
    # Acces each players stats site    
    for ID in kickerIDlist:
        if league == '1':
            PlayerURL = 'http://manager.kicker.de/interactive/bundesliga/spieleranalyse/spielerid/{}'.format(ID)  
        elif league == '2':
            PlayerURL = 'http://manager.kicker.de/interactive/2bundesliga/spieleranalyse/spielerid/{}'.format(ID)
        #print(PlayerURL)
        driver.get(PlayerURL) 
        BLrankHTLM = driver.page_source
        soup = BeautifulSoup(BLrankHTLM, "lxml")

        
        # try to access player page in 1.BL, if error is raised, open player page in 2.BL
        try:
            PlayerURL = 'http://manager.kicker.de/interactive/bundesliga/spieleranalyse/spielerid/{}'.format(ID) 
            driver.get(PlayerURL) 
            BLrankHTLM = driver.page_source
            soup = BeautifulSoup(BLrankHTLM, "lxml")
            
            assert "Das von Ihnen angeforderte Dokument konnte nicht erstellt werden" not in BLrankHTLM
       
        except AssertionError:
            PlayerURL = 'http://manager.kicker.de/interactive/2bundesliga/spieleranalyse/spielerid/{}'.format(ID)
            driver.get(PlayerURL) 
            BLrankHTLM = driver.page_source
            soup = BeautifulSoup(BLrankHTLM, "lxml")
            
        
        # Basic Info
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblSpielerVorname")
        firstName = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblSpielerNachname")    
        lastName = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblRueckenNr")
        backNumber = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblAktuellePos")
        position = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblAktuellerVerein")
        team = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblGeborenAm")
        birthday = entry.parent.parent.findNextSibling().text.strip()
        
        # the following uses a wildcard, as german ß is used, throwing errors for some players
        entry = soup.find(id=re.compile("ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblGroe*e"))    
        height = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblGewicht")
        weight = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblNation")
        nation = entry.parent.parent.findNextSibling().text.strip()
        
        entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblMarktwert")
        worth = entry.parent.parent.findNextSibling().text.strip()
        worth = float( worth[:worth.find('Mio')-1].replace(',','.') )
        
        # put all into a list, check first if no variable is empty, if empty change to " "
        # otherwise SQL error is raised
        parseList = (firstName, lastName, team, position, backNumber, 
                     worth, birthday, height, weight, nation, ID)
        parseList = [x if x != '' else '\" \"' for x in parseList]
        
        
        c.execute('UPDATE Player SET FirstName="{}", \
                                          LastName="{}", \
                                          Team="{}", \
                                          POS="{}", \
                                          BackNum={}, \
                                          Mio={}, \
                                          Born="{}", \
                                          Height={}, \
                                          Weight={}, \
                                          Nationality="{}" \
                                    WHERE Player_ID ={}'.format(*parseList) )
        conDB.commit()  
        
                
        # Gameday related info
        
        try:
            entry = soup.find('table', attrs={'class':"tStat", 'summary':"spieler", 'width':"100%"})    
            
            # Each 'first' td tag is a gameday: if gameday was not played, no information is scraped
            for firstTag in entry.findChildren('td', attrs={'class':"first"}):
                gameDay = firstTag.text
                
                goals = firstTag.findNext().text.replace("-","0")
                
                elfer = firstTag.findNext().findNext().text.replace('\xa0', "")
                
                assists = firstTag.findNext().findNext().findNext().text.replace("-","0")
            
                scorer = firstTag.findNext().findNext().findNext().findNext().text.replace("-","0")
                scoretag = firstTag.findNext().findNext().findNext().findNext()
        
                red = scoretag.findNext().text.replace("-","0")
                
                yelred = scoretag.findNext().findNext().text.replace("-","0")
                
                yellow = scoretag.findNext().findNext().findNext().text.replace("-","0")
                
                gotIn = scoretag.findNext().findNext().findNext().findNext().text.replace("-","0")
                
                gotOut = scoretag.findNext().findNext().findNext().findNext().findNext().text.replace("-","0")
                gotOutTag = scoretag.findNext().findNext().findNext().findNext().findNext()
                
                grade = gotOutTag.findNext().text.replace("-","0").replace(',','.')   
                
                ha = gotOutTag.findNext().findNext().findNext().findNext().text.replace("-","0").replace(',','.')
                
                #result = gotOutTag.findNext().findNext().findNext().findNext().findNext().text.replace('\xa0', "")
                resultTag = gotOutTag.findNext().findNext().findNext().findNext().findNext()
                
                gameURL = resultTag.findNext().findChild().get('href')
                
                gameID = gameURL[ gameURL.rfind('/', 0, gameURL.rfind('/spielanalyse')) + 1  : gameURL.rfind('/spielanalyse')]
                
                
                # Unique ID as a combination of player ID and gameday, 000 added to avoid mapping
                # into another player ID by accident
                UID = str(ID)+ "000" +str(gameDay)

                c.execute('INSERT OR IGNORE INTO PlayerStats VALUES ({}, {}, {}, {}, "{}", {}, {}, {}, {}, {}, {}, {}, {}, NULL, {}, "{}","{}")'.format(
                                    UID, ID, gameDay, goals, elfer, assists, scorer,
                                                        red, yelred, yellow, gotIn, gotOut, grade, gameID, gameURL, ha) )
                conDB.commit()  
            
        except:
            continue
    
    driver.close()
    conDB.commit()
    conDB.close()



def scrapePlayers2(dbName):
        """
        ScrapePlayers doesnt account for players that have left during the season
        This function iterates through all IDs and saves information if the playerID exists
        """  
        
        conDB = sqlite3.connect(dbName)
        c = conDB.cursor()
        
        # create a table that stores PLayerIDs that are non existent
        c.execute('CREATE TABLE IF NOT EXISTS NonPlayer (Player_ID INTEGER PRIMARY KEY)')
        
        # create a list of existing IDs and skip these
        kickerIDlist = []
        for x in c.execute('SELECT Player_ID FROM Player').fetchall():
           kickerIDlist.append(str(x[0]))
           
        # also skip known non existing IDs
        for x in c.execute('SELECT Player_ID FROM NonPlayer ').fetchall():
            kickerIDlist.append(str(x[0]))
        
        for x in range(120000):
            if str(x) not in  kickerIDlist:
                URL = "http://manager.kicker.de/interactive/bundesliga/meinteam/spieleranalyse/spielerid/" + str(x)
                
                try:
                    driver.get(URL) 
                    BLrankHTLM = driver.page_source
                    soup = BeautifulSoup(BLrankHTLM, "lxml")
                    
                    assert "Das von Ihnen angeforderte Dokument konnte nicht erstellt werden" not in BLrankHTLM    
                    
                    # Basic Info
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblSpielerVorname")
                    firstName = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblSpielerNachname")    
                    lastName = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblRueckenNr")
                    backNumber = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblAktuellePos")
                    position = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblAktuellerVerein")
                    team = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblGeborenAm")
                    birthday = entry.parent.parent.findNextSibling().text.strip()
                    
                    # the following uses a wildcard, as german ß is used, throwing errors for some players
                    entry = soup.find(id=re.compile("ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblGroe*e"))    
                    height = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblGewicht")
                    weight = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblNation")
                    nation = entry.parent.parent.findNextSibling().text.strip()
                    
                    entry = soup.find(id="ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_LblMarktwert")
                    worth = entry.parent.parent.findNextSibling().text.strip()
                    worth = float( worth[:worth.find('Mio')-1].replace(',','.') )
                    
                    # put all into a list, check first if no variable is empty, if empty change to " "
                    # otherwise SQL error is raised
                    parseList = (x, firstName,lastName, team, position, backNumber, worth, birthday,height, weight)
                    parseList = [t if t != '' else '\" \"' for t in parseList]
               
                    
                    c.execute('INSERT OR IGNORE INTO Player VALUES ({}, "{}", "{}","{}","{}",{},{},"{}",{},{})'.format(*parseList) )
                    
                    conDB.commit()
        
                except AssertionError:
                    # Update KeepTrack table and exit loop
                    c.execute('INSERT OR IGNORE INTO NonPlayer VALUES ({})'.format(x) )
                    conDB.commit()
                    continue

        driver.close()
        conDB.commit()
        conDB.close()




#########################################################################################
################### Tactics Page Scraping  ##############################################
#########################################################################################
#
#def runIterList(cur_window_handle,iterManList, Spieltag, season, league):
#    """
#    executes the calling and scraping of a single page, is called by scrapeTacticsMult()
#     
#     cur_window_handle : a unique window handle ID for PhantomJS
#     iterManList : the list of all Manager IDs this function should plow through
#     c : the database pointer
#     Spieltag : the one gameday
#     season : current season
#     league : current league
#    
#    """
#    
#    # list that will store each line and is returned -> DB write is outside of this func
#    resList = []
#    
#    #w = open("D:/Test/kicker_db/" + cur_window_handle +".txt", 'w')
#
#    driver.switch_to_window(cur_window_handle)
#
#    for manID in iterManList:   
#      
#        # Define URL for each Manager/league/Day combination
#        if league == '1':
#            manURL = 'http://manager.kicker.de/interactive/bundesliga/meinteam/steckbrief/manid/{}/spieltag/{}'.format(manID,Spieltag)
#        elif league == '2':
#            manURL = 'http://manager.kicker.de/interactive/2bundesliga/meinteam/steckbrief/manid/{}/spieltag/{}'.format(manID,Spieltag)
#        else:
#            print('Only League 1 or 2 supported')
#                    
#        driver.get(manURL) 
#        BLrankHTLM = driver.page_source
#        soup = BeautifulSoup(BLrankHTLM, "lxml")
#        
#        # put in try/except, as sometime empty pages are scraped?! 
#        try:
#            # Find the tag containing the ID for chosen tactic (0-4 see above)
#            entry = soup.find('form', attrs={'name':"PlayerForm"})
#            tacTag = entry.find('input', attrs={'id':'inptactic'})
#            tacID = tacTag.get('value')
#        except:
#            print(manID, len(BLrankHTLM))
#            continue
#        
#        # Find the long string containing all Players in order
#        startStr = BLrankHTLM.find("""ovTeamPlayerElements = "{'players':""")
#        endStr = BLrankHTLM.find("\n", startStr)
#        longStr = BLrankHTLM[startStr:endStr]
#        
#        # search player ID, save to list, delete obolote first part of string, repeat
#        playerList = []
#        pos = 0
#        while pos != -1:
#            pos = longStr.find('splid')
#            first = pos + 8 # finds first digit of the ID
#            last = longStr.find("'", first) # look for next ' after pos
#            playerList.append(longStr[first:last])
#            longStr = longStr[last:]
#        
#        # remove empty entry from the back
#        addTuple = tuple([manID, Spieltag, tacID ] + [x for x in playerList if x != ''])
#        
#        resList.append(addTuple)
#        #w.write(str(addTuple))
#
#    
#    #driver.close()
#    #w.close()
#    return (resList)
#    
#    
#    
#    
#
#def scrapeTacticsMult(dbName, season, league, Spieltag=0):
#    """
#    executes several PhantomJS calls in parallel for speedup, all calls write into
#    the same DB
#    
#    Uses Mananger IDs from Manager table in DB to extract teams by 
#    scrapePoints() must be run before for each GD
#    
#    Gamedays are manual input, KeepTrack table is not used nor updated!
#    
#    If gameday was not finished: will pick up unfinished Managers during gameday
#    
#    Process may get stuck for unknown reasons (website opens and never finishes?) and has to be restarted manually
#    """
#    
#    # Overwrite dbname, should be off by default
#    #dbName = 'D:/Test/kicker_db/kicker_main_22.sqlite'
#      
#    conDB = sqlite3.connect(dbName)
#    c = conDB.cursor()
#    
##    # create a list of rowids (=identical to gameday) where flag for manager teams = 0
##    zeroList = [x[0] for x in c.execute('SELECT rowid FROM KeepTrack WHERE Man{}_{}=0'.format(league,season[2:])).fetchall()]
##    # new list of zeroList reduced by all numbers > maxGD, results in all valid undone gameDays
##    iterList = [x for x in zeroList if int(x)<=maxGD]
##    
##    # Use this to force one certain Spieltag, should be off by default
##    iterList = [1]
#   
#    
#    # get List of all Managers if points have been scraped this season
#    manIDList = [x[0] for x in c.execute('SELECT Manager_ID FROM BL{}_{}'.format(league,season[2:])).fetchall()]
#    # reduce list by already exisiting entries -> no double scraping
#    manReduceList = [x[0] for x in c.execute('SELECT Manager_ID FROM Tactics{}_{} WHERE GameDay={}'.format(league,season[2:],Spieltag)).fetchall()]
#    iterManListLong = list(set(manIDList) - set(manReduceList))
#    #iterManList = [x for x in manIDList if x not in manReduceList] # This takes forever for a large number of values
#    
#    
#    # max Number of threads, e.submit threads must be changed manually
#    maxThreads = 10
#    
#    # open "maxThreads" new windows wth unique windows IDs    
#    for x in range(maxThreads):
#        driver.execute_script("$(window.open())")
#    #driver.current_window_handle #get current window handle
#    #driver.window_handles #get a list of all current handles
#    #driver.switch_to_window(driver.window_handles[-1]) # switch to last opened window
#    
#    # Divide the list up in chunks of 1000, after each of these chunks these are written to DB
#    for x in range(0,len(iterManListLong)+1, 1000):
#        iterManList = iterManListLong[x:x+1000]
#        
#        # split iterManList list into "maxThreads" equal sized parts, last parts length may be shorter 
#        n = int(len(iterManList)/maxThreads)
#        
#        # gameDays may have left few unsolved manager IDs, these throw errors if too few to devide
#        if n < maxThreads:
#            break
#        
#        # create a list of sublists, each sublist is passed to it owm process
#        iterManSubList = [iterManList[i:i+n] for i in range(0, len(iterManList), n)]
#        
#        with cf.ThreadPoolExecutor(max_workers=maxThreads) as e:
#            x = e.submit(runIterList, driver.window_handles[1], iterManSubList[0], Spieltag, season, league)
#            x2 = e.submit(runIterList, driver.window_handles[2], iterManSubList[1], Spieltag, season, league)
#            x3 = e.submit(runIterList, driver.window_handles[3], iterManSubList[2], Spieltag, season, league)
#            x4 = e.submit(runIterList, driver.window_handles[4], iterManSubList[3], Spieltag, season, league)
#            x5 = e.submit(runIterList, driver.window_handles[5], iterManSubList[4], Spieltag, season, league)
#            
#            x6 = e.submit(runIterList, driver.window_handles[6], iterManSubList[5], Spieltag, season, league)
#            x7 = e.submit(runIterList, driver.window_handles[7], iterManSubList[6], Spieltag, season, league)
#            x8 = e.submit(runIterList, driver.window_handles[8], iterManSubList[7], Spieltag, season, league)
#            x9 = e.submit(runIterList, driver.window_handles[9], iterManSubList[8], Spieltag, season, league)
#            x10 = e.submit(runIterList, driver.window_handles[10], iterManSubList[9], Spieltag, season, league)
#            
#    
#        for w in ( x.result(),x2.result(),x3.result(),x4.result(),x5.result(),
#                  x6.result(),x7.result(),x8.result(),x9.result(),x10.result()):
#            
#            
#            # write each output line-by-line to the DB
#            for line in w:
#                try:
#                    c.execute( 'INSERT OR IGNORE INTO Tactics' + league + '_' + season[2:] + ' VALUES {}'.format(line) )
#                except:
#                    pass
#            conDB.commit()
#
#    
#    #conDB.close()

   


# single execution
def scrapeTactics(dbName, season, league, SpieltagList):
    """
    Uses Mananger IDs from Manager table in DB to extract teams by 
    scrapePoints() must be run before for each GD
    
    :SpieltagList: can be a single integer or a list of integers
    
    If gameday was not finished: will pick up unfinished Managers during gameday
    """
    
    if type(SpieltagList) == int:
        spList = []
        spList.append(SpieltagList)
    elif type(SpieltagList) == list:
        spList = SpieltagList
    else:
        print("Spieltag must be integer or list of integers")
        
    for Spieltag in spList:    
        
        # Overwrite dbname, should be off by default
        #dbName = 'D:/Test/kicker_db/kicker_main_22.sqlite'
        
        conDB = sqlite3.connect(dbName)
        c = conDB.cursor()
        
        # counter to keep track of speed of processing
        ctr = 0
        startTime = datetime.datetime.now()
        
            
        # get List of all Managers if points have been scraped this season
        manIDList = [x[0] for x in c.execute('SELECT Manager_ID FROM BL{}_{}'.format(league,season[2:])).fetchall()]
        # reduce list by already exisiting entries -> no double scraping
        manReduceList = [x[0] for x in c.execute('SELECT Manager_ID FROM Tactics{}_{} WHERE GameDay={}'.format(league,season[2:],Spieltag)).fetchall()]
        iterManSetLong = set(manIDList) - set(manReduceList)
        iterManListLong = list(iterManSetLong)
        iterManListLongLen = len(iterManListLong)
       
        print(Spieltag, " started with ", len(manIDList), "Managers, with ", len(manReduceList), "already processed (", len(iterManListLong), ") remaining")
        
        # split list into 5 equal sized parts, last parts length may be shorter (test case)
        #n = int(len(iterManList)/5)
        #iterManSubList = [iterManList[i:i+n] for i in range(0, len(iterManList), n)]
        
        for x in range(0,len(iterManListLong)+1, 100):
            iterManList = iterManListLong[x:x+100]
                        
            # list that will store each line and is returned
            resList = []
        
            for manID in iterManList:
                
                # increase counter for each Manager ID
                ctr = ctr + 1
                
                # check if Manager has points on respective gameday, if not continue with next manID
                if c.execute('SELECT GD{} FROM BL{}_{} WHERE Manager_ID={}'.format(Spieltag,league,season[2:],manID)).fetchone()[0] == None:
                    continue
               
                # Define URL for each Manager/league/Day combination
                if league == '1':
                    manURL = 'http://manager.kicker.de/interactive/bundesliga/meinteam/steckbrief/manid/{}/spieltag/{}'.format(manID,Spieltag)
                elif league == '2':
                    manURL = 'http://manager.kicker.de/interactive/2bundesliga/meinteam/steckbrief/manid/{}/spieltag/{}'.format(manID,Spieltag)
                else:
                    'Only League 1 or 2 supported'
                
                driver.get(manURL) 
                BLrankHTLM = driver.page_source
                soup = BeautifulSoup(BLrankHTLM, "lxml")
                
                # put in try/except, as sometime empty pages are scraped?! 
                try:
                    # Find the tag containing the ID for chosen tactic (0-4 see above)
                    entry = soup.find('form', attrs={'name':"PlayerForm"})
                    tacTag = entry.find('input', attrs={'id':'inptactic'})
                    tacID = tacTag.get('value')
                except:
                    print(manID, len(BLrankHTLM))
                    continue
                
                # Find the long string containing all Players in order
                startStr = BLrankHTLM.find("""ovTeamPlayerElements = "{'players':""")
                endStr = BLrankHTLM.find("\n", startStr)
                longStr = BLrankHTLM[startStr:endStr]
                
                # search player ID, save to list, delete obolote first part of string, repeat
                playerList = []
                pos = 0
                while pos != -1:
                    pos = longStr.find('splid')
                    first = pos + 8 # finds first digit of the ID
                    last = longStr.find("'", first) # look for next ' after pos
                    playerList.append(longStr[first:last])
                    longStr = longStr[last:]
                
                # remove empty entry from the back
                addTuple = tuple([manID, Spieltag, tacID ] + [x for x in playerList if x != ''])
                
                resList.append(addTuple)
                
                # Print time (average seconds per 10 Managers) and Managers to keep track of process
                if ctr%10 == 0:
                    avgTime = round((datetime.datetime.now()-startTime).seconds / ctr, 2)
                    startTime = datetime.datetime.now()
                    print("\r" + str(ctr) + "/" + str(iterManListLongLen) + " Managers of GameDay " + str(Spieltag) 
                    + " processed. Avg. time per 10 Managers: " + str(avgTime) + "sec", end="")
                
            for line in resList:
                try:
                    c.execute( 'INSERT OR IGNORE INTO Tactics' + league + '_' + season[2:] + ' VALUES {}'.format(line) )
                except:
                    pass
                
            conDB.commit()
            
        # write everything to the DB
        #c.execute( 'INSERT OR IGNORE INTO Tactics' + league + '_' + season[2:] + ' VALUES {}'.format(addTuple) )
        #print(Spieltag, manID, "done")
        #conDB.commit()
        
    # Update KeepTrack after successful scraping
    #c.execute('UPDATE KeepTrack SET Man{}_{}=1 WHERE rowid = "{}"'.format(league,season[2:],Spieltag) )
    print(Spieltag, " finished")
    driver.close()
    conDB.commit()
    conDB.close()
        

#########################################################################################
###################### Game Page Scraping  ##############################################
#########################################################################################

def scrapeGames(season, league):
    """
    will get the GameURL from PlayerStats Table, calls un-called URLs, extracts info and stores in Games Table
    
    -> scrapePlayers() must be run first for each gameDay
    """
    
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    # get all URLs from PlayerStats
    URLlist = [x[0] for x in c.execute('SELECT GameURL FROM PlayerStats').fetchall()]
    
    # get all existing URLs from Games
    exURLlist = [x[0] for x in c.execute('SELECT GameURL FROM Games').fetchall()]
    
    # unique URl list -> double entries are thrown out
    uniqueURLs = list(set(URLlist)-set(exURLlist))
    
    for curURL in uniqueURLs:
        try:
            driver.get(curURL) 
            BLrankHTLM = driver.page_source
            soup = BeautifulSoup(BLrankHTLM, "lxml")
            
            homeGoals = soup.find('div', attrs={'id':'ovBoardExtMainH'}).text
            guestGoals = soup.find('div', attrs={'id':'ovBoardExtMainA'}).text
            endResult = homeGoals+":"+guestGoals
            
            # Viewers may be only a number, or with text appended (eg 'ausverkauft') -> only return number
            viewersX = soup.find('div', attrs={'class':'zuschauer'}).findNext().findNext().text
            viewers = int(viewersX.split()[0])
            
            gameGTag = soup.find('div', attrs={'class':'spielnote'})
            txtGrade = gameGTag.text[gameGTag.text.find(':') + 1 : ].strip()
            gameGrade = txtGrade.replace("-","0").replace(',','.')
            
            chancesRel = soup.find('div', attrs={'class':'chancen'}).findNext().findNext().text
            
            cornersRel = soup.find('div', attrs={'class':'ecken'}).findNext().findNext().text
            
            refEntry = soup.find('div', attrs={'class':'schiedsrichter'}).findNext()
            refree = refEntry.findNext('a').text
            
            sText = sText = soup.find('div', attrs={'class':'schiedsrichter'}).findNext().findNext().text
            sText = sText[sText.find('Note') + 5 :  sText.find('\n', sText.find('Note')+5)]
            refrGrade = sText.replace("-","0").replace(',','.')
            
            mvpLink = soup.find('div', attrs={'class':'spldesspiels'}).findNext('a').get('href')
            MVP = mvpLink[ mvpLink.rfind('/', 0, mvpLink.rfind('/')) + 1  :  mvpLink.rfind('/') ]
            
            leagueURL = curURL[curURL.find('bundesliga')-1 : curURL.find('bundesliga')]
            if leagueURL == '2':
                league = 2
            else:
                league = 1
        
    
            gameID = curURL[curURL.rfind('/', 0, curURL.rfind('/spielanalyse')) + 1  : curURL.rfind('/spielanalyse')]
        except:
            continue
        
        
        c.execute( 'INSERT OR IGNORE INTO Games VALUES ({}, "{}", {}, {}, "{}", {}, {}, {}, "{}", "{}", "{}", {})'.format(
                                    gameID, curURL, season, league, endResult, MVP, viewers, gameGrade, chancesRel, 
                                    cornersRel, refree, refrGrade) )

        conDB.commit()
    
    
    driver.close()
    conDB.close()



#########################################################################################
############################# download player imgs ######################################
#########################################################################################

def dlPic(league, season):    
    """
    uses the Player_ID stored in PlayerX_Y table to download each player image
    saves it using ID_LastName_FirstName.jpg
    """
    
    import urllib

    dlFol = 'D:/Test/kicker_x_db/pics/'
    
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    # get all Player IDs
    idListTup = c.execute('SELECT Player_ID FROM Player{}_{}'.format(league, season[2:])).fetchall()
    idList = [x[0] for x in idListTup]
    
    # check ids agains existing files
    checkList = []
    for picFile in os.listdir(dlFol):
        checkList.append(int(picFile[:picFile.find('_')]))
            
    cleanList = list(set(idList) - set(checkList))   
    
    
    for plID in cleanList:    
        
        firstName = c.execute('SELECT FirstName FROM Player{}_{} WHERE Player_ID={}'.format(league, season,plID) ).fetchone()[0]
        lastName = c.execute('SELECT LastName FROM Player{}_{} WHERE Player_ID={}'.format(league,season[2:],plID) ).fetchone()[0]
        
        # Define URL for each Manager/league/Day combination
        if league == '1':
            playrURL = 'http://manager.kicker.de/interactive/bundesliga/meinteam/spieleranalyse/spielerid/{}'.format(plID)
        elif league == '2':
            playrURL = 'http://manager.kicker.de/interactive/2bundesliga/meinteam/spieleranalyse/spielerid/{}'.format(plID)
        else:
            'Only League 1 or 2 supported'
    
        
        driver.get(playrURL) 
        BLrankHTLM = driver.page_source
        soup = BeautifulSoup(BLrankHTLM, "lxml")
        
        tag = soup.find('img', attrs={'id':'ctl00_PlaceHolderContent_ctrlSpielerSteckbrief_ImgSpieler'})
        picLink = tag.get('src')
        
        saveName = dlFol + str(plID) + "_" + str(lastName) + "_" + str(firstName) + ".jpg"
        urllib.request.urlretrieve(picLink, saveName)
        
        


#dlPic('1', '2015')

#########################################################################################
############################# DB Scripts  ###############################################
#########################################################################################    


   
def mergeDBs(mainDB, secDB, tblName):
    """
    merges a table from a second DB into a main DB by appending data from one to the other
    Does NOT work if rows already exist, to upate existing rows use fillDB()
    
        :mainDB:  str path to the main DB, this is the DB that will be kept
        :secDB:   str path to the secondary DB, this could be deleted afterwards
        :tblName: str table name in both DBs, must be identical
    """
    
    conDB = sqlite3.connect(mainDB)
    c = conDB.cursor()
    
    c.execute("ATTACH DATABASE ? AS secondDB", (secDB,) )
    
    myQuery = c.execute("SELECT * FROM secondDB.{}".format(tblName)).fetchall()
    
    for x in myQuery:
        try:
            c.execute("INSERT OR IGNORE INTO main.{} VALUES {}".format(tblName, x))
        except:
            pass
  
    conDB.commit()
    c.execute( "DETACH DATABASE secondDB" )    
    conDB.close()
    



def fillDBs(mainDB, secDB, tblName, idField):
    """
    merges a table from a second DB into a main DB by filling all NoData values in mainDB
    with exisiting values from secDB
    
        :mainDB:  str path to the main DB, this is the DB that will be kept
        :secDB:   str path to the secondary DB, this could be deleted afterwards
        :tblName: str table name in both DBs, must be identical
        :idField: str name of the key that is identical in both tables
    """
    
    conDB = sqlite3.connect(mainDB)
    c = conDB.cursor()
    
    c.execute("ATTACH DATABASE ? AS secondDB", (secDB,) )
    
    # Get a list of all column names (except idField)
    colNamesQuery = c.execute("PRAGMA table_info('{}')".format(tblName)).fetchall()
    colNamesList = []
    
    for entry in colNamesQuery:
        if entry[1] == idField:
            continue
        else:
            colNamesList.append(entry[1])
    
    
    # Load the entire table from DB1
    myQuery = c.execute("SELECT * FROM {}".format(tblName)).fetchall()
    
    # Iterate over each row in DB1 table
    for x in myQuery:
        manID = x[0]
        
        # Get the correposing row from DB2
        secQuery = c.execute("SELECT * FROM secondDB.{} WHERE {} = {}".format(tblName, idField, manID)).fetchone()
        
        # update first list if NoData, with values from second list
        xList = list(x)
        for idx,val in enumerate(xList):
            if xList[idx] == None:
                xList[idx] = secQuery[idx]

        # replace None value with NULL for SQLite, remove first column with Key
        listNULL = ['NULL' if x == None else x for x in xList][1:]
        #singleString = ','.join(map(str, ['NULL' if x == None else x for x in xList]))
        
        # create a single update string for SQLite
        singleString = ''
        for idx,val in enumerate(colNamesList):
            singleString = singleString + " " + val + "=" + str(listNULL[idx]) + ","
        singleString = singleString[:-1] #remove last comma
            
        
        # update table in first DB with new        
        c.execute('UPDATE {} SET {} WHERE {} = {}'.format(tblName, singleString, idField, manID))
        
    conDB.commit()
    c.execute( "DETACH DATABASE secondDB" )    
    conDB.close()

#########################################################################################
############################### Others  #################################################
######################################################################################### 



def calcPoints(UQID):
    """
    calculate the points a player gained by using his grade, score etc.
    UQID is the unique ID in PlayerStats composed of PlayerID+000+Gameday
    """
    
    
    # Dictionary with Grades and related Points, grades are keys
    gradeDict = {1.0:10, 1.5:8, 2.0:6, 2.5:4, 3.0:2, 3.5:0, 4.0:-2, 4.5:-4, 5.0:-6, 5.5:-8, 6.0:-10}    
    # Dictionary Points for Goals related to poisiion, positions are keys
    goalDict = {'Torwart':6, 'Abwehr':5,'Mittelfeld':4,'Sturm':3}
       
    # PlayerStats query (related to gameday)
    Uq = c.execute("SELECT * FROM PlayerStats{}_{} WHERE UQID={}".format(league, season[2:], UQID)).fetchone()    

    # Player query (related to general info), get PlayerID from Uq
    Pq =  c.execute("SELECT * FROM Player WHERE Player_ID={}".format(Uq[1])).fetchone()    
    # Game query (related to game info), get GameID from Uq
    Gq =  c.execute("SELECT * FROM Games WHERE GameID={}".format(Uq[14])).fetchone()
     
    
    totP = 0 # Var to store all points
    
    # Played from beginning and got a grade?
    if Uq[12] > 0 and Uq[10] == 0:           # played from start               
        totP = totP + 2                     
        totP = totP + gradeDict[Uq[12]]     
    elif Uq[12] > 0 and Uq[10] != 0:        # played NOT from start, but got grade
        totP = totP + 1
        totP = totP + gradeDict[Uq[12]]
    else:                                   #  played NOT from start, got NO grade
        totP = totP + 1                     
    
    # Scored Goals?
    if Uq[3] > 0:
        totP = totP + Uq[3] * goalDict[Pq[4]]
    
    # Assisted?
    if Uq[5] > 0:
        totP = totP + Uq[5]
        
    # Got red or red-yellow card?
    if Uq[7] > 0:
        totP = totP - 6
    if Uq[8] > 0:
        totP = totP - 3
    
    # Goalkeeper :0
    if Pq[4] == 'Torwart':
        
        if Uq[16] == 'A':   # A means goalie is from visiting team
            if Gq[4][:Gq[4].find(':')] == '0':
                totP = totP + 2
        else:                                           # goalie is from home team
            if Gq[4][Gq[4].find(':') + 1 :] == '0':
                totP = totP + 2
    
    # Player is player of the game
    if Gq[5] == Uq[1]:
        totP = totP + 3
    
    return(totP)
    
            

        
 #Add points to empty Points Column
#UQlist = c.execute("SELECT UQID FROM PlayerStats").fetchall()
#UQlist2 = [x[0] for x in UQlist]
#for UQID in UQlist2:
#    #print (UQID)
#    p = calcPoints(UQID)
#    c.execute('UPDATE PlayerStats SET Points={} WHERE UQID={}'.format(p,UQID))
#conDB.commit()
    
    



# Get count of exisiting entries

#dbName2 = 'D:/Test/kicker_x_db/kicker_main.sqlite'
#conDB2 = sqlite3.connect(dbName2)
#d = conDB2.cursor()  
#
#myList = []
#for x in range(1,35):
#    liste = d.execute('SELECT Manager_ID FROM Tactics1_15 WHERE GameDay='+str(x) ).fetchall()
#    myList.append(len(liste))
#for x,y in enumerate(myList):
#    print(x+1,y)
#conDB2.close()

    
#########################################################################################
    
#########################################################################################
######################### Function Calls  ###############################################
######################################################################################### 

  
#mergeDBs('D:/Test/kicker16/kicker_main.sqlite', 'D:/Test/kicker16/kicker_sub_4_6.sqlite', 'Tactics1_16')

#fillDBs('D:/Test/kicker/kicker_main.sqlite', 'D:/Test/kicker/kicker_main_2.sqlite', 'BL1_16', 'Manager_ID') 
 
 


scrapeTactics('D:/Test/kicker/kicker_main.sqlite', season, league, list(range(26,29))) 


  
#scrapePoints(dbName,league,30,minGD=27)



#scrapeTactics('D:/Test/kicker16/kicker_sub_25.sqlite', season, league, 25)
 

#scrapePlayers(dbName, season, league, update=0)
   
   
#scrapeGames(season, league)   
 


   

   
   
   
   
   
   
   