# -*- coding: utf8 -*-
# Copyright (c) 2014 by Ecreall under licence AGPL terms
# avalaible on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

from pyramid.view import view_config

from substanced.util import Batch

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.objectofcollaboration.principal.util import get_current
from pontus.view import BasicView

from novaideo.content.processes.novaideo_view_manager.behaviors import SeeHome
from novaideo.content.novaideo_application import NovaIdeoApplication
from novaideo import _
from novaideo.core import BATCH_DEFAULT_SIZE
from novaideo.content.processes import get_states_mapping
from novaideo.views.filter import (
    get_filter, FILTER_SOURCES,
    merge_with_filter_view, find_entities)
from .search import get_default_searchable_content


CONTENTS_MESSAGES = {
    '0': _(u"""No element found"""),
    '1': _(u"""One element found"""),
    '*': _(u"""${nember} elements found""")
}


@view_config(
    name='index',
    context=NovaIdeoApplication,
    renderer='pontus:templates/views_templates/grid.pt',
    )
@view_config(
    name='',
    context=NovaIdeoApplication,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class HomeView(BasicView):
    title = _('Nova-Ideo contents')
    name = ''
    behaviors = [SeeHome]
    template = 'novaideo:views/novaideo_view_manager/templates/search_result.pt'
    anonymous_template = 'novaideo:views/novaideo_view_manager/templates/anonymous_view.pt'
    viewid = 'home'

    def _add_filter(self, user):
        def source(**args):
            default_content = [key[0] for key in
                               get_default_searchable_content(self.request)]
            default_content.remove("person")
            filter_ = {
                'metadata_filter': {'content_types': default_content}
            }
            objects = find_entities(user=user, filters=[filter_], **args)
            return objects

        url = self.request.resource_url(self.context, '@@novaideoapi')
        select = ['metadata_filter', 'geographic_filter',
                  'contribution_filter',
                  ('temporal_filter', ['negation', 'created_date']),
                  'text_filter', 'other_filter']
        return get_filter(
            self,
            url=url,
            source=source,
            select=select,
            filter_source="home")

    def update_anonymous(self):
        values = {}
        result = {}
        body = self.content(
            args=values, template=self.anonymous_template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates: [item]}
        self.title = ''
        self.wrapper_template = 'novaideo:views/novaideo_view_manager/templates/anonymous_view_wrapper.pt'
        return result

    def update(self):
        user = get_current()
        if not self.request.accessible_to_anonymous:
            return self.update_anonymous()

        filter_form, filter_data = self._add_filter(user)
        default_content = [key[0] for key in
                           get_default_searchable_content(self.request)]
        default_content.remove("person")
        validated = {
            'metadata_filter': {'content_types': default_content}
        }
        args = {}
        args = merge_with_filter_view(self, args)
        args['request'] = self.request
        objects = find_entities(
            user=user,
            sort_on='release_date', reverse=True,
            filters=[validated],
            **args)
        url = self.request.resource_url(self.context, '')
        batch = Batch(objects,
                      self.request,
                      url=url,
                      default_size=BATCH_DEFAULT_SIZE)
        batch.target = "#results"
        len_result = batch.seqlen
        index = str(len_result)
        if len_result > 1:
            index = '*'

        self.title = _(CONTENTS_MESSAGES[index],
                       mapping={'nember': len_result})

        filter_instance = getattr(self, 'filter_instance', None)
        filter_body = None
        if filter_instance:
            filter_data['filter_message'] = self.title
            filter_body = filter_instance.get_body(filter_data)

        result_body = []
        for obj in batch:
            render_dict = {'object': obj,
                           'current_user': user,
                           'state': get_states_mapping(user, obj,
                                   getattr(obj, 'state_or_none', [None])[0])}
            body = self.content(args=render_dict,
                                template=obj.templates['default'])['body']
            result_body.append(body)

        result = {}
        values = {'bodies': result_body,
                  'batch': batch,
                  'filter_body': filter_body}
        body = self.content(args=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates: [item]}
        if filter_form:
            result['css_links'] = filter_form['css_links']
            result['js_links'] = filter_form['js_links']

        return result


DEFAULTMAPPING_ACTIONS_VIEWS.update({SeeHome: HomeView})


FILTER_SOURCES.update(
    {"home": HomeView})