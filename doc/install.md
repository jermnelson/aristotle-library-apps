Installing Aristotle Library Apps 
---------------------------------

## Background
The Aristotle Library Apps is an open source project licensed under the Apache 
Two. Aristotle Library Apps is based on Django to provide an HTML5 mobile app
environment to a Redis bibliograhic datastore based on a 
[BIBFRAME Datastore](https://github.com/jermnelson/BIBFRAME-Datastore)
set-up . The Aristotle Library Apps project also included interfaces to a 
Fedora Commons Server for digital object storage, and Solr for full-text 
indexing.

## Quick set-up with PIP
These directions work on POSIX based installed systems. We recommend you use
a dedicated Virtual Machine running the lastest version of the 64-bit Ubuntu
server.

1. Create a virtualenv for running Aristotle Library Apps environment with
   the following dependancies installed in the virtualenv **NOTE**: We recommend
   using at least the Python 2.7 version.

   1. Install these open-source projects Django, Sunburnt, lxml, redis, and pymarc

      **pip install django**

      **pip install sunburnt**

      **pip install lxml**

      **pip install pymarc**

      **pip install redis**

      **pip install eulfedora**

      **pip install docutils**

      **pip install beautifulsoup4**

      **pip install flup**

2. Clone Aristotle Library Apps project from GitHub at (https://github.com/jermnelson/aristotle-library-apps)

3. Create or modify a local_settings.py file in the aristotle app directory.
   Make sure that it includes the following settings variables:

      **ACTIVE_APPS = [app names]** A list of active apps in your Django environment

      **INSTITUTION = { }** A python dictionary that should include the institution's name a logo

      **FEDORA_URI = '0.0.0.0'**

      **FEDORA_ROOT = ''**
      
      **FEDORA_USER = ''**

      **FEDORA_PASSWORD = ''**

      **REDIS_MASTER_HOST = '0.0.0.0'**  Or other IP address of running Redis instance

      **SOLR_URL = ''** URL of Solr server
      

4. Follow directions for creating a database for Django admin and
   by Aristotle Library Apps applications.
