from __future__ import with_statement
import sys
import os

#from rhodecode.bin.base import json, api_call
from kallithea.lib.compat import json

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

def main(argv=None):
    #print ','.join(os.environ)
    #print os.environ['RC_SCM_DATA']
    rc_scm_data = json.loads(os.environ['KALLITHEA_EXTRAS'])
    username = rc_scm_data['username']
    repoid = rc_scm_data['repository']
    apihost = rc_scm_data['server_url']

    apikey = 'CHANGEME'
    method = 'get_repo'
    margs = {'repoid': repoid}

    #print 'Calling method %s(%s) => %s' % (method, margs, apihost)

    json_resp = api_call(apikey, apihost, method, **margs)
    if json_resp['error']:
        json_data = json_resp['error']
    else:
        json_data = json_resp['result']

    #print 'Server response \n%s' % (json.dumps(json_data, indent=4, sort_keys=True))
    #print 'members:', json_data['members']

    # if we are the owner, allow pushing
    #if json_data['owner'] == username:
    #    return 0

    # if we, or the default user, have write or admin permissions, allow pushing
    for member in json_data['members']:
        #if (member['username'] == 'default' or member['username'] == username) and (member['permission'] == 'repository.write' or member['permission'] == 'repository.admin'):
        if (member['name'] == 'default' or member['name'] == username) and (member['permission'] == 'repository.write' or member['permission'] == 'repository.admin'):
            return 0

    # otherwise deny pushing
    print 'You do not have the proper permissions to write to this repository! Ask the owner to add you.'
    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
