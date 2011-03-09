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
        response = urllib2.urlopen("http://api.ipinfodb.com/v2/ip_query.php?"
            "key={0}&ip={1}&timezone=true".format(apikey, ip))
        xml = ElementTree.parse(response)

        zip = xml.find("ZipPostalCode").text
        zip = int(zip) if zip else None
        latitude = xml.find("Latitude").text
        latitude = float(latitude) if latitude else None
        longitude = xml.find("Longitude").text
        longitude = float(longitude) if longitude else None

        cache[ip] = Location(countrycode = xml.find("CountryCode").text,
                             country = xml.find("CountryName").text,
                             region = xml.find("RegionName").text,
                             city = xml.find("City").text,
                             zip = zip,
                             latitude = latitude,
                             longitude = longitude,
                             timezone = xml.find("TimezoneName").text,
                             ip = ip)
    return cache[ip]
