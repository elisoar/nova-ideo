# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

from pyramid.httpexceptions import HTTPFound

from dace.util import getSite
from dace.objectofcollaboration.principal.util import has_role
from dace.processinstance.activity import (
    InfiniteCardinality,
    ActionType)
from novaideo.ips.xlreader import create_object_from_xl
from novaideo.content.interface import INovaIdeoApplication, IOrganization
from novaideo.content.organization import Organization
from novaideo import _
from ..user_management.behaviors import global_user_processsecurity
from novaideo.core import acces_action


def add_roles_validation(process, context):
    return False#has_role(role=('Moderator',))


def add_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


class AddOrganizations(InfiniteCardinality):
    style_descriminator = 'admin-action'
    style_picto = 'glyphicon glyphicon-home'
    style_order = 1
    submission_title = _('Save')
    isSequential = True
    context = INovaIdeoApplication
    roles_validation = add_roles_validation
    processsecurity_validation = add_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        xlfile = appstruct['file']['_object_data']
        organizations = create_object_from_xl(file=xlfile, 
                            factory=Organization, 
                            properties={'title':('String', False),
                                        'description':('String', False)})
        root.setproperty('organizations', organizations)
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context))


def creatorg_roles_validation(process, context):
    return has_role(role=('Moderator',))


def creatorg_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


class CreatOrganizations(InfiniteCardinality):
    style_descriminator = 'admin-action'
    style_picto = 'glyphicon glyphicon-home'
    style_order = 2
    submission_title = _('Save')
    isSequential = True
    context = INovaIdeoApplication
    roles_validation = creatorg_roles_validation
    processsecurity_validation = creatorg_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        new_organizations = appstruct['organizations']
        for organization_dict in new_organizations:
            organization = organization_dict['_object_data']
            root.addtoproperty('organizations', organization)
            #send mail

        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, '@@seeorganizations'))


def edit_roles_validation(process, context):
    return has_role(role=('Moderator',))


def edit_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context) and \
           context.organizations


class EditOrganizations(InfiniteCardinality):
    style_descriminator = 'admin-action'
    style_picto = 'glyphicon glyphicon-pencil'
    style_order = 4
    submission_title = _('Save')
    isSequential = True
    context = INovaIdeoApplication
    roles_validation = edit_roles_validation
    processsecurity_validation = edit_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, '@@seeorganizations'))


def seeorgs_roles_validation(process, context):
    return has_role(role=('Collaborator',))


def seeorgs_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context) and \
           context.organizations


class SeeOrganizations(InfiniteCardinality):
    style_descriminator = 'admin-action'
    style_picto = 'glyphicon glyphicon-th-list'
    style_order = 3
    isSequential = False
    context = INovaIdeoApplication
    roles_validation = seeorgs_roles_validation
    processsecurity_validation = seeorgs_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context))


def see_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context) and \
           has_role(role=('Member',))


@acces_action()
class SeeOrganization(InfiniteCardinality):
    isSequential = False
    title = _('Details')
    actionType = ActionType.automatic
    context = IOrganization
    processsecurity_validation = see_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def editorg_roles_validation(process, context):
    return has_role(role=('Moderator',)) or \
           has_role(role=('OrganizationResponsible', context))


def editorg_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


class EditOrganization(InfiniteCardinality):
    isSequential = False
    style_picto = 'glyphicon glyphicon-pencil'
    style_order = 1
    title = _('Edit organization')
    submission_title = _('Save')
    context = IOrganization
    roles_validation = editorg_roles_validation
    processsecurity_validation = editorg_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))

#TODO behaviors
