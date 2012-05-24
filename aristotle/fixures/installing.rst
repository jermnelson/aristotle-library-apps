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

#. (If not using `dotCloud`_) Download and install Redis
  
.. _`Aristotle Library Apps`: https://github.com/jermnelson/aristotle-library-apps
.. _`dotCloud`: "https://www.dotcloud.com/"
.. _`Python`: http://www.python.org/
.. _`Redis`: http://redis.io
.. _`virtualenv`: http://www.virtualenv.org/en/latest/index.html
