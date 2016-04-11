# kicker
scripts for scraping the kicker website

*kicker.py* uses functions to scrape the kicker website for Manager Points and Player related data. No html files
are downloaded and saved anymore, information is directly stored in a SQLite DB


*Selenium_Webscaper.py* and *html_miner_BS.py*  were devloped seperately. The first does the actual 
webscraping and downloads html files, the second extracts the info and puts it into an SQLite
database. Both are now included in kicker.py and deprecated

*html_miner_xmletree.py* did not work properly and is not used anymore