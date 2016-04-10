# -*- coding: utf-8 -*-

import os, sys

from bs4 import BeautifulSoup
import sqlite3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# define used season (starting year), used for naming within database
season = '2015'
league = '2'

# Last played GameDay
maxGD = 29

# Database filepath
dbName = 'D:/Test/kicker_db/TEST.sqlite'


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
    # columns are League/Seasons; rows are Gamedays
    try:
        c.execute('CREATE TABLE KeepTrack (GameDay TEXT, BL1_{0} INTEGER, BL2_{0} INTEGER)'.format(season[2:]))
        for rowName in ['GD' + str(n) for n in range(1,35)]:
            c.execute('INSERT OR IGNORE INTO KeepTrack (GameDay, BL1_{0}, BL2_{0}) VALUES ("{1}","0","0")'.format(season[2:],rowName))
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
                c.execute('ALTER TABLE %s ADD COLUMN %s INTEGER' % (pointTblName, colName) )
    except:
        pass

conDB.commit()
conDB.close()


#############################
## ###  Website Login  ## ###
############################# 

loginURL = "http://www.kicker.de/games/interactive/startseite/gamesstartseite.html"

# Username and PW read from separate file (first and second line)
uName = open('D:\Python\Info.txt', "r").readlines()[0].rstrip('\n')
uPass = open('D:\Python\Info.txt', "r").readlines()[1].rstrip('\n')

#driver = webdriver.Firefox()
#driver = webdriver.Chrome()
driver = webdriver.PhantomJS()

driver.get(loginURL)

# Get the Username and Password fields by their ID
login_name_form = driver.find_element_by_id('nicknameLoginBox')
login_pw_form = driver.find_element_by_id('passwordLoginBox')
# Get the LOS Button by its name
LOS_Button = driver.find_element_by_name('Submit')

# Fill in Username and Password and confirm with Enter
login_name_form.send_keys(uName)
login_pw_form.send_keys(uPass)
LOS_Button.send_keys(Keys.ENTER)



def scrapePoints(dbName,league,maxGD):
    """
    function that scrapes the points of every single gameday for each manager and stores them
    in the database
    
    The script will call the KeepTrack table in the DB to check which gamedays are already
    finished. Started but not finished days are still scraped from the beginning
    
        :dbName:    must be a sqlite3 DB connection
        :league:    takes 1 or 2, for Bundesliga 1 or 2
        :maxGD:     last played/available Gameday. Kicker would treat all non-played days
                    as the last played -> would not stop scraping + wrong values
        
    """
    # connect to SQLite3 DB
    conDB = sqlite3.connect(dbName)
    c = conDB.cursor()
    
    for Spieltag in range(1,maxGD+1):
        
        # check if gameday is already in DB by checking KeepTrack table, skip if existing
        x = c.execute('SELECT BL{}_{} FROM KeepTrack WHERE GameDay = "GD{}"'.format(league,season[2:],Spieltag)).fetchone()
        if x[0] == 1:
            print("Skipping GameDay {}: already existing".format(Spieltag))
            continue        
        
        for counter in range(1,32,30):
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
                        print(kickerName, kickerID, kickerPoints)
                        print(type(kickerName), type(kickerID), type(kickerPoints))
                     
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
            
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print(sys.exc_info()[0])
                continue
    
    driver.close()
    conDB.commit()
    conDB.close()
    

scrapePoints(dbName,league,maxGD)