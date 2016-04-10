# kicker
scripts for scraping the kicker website

Right now, *Selenium_Webscaper.py* and *html_miner_BS.py*  are the main files. The first does the actual 
webscraping and downloads html files, the second extracts the info and puts it into an SQLite
database

*kicker.py* will combine both and will be the only file needed in the future. No html files
are downloaded, information is directly stored in the DB

*html_miner_xmletree.py* did not work properly and is not used anymore