MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = ''
MONGO_PASSWORD = ''
MONGO_DBNAME = 'arduinolog'

RESOURCE_METHODS = ['GET', 'POST', 'DELETE']
ITEM_METHODS = ['GET']

CACHE_CONTROL = 'max-age=20'
CACHE_EXPIRES = 20

timeseriesdata = {
    'item_title': 'snapshot',
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'name'
    },
    'datasource': {
        'default_sort': [('ts_hour', -1)]
    },
    'schema': {
        'name': {
            'type': 'string',
        },
        'ts_hour': {
            'type': 'datetime',
        },
        'values': {
            'type': 'list',
            'schema': {
                'type': 'float'
            },
        },
    }
}

eventdata = {
    'item_title': 'event',
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'name'
    },
    'datasource': {
        'default_sort': [('ts', -1)]
    },
    'schema': {
        'name': {
            'type': 'string',
        },
        'ts': {
            'type': 'datetime',
        },
        'value': {
            'type': 'float',
        },
    },
}

DOMAIN = {
    'timeseriesdata': timeseriesdata,
    'eventdata': eventdata,
}
