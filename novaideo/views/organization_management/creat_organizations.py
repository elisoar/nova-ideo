# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import colander
from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.form import FormView
from pontus.schema import Schema, omit, select

from novaideo.content.processes.organization_management.behaviors import (
    CreatOrganizations)
from novaideo.content.novaideo_application import NovaIdeoApplication
from novaideo.content.organization import OrganizationSchema, Organization
from novaideo import _


class CreatOrganizationsSchema(Schema):

    organizations = colander.SchemaNode(
                colander.Sequence(),
                select(omit(OrganizationSchema(factory=Organization,
                                               editable=True,
                                               name='Organization'), 
                            ['_csrf_token_']),
                       ['title',
                        'description',
                        'email',
                        'phone',
                        'fax',
                        'logo',
                        'members']),
                title=_('Organizations to creat')
                )


@view_config(
    name='creatorganizations',
    context=NovaIdeoApplication,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class CreatOrganizationsView(FormView):

    title = _('Creat organizations')
    schema = CreatOrganizationsSchema()
    behaviors = [CreatOrganizations]
    formid = 'formcreatorganizations'
    name = 'creatorganizations'


DEFAULTMAPPING_ACTIONS_VIEWS.update({CreatOrganizations:CreatOrganizationsView})
