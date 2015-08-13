#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################################################
#
# Developer: francois.schnell   francois.schnell@gmail.com
#                               http://francois.schnell.free.fr
#            Nicolas Alt
#
# Contributors, see: http://code.google.com/p/gpicsync/wiki/Contributions
#
# This script is released under the GPL license version 2 license
#
###############################################################################

"""
GPicSync is a geolocalisation tool to synchronise data from a GPS and a camera.
USAGE (preparation):
- Synchronize the time on your GPS and camera.
- Leave your GPS always ON (taking a track log) when outdoor
- After coming back extract the track-log of the day in your GPS and save it as
  a .gpx file(with a freeware like easygps on windows or another software)

USAGE (command line):
---------------------

python gpicsync-kml.py -d myfoderWithPictures -g myGpxFile.gpx -o UTCoffset

Generates a KML file from a GPX file and geo-tagged images.
Thumbnails are generated with ImageMagick convert  / dcraw (for raw images).
This script does not perform geotagging; use gpicsync.py before.
For more options type gpicsync.py --help
"""

import gettext,time,datetime

try: import pytz
except ImportError: pass

from geoexif import *
from gpx import *
from kmlGen import *


def getFileList(dir):
    for fileName in sorted(os.listdir ( dir )):
        if (fnmatch.fnmatch ( fileName, '*.JPG' )
         or fnmatch.fnmatch ( fileName, '*.jpg' )
         or fnmatch.fnmatch ( fileName, '*.TIF' )
         or fnmatch.fnmatch ( fileName, '*.tif' )
         or fnmatch.fnmatch ( fileName, '*.CR2' )
         or fnmatch.fnmatch ( fileName, '*.cr2' )
         or fnmatch.fnmatch ( fileName, '*.CRW' )
         or fnmatch.fnmatch ( fileName, '*.crw' )
         or fnmatch.fnmatch ( fileName, '*.NEF' )
         or fnmatch.fnmatch ( fileName, '*.nef' )
         or fnmatch.fnmatch ( fileName, '*.PEF' )
         or fnmatch.fnmatch ( fileName, '*.pef' )
         or fnmatch.fnmatch ( fileName, '*.RAW' )
         or fnmatch.fnmatch ( fileName, '*.raw' )
         or fnmatch.fnmatch ( fileName, '*.ORF' )
         or fnmatch.fnmatch ( fileName, '*.orf' )
         or fnmatch.fnmatch ( fileName, '*.DNG' )
         or fnmatch.fnmatch ( fileName, '*.dng' )
         or fnmatch.fnmatch ( fileName, '*.RAF' )
         or fnmatch.fnmatch ( fileName, '*.raf' )
         or fnmatch.fnmatch ( fileName, '*.MRW' )
         or fnmatch.fnmatch ( fileName, '*.mrw' )
         or fnmatch.fnmatch ( fileName, '*.RW2' )
         or fnmatch.fnmatch ( fileName, '*.rw2' )):
            yield fileName, options.dir+'/'+fileName

def getTimeUTC(pic, UTCoffset, timezone=None):
    picDateTimeSize=pic.readDateTimeSize()
    if picDateTimeSize[0]=="nodate":
        return [" : WARNING: DIDN'T GEOCODE, no Date/Time Original in this picture.", ""]

    # create a proper datetime object (self.shot_datetime)
    pict=(picDateTimeSize[0]+":"+picDateTimeSize[1]).split(":")
    #print ">>> picture original date/time from EXIF: ",pict
    pic_datetime=datetime.datetime(int(pict[0]), int(pict[1]), int(pict[2]), int(pict[3]), int(pict[4]), int(pict[5]))
    #print ">>> self.pic_datetime (from picture EXIF): ",self.pic_datetime
    pic_datetimeUTC = pic_datetime-datetime.timedelta(seconds=UTCoffset*3600)
    if timezone:
        tz = pytz.timezone(timezone)
        pic_datetimeUTC = tz.localize(self.pic_datetimeUTC).astimezone(pytz.utc).replace(tzinfo=None)
    return pic_datetimeUTC

if __name__=="__main__":
    import os,sys,fnmatch
    from optparse import OptionParser
    import gettext
    gettext.install("gpicsync-GUI", "None")

    parser=OptionParser()
    parser.add_option("-d", "--directory",dest="dir", default=".",
     help="Directory containing the pictures. Expl. mypictures")
    parser.add_option("-g", "--gpx",dest="gpx",
     help="Path to the gpx file. Expl. mypicture/tracklog.gpx")
    parser.add_option("-r", "--range",dest="timerange", default=3600,
     help="Max. time difference between GPS point and image (in seconds)")
    parser.add_option("-o", "--offset",dest="offset", default=0,
     help="A positive or negative number to indicate offset hours\
    to the greenwich meridian (East positive, West negative, 1 for France)")
    parser.add_option("-z", "--timezone", dest="timezone",
     help="A Time Zone name in which the photos have been taken (Europe/Paris for France).")
    #parser.add_option("--tcam",dest="tcam",
    # help="Actual time of the camera only if it was out of sync with the gps \
    # Expl. 09:34:02")
    #parser.add_option("--tgps",dest="tgps",
    # help="Actual time of the GPS only if it was out of sync with the camera \
    #Expl. 10:06:00")
    #parser.add_option("--qr-time-image",dest="qr_time_image",
    # help="Image with QR code with time from GPS phone with same camera to \
    # calculate offset or 'auto' to detect the image automatically")
    parser.add_option("--kml",dest="kml", default=None,
     help="Name of KML file")

    (options,args)=parser.parse_args()

    #if options.qr_time_image is not None and (options.offset is not None 
    #    or options.timezone is not None or options.tcam is not None 
    #        or options.tgps is not None):
    #    print >> sys.stderr, "You cannot specify any time options along with --qr-time-image"
    #    sys.exit(1)
    #if options.tcam==None: options.tcam="00:00:00"
    #if options.tgps==None: options.tgps="00:00:00"
    if options.offset is not None and options.timezone is not None:
        print >> sys.stderr, "You cannot specify both timezone and offset. Please choose one."
        sys.exit(1)
    if options.gpx==None:
        print >> sys.stderr, "I need a .gpx file \nType Python gpicsync.py -h for help."
        sys.exit(1)
    options.gpx=[options.gpx]
    print "\nEngage processing using the following arguments ...\n"
    print "-Directory containing the pictures:",options.dir
    print "-Path to the gpx file:",options.gpx
    print "-Timerange:", int(options.timerange)
    if options.timezone:
        print "-Time Zone name:",options.timezone
    else:
        print "-UTC Offset (hours):",options.offset
    print "\n"

    myGpx=Gpx(options.gpx)
    track=myGpx.extract()
    print "Track with", len(track), "points, ", track[0]["datetime"] , "to", track[-1]["datetime"], "UTC"

    files = list(getFileList(options.dir))

    # Create KML header
    if options.kml is None:
        kml_file = options.dir + "/" + os.path.splitext(os.path.basename(options.gpx[0]))[0]
    else:
        kml_file = options.kml
    name = os.path.splitext(os.path.basename(options.gpx[0]))[0]
    print "Writing KML file: "+ kml_file
    localKml=KML(kml_file, name, utc=options.offset,
        timeStampOrder=True, eleMode=0, iconsStyle=0,gmaps=False)
    localKml.writeInKml("\n<Folder>\n<name>Photos</name>")

    # Create thumbs directory
    try:
        os.mkdir(options.dir+'/thumbs')
    except:
        print "Couldn't create the thumbs folder, it maybe already exist"

    # Iterate through image files
    for fileName, filePath in files:
        print fileName,
        pic = GeoExif(filePath)
        pic_time = getTimeUTC(pic, int(options.offset))
        pic_time_size=pic.readDateTimeSize()
        pic_w,pic_h=int(pic_time_size[2]),int(pic_time_size[3])
        print "(", pic_time, "): ",
        israw = not (fnmatch.fnmatch (fileName, '*.JPG') or fnmatch.fnmatch (fileName, '*.jpg') or \
            fnmatch.fnmatch (fileName, '*.TIF') or fnmatch.fnmatch (fileName, '*.tif'))

        # Check if picture is in time range of track
        if (pic_time + datetime.timedelta(0,int(options.timerange))) >= track[0]["datetime"] and \
            (pic_time - datetime.timedelta(0,int(options.timerange))) <= track[-1]["datetime"]:
            latlon = pic.readLatLong()
            if latlon is not None:
                latlon = latlon.split(" ")
                if latlon[0][0] == 'S': latlon[0] = "-" + latlon[0][1:]
                else: latlon[0] = latlon[0][1:]
                if latlon[1][0] == 'W': latlon[1] = "-" + latlon[1][1:]
                else: latlon[1] = latlon[1][1:]
                print latlon

                # Create Thumbnail
                thumbfile = "thumbs/"+"thumb_" + fileName + ".jpg"
                if not israw:
                    print "Creating thumbnail with convert...",
                    ret = os.system("convert '%s' -auto-orient -resize 320 '%s'" % \
                        (options.dir+'/'+fileName, options.dir+"/"+thumbfile))
                    print "ok" if (ret == 0) else "failed"
                else:
                    print "Creating thumbnail with dcraw+convert...",
                    ret = os.system("dcraw -w -c '%s' | convert - -resize 640 '%s'" % 
                        (options.dir+'/'+fileName, options.dir+"/"+thumbfile))
                    print "ok" if (ret == 0) else "failed"
                    # Get width/height (orientation might have changed)
                    if ret  == 0:
                        thumb=GeoExif( options.dir+"/"+thumbfile)
                        thumb_time_size=thumb.readDateTimeSize()
                        pic_w,pic_h=int(thumb_time_size[2]),int(thumb_time_size[3])

                # Add KML placemark
                #scale=float(800.0/max(pic_w,pic_h))
                timeStamp = pic_time_size[0].replace(":","-") + "T" + pic_time_size[1]
                localKml.placemark(options.dir+'/'+fileName, thumbName=thumbfile, useThumb=israw,
                    lat=latlon[0], long=latlon[1], timeStamp=timeStamp,
                    width=pic_w,height=pic_h) #, elevation=result[6]);

                print

            else:
                print "not geo-coded"
                continue
        else:
            print "not in time range of track"

       
    localKml.writeInKml("</Folder>\n")
    print "Adding the GPS track log to the Google Earth kml file..."
    localKml.path(options.gpx, cut=10000)
    localKml.close()

    print "Finished"
