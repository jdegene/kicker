# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET


Spieltag = 1

myFile = 'D:/Test/kicker3/1BL_' + str(Spieltag) +'_121.txt'


# first convert xml txt file from windows to utf8 encoding
# xml doesnt allow some characters and throws exceptoion otherwise
with open(myFile,encoding='Windows-1252') as f:
    data = f.read()
with open(myFile,'w',encoding='utf8') as f:
    f.write(data)

# then parse file into a tree
tree = ET.parse(myFile)
root = tree.getroot()


#iterate through all elemtents and find the table containing the stats
for entry in root.iter('{http://www.w3.org/1999/xhtml}table'):
    if entry.get('summary') == 'Ranking':
        summryTab = entry
        break


# iterate through the table and extract name, ID and points
for child in summryTab[0]:
    if child.get('class') == 'alt':
        kickerName = child[1][0].text
        kickerURL = child[1][0].get('href')
        kickerID = kickerURL[kickerURL.find('manid')+6 : kickerURL.find('/', kickerURL.find('manid')+6)]
        kickerPoints = child[3].text
        
        print(kickerID, kickerName,  kickerPoints)


