from xml.etree import ElementTree
import urllib2
import logging

logger = logging.getLogger("turkic.geolocation")

try:
    import config
except ImportError:
    apikey = None
    logger.warning("API key not automatically loaded")
else:
    apikey = config.geolocation

class Location(object):
    def __init__(self, countrycode, country, region, city, zip, 
                 latitude, longitude, timezone, ip):
        self.countrycode = countrycode
        self.country = country
        self.region = region
        self.city = city
        self.zip = zip
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.ip = ip

    def __repr__(self):
        return "{0}, {1} {2}".format(self.city, self.region, self.country)

cache = {}

def lookup(ip):
    if ip not in cache:
        logger.info("Query for {0}".format(ip))
        response = urllib2.urlopen("http://api.ipinfodb.com/v3/ip-city?"
            "key={0}&ip={1}&format=xml".format(apikey, ip))
        xml = ElementTree.parse(response)

        zip = xml.find("zipCode").text
        latitude = xml.find("latitude").text
        latitude = float(latitude) if latitude else None
        longitude = xml.find("longitude").text
        longitude = float(longitude) if longitude else None

        cache[ip] = Location(countrycode = xml.find("countryCode").text,
                             country = xml.find("countryName").text,
                             region = xml.find("regionName").text,
                             city = xml.find("cityName").text,
                             zip = zip,
                             latitude = latitude,
                             longitude = longitude,
                             timezone = xml.find("timeZone").text,
                             ip = ip)
    return cache[ip]
