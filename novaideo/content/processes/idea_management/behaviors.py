# -*- coding: utf8 -*-
import datetime
from pyramid.httpexceptions import HTTPFound

from dace.util import (
    getSite,
    getBusinessAction,
    copy)
from dace.objectofcollaboration.principal.util import has_any_roles, grant_roles, get_current
from dace.processinstance.activity import InfiniteCardinality, ActionType

from novaideo.ips.mailer import mailer_send
from novaideo.content.interface import INovaIdeoApplication, Iidea
from ..user_management.behaviors import global_user_processsecurity
from novaideo.mail import PRESENTATION_IDEA_MESSAGE
from novaideo import _


def createidea_relation_validation(process, context):
    return True


def createidea_roles_validation(process, context):
    return has_any_roles(roles=('Member',))


def createidea_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def createidea_state_validation(process, context):
    return True


class CreateIdea(InfiniteCardinality):
    context = INovaIdeoApplication
    relation_validation = createidea_relation_validation
    roles_validation = createidea_roles_validation
    processsecurity_validation = createidea_processsecurity_validation
    state_validation = createidea_state_validation

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        keywords_ids = appstruct.pop('keywords')
        result, newkeywords = root.get_keywords(keywords_ids)
        for nk in newkeywords:
            root.addtoproperty('keywords', nk)

        result.extend(newkeywords)
        idea = appstruct['_object_data']
        root.addtoproperty('ideas', idea)
        idea.setproperty('keywords_ref', result)
        idea.state.append('to work')
        grant_roles(roles=(('Owner', idea), ))
        idea.setproperty('author', get_current())
        self.newcontext = idea
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def duplicate_relation_validation(process, context):
    return True


def duplicate_roles_validation(process, context):
    return True


def duplicate_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context) and \
           ((has_any_roles(roles=(('Owner', context), )) and not ('abandoned' in context.state)) or 'published' in context.state)


def duplicate_state_validation(process, context):
    return True


class DuplicateIdea(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    context = Iidea
    relation_validation = duplicate_relation_validation
    roles_validation = duplicate_roles_validation
    processsecurity_validation = duplicate_processsecurity_validation
    state_validation = duplicate_state_validation

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        copy_of_idea = copy(context)
        copy_of_idea.created_at = datetime.datetime.today()
        copy_of_idea.modified_at = datetime.datetime.today()
        keywords_ids = appstruct.pop('keywords')
        result, newkeywords = root.get_keywords(keywords_ids)
        for nk in newkeywords:
            root.addtoproperty('keywords', nk)

        result.extend(newkeywords)
        appstruct['keywords_ref'] = result
        files = [f['_object_data'] for f in appstruct.pop('attached_files')]
        appstruct['attached_files'] = files
        copy_of_idea.set_data(appstruct)
        root.addtoproperty('ideas', copy_of_idea)
        copy_of_idea.addtoproperty('originalideas', context)
        copy_of_idea.setproperty('version', None)
        copy_of_idea.setproperty('nextversion', None)
        copy_of_idea.state = ['to work']
        copy_of_idea.setproperty('author', get_current())
        grant_roles(roles=(('Owner', copy_of_idea), ))
        self.newcontext = copy_of_idea
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def del_relation_validation(process, context):
    return True


def del_roles_validation(process, context):
    return has_any_roles(roles=(('Owner', context),))


def del_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def del_state_validation(process, context):
    return ('abandoned' in context.state)


class DelIdea(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    context = Iidea
    relation_validation = del_relation_validation
    roles_validation = del_roles_validation
    processsecurity_validation = del_processsecurity_validation
    state_validation = del_state_validation

    def start(self, context, request, appstruct, **kw):
        root  = getSite()
        root.delproperty('ideas', context)
        return True

    def redirect(self, context, request, **kw):
        root = getSite()
        return HTTPFound(request.resource_url(root))


def edit_relation_validation(process, context):
    return True


def edit_roles_validation(process, context):
    return has_any_roles(roles=(('Owner', context),))


def edit_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def edit_state_validation(process, context):
    return not ("published" in context.state) and not("Archived" in context.state)


class EditIdea(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    context = Iidea
    relation_validation = edit_relation_validation
    roles_validation = edit_roles_validation
    processsecurity_validation = edit_processsecurity_validation
    state_validation = edit_state_validation

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        copy_of_idea = copy(context)
        copy_of_idea.created_at = datetime.datetime.today()
        copy_of_idea.modified_at = datetime.datetime.today()
        files = [f['_object_data'] for f in appstruct.pop('attached_files')]
        appstruct['attached_files'] = files
        keywords_ids = appstruct.pop('keywords')
        result, newkeywords = root.get_keywords(keywords_ids)
        for nk in newkeywords:
            root.addtoproperty('keywords', nk)

        result.extend(newkeywords)
        appstruct['keywords_ref'] = result
        copy_of_idea.set_data(appstruct)
        context.state = ['Archived']
        copy_of_idea.setproperty('version', context)
        root.addtoproperty('ideas', copy_of_idea)
        copy_of_idea.setproperty('author', get_current())
        grant_roles(roles=(('Owner', copy_of_idea), ))
        grant_roles(roles=(('Owner', context), ))#TODO attribute SubstanceD.Folder.moving
        user = get_current()
        self.newcontext = copy_of_idea
        if 'abandoned' in copy_of_idea.state:
            recuperate_actions = getBusinessAction('ideamanagement',
                                                   'recuperate',
                                                   '',
                                                    request,
                                                    copy_of_idea)
            if recuperate_actions:
                recuperate_actions[0].execute(copy_of_idea, request, appstruct, **kw)

        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def pub_relation_validation(process, context):
    return True


def pub_roles_validation(process, context):
    return has_any_roles(roles=(('Owner', context),))


def pub_processsecurity_validation(process, context):
    if getattr(context, 'originalideas', None):
        orignial_ideas = getattr(context, 'originalideas')
        for orignial_idea in orignial_ideas:
            if orignial_idea.text == context.text:
                return False

    return global_user_processsecurity(process, context)


def pub_state_validation(process, context):
    return 'to work' in context.state


class PublishIdea(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    context = Iidea
    relation_validation = pub_relation_validation
    roles_validation = pub_roles_validation
    processsecurity_validation = pub_processsecurity_validation
    state_validation = pub_state_validation

    def start(self, context, request, appstruct, **kw):
        context.state.remove('to work')
        context.state.append('published')
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def ab_relation_validation(process, context):
    return True


def ab_roles_validation(process, context):
    return has_any_roles(roles=(('Owner', context),))


def ab_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def ab_state_validation(process, context):
    return 'to work' in context.state


class AbandonIdea(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    context = Iidea
    relation_validation = ab_relation_validation
    roles_validation = ab_roles_validation
    processsecurity_validation = ab_processsecurity_validation
    state_validation = ab_state_validation

    def start(self, context, request, appstruct, **kw):
        context.state.remove('to work')
        context.state.append('abandoned')
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def re_relation_validation(process, context):
    return True


def re_roles_validation(process, context):
    return has_any_roles(roles=(('Owner', context),))


def re_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def re_state_validation(process, context):
    return 'abandoned' in context.state


class RecuperateIdea(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    context = Iidea
    relation_validation = re_relation_validation
    roles_validation = re_roles_validation
    processsecurity_validation = re_processsecurity_validation
    state_validation = re_state_validation

    def start(self, context, request, appstruct, **kw):
        context.state.remove('abandoned')
        context.state.append('to work')
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def comm_relation_validation(process, context):
    return True


def comm_roles_validation(process, context):
    return has_any_roles(roles=('Member',))


def comm_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def comm_state_validation(process, context):
    return 'published' in context.state


class CommentIdea(InfiniteCardinality):
    isSequential = False
    context = Iidea
    relation_validation = comm_relation_validation
    roles_validation = comm_roles_validation
    processsecurity_validation = comm_processsecurity_validation
    state_validation = comm_state_validation

    def start(self, context, request, appstruct, **kw):
        comment = appstruct['_object_data']
        context.addtoproperty('comments', comment)
        comment.setproperty('author', comment)
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def present_relation_validation(process, context):
    return True


def present_roles_validation(process, context):
    return has_any_roles(roles=(('Owner', context),))


def present_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def present_state_validation(process, context):
    return 'published' in context.state


class PresentIdea(InfiniteCardinality):
    context = Iidea
    relation_validation = present_relation_validation
    roles_validation = present_roles_validation
    processsecurity_validation = present_processsecurity_validation
    state_validation = present_state_validation

    def start(self, context, request, appstruct, **kw):
        members = appstruct['members']
        exterior_emails = appstruct['exterior_emails']
        user = get_current()
        user_title=getattr(user, 'user_title',''),
        user_first_name=getattr(user, 'first_name', user.name)
        user_last_name=getattr(user, 'last_name','')
        url = request.resource_url(context, "@@index")
        for member in members:
            message = PRESENTATION_IDEA_MESSAGE.format(
                member_title=getattr(user, 'user_title',''),
                member_first_name=getattr(user, 'first_name', member.name),
                member_last_name=getattr(user, 'last_name',''),
                idea_url=url,
                user_title=user_title,
                user_first_name=user_first_name,
                user_last_name=user_last_name
                 )
            mailer_send(subject='Présentation : '+context.title, recipients=[member.email], body=message)

        for email in exterior_emails:
            message = PRESENTATION_IDEA_MESSAGE.format(
                member_title='',
                member_first_name='',
                member_last_name='',
                idea_url=url,
                user_title=user_title,
                user_first_name=user_first_name,
                user_last_name=user_last_name
                 )
            mailer_send(subject='Présentation : '+context.title, recipients=[email], body=message)


        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def associate_relation_validation(process, context):
    return True


def associate_roles_validation(process, context):
    return True


def associate_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context) and \
           (has_any_roles(roles=(('Owner', context),)) or \
           (has_any_roles(roles=('Member',)) and 'published' in context.state))


def associate_state_validation(process, context):
    return True


class Associate(InfiniteCardinality):
    context = Iidea
    relation_validation = associate_relation_validation
    roles_validation = associate_roles_validation
    processsecurity_validation = associate_processsecurity_validation
    state_validation = associate_state_validation

    def start(self, context, request, appstruct, **kw):
        correlation = appstruct['_object_data']
        correlation.setproperty('source', context)
        root = getSite()
        root.addtoproperty('correlations', correlation)
        self.newcontext = correlation
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))

def seeidea_relation_validation(process, context):
    return True


def seeidea_roles_validation(process, context):
    return True


def seeidea_processsecurity_validation(process, context):
    return (has_any_roles(roles=(('Owner', context),)) or 'published' in context.state)


def seeidea_state_validation(process, context):
    return True


class SeeIdea(InfiniteCardinality):
    title = _('Details')
    context = Iidea
    actionType = ActionType.automatic
    relation_validation = seeidea_relation_validation
    roles_validation = seeidea_roles_validation
    processsecurity_validation = seeidea_processsecurity_validation
    state_validation = seeidea_state_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def seecompare_relation_validation(process, context):
    return True


def seecompare_roles_validation(process, context):
    return has_any_roles(roles=(('Owner', context),))


def seecompare_processsecurity_validation(process, context):
    return getattr(context, 'version', None) is not None


def seecompare_state_validation(process, context):
    return True


class CompareIdea(InfiniteCardinality):
    title = _('Compare')
    context = Iidea
    relation_validation = seeidea_relation_validation
    roles_validation = seeidea_roles_validation
    processsecurity_validation = seeidea_processsecurity_validation
    state_validation = seeidea_state_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


#TODO behaviors
