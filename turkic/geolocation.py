from xml.etree import ElementTree
import urllib2

try:
    import config
except ImportError:
    apikey = None
else:
    apikey = config.geolocationkey

class Location(object):
    def __init__(self, countrycode, country, region, city, zip, 
                 latitude, longitutde, timezone, ip):
        self.countrycode = countrycode
        self.country = country
        self.region = region
        self.city = city
        self.zip = zip
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.ip = ip

cache = {}

def lookup(ip):
    if ip not in cache:
        response = urllib2.urlopen("http://api.ipinfodb.com/v2/ip_query.php?"
            "key={0}&ip={1}&timezone=true".format(apikey, ip))
        xml = ElementTree.parse(response)
        cache[ip] = Location(countrycode = xml.find("CountryCode").text,
                             country = xml.find("CountryName").text,
                             region = xml.find("RegionName").text,
                             city = xml.find("City").text,
                             zip = int(xml.find("ZipPostalCode").text),
                             latitude = float(xml.find("Latitude").text),
                             longitude = float(xml.find("Longitude").text),
                             timezone = xml.find("TimezoneName").text,
                             ip = ip)
    return cache[ip]
