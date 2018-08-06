"""
A component which allows you to get information from Untappd.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/sensor.untappd
"""

import logging
import voluptuous as vol
from datetime import timedelta
from dateutil import parser
from datetime import datetime
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (PLATFORM_SCHEMA)

REQUIREMENTS = ['pyuntappd==0.0.5']

__version__ = '0.0.6'

_LOGGER = logging.getLogger(__name__)

CONF_USERNAME = 'username'
CONF_ID = 'id'
CONF_SECRET = 'secret'

COMPONENT_REPO = 'https://github.com/custom-components/sensor.untapped/'

WISHLIST_DATA = 'untappd_wishlist'

ATTR_ABV = 'abv'
ATTR_BEER = 'beer'
ATTR_SCORE = 'score'
ATTR_TOTAL_BADGES = 'total badges'
ATTR_TOTAL_BEERS = 'total beers'
ATTR_TOTAL_CREATED_BEERS = 'total created beers'
ATTR_TOTAL_CHECKINS = 'total checkins'
ATTR_TOTAL_FOLLOWINGS = 'total followings'
ATTR_TOTAL_FRIENDS = 'total friends'
ATTR_TOTAL_PHOTOS = 'total photos'

ATTR_BADGE = 'badge'
ATTR_LEVEL = 'level'
ATTR_DESCRIPTION = 'description'

SCAN_INTERVAL = timedelta(seconds=300)

ICON = 'mdi:untappd'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_ID): cv.string,
    vol.Required(CONF_SECRET): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    _LOGGER.warning('Data provided by Untappd, report any issues to %s', COMPONENT_REPO)
    username = config.get(CONF_USERNAME)
    api_id = config.get(CONF_ID)
    api_secret = config.get(CONF_SECRET)
    add_devices([UntappdCheckinSensor(username, api_id, api_secret)])
    add_devices([UntappdWishlistSensor(hass, username, api_id, api_secret)])
    add_devices([UntappdLastBadgeSensor(hass, username, api_id, api_secret)])

class UntappdCheckinSensor(Entity):
    def __init__(self, username, api_id, api_secret):
        from pyuntappd import Untappd
        self._untappd = Untappd()
        self._username = username
        self._apiid = api_id
        self._apisecret = api_secret
        self._total_badges = None
        self._total_beers = None
        self._total_created_beers = None
        self._total_checkins = None
        self._total_followings = None
        self._total_friends = None
        self._total_photos = None
        self._abv = None
        self._state = None
        self._picture = None
        self.update()

    def update(self):
        current_date = parser.parse(str(datetime.now())).replace(tzinfo=None)
        result = self._untappd.get_last_activity(self._apiid, 
            self._apisecret, self._username)
        if not result :
            return False
        else:
            checkin_date = parser.parse(result['created_at']).replace(tzinfo=None)
            if (current_date - checkin_date).days > 0:
                relative_checkin_date = str((current_date - checkin_date).days + 1) + " days ago"
            elif (current_date - checkin_date).days == 0:
                relative_checkin_date = 'Yesterday'
            else:
                relative_checkin_date = 'Today'

            self._state = relative_checkin_date
            self._beer = result['beer']['beer_name']
            self._score = str(result['rating_score'])
            self._picture = result['beer']['beer_label']
            self._beer_abv = str(result['beer']['beer_abv']) + '%'
        result = self._untappd.get_info(self._apiid, 
            self._apisecret, self._username)
        if not result :
            return False
        else:
            self._total_badges = result['stats']['total_badges']
            self._total_beers = result['stats']['total_beers']
            self._total_checkins = result['stats']['total_checkins']
            self._total_created_beers = result['stats']['total_created_beers']
            self._total_friends = result['stats']['total_friends']
            self._total_followings = result['stats']['total_followings']
            self._total_photos = result['stats']['total_photos']
    
    @property
    def name(self):
        return 'Untappd Last Check-in'

    @property
    def entity_picture(self):
        return self._picture

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        return {
            ATTR_ABV: self._abv,
            ATTR_BEER: self._beer,
            ATTR_SCORE: self._score,
            ATTR_TOTAL_BADGES: self._total_badges,
            ATTR_TOTAL_BEERS: self._total_beers,
            ATTR_TOTAL_CHECKINS: self._total_checkins,
            ATTR_TOTAL_CREATED_BEERS: self._total_created_beers,
            ATTR_TOTAL_FRIENDS: self._total_friends,
            ATTR_TOTAL_FOLLOWINGS: self._total_followings,
            ATTR_TOTAL_PHOTOS: self._total_photos,
        }

class UntappdWishlistSensor(Entity):
    def __init__(self, hass, username, api_id, api_secret):
        from pyuntappd import Untappd
        self.hass = hass
        self._untappd = Untappd()
        self._username = username
        self._apiid = api_id
        self._apisecret = api_secret
        self._total_wishlist = None
        self._state = None
        self.hass.data[WISHLIST_DATA] = {}
        self.update()

    def update(self):
        result = self._untappd.get_wishlist(self._apiid, 
            self._apisecret, self._username)
        if not result :
            return False
        else:
            self._state = result['count']
            for beer in result['items']:
                name = beer['beer']['beer_name']
                beer_label = beer['beer']['beer_label']
                brewery_name = beer['brewery']['brewery_name']
                self.hass.data[WISHLIST_DATA][name] = {
                    "brewery_name": brewery_name,
                    "beer_label": beer_label,
                }

    @property
    def name(self):
        return 'Untappd On The Wishlist'

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        return self.hass.data[WISHLIST_DATA]

class UntappdLastBadgeSensor(Entity):
    def __init__(self, hass, username, api_id, api_secret):
        from pyuntappd import Untappd
        self.hass = hass
        self._untappd = Untappd()
        self._username = username
        self._apiid = api_id
        self._apisecret = api_secret
        self._state = None
        self.update()


    def update(self):
        result = self._untappd.get_badges(self._apiid, 
            self._apisecret, self._username)
        if not result or len(result) < 1 :
            return False
        else:
            current_date = parser.parse(str(datetime.now())).replace(tzinfo=None)
            checkin_date = parser.parse(result[0]['created_at']).replace(tzinfo=None)
            if (current_date - checkin_date).days > 0:
                relative_checkin_date = str((current_date - checkin_date).days + 1) + " days ago"
            elif (current_date - checkin_date).days == 0:
                relative_checkin_date = 'Yesterday'
            else:
                relative_checkin_date = 'Today'

            self._state = relative_checkin_date
            self._badge = result[0]['badge_name']
            self._level = result[0]['levels']['count'] if result[0]['is_level'] else 1
            self._description = result[0]['badge_description']
            self._picture = result[0]['media']['badge_image_sm']

    @property
    def name(self):
        return 'Untappd Last Badge'

    @property
    def entity_picture(self):
        return self._picture

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def device_state_attributes(self):
        return {
            ATTR_BADGE: self._badge,
            ATTR_LEVEL: self._level,
            ATTR_DESCRIPTION: self._description,
        }
