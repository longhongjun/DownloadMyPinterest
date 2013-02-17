This is a simple Python script that will download a copy of your (or anyone else's!) Pinterest boards: the images, their captions, and (if applicable) the URL of the original source, organized like so:

PinterestData
  PinterestUsername
    BoardName
      index.html with the pins and their info from that board
      image files


Last tested on 2/17/2013, but subject to break inelegantly whenever Pinterest changes their site markup.

From a command line with Python2.7 installed (it will probably work with most Python2.x but I haven't tested it), usage is:

$ python ./PinterestScraper.py <Pinterest username> <path to folder you want the downloaded Pin folders and files to be saved in>

