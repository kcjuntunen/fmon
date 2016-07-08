from random import randint
import json

config = {
    "email" : {
        "server" : "",
        "sender" : "",
        "passwd" : ""
    },
    "id_info" : {
        "uuid" : "338e1134-4364-11e6-b3b2-080027d5fb8e",
        "store" : "The office",
        "fixture" : "a desk"
    },
    "sensors" :
    [
        {
            "sensor" : "obstruction",
            "type" : "timeseries"
        },
        {
            "sensor" : "reed_switch2",
            "type" : "event"
        },
        {
            "sensor" : "light_level",
            "type" : "timeseries"
        },
        {
            "sensor" : "humidity",
            "type" : "timeseries"
        },
        {
            "sensor" : "temperature",
            "type" : "timeseries"
        },
        {
            "sensor" : "pressure",
            "type" : "timeseries"
        },
        {
            "sensor" : "PIR",
            "type" : "event"
        },
        {
            "sensor" : "volts",
            "type" : "timeseries"
        },
        {
            "sensor" : "amps",
            "type" : "timeseries"
        }
    ],
    "serial" : {
        "port" : "/dev/ttyAMA0",
        "baudrate" : 115200
    }
}

# config = {
#     "email" : {
#         "server" : "",
#         "sender" : "",
#         "passwd" : ""
#     },
#     "id_info" : {
#         "uuid" : "338e1134-4364-11e6-b3b2-080027d5fb8e",
#         "store" : "The office",
#         "fixture" : "a desk"
#     },
#     "sensors" :
#     [
#         {
#             "sensor" : "obstruction",
#             "type" : "timeseries"
#         },
#         {
#             "sensor" : "reed_switch2",
#             "type" : "event"
#         },
#         {
#             "sensor" : "light_level",
#             "type" : "timeseries"
#         },
#         {
#             "sensor" : "humidity",
#             "type" : "timeseries"
#         },
#         {
#             "sensor" : "temperature",
#             "type" : "timeseries"
#         },
#         {
#             "sensor" : "pressure",
#             "type" : "timeseries"
#         },
#         {
#             "sensor" : "PIR",
#             "type" : "event"
#         },
#         {
#             "sensor" : "volts",
#             "type" : "timeseries"
#         },
#         {
#             "sensor" : "amps",
#             "type" : "timeseries"
#         }
#     ],
#     "serial" : {
#         "port" : "/dev/ttyAMA0",
#         "baudrate" : 115200
#     }
# }

_al1 = {
    "active" : True,
    "friendly_name" : "brightness",
    "limits" :
    { "days" : 124,
      "daystart" : 540,
      "dayend" : 1050 },
    "ltgt" : [  880,  1000 ],
    "message" : "<html><head></head><body><imgsrc=\"http: //a.dryicons.com/images/icon_sets/colorful_stickers_part_2_icons_set/png/256x256/light_bulb.png\"><br>Lightlow@{}<br>Store: {}<br>Fixture: {}<br>Value: {}</body></html>",
    "recipients" : [  "kcjuntunen@amstore.com" ],
    "sensor" : "light_level" }
_al2 = {
     "active" : True,
     "friendly_name" : "thermometer",
     "limits" :
     { "days" : 124,
       "daystart" : 540,
       "dayend" : 1050 },
     "ltgt" : [  80,  90 ],
     "message" : "{} {} {} {}",
     "recipients" : [  "kcjuntunen@amstore.com" ],
     "sensor" : "temperature" }
alerts = [_al1, _al2]

json_string = '{' + ','.join(['"{}": {}'.format(sensor['sensor'], randint(-100, 1000))
                              for sensor in config['sensors'] if sensor['type'] == 'timeseries']) + '}'

js = json.loads(json_string)
j1 = js.copy()
j1['light_level'] = 950
light_transgressing = j1
j2 = js.copy()
j2['light_level'] = 200
light_not_transgressing = j2
