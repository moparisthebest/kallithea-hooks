# Additional mappings that are not present in the pygments lexers
# used for building stats
# format is {'ext':['Names']} eg. {'py':['Python']} note: there can be
# more than one name for extension
# NOTE: that this will overide any mappings in LANGUAGES_EXTENSIONS_MAP
# build by pygments
EXTRA_MAPPINGS = {}

# additional lexer definitions for custom files
# it's overrides pygments lexers, and uses defined name of lexer to colorize the
# files. Format is {'ext': 'lexer_name'}
# List of lexers can be printed running:
# python -c "import pprint;from pygments import lexers;pprint.pprint([(x[0], x[1]) for x in lexers.get_all_lexers()]);"

EXTRA_LEXERS = {}

#==============================================================================
# WHOOSH INDEX EXTENSIONS
#==============================================================================
# if INDEX_EXTENSIONS is [] it'll use pygments lexers extensions by default.
# To set your own just add to this list extensions to index with content
INDEX_EXTENSIONS = []

# additional extensions for indexing besides the default from pygments
# those get's added to INDEX_EXTENSIONS
EXTRA_INDEX_EXTENSIONS = []

# without trailing slash
# CHANGE NEXT TWO VARIABLES, if no auth is required JENKINS_AUTH can be None
JENKINS_URL = 'http://CHANGEME/jenkins'
import base64
JENKINS_AUTH = "Basic {0}".format(base64.b64encode("{0}:{1}".format('CHANGEME-username', 'CHANGEME-apikey')))

def cleanRepoNameJenkins(repo_name):
    if repo_name is None:
        return None
    try:
        # 2 options, either strip off everything before last /, results in possible duplicates
        #return repo_name[repo_name.rindex('/')+1:]
        # or replace all / with _, no duplicates
        return repo_name.replace('/', '_')
    except Exception as e:
        #raise
        return repo_name

# generic helper functions to get and post resources

def getUrl(url, **kwargs):
    #print 'url:', url, 'kwargs:', kwargs
    import urllib2
    req = urllib2.Request(url, **kwargs)
    f = urllib2.urlopen(req)
    ret = f.read().strip()
    f.close()
    return ret

def getJenkins(url, **kwargs):
    if JENKINS_AUTH is not None:
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = JENKINS_AUTH
    return getUrl(JENKINS_URL + url, **kwargs)

def postJenkins(url, **kwargs):
    if 'data' not in kwargs:
        kwargs['data'] = '' # force POST
    return getJenkins(url, **kwargs)

# specific functions to make jenkins do certain things

def deleteJenkins(**kwargs):
    import urllib2
    try:
        postJenkins('/job/%(jenkins_job)s/doDelete' % kwargs)
        output = 'successful!'
    except urllib2.HTTPError as e:
        output = 'Error code '+str(e.code)
    if output:
        print 'Jenkins: Delete job %(jenkins_job)s' % kwargs, output
    return 0

def pollJenkins(**kwargs):
    import urllib2
    try:
        # only supported for mercurial, the second should be supported for everything
        #if kwargs['scm'] == 'hg':
        #    output = getJenkins('/mercurial/notifyCommit?url=%(server_url)s/%(repository)s' % kwargs)
        postJenkins('/job/%(jenkins_job)s/polling' % kwargs)
        output = 'Scheduled polling of %(jenkins_job)s' % kwargs
        output = 'successfully!'
    except urllib2.HTTPError as e:
        output = 'Error code '+str(e.code)
    if output:
        print 'Jenkins: Scheduled polling of %(jenkins_job)s' % kwargs, output
    return 0

def jsonJenkins(url):
    import urllib2, json
    try:
        ret = json.loads(postJenkins(url))
    except urllib2.HTTPError as e:
        ret = "Error code "+str(e.code)
    return ret

def lastBuildStatusJenkins(**kwargs):
    job = jsonJenkins('/job/%(jenkins_job)s/api/json' % kwargs)
    if isinstance(job, basestring):
        print "Jenkins:", job
        return 0
    #print 'jsonJenkins:', job
    lastBuild = job['lastBuild']
    if lastBuild is None:
        print 'Jenkins: No builds yet for', kwargs['jenkins_job']
        return 0
    lastSuccessfulBuild = job['lastSuccessfulBuild']
    if lastSuccessfulBuild is None:
        print 'Jenkins: No successful builds yet for', kwargs['jenkins_job']
        print 'Jenkins: Last build failed: ', lastBuild['url']
        return 0
    if lastBuild['number'] == lastSuccessfulBuild['number']:
        print 'Jenkins: Last build was successful: ', lastBuild['url']
    else:
        print 'Jenkins: Last build failed: ', lastBuild['url']
        print 'Jenkins: Last successful build: ', lastSuccessfulBuild['url']
    return 0

# obviously this can go away when all info is sent into all functions
def getRepoDescription(repo_name):
    try:
        #from rhodecode.bin.base import json, api_call
        from rhodecode.lib.compat import json
        #from rhodecode.tests.api.api_base import api_call

        def api_call(apikey, apihost, method=None, **kw):
            import random
            import urllib2
            import pprint
            """
            Api_call wrapper for RhodeCode.

            :param apikey:
            :param apihost:
            :param format: formatting, pretty means prints and pprint of json
            json returns unparsed json
            :param method:
            :returns: json response from server
            """
            def _build_data(random_id):
                """
                Builds API data with given random ID

                :param random_id:
                """
                return {
                    "id": random_id,
                    "api_key": apikey,
                    "method": method,
                    "args": kw
                }

            if not method:
                raise Exception('please specify method name !')

            id_ = random.randrange(1, 9999)
            req = urllib2.Request('%s/_admin/api' % apihost,
                            data=json.dumps(_build_data(id_)),
                            headers={'content-type': 'text/plain'})
            ret = urllib2.urlopen(req)
            raw_json = ret.read()
            json_data = json.loads(raw_json)
            id_ret = json_data['id']
            if id_ret == id_:
                return json_data

            else:
                _formatted_json = pprint.pformat(json_data)
                raise Exception('something went wrong. '
                                'ID mismatch got %s, expected %s | %s' % (
                                                    id_ret, id_, _formatted_json))

        # CHANGE apikey AND server-name
        apikey = 'CHANGEME'
        json_resp = api_call(apikey, 'http://CHANGEME/hg', 'get_repo', repoid=repo_name)

        # for testing purposes
        #with open('response.txt','a') as f:
            #f.write(json.dumps(json_resp))

        if json_resp['error']:
            return repo_name, None, None
        else:
            response = json_resp['result']
            return response['description'], response['repo_name'], response['fork_of']
    except Exception as e:
        return repo_name, None, None

def createJobJenkins(**kwargs):
    # fix to give us info that should be sent in in future
    if 'repo_name' not in kwargs:
        # called from push or pull, repo exists so just get info
        kwargs['repo_name'] = kwargs['repository']
        kwargs['description'], trash, kwargs['fork_name'] = getRepoDescription(kwargs['repository'])
    else:
        # called from create_repo, repo doesn't exist so must get info from parent and use what we have here
        trash, kwargs['fork_name'], trash = getRepoDescription(kwargs['fork_id'])
    kwargs['fork_jenkins_job'] = cleanRepoNameJenkins(kwargs['fork_name'])

    # for testing purposes
    if 'jenkins_job' not in kwargs:
        kwargs['jenkins_job'] = cleanRepoNameJenkins(kwargs['repo_name'])
    #with open('kwargs.txt','a') as f:
        #f.write('\n---------------------------------------------\nnew kwargs\n')
        #for key, val in kwargs.iteritems():
            #f.write('%s : %s\n' % (key, val))

    # variables we will eventually get from extra_fields, after they are copied over from forks
    # CHANGE THE NEXT 3 VARIABLES
    create_jenkins_job = True
    # default config for projects without fork
    config_xml_url = 'http://CHANGEME/config.xml'
    config_replacements = {
        # should we just always do this one?
        '<description>.*<\/description>':'<description>%(description)s</description>',
        # you might want to include these for a default config
        'JOBNAME':'%(repo_name)s',
        'ARTIFACTS_TO_ARCHIVE':'**/target/*.war,**/target/*.ear,**/target/*.jar',
        # this is definitly specific to our company, removing all permission restrictions
        '<hudson.security.AuthorizationMatrixProperty>.*<\/hudson.security.AuthorizationMatrixProperty>':'',
        }
    if not create_jenkins_job:
        return False
    #print 'jenkins_job: %(jenkins_job)s description: %(description)s' % kwargs
    import urllib2, re
    try:
        config = None
        if kwargs['fork_jenkins_job'] is not None:
            try:
                # then we will get the config from there, and replace it
                config = getJenkins('/job/%(fork_jenkins_job)s/config.xml' % kwargs)
                config_replacements[kwargs['fork_jenkins_job']] = '%(jenkins_job)s'
                config_replacements[kwargs['fork_name']] = '%(repo_name)s'
            except Exception as e:
                config = None
        if config == None:
            config = getUrl(config_xml_url)
        for key, replacement in config_replacements.iteritems():
            #config = config.replace(key, replacement)
            config = re.compile(key, re.DOTALL).sub(replacement, config)
        #config = re.sub('<description>.*<\/description>', '<description>%(description)s</description>', config)
        config = config % kwargs
        #print "Jenkins config:", config,
        postJenkins('/createItem?name=%(jenkins_job)s' % kwargs, data=config, headers={'Content-type':'text/xml'})
        print 'Jenkins: Create job %(jenkins_job)s successful!' % kwargs
        return True
    except urllib2.HTTPError:
        #print 'Jenkins: Create job %(jenkins_job)s failed, maybe it already exists?' % kwargs
        return False

#==============================================================================
# POST CREATE REPOSITORY HOOK
#==============================================================================
# this function will be executed after each repository is created
def _crhook(*args, **kwargs):
    """
    Post create repository HOOK
    kwargs available:
     :param repo_name:
     :param repo_type:
     :param description:
     :param private:
     :param created_on:
     :param enable_downloads:
     :param repo_id:
     :param user_id:
     :param enable_statistics:
     :param clone_uri:
     :param fork_id:
     :param group_id:
     :param created_by:
    """
    kwargs['jenkins_job'] = cleanRepoNameJenkins(kwargs['repo_name'])
    createJobJenkins(**kwargs)
    return 0
CREATE_REPO_HOOK = _crhook


#==============================================================================
# POST DELETE REPOSITORY HOOK
#==============================================================================
# this function will be executed after each repository deletion
def _dlhook(*args, **kwargs):
    """
    Post create repository HOOK
    kwargs available:
     :param repo_name:
     :param repo_type:
     :param description:
     :param private:
     :param created_on:
     :param enable_downloads:
     :param repo_id:
     :param user_id:
     :param enable_statistics:
     :param clone_uri:
     :param fork_id:
     :param group_id:
     :param deleted_by:
     :param deleted_on:
    """
    kwargs['jenkins_job'] = cleanRepoNameJenkins(kwargs['repo_name'])
    deleteJenkins(**kwargs)
    return 0
DELETE_REPO_HOOK = _dlhook


#==============================================================================
# POST PUSH HOOK
#==============================================================================

# this function will be executed after each push it's executed after the
# build-in hook that RhodeCode uses for logging pushes
def _pushhook(*args, **kwargs):
    """
    Post push hook
    kwargs available:

      :param server_url: url of instance that triggered this hook
      :param config: path to .ini config used
      :param scm: type of VS 'git' or 'hg'
      :param username: name of user who pushed
      :param ip: ip of who pushed
      :param action: push
      :param repository: repository name
      :param pushed_revs: list of pushed revisions
    """
    kwargs['jenkins_job'] = cleanRepoNameJenkins(kwargs['repository'])
    if not createJobJenkins(**kwargs):
        lastBuildStatusJenkins(**kwargs)
    pollJenkins(**kwargs)
    return 0
PUSH_HOOK = _pushhook


#==============================================================================
# POST PULL HOOK
#==============================================================================

# this function will be executed after each push it's executed after the
# build-in hook that RhodeCode uses for logging pulls
def _pullhook(*args, **kwargs):
    """
    Post pull hook
    kwargs available::

      :param server_url: url of instance that triggered this hook
      :param config: path to .ini config used
      :param scm: type of VS 'git' or 'hg'
      :param username: name of user who pulled
      :param ip: ip of who pulled
      :param action: pull
      :param repository: repository name
    """
    kwargs['jenkins_job'] = cleanRepoNameJenkins(kwargs['repository'])
    createJobJenkins(**kwargs)
    # turns out output from this function isn't visible to the user, so might as well just run create...
    #if not createJobJenkins(**kwargs):
    #    lastBuildStatusJenkins(**kwargs)
    return 0
PULL_HOOK = _pullhook
