#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
awb json api:
https://offenedaten-koeln.de/anfragen/m%C3%BCllabholungstermine-der-abfallwirtschaftsbetriebe-api

street codes:
https://www.offenedaten-koeln.de/dataset/strassenverzeichnis
"""
import logging
from homeassistant.const import (
    CONF_NAME, CONF_VALUE_TEMPLATE,
    STATE_UNKNOWN)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
import voluptuous as vol
import urllib.request
import json
from datetime import datetime
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

DATE_FORMAT = '%Y-%m-%d'
AWB_HOST = 'https://www.awbkoeln.de/sensis/trashdate.php'
AWB_PARAMS = '?streetcode={}&streetnumber={}&startyear={}&endyear={}&startmonth={}&endmonth={}&form=json'
STATE_NONE = 'Keine'
NAMES_DICT = {
    'grey': 'Restm\u00fcll',
    'brown': 'Bio',
    'blue': 'Papier',
    'wertstoff': 'Wertstoff',
    }

CONF_STREET_CODE = 'street_code'
CONF_STREET_NUMBER = 'street_number'
CONF_DAY = 'day'

_QUERY_SCHEME = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_STREET_CODE): cv.string,
    vol.Required(CONF_STREET_NUMBER): cv.string,
    vol.Optional(CONF_DAY): cv.string,
    vol.Optional(CONF_VALUE_TEMPLATE): cv.template
})

def setup_platform(
    hass,
    config,
    add_devices,
    discovery_info=None
    ):
    """Setup the sensor platform."""
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    add_devices([AwbSensor(config.get(CONF_NAME), config.get(CONF_STREET_CODE), config.get(CONF_STREET_NUMBER), config.get(CONF_DAY), value_template)])

class AwbSensor(Entity):

    """Representation of a Sensor."""
    def __init__(self, name, streetCode, streetNumber, day, value_template):
        """Initialize the sensor."""
        self._name = name
        self._streetCode = streetCode 
        self._streetNumber = streetNumber
        self._day = day
        self._value_template = value_template
        self._state = STATE_UNKNOWN
        self._attributes = None

        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        day = datetime.now() + timedelta(days=(0 if self._day == 'today' else 1))
        dayInDelta = day + timedelta(days=30)

        try:
          with urllib.request.urlopen((AWB_HOST + AWB_PARAMS).format(
              self._streetCode,
              self._streetNumber,
              day.year,
              dayInDelta.year,
              day.month,
              dayInDelta.month
              )) as url:
              value_json = json.loads(url.read().decode())
        except:
          _LOGGER.error('API call error')
          return

        trashdates = value_json['trashdates']['trashdate']
        attributes = {}
        for trashdate in trashdates:
            dayDate = datetime.strptime(str(trashdate['year']) + '-' + str(trashdate['month']) + '-' + str(trashdate['day']), DATE_FORMAT)
            typ = NAMES_DICT.get(trashdate['typ'])
            existingTyp = attributes.get(dayDate.strftime(DATE_FORMAT))
            if existingTyp is not None:
                typ = typ + ', ' + existingTyp
            attributes.update({dayDate.strftime(DATE_FORMAT): typ})
        
        attributes.update({'Zuletzt aktualisiert': datetime.now().strftime(DATE_FORMAT + ' %H:%M:%S')})
        data = attributes.get(day.strftime(DATE_FORMAT), "Keine")

        if self._value_template is not None:
            self._state = self._value_template.async_render_with_possible_json_value(
                data, None)
        else:
            self._state = data

        self._attributes = dict(sorted(attributes.items()))
