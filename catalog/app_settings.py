"""
 mod:`app_settings` Discovery App Settings
"""
__author__ = "Jeremy Nelson"

APP = {'current_view': {'title': 'Catalog'},
       'description': '''This is the catalog for bibliographic entities in
the Redis Library Services Platform''',
       'icon_url': 'discovery.png',
       'productivity': False,
       'url': 'catalog/'}

CARRIER_TYPE_GRAPHICS = {'Book':'publishing_48x48.png',
		         'Collection':'file-cabinet_48x48.png',
		         'DVD Video':'cinema_48x48.png',
			 'Electronic':'internet_48x48.png',
			 'Map':'maps_48x48.png',
			 'Manuscript':'creative_writing_48x48.png',
                         'LP Record': 'dj_48x48.png',
                         'Microfilm':'microfilm_48x48.png',
			 'Music CD':'music_48x48.png',
			 'Musical Score':'music_48x48.png',
			 'Music Sound Recordings':'music_48x48.png',
                         'online resource': 'internet_48x48.png',
			 'Photo':'photos_48x48.png',
			 'VHS Video':'cinema_48x48.png'}


PAGINATION_SIZE = 25 # Size of pagination, default is 25
