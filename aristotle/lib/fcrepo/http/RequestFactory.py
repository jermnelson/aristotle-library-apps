""" Pure Python Implementation of FCRepoRequestFactory and FCRepoResponse
"""
import base64
from types import StringTypes
from httplib2 import Http

from fcrepo.http.base import B_FCRepoRequestFactory
from fcrepo.http.base import B_FCRepoResponse
from fcrepo.http.base import B_FCRepoResponseBody

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class ResponseBody(B_FCRepoResponseBody):

    def getContent(self):
        if 'text' in self._mime_type:
            return unicode(base64.b64decode(self._raw_data), 'utf-8')
        else:
            return self._raw_data

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class FCRepoResponse(B_FCRepoResponse):

    def __init__(self, repository, http_method, request_uri, response, body):
        self._repository = repository
        self._http_method = http_method
        self._request_uri = request_uri
        self._status = response['status']
        #
        self._headers = {}
        for name, value in response.items():
            self._headers[name] = value
        self._footers = {}
        #
        mime_type = self._headers.get('Content-Type','unknown')
        self._body = ResponseBody(body, mime_type)

    def getBody(self):
        return self._body

    def getFooter(self, name, default=None):
        return self._footers.get(name, default)

    def getFooters(self):
        return self._footers

    def getHeader(self, name, default=None):
        return self._headers.get(name, default)

    def getHeaders(self):
        return self._headers

    def getStatus(self):
        return self._status

    def getRequestMethod(self):
        return self._http_method

    def getRequestURI(self):
        return self._request_uri

    def getRepository(self):
        return self._repository

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class FCRepoRequestFactory(B_FCRepoRequestFactory):

    def DELETE(self, request_uri):
        return self.submit('DELETE', request_uri)

    def GET(self, request_uri):
        return self.submit('GET', request_uri)

    def POST(self, request_uri, content=None, content_type='unknown',
                   chunked=False):
        return self.submit('POST', request_uri, content, content_type, chunked)

    def PUT(self, request_uri, content=None,  content_type='unknown',
                  chunked=False):
        return self.submit('PUT', request_uri, content, content_type, chunked)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def submit(self, method, request_uri, content=None, content_type=None,
                     chunked=False):
        headers = { 'Connection' : 'Keep-Alive'
                  , 'Keep-Alive' : '300'
                  }
        repository = self.getRepositoryURL()
        url = self.getRequestURL(request_uri)
        #
        http = Http()
        #http.add_credentials(self.auth_user, self.auth_pwd, self.domain)
        auth = base64.encodestring("%s:%s" % (self.auth_user, self.auth_pwd))
        headers['Authorization'] = 'Basic ' + auth
        if content is None:
            self._last_request = '%s ' % method + url
            response, body = http.request(url, method, headers=headers)
        else:
            self._last_request = '%s (%s) ' % (method, content_type)  + url
            headers['Content-Type'] = content_type
            headers['Content-Length'] = str(len(content))
            response, body = http.request(url, method, body=content,
                                          headers=headers)
        response = FCRepoResponse(repository, method, request_uri,
                                  response, body)
        return response

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAuthScope(self):
        return (self.domain, self.port, self.auth_realm)

    def getCredentials(self):
        return (self.auth_user, self.auth_pwd)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAuthRealm(self, realm):
        self.auth_realm = realm

