=================================
Aristotle Library Apps Installing
=================================
The `Aristotle Library Apps`_ is a Python Django project that can run
on multiple platforms but requires the following open-source technologies
to run correctly.

#. Download and install `Python`_ version 2.6 or above (but not Python 3)
   on your computer. If you have a Macintosh or Linux computer, this
   requirement is already fulfilled.

#. Download and extract `Aristotle Library Apps`_ zip file from the 
   Githup repository at `<https://github.com/jermnelson/aristotle-library-apps/zipball/master>`_
  
#. Create a Python virtual enviroment using `virtualenv`_. 

#. From the command-line, change to the `Aristotle Library Apps`_ root director
   and run the following::
   
      pip install -r requirements.txt

#. Download and install Redis, for Linux and Macintosh, follow the `Redis
   installation directions`_. If you are using Windows, download this
   experimental Window's port of `Redis`_ `here`_.
   
#. Start the `Redis`_ server::

     redis-server

#. In a separate command-line window, start `Django`_ with this command::

      python manage.py runserver
      
#. Your new Library App environment will now be live at port 8000 on your
   computer; i.e. http://localhost:8000/
  
.. _`Aristotle Library Apps`: https://github.com/jermnelson/aristotle-library-apps
.. _`Django`: https://www.djangoproject.com/
.. _`dotCloud`: https://www.dotcloud.com/
.. _`here`: /static/RedisWinDebug20120510.zip
.. _`Python`: http://www.python.org/
.. _`Redis`: http://redis.io
.. _`Redis installation directions`: http://redis.io/download
.. _`virtualenv`: http://www.virtualenv.org/en/latest/index.html

