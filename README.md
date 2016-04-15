
# kicker
This little project intends to gather information from the kicker.de Manager Interactive game, to gain some statistical insights by analysing manager behaviour.
Currently (April 2016) only the data gathering scripts are finished. Data analysis scripts will follow.

Before any function is run, the Database is connected to and created if necessary. Also an PhantomJS instance is started using Selenium and logged into the website. Username and Password are stored in 
a separate file (.../Info.txt) but could as well be hardcoded into the script.


### kicker.py 

Is the main file and the only one that is updated. It scrapes Manager Points, Manager Tactics and Player related data. Data is stored in a SQLite DB

Run scrapePoints() first, as scrapeTactic() will access the results to determine which Manager IDs are acutally available for scraping

* scrapePoints()
Uses the results of each gameday to scrape points for each Manager. 30 Managers per site are extracted. No parallel extraction implemented yet.
Does not check for double entries currently, but will only scrape gamedays that are not marked as finished yet.
 
Must be run for each gameday before scrapeTactics() can be run

* scrapeTactics()
Access each Managers gameday tactics setup and saves formation ID and ordered Player IDs for each gameday. 
No parallel processing -> very slow as each gameday for each manager is called in serial order

* scrapeTacticsMult() and runIterList()
The parallel version of scrapeTactics(), where the first calls the latter. Gamedays have to be called manually, for each day all Manager IDs are scraped. 
If gameday is aborted during the run, the script on return will only scrape unfinished Manager IDs.

For each PhantomJS instance 10 windows are opened in parallel to scrape information. Each window gets its own Manager list. 
After 1000 calls all 10 windows return a list which is then stored in the DB (this system might be changed in the future by using Queues for each return)

This will not set the flag to "finished" in the KeepTrack DB table -> do this manually or let scrapeTactics() run over it once


* mergeDBs()
scrapeTactics() and scrapeTacticsMult() can be run in parallel using seperated Python processes. However, these should not access the same db with different pointers.
-> The use of seperate DBs is advised.

The result are two or more DBs that need to merged into one again, achieved using this function


### deprecated files

*Selenium_Webscaper.py* and *html_miner_BS.py*  were devloped seperately. The first does the actual 
webscraping and downloads html files, the second extracts the info from these downloaded files and puts it into an SQLite
database. Both are now included in kicker.py and deprecated

*html_miner_xmletree.py* was used to get information from the downloaded html files -> did not work properly and was abandoned early