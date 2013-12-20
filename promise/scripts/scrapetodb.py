import os
import sys
import datetime

import transaction

import simplejson

import requests

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Base,
    Promise,
    GithubUser,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    client_id = settings['github_client_id']
    client_secret = settings['github_client_secret']

    endpoint = "https://api.github.com/repos/Sinar/ElectionPromises/issues"
    headers = {'Accept': 'application/vnd.github.beta+json',
               'User-Agent': 'Sinar-Promise-App'}
    params = {'client_id': client_id,
              'client_secret': client_secret,
              'page': 1}

    promise_list = []
    print('Downloading issues...')
    while True:
        resp = requests.get(endpoint, params=params, headers=headers)
        issues = simplejson.loads(resp.text)
        if not issues:
            break

        promise_list.extend(issues)
            
        params['page'] += 1
    print('Download done!')

    session = DBSession()

    user_cache = {}
    print('Processing to db...')
    for p in promise_list:
        user_d = p['user']
        user_login = user_d['login']

        user = user_cache.get(user_login)

        if not user:
            user = (session.query(GithubUser)
                    .filter(GithubUser.login==user_d['login'])
                    .first())

            if not user:
                user = GithubUser()
                user.login = user_d['login']
                user.html_url = user_d['html_url']
                user.avatar_url = user_d['avatar_url']
                user.last_updated = datetime.datetime.now()
                session.add(user)
                session.flush()

            user_cache[user_login] = user

        promise = (session.query(Promise)
                   .filter(Promise.number==int(p['number']))
                   .first())

        if not promise or promise.has_update(p['updated_at']):
            if not promise:
                promise = Promise()
                session.add(promise)
            
            promise.title = p['title']
            promise.state = p['state']
            promise.number = int(p['number'])
            promise.html_url = p['html_url']
            promise.github_created_at = p['created_at']
            promise.github_updated_at = p['updated_at']
            promise.github_user = user
            promise.last_updated = datetime.datetime.now()
            session.flush()

    transaction.commit()
    print('Done!')