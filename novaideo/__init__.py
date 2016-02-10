# -*- coding: utf8 -*-
# Copyright (c) 2015 by Ecreall under licence AGPL terms
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

import logging
from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.i18n import TranslationStringFactory
from pyramid.session import SignedCookieSessionFactory

from substanced.db import root_factory

from dace.util import getSite


log = logging.getLogger('creationculturelle')

_ = TranslationStringFactory('novaideo')


DEFAULT_SESSION_TIMEOUT = 25200


ANALYTICS_DEFAUT_CONTENTS = ['idea', 'proposal']


ACCESS_ACTIONS = {}


def get_access_keys(context):
    declared = context.__provides__.declared
    if declared:
        for data in ACCESS_ACTIONS.get(declared[0], []):
            if data['access_key']:
                return data['access_key'](context)

    return ['always']


def get_novaideo_title():
    return getSite().title


def my_locale_negotiator(request):
    return request.accept_language.best_match(('en', 'fr'), 'fr')


def moderate_ideas(request):
    return getattr(request.root, 'moderate_ideas', False)


def is_idea_box(request):
    return getattr(request.root, 'is_idea_box', False)


def content_to_examine(request):
    return getattr(request.root, 'content_to_examine', [])


def content_to_support(request):
    return getattr(request.root, 'content_to_support', [])


def accessible_to_anonymous(request):
    only_for_members = getattr(request.root, 'only_for_members', False)
    if not only_for_members or \
       (only_for_members and \
        request.user):
        return True

    return False


def analytics_default_content_types(request):
    if request.is_idea_box:
        return ['idea']
    else:
        return list(ANALYTICS_DEFAUT_CONTENTS)


def searchable_contents(request):
    from novaideo.core import SEARCHABLE_CONTENTS
    if getattr(request, 'is_idea_box', False):
        searchable_contents = dict(SEARCHABLE_CONTENTS)
        searchable_contents.pop('proposal')
        return searchable_contents

    return SEARCHABLE_CONTENTS


def evolve_wg(root, registry):
    from novaideo.views.filter import find_entities
    from novaideo.content.interface import IWorkingGroup
    import transaction

    contents = find_entities(interfaces=[IWorkingGroup])
    len_entities = str(len(contents))
    for index, wg in enumerate(contents):
        if hasattr(wg, 'first_decision'):
            wg.first_improvement_cycle = wg.first_decision
            wg.reindex()

        if index % 1000 == 0:
            log.info("**** Commit ****")
            transaction.commit()

        log.info(str(index) + "/" + len_entities)

    log.info('Working groups evolved.')


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=root_factory)
    config.add_request_method(moderate_ideas, reify=True)
    config.add_request_method(content_to_examine, reify=True)
    config.add_request_method(content_to_support, reify=True)
    config.add_request_method(is_idea_box, reify=True)
    config.add_request_method(accessible_to_anonymous, reify=True)
    config.add_request_method(searchable_contents, reify=True)
    config.add_request_method(analytics_default_content_types, reify=True)
    config.add_evolution_step(evolve_wg)
    config.add_translation_dirs('novaideo:locale/')
    config.add_translation_dirs('pontus:locale/')
    config.add_translation_dirs('dace:locale/')
    config.add_translation_dirs('deform:locale/')
    config.add_translation_dirs('colander:locale/')
    config.scan()
    config.add_static_view('novaideostatic',
                           'novaideo:static',
                           cache_max_age=86400)
    #    config.set_locale_negotiator(my_locale_negotiator)
    settings = config.registry.settings
    secret = settings.get('novaideo.secret')
    if secret is None:
        raise ConfigurationError(
            'You must set a novaideo.secret key in your .ini file')

    session_factory = SignedCookieSessionFactory(
        secret,
        timeout=DEFAULT_SESSION_TIMEOUT,
        reissue_time=3600)
    config.set_session_factory(session_factory)
    return config.make_wsgi_app()


DEFAULT_FILES = [
    {'name': 'ml_file',
     'title': _('Legal notices'),
     'description': _('The legal notices'),
     'content': ''},
    {'name': 'terms_of_use',
     'title': _('Terms of use'),
     'description': _('The terms of use'),
     'content': ''}
]
