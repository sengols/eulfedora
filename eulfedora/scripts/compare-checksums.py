#!/usr/bin/env python

# file eulfedora/scripts/compare-checksums.py
# 
#   Copyright 2012 Emory University Libraries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
from collections import defaultdict
from eulfedora.server import Repository
from getpass import getpass
import logging
from logging import config

logger = logging.getLogger(__name__)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'basic': {
            'format': '[%(asctime)s] %(levelname)s:%(name)s::%(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
         },
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'basic'
        },
    },
    'loggers': {
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # 'eulfedora': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },
        # 'eulxml': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },
    }
}

config.dictConfig(LOGGING)


def main():

    parser = argparse.ArgumentParser(description='''Validate datastream checksums
    for Fedora repository content.  By default, iterates through all objects that
    are findable by the findObjects REST API and checks all datastreams.
    ''')
    parser.add_argument('pids', metavar='PID', nargs='*',
                        help='list specific pids to be checked (optional)')
    parser.add_argument('--fedora-root', dest='fedora_root', required=True,
                        help='URL for accessing fedora, e.g. http://localhost:8080/fedora/')
    parser.add_argument('--fedora-user', dest='fedora_user', default=None, 
                        help='Fedora username (requires permission to run compareDatastreamChecksum)')
    # TODO: make both options available?
    # prompt for password, but allow passing on command-line in dev/staging
    # parser.add_argument('--fedora-password', dest='fedora_password',
    #                      action=PasswordAction, default=None)
    parser.add_argument('--fedora-password', dest='fedora_password', metavar='PASSWORD',
                        default=None, help='Password for the specified Fedora user')
    args = parser.parse_args()

    
    stats = defaultdict(int)

    repo = Repository(args.fedora_root, args.fedora_user, args.fedora_password)

    if args.pids:
        # if pids were specified on the command line, use those
        objects = (repo.get_object(pid) for pid in args.pids)
    else:
        # otherwise, process all find-able objects
        objects = repo.find_objects()
    
    for obj in objects:
        for dsid in obj.ds_list.iterkeys():
            stats['ds'] += 1
            dsobj = obj.getDatastreamObject(dsid)
            if not dsobj.validate_checksum():
                print "%s/%s has an invalid checksum" % (obj.pid, dsid)
                stats['invalid_ds'] += 1

            # TODO: check if checksum type is DISABLED / checksum value none
            
        stats['objects'] += 1

    print '\nTested %(ds)d datastream(s) on %(objects)d object(s)' % stats
    print 'Found %(invalid_ds)d invalid checksum(s)' % stats


class PasswordAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, getpass())

    


if __name__ == '__main__':
    main()
