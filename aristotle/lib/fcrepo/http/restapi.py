""" Python implmentation of the REST API for the Fedora Repository. It is
    framework independent in that all it requires is an HTTP module with
    a FCRepoRequestFactory class and a FCRepoPesponse class.

    The imported FCRepoFactory needs to provide only a constructor and
    four methods :
        GET    : takes a sinlge argument, the method URI
        PUT    : takes two arguments, the method URI and content
        POST   : takes two arguments, the method URI and content
        DELETE : takes a sinlge argument, the method URI
    The FCRepoFactory constructor must take at least four arguments :
       repository_url = base URL of the Fedora Repository instance, for
                        example 'http://localhost:8080/fedora'
       username = name of a user that is authorized to execute methods
                  of the REST API
       password = password the the authorized user
       realm = authorization realm 
"""

from exceptions import NotImplementedError
from types import StringTypes

from fcrepo.http.RequestFactory import FCRepoRequestFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
class FCRepoRestAPI:

    METHOD_PARAMS = { }
    RETURN_STATUS = { }
    FORMAT_AS_XML = [ ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self, repository_url='http://localhost:8080/fedora',
                       username='fedoraAdmin', password='fedora',
                       realm='any', namespace='fedora'):
        self.repository_url= repository_url
        self.username = username
        self.password = password
        self.auth_realm = realm
        self.namespace = namespace

    def guessMimeType(self, content):
        # make a very simplistic guess at strings
        if type(content) in StringTypes:
            if content.rfind('</html>') > 0:
                return 'text/html'
            elif content.rfind('</xhtml>') > 0:
                return 'text/xhtml'
            else:
                less = content.count('<')
                more = content.count('>')
                if less == more:
                    return 'text/xml'
                else:
                    return 'text/plain'
        # don't even attempt to figure out all possible Mime Types
        return 'unknown'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getRequestFactory(self):
        return FCRepoRequestFactory(self.repository_url, self.username,
                                    self.password, self.auth_realm)

    def paramsAsURI(self, method_name, params, ignore=()):
        valid_params = self.METHOD_PARAMS[method_name]
        uri = ''
        for name in params:
            if name in valid_params and name not in ignore:
                if uri: uri += '&'
                uri += name + '=' + self.urlSafeString(params[name])
        if method_name in self.FORMAT_AS_XML and 'format' not in params:
            if uri: uri += '&'
            uri += 'format=xml'
        return uri

    def urlSafeString(self, text):
        return text.replace(' ','%20')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def describeRepository(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addDatastream(self, pid, dsID, **kwargs):
        uri = '/objects/' + pid + '/datastreams/' + dsID
        param_uri = self.paramsAsURI('addDatastream', kwargs,
                                     ignore=('content',))
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        content = kwargs.get('content', None)
        mime_type = kwargs.get('mimeType',None)
        if mime_type is None:
            mime_type = self.guessMimeType(content)
        return repo.POST(uri, content, mime_type)

    METHOD_PARAMS['addDatastream'] = ( 'controlGroup', 'dsLocation', 'altIDs'
                                     , 'dsLabel', 'versionable', 'dsState'
                                     , 'formatURI', 'checksumType', 'checksum'
                                     , 'mimeType', 'logMessage'
                                     )
    RETURN_STATUS['addDatastream'] = '201'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addRelationship(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def compareDatastreamChecksum(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def export(self, pid, **kwargs):
        uri = '/objects/' + pid + '/export'
        param_uri = self.paramsAsURI('export', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)

    METHOD_PARAMS['export'] = ('format', 'context', 'encoding')
    RETURN_STATUS['export'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def findObjects(self, **kwargs):
        uri = '/objects?'
        if 'query' in kwargs:
            uri += 'query=' + kwargs['query']
        elif 'terms' in kwargs:
            uri += 'terms=' + kwargs['terms']
        else:
            uri += 'terms=*' 
        if 'resultFormat' in kwargs:
            uri += '&resultFormat=' + kwargs['resultFormat']
        else:
            uri += '&resultFormat=xml'
        param_uri = self.paramsAsURI('findObjects', kwargs,
                                     ignore=('terms','query','resultFormat'))
        if len(param_uri) < 2:
            param_uri = 'pid=true&label=true'
        uri += '&' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)

    METHOD_PARAMS['findObjects'] = ( 'terms', 'query', 'maxResults'
                                   , 'resultFormat', 'pid', 'label', 'state'
                                   , 'ownerid', 'cDate'  'mDate', 'dcnDate'
                                   , 'title', 'creator', 'subject'
                                   , 'description', 'publisher', 'contributor'
                                   , 'date', 'type', 'format', 'identifier'
                                   , 'source', 'language', 'relation'
                                   , 'coverage', 'rights'
                                   )
    RETURN_STATUS['findObjects'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDatastream(self, pid, dsID, **kwargs):
        uri = '/objects/' + pid + '/datastreams/' + dsID
        param_uri = self.paramsAsURI('getDatastream', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)

    FORMAT_AS_XML.append('getDatastream')
    METHOD_PARAMS['getDatastream'] = ('format', 'asOfDateTime')    
    RETURN_STATUS['getDatastream'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDatastreamHistory(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDatastreamDissemination(self, pid, dsID, **kwargs):
        uri = '/objects/' + pid + '/datastreams/' + dsID + '/content'
        param_uri = self.paramsAsURI('getDatastreamDissemination', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)

    METHOD_PARAMS['getDatastreamDissemination'] = ('asOfDateTime',)    
    RETURN_STATUS['getDatastreamDissemination'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDatastreams(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDissemination(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getNextPID(self, **kwargs):
        uri = '/objects/nextPID'
        param_uri = self.paramsAsURI('getNextPID', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.POST(uri)

    FORMAT_AS_XML.append('getNextPID')
    METHOD_PARAMS['getNextPID'] = ('numPIDs', 'namespace', 'format')    
    RETURN_STATUS['getNextPID'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getObjectHistory(self, pid, **kwargs):
        uri = '/objects/' + pid + '/versions'
        param_uri = self.paramsAsURI('getObjectHistory', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)

    FORMAT_AS_XML.append('getObjectHistory')
    METHOD_PARAMS['getObjectHistory'] = ('format',)    
    RETURN_STATUS['getObjectHistory'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getObjectProfile(self, **kwargs):
        if 'pid' not in kwargs:
            return None
        uri = '/objects/' + pid
        param_uri = self.paramsAsURI('getObjectProfile', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)

    FORMAT_AS_XML.append('getObjectProfile')
    METHOD_PARAMS['getObjectProfile'] = ('asOfDateTime','format',)    
    RETURN_STATUS['getObjectProfile'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getObjectXML(self, pid, **kwargs):
        uri = '/objects/' + pid + '/objectXML'
        repo = self.getRequestFactory()
        return repo.GET(uri)

    METHOD_PARAMS['getObjectXML'] = ()
    RETURN_STATUS['getObjectXML'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getRelationships(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ingest(self, pid='new', **kwargs):
        uri = '/objects/' + pid
        param_uri = self.paramsAsURI('ingest', kwargs,
                                     ignore=('pid', 'content'))
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        content = kwargs.get('content', None)
        return repo.POST(uri, content, 'text/xml')

    METHOD_PARAMS['ingest'] = ( 'label', 'format', 'encoding', 'namespace'
                              , 'ownerId', 'logMessage', 'ignoreMime'
                              , 'content'
                              )
    RETURN_STATUS['ingest'] = '201'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def listDatastreams(self, pid, **kwargs):
        uri = '/objects/' + pid + '/datastreams'
        param_uri = self.paramsAsURI('listDatastreams', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)
 
    FORMAT_AS_XML.append('listDatastreams')
    METHOD_PARAMS['listDatastreams'] = ('format', 'asOfDateTime')
    RETURN_STATUS['listDatastreams'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def listMethods(self, pid, **kwargs):
        uri = '/objects/' + pid + '/methods'
        param_uri = self.paramsAsURI('listMethods', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)
 
    FORMAT_AS_XML.append('listMethods')
    METHOD_PARAMS['listMethods'] = ('format', 'asOfDateTime')
    RETURN_STATUS['listMethods'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def modifyDatastream(self, pid, dsID, **kwargs):
        uri = '/objects/' + pid+ '/datastreams/' + dsID
        param_uri = self.paramsAsURI('modifyDatastream', kwargs,
                                     ignore=('content',))
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        content = kwargs.get('content', None)
        mime_type = kwargs.get('mimeType',None)
        if mime_type is None:
            mime_type = self.guessMimeType(content)
        return repo.POST(uri, content, mimetype)

    METHOD_PARAMS['modifyDatastream'] = ( 'dsLocation', 'altIDs', 'dsLabel'
                                        , 'versionable', 'dsState', 'formatURI'
                                        , 'checksumType', 'checksum'
                                        , 'mimeType', 'logMessage', 'force'
                                        , 'ignoreContent', 'content'
                                        )
    RETURN_STATUS['modifyDatastream'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def modifyObject(self, pid, **kwargs):
        uri = '/objects/' + pid
        param_uri = self.paramsAsURI('modifyObject', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.PUT(uri)

    METHOD_PARAMS['modifyObject'] = ('label', 'ownerId', 'state', 'logMessage')
    RETURN_STATUS['modifyObject'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def purgeDatastream(self, pid, dsID, **kwargs):
        uri = '/objects/' + pid + '/datastreams/' + dsID
        param_uri = self.paramsAsURI('purgeDatastream', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.DELETE(uri)

    METHOD_PARAMS['purgeDatastream'] = ( 'startDT', 'endDT', 'logMessage'
                                       , 'force'
                                       )
    RETURN_STATUS['purgeDatastream'] = '204'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def purgeObject(self, pid, **kwargs):
        uri = '/objects/' + pid
        param_uri = self.paramsAsURI('purgeObject', kwargs)
        if param_uri:
            uri += '?' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.DELETE(uri)

    METHOD_PARAMS['purgeObject'] = ( 'logMessage', 'force')
    RETURN_STATUS['purgeObject'] = '204'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def purgeRelationship(self, **kwargs):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def resumeFindObjects(self, **kwargs):
        uri = '/objects?'
        if 'query' in kwargs:
            uri += 'query=' + kwargs['query']
        elif 'terms' in kwargs:
            uri += 'terms=' + kwargs['terms']
        else:
            uri += 'terms=*' 
        if 'resultFormat' in kwargs:
            uri += '&resultFormat=' + kwargs['resultFormat']
        else:
            uri += '&resultFormat=xml'
        param_uri = self.paramsAsURI('findObjects', kwargs,
                                     ignore=('terms','query','resultFormat'))
        if len(param_uri) < 2:
            param_uri = 'pid=true&label=true'
        uri += '&' + param_uri
        #
        repo = self.getRequestFactory()
        return repo.GET(uri)

    METHOD_PARAMS['resumeFindObjects'] = ( 'sessionToken', 'terms', 'query'
                                         , 'maxResults', 'resultFormat', 'pid'
                                         , 'label', 'state', 'ownerid', 'cDate'
                                         , 'mDate', 'dcnDate', 'title'
                                         , 'creator', 'subject', 'description'
                                         , 'publisher', 'contributor', 'date'
                                         , 'type', 'format', 'identifier'
                                         , 'source', 'language', 'relation'
                                         , 'coverage', 'rights'
                                         )
    RETURN_STATUS['resumeFindObjects'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setDatastreamState(self, pid, dsID, **kwargs):
        uri = '/objects/' + pid + '/datastreams/' + dsID
        state = kwargs.get('dsState', 'A')
        if len(state) < 1:
            state = state[0]
        uri += '?dsState=' + state
        #
        repo = self.getRequestFactory()
        return repo.PUT(uri)

    METHOD_PARAMS['setDatastreamState'] = ('dsState',)
    RETURN_STATUS['setDatastreamState'] = '200'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setDatastreamVersionable(self, pid, dsID, **kwargs):
        uri = '/objects/' + pid + '/datastreams/' + dsID
        versionable = kwargs.get('versionable', 'true')
        if type(versionable) == type(True):
            if versionable:
                versionable = 'true'
            else:
                versionable = 'false'
        uri += '?versionable=' + versionable
        #
        repo = self.getRequestFactory()
        return repo.PUT(uri)

    METHOD_PARAMS['setDatastreamVersionable'] = ('versionable',)
    RETURN_STATUS['setDatastreamVersionable'] = '200'

