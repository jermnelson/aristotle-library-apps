""" Interfaces for FCRepoRequestFactory, FCRepoResponse and FCRepoResponseBody.
"""

from exceptions import NotImplementedError


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class I_FCRepoResponseBody:

    def __init__(self, raw_content, mime_type):
        """ Constructor takes tow arguments :
            raw_content = raw body content (Base64 encoded).
            mime_type = MimeTyoe of the body content.
        """
        raise NotImplementedError

    def getContent(self):
        """ Returns the reponse body properly formatted for the MimeType.
        """
        raise NotImplementedError

    def getMimeType(self):
        """ Returns the MimeType of the body content.
        """
        raise NotImplementedError

    def getRawData(self):
        """ Returns the raw response body (Base64 encoded).
        """
        raise NotImplementedError


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class I_FCRepoResponse:

    def __init__(self):
        # init method args are implementation-dependent
        pass

    def getBody(self):
        """ Provides accces to body content enclosed in the response
        """
        raise NotImplementedError

    def getFooter(self, name, default):
        """ Returns value of a response footer parameter. Takes two arguments:
            name = name of the parameter
            default = default value to be returned when parameter is NOT
                      in the footer.
        """
        raise NotImplementedError

    def getFooters(self):
        """ Returns all response footer parameters as a Python dictionary.
        """
        raise NotImplementedError

    def getHeader(self, name, default):
        """ Returns value of a response header parameter. Takes two arguments:
            name = name of the parameter
            default = default value to be returned when parameter is NOT
                      in the header.
        """
        raise NotImplementedError

    def getHeaders(self):
        """ Returns all response header parameters as a Python dictionary.
        """
        raise NotImplementedError

    def getStatus(self):
        """ Returns the HTTP status code returned for the request.
        """
        raise NotImplementedError

    def getRequestMethod(self):
        """ Returns the name of the HTTP method used for the request.
        """
        raise NotImplementedError

    def getRequestURI(self):
        """ Returns the complete escaped URI used for the request.
        """
        raise NotImplementedError

    def getRequest(self):
        """ Returns the reguest method and the complete escaped request
        URI as a single string.
        """
        raise NotImplementedError


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class I_FCRepoRequestFactory:

    def __init__(self, repository_url, username, password, realm='any'):
        """ Requires at least four arguments:
            repository_url = the base URL for the Fedora Repository
                             including the protocol, domain, port, 
                             and context.
            username = name of a user that is authorized to perform
                       requests using the Fedora REST API.
            password = password for the authorized user.
            realm = authorization realm, must ak=llow the string 'any' to
                    designate that authentication is valid for anty realm.
        """
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def DELETE(self, request_uri):
        """ Submits a DELETE request for the requested URI.
        Takes a single argument:
            request_uri = the query portion of the DELETE request
                          i.e. the URL for the request without the protocol,
                          domain, port and context of the Fedora Repository.
        Returns results of the request as a FCRepoResponse object.
        """
        raise NotImplementedError

    def GET(self, request_uri):
        """ Submits a GET request for the requested URI
        Takes a single argument:
            request_uri = the query portion of the DELETE request
                          i.e. the URL for the request without the protocol,
                          domain, port and context of the Fedora Repository.
        """
        raise NotImplementedError

    def POST(self, request_uri, content=None, chunked=False):
        """ Submits a POST request for the requested URI
        Takes a three arguments:
            request_uri = the query portion of the DELETE request
                          i.e. the URL for the request without the protocol,
                          domain, port and context of the Fedora Repository.
            content = contet to be include in POST request (if any)
            chunked = boolean indiciating whether contant is to be provided
                      in chunks.
        """
        raise NotImplementedError

    def PUT(self, request_uri, content=None, chunked=False):
        """ Submits a PUT request for the requested URI
        Takes a three arguments:
            request_uri = the query portion of the DELETE request
                          i.e. the URL for the request without the protocol,
                          domain, port and context of the Fedora Repository.
            content = contet to be include in POST request (if any)
            chunked = boolean indiciating whether contant is to be provided
                      in chunks.
        """
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAuthPassword(self):
        """ Returns current value of password to be used for authenticating
        access to the Fedora Repository (as set in the constructor or by
        the setAuthPassword method).
        """
        raise NotImplementedError

    def getAuthRealm(self):
        """ Returns current value of realm to be used for authenticating
        access to the Fedora Repository (as set in the constructor or by
        the setAuthRealm method).
        """
        raise NotImplementedError

    def getAuthUser(self):
        """ Returns current value of the username to be used for
        authenticating access to the Fedora Repository (as set in the
        constructor or by the setAuthUser method).
        """
        raise NotImplementedError

    def getContext(self):
        """ Returns current value of the context to be used for accesssing
        the Fedora Repository (as initialized by the constructor or
        set by the setContext method).
        """
        raise NotImplementedError

    def getDomain(self):
        """ Returns current value of the internat domain to be used for
        accesssing the Fedora Repository (as initialized by the constructor
        or set by the setDomain method).
        """
        raise NotImplementedError

    def getPort(self):
        """ Returns current value of the port to be used for accesssing
        the Fedora Repository (as initialized by the constructor or set
        by the setPort method).
        """
        raise NotImplementedError

    def getProtocol(self):
        """ Returns current value of the HTTP protocol to be used for
        accesssing the Fedora Repository (as initialized by the constructor
        or set by the setProtocol method).
        """
        raise NotImplementedError

    def getRepositoryURL(self):
        """ Returns current value of the root URL to be used for accesssing
        the Fedora Repository. It is constructed from the current values
        of the HTTP protocol, repository domain name, port number and
        repository context.
        """
        raise NotImplementedError

    def getLastRequest(self):
        """ Returns a string representing the last HTTP Request that was
        submitted by the factory. It will include the HTTP method and the
        URL submitted. PUT and POST request strings will NOT include the
        content submitted with the request.
        """
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAuthPassword(self, password):
        """ Changes the value of the password to be used for authenticating
        access to the Fedora Repository.
        """
        raise NotImplementedError

    def setAuthRealm(self, realm):
        """ Changes the value of the realm to be used for authenticating
        access to the Fedora Repository.
        """
        raise NotImplementedError

    def setAuthUser(self, username):
        """ Changes the name of the user to be used for authenticating
        access to the Fedora Repository.
        """
        raise NotImplementedError

    def setContext(self, context):
        """ Changes the value of the context to be used for accessing
        the Fedora Repository.
        """
        raise NotImplementedError

    def setDomain(self, url):
        """ Changes the value of the domain to be used for accesssing
        the Fedora Repository.
        """
        raise NotImplementedError

    def setPort(self, port):
        """ Changes the value of the port used to be used for accesssing
        the Fedora Repository.
        """
        raise NotImplementedError

    def setProtocol(self, protocol):
        """ Changes the value of the HTTP protocol to be used for accesssing
        the Fedora Repository.
        """
        raise NotImplementedError

