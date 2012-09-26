""" Base implementation of FCRepoRequestFactory interface.
"""

from fcrepo.http.interfaces import I_FCRepoRequestFactory
from fcrepo.http.interfaces import I_FCRepoResponse
from fcrepo.http.interfaces import I_FCRepoResponseBody


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class B_FCRepoResponseBody(I_FCRepoResponseBody):
    """ Abstract base implementation of I_FCRepoResponseBody interface.
    """

    def __init__(self, raw_data, mime_type):
        self._raw_data = raw_data
        self._mime_type = mime_type

    def getMimeType(self):
        return self._mime_type

    def getRawData(self):
        return self._raw_data


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class B_FCRepoResponse(I_FCRepoResponse):
    """ Abstract base implementation of I_FCRepoResponse interface.
    """

    def getFooter(self, name, default=''):
        return self.getFooters().get(name, default)

    def getHeader(self, name, default=''):
        return self.getHeaders().get(name, default)

    def getRequest(self):
        request = self.getRequestMethod() + ' ' + self.getRequestURI()
        return request


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class B_FCRepoRequestFactory(I_FCRepoRequestFactory):
    """ Abstract base implementation of I_FCRepoRequestFactory interface.
    """

    def __init__(self, repository_url, username='fedoraAdmin',
                       password='fedora', realm='any'):
        self.initRepository(repository_url)
        self.setAuthUser(username)
        self.setAuthPassword(password)
        self.setAuthRealm(realm)
        self._last_request = ''

    def initRepository(self, url):
        slash_slash = url.find('://')
        self.protocol = url[:slash_slash]
        remainder = url[slash_slash+3:]
        colon = remainder.find(':')
        self.setDomain(remainder[:colon])
        remainder = remainder[colon+1:]
        slash = remainder.find('/')
        self.setPort(remainder[:slash])
        remainder = remainder[slash+1:]
        slash = remainder.find('/')
        if slash > -1:
            self.setContext(remainder[:slash])
        else:
            self.setContext(remainder)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAuthPassword(self):
        return self.auth_pwd

    def getAuthRealm(self):
        return self.auth_realm

    def getAuthUser(self):
        return self.auth_user

    def getContext(self):
        return self.context

    def getDomain(self):
        return self.domain

    def getLastRequest(self):
        return self._last_request

    def getPort(self):
        return str(self.port)

    def getProtocol(self):
        return self.protocol

    def getRepositoryURL(self):
        url = self.protocol + '://' + self.domain + ':' + str(self.port)
        url += '/' + self.context
        return url

    def getRequestURL(self, request_uri):
        url = self.getRepositoryURL() 
        if not request_uri.startswith('/'):
            url += '/'
        url += request_uri
        return url

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAuthPassword(self, password):
        self.auth_pwd = password

    def setAuthRealm(self, realm):
        self.auth_realm = realm

    def setAuthUser(self, username):
        self.auth_user = username

    def setContext(self, context):
        if context.startswith('/'):
            context = context[1:]
        if context.endswith('/'):
            context = context[:-1]
        self.context = context

    def setDomain(self, url):
        slash_slash = url.find('://')
        if slash_slash > -1:
            domain = url[slash_slash+3:]
            colon = domain.find(':')
            if colon > -1:
                self.domain = domain[:colon]
        else:
            self.domain = url

    def setPort(self, port):
        self.port  = int(port)

    def setProtocol(self, protocol):
        if '://' in protocol:
            slash_slash = url.find('://')
            protocol = protocol[:slash_slash-1]
        self.protocol = protocol

