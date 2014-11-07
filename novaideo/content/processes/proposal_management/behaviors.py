# -*- coding: utf8 -*-
import datetime
from bs4 import BeautifulSoup
from persistent.list import PersistentList
from pyramid.httpexceptions import HTTPFound
from pyramid.threadlocal import get_current_registry
from pyramid import renderers
from substanced.util import get_oid

from dace.util import (
    getSite,
    copy,
    get_obj)
from dace.objectofcollaboration.principal.util import (
    has_role, 
    grant_roles, 
    get_current, 
    revoke_roles)
#from dace.objectofcollaboration import system
from dace.processinstance.activity import InfiniteCardinality, ElementaryAction
from pontus.dace_ui_extension.interfaces import IDaceUIAPI

from novaideo.ips.mailer import mailer_send
from novaideo.content.interface import (
    INovaIdeoApplication, 
    IProposal, 
    ICorrection, 
    Iidea)
from ..user_management.behaviors import global_user_processsecurity
from novaideo.mail import (
    ALERT_SUBJECT,
    ALERT_MESSAGE,
    RESULT_VOTE_AMENDMENT_SUBJECT,
    RESULT_VOTE_AMENDMENT_MESSAGE,
    PUBLISHPROPOSAL_SUBJECT,
    PUBLISHPROPOSAL_MESSAGE,
    VOTINGPUBLICATION_SUBJECT,
    VOTINGPUBLICATION_MESSAGE,
    VOTINGAMENDMENTS_SUBJECT,
    VOTINGAMENDMENTS_MESSAGE,
    WITHDRAW_SUBJECT,
    WITHDRAW_MESSAGE,
    PARTICIPATE_SUBJECT,
    PARTICIPATE_MESSAGE,
    RESIGN_SUBJECT,
    RESIGN_MESSAGE,
    WATINGLIST_SUBJECT,
    WATINGLIST_MESSAGE)

from novaideo import _
from novaideo.content.proposal import Proposal
from ..comment_management.behaviors import VALIDATOR_BY_CONTEXT
from novaideo.content.correlation import Correlation
from novaideo.content.token import Token
from novaideo.content.amendment import Amendment
from novaideo.content.working_group import WorkingGroup
from novaideo.content.processes.idea_management.behaviors import (
    PresentIdea, 
    CommentIdea, 
    Associate as AssociateIdea)
from novaideo.utilities.text_analyzer import ITextAnalyzer


try:
    basestring
except NameError:
    basestring = str

DEFAULT_NB_CORRECTORS = 1

def createproposal_roles_validation(process, context):
    return has_role(role=('Member',))


def createproposal_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def associate_to_proposal(related_ideas, proposal, add_idea_text=True):
    root = getSite()
    datas = {'author': get_current(),
             'source': proposal,
             'comment': '',
             'intention': 'Creation'}
    for idea in related_ideas:
        correlation = Correlation()
        datas['targets'] = [idea]
        correlation.set_data(datas)
        correlation.tags.extend(['related_proposals', 'related_ideas'])
        correlation.type = 1
        root.addtoproperty('correlations', correlation)
        if add_idea_text:
            proposal.text = getattr(proposal, 'text', '') + \
                            ('<div>' + idea.text + '</div>')


class CreateProposal(ElementaryAction):
    context = INovaIdeoApplication
    roles_validation = createproposal_roles_validation
    processsecurity_validation = createproposal_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        keywords_ids = appstruct.pop('keywords')
        related_ideas = appstruct.pop('related_ideas')
        result, newkeywords = root.get_keywords(keywords_ids)
        for nkw in newkeywords:
            root.addtoproperty('keywords', nkw)

        result.extend(newkeywords)
        proposal = appstruct['_object_data']
        root.addtoproperty('proposals', proposal)
        proposal.setproperty('keywords_ref', result)
        proposal.state.append('draft')
        grant_roles(roles=(('Owner', proposal), ))
        grant_roles(roles=(('Participant', proposal), ))
        proposal.setproperty('author', get_current())
        self.process.execution_context.add_created_entity('proposal', proposal)
        wg = WorkingGroup()
        root.addtoproperty('working_groups', wg)
        wg.setproperty('proposal', proposal)
        wg.addtoproperty('members', get_current())
        wg.state.append('deactivated')
        if related_ideas:
            associate_to_proposal(related_ideas, proposal)

        proposal.reindex()
        wg.reindex()
        self.newcontext = proposal
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def pap_processsecurity_validation(process, context):
    if getattr(context, 'originalentity', None):
        originalentity = getattr(context, 'originalentity')
        if originalentity.text == context.text:
            return False

    return ('to work' in context.state) and has_role(role=('Owner', context))  or \
           (('published' in context.state) and has_role(role=('Member',)))


class PublishAsProposal(ElementaryAction):
    style = 'button' #TODO add style abstract class
    context = Iidea
    style_descriminator = 'global-action'
    style_picto = 'glyphicon glyphicon-file'
    processsecurity_validation = pap_processsecurity_validation

    def _associate(self, related_ideas, proposal):
        root = getSite()
        datas = {'author': get_current(),
                 'source': proposal,
                 'comment': _('Publish the idea as a proposal'),
                 'intention': 'Creation'}
        for idea in related_ideas:
            correlation = Correlation()
            datas['targets'] = [idea]
            correlation.set_data(datas)
            correlation.tags.extend(['related_proposals', 'related_ideas'])
            correlation.type = 1
            root.addtoproperty('correlations', correlation)

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        proposal = Proposal()
        root.addtoproperty('proposals', proposal)
        for k in context.keywords_ref:
            proposal.addtoproperty('keywords_ref', k)

        proposal.title = context.title + _(" (The proposal)") 
        proposal.description = context.description
        proposal.text = context.text
        proposal.state.append('draft')
        if ('to work' in context.state):
            context.state = PersistentList(['published'])

        grant_roles(roles=(('Owner', proposal), ))
        grant_roles(roles=(('Participant', proposal), ))
        proposal.setproperty('author', get_current())
        self.process.execution_context.add_created_entity('proposal', proposal)
        wg = WorkingGroup()
        root.addtoproperty('working_groups', wg)
        wg.setproperty('proposal', proposal)
        wg.addtoproperty('members', get_current())
        wg.state.append('deactivated')
        self._associate([context], proposal)
        proposal.reindex()
        wg.reindex()
        context.reindex()
        self.newcontext = proposal
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def submit_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def submit_roles_validation(process, context):
    return has_role(role=('Owner', context))


def submit_processsecurity_validation(process, context):
    user = get_current()
    root = getSite()
    return len(user.active_working_groups) < root.participations_maxi and \
           global_user_processsecurity(process, context)
          

def submit_state_validation(process, context):
    return "draft" in context.state


class SubmitProposal(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_picto = 'glyphicon glyphicon-share'
    style_order = 1
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = submit_relation_validation
    roles_validation = submit_roles_validation
    processsecurity_validation = submit_processsecurity_validation
    state_validation = submit_state_validation


    def start(self, context, request, appstruct, **kw):
        context.state.remove('draft')
        root = getSite()
        if root.participants_mini > 1:
            context.state.append('open to a working group')
        else:
            context.state.append('votes for publishing')

        for idea in [i for i in context.related_ideas \
                     if not('published' in i.state)]:
            idea.state = PersistentList(['published'])
            idea.reindex()

        context.reindex()
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def duplicate_processsecurity_validation(process, context):
    return not ('draft' in context.state) and \
           global_user_processsecurity(process, context)


class DuplicateProposal(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_picto = 'glyphicon glyphicon-resize-full'
    style_order = 3
    context = IProposal
    processsecurity_validation = duplicate_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        copy_of_proposal = copy(context, (root, 'proposals'), 
                             omit=('created_at', 'modified_at'))
        keywords_ids = appstruct.pop('keywords')
        result, newkeywords = root.get_keywords(keywords_ids)
        for nkw in newkeywords:
            root.addtoproperty('keywords', nkw)

        result.extend(newkeywords)
        related_ideas = appstruct.pop('related_ideas')
        appstruct['keywords_ref'] = result
        copy_of_proposal.set_data(appstruct)
        copy_of_proposal.setproperty('originalentity', context)
        copy_of_proposal.state = PersistentList(['draft'])
        copy_of_proposal.setproperty('author', get_current())
        grant_roles(roles=(('Owner', copy_of_proposal), ))
        grant_roles(roles=(('Participant', copy_of_proposal), ))
        copy_of_proposal.setproperty('author', get_current())
        self.process.execution_context.add_created_entity(
                                       'proposal', copy_of_proposal)
        wg = WorkingGroup()
        root.addtoproperty('working_groups', wg)
        wg.setproperty('proposal', copy_of_proposal)
        wg.addtoproperty('members', get_current())
        wg.state.append('deactivated')
        if related_ideas:
            associate_to_proposal(related_ideas, copy_of_proposal, False)

        wg.reindex()
        copy_of_proposal.reindex()
        context.reindex()
        self.newcontext = copy_of_proposal
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def edit_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def edit_roles_validation(process, context):
    return has_role(role=('Owner', context))


def edit_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def edit_state_validation(process, context):
    return "draft" in context.state


class EditProposal(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'text-action'
    style_picto = 'glyphicon glyphicon-pencil'
    style_order = 1
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = edit_relation_validation
    roles_validation = edit_roles_validation
    processsecurity_validation = edit_processsecurity_validation
    state_validation = edit_state_validation

    def _add_related_ideas(self, context, root, ideas, comment, intention):
        datas = {'author': get_current(),
                 'targets': ideas,
                 'comment': comment,
                 'intention': intention,
                 'source': context}
        correlation = Correlation()
        correlation.set_data(datas)
        correlation.tags.extend(['related_proposals', 'related_ideas'])
        correlation.type = 1
        root.addtoproperty('correlations', correlation)
        return True


    def _del_related_ideas(self, context, root, ideas):
        correlations = [c for c in context.source_correlations \
                        if ((c.type==1) and ('related_ideas' in c.tags))]
        for idea in ideas:
            for correlation in correlations:
                if idea in correlation.targets:
                    root.delproperty('correlations', correlation)
                    correlation.delproperty('source', context)
                    for target in correlation.targets:
                        correlation.delproperty('targets', target)
        return True

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        if 'related_ideas' in appstruct:
            relatedideas = appstruct['related_ideas']
            related_ideas_to_add = [i for i in relatedideas \
                                    if not(i in context.related_ideas)]
            related_ideas_to_del = [i for i in context.related_ideas \
                                     if not(i in relatedideas) and \
                                        not (i in related_ideas_to_add)]
            self._add_related_ideas(context, root,
                                    related_ideas_to_add,
                                   'Add ideas to the proposal', 'Edit proposal')
            self._del_related_ideas(context, root, related_ideas_to_del)

        context.modified_at = datetime.datetime.today()
        keywords_ids = appstruct.pop('keywords')
        result, newkeywords = root.get_keywords(keywords_ids)
        for nkw in newkeywords:
            root.addtoproperty('keywords', nkw)

        result.extend(newkeywords)
        datas = {'keywords_ref': result}
        context.set_data(datas)
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def proofreading_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def proofreading_roles_validation(process, context):
    return has_role(role=('Participant', context))


def proofreading_processsecurity_validation(process, context):
    correction_in_process = any(('in process' in c.state for c in context.corrections))
    return not correction_in_process and \
           not getattr(process, 'first_decision', True) and \
           global_user_processsecurity(process, context)


def proofreading_state_validation(process, context):
    wg = context.working_group
    return 'active' in wg.state and 'proofreading' in context.state


class ProofreadingDone(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_picto = 'glyphicon glyphicon-ok'
    style_descriminator = 'text-action'
    style_order = 2
    context = IProposal
    processs_relation_id = 'proposal'
    roles_validation = proofreading_roles_validation
    relation_validation = proofreading_relation_validation
    processsecurity_validation = proofreading_processsecurity_validation
    state_validation = proofreading_state_validation

    def start(self, context, request, appstruct, **kw):
        context.state.remove('proofreading')
        context.state.append('amendable')
        context.reindex()
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def pub_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def pub_roles_validation(process, context):
    return has_role(role=('Member',))#has_role(role=('System',)) #System


def pub_state_validation(process, context):
    return 'active' in context.working_group.state and 'votes for publishing' in context.state


class PublishProposal(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_picto = 'glyphicon glyphicon-certificate'
    style_order = 2
    context = IProposal
    processs_relation_id = 'proposal'
    #actionType = ActionType.system
    roles_validation = pub_roles_validation
    relation_validation = pub_relation_validation
    state_validation = pub_state_validation

    def start(self, context, request, appstruct, **kw):
        wg = context.working_group
        context.state.remove('votes for publishing')
        context.state.append('published')
        wg.state = PersistentList(['archived'])
        members = wg.members
        url = request.resource_url(context, "@@index")
        subject = PUBLISHPROPOSAL_SUBJECT.format(subject_title=context.title)
        for member in  members:
            token = Token(title='Token_'+context.title)
            token.setproperty('proposal', context)
            member.addtoproperty('tokens_ref', token)
            member.addtoproperty('tokens', token)
            token.setproperty('owner', member)
            revoke_roles(member, (('Participant', context),))
            message = PUBLISHPROPOSAL_MESSAGE.format(
                recipient_title=getattr(member, 'user_title',''),
                recipient_first_name=getattr(member, 'first_name', member.name),
                recipient_last_name=getattr(member, 'last_name',''),
                subject_title=context.title,
                subject_url=url
                 )
            mailer_send(subject=subject,
              recipients=[member.email],
              body=message)

        wg.reindex()
        context.reindex()
        #TODO wg desactive, members vide...
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def support_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def support_roles_validation(process, context):
    return has_role(role=('Member',))


def support_processsecurity_validation(process, context):
    user = get_current()
    return user.tokens and  \
           not (user in [t.owner for t in context.tokens]) and \
           global_user_processsecurity(process, context)


def support_state_validation(process, context):
    return 'published' in context.state


class SupportProposal(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_picto = 'glyphicon glyphicon-thumbs-up'
    style_order = 2
    context = IProposal
    processs_relation_id = 'proposal'
    roles_validation = support_roles_validation
    relation_validation = support_relation_validation
    processsecurity_validation = support_processsecurity_validation
    state_validation = support_state_validation

    def start(self, context, request, appstruct, **kw):
        user = get_current()
        token = None
        for tok in user.tokens:
            if tok.proposal is context:
                token = tok

        if token is None:
            token = user.tokens[-1]

        context.addtoproperty('tokens_support', token)
        context._support_history.append((get_oid(user), datetime.datetime.today(), 1))
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


class OpposeProposal(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_picto = 'glyphicon glyphicon-thumbs-down'
    style_order = 3
    context = IProposal
    processs_relation_id = 'proposal'
    roles_validation = support_roles_validation
    relation_validation = support_relation_validation
    processsecurity_validation = support_processsecurity_validation
    state_validation = support_state_validation

    def start(self, context, request, appstruct, **kw):
        user = get_current()
        token = None
        for tok in user.tokens:
            if tok.proposal is context:
                token = tok

        if token is None:
            token = user.tokens[-1]

        context.addtoproperty('tokens_opposition', token)
        context._support_history.append((get_oid(user), datetime.datetime.today(), 0))
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def withdrawt_processsecurity_validation(process, context):
    user = get_current()
    return any((t.owner is user) and \
                t.proposal is None for t in context.tokens) and \
           global_user_processsecurity(process, context)


class WithdrawToken(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_picto = 'glyphicon glyphicon-share-alt'
    style_order = 2
    context = IProposal
    processs_relation_id = 'proposal'
    roles_validation = support_roles_validation
    relation_validation = support_relation_validation
    processsecurity_validation = withdrawt_processsecurity_validation
    state_validation = support_state_validation

    def start(self, context, request, appstruct, **kw):
        user = get_current()
        user_tokens = [t for t in context.tokens \
                       if (t.owner is user) and t.proposal is None]
        token = user_tokens[-1]
        context.delproperty(token.__property__, token)
        user.addtoproperty('tokens', token)
        context._support_history.append((get_oid(user), datetime.datetime.today(), -1))
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def alert_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def alert_roles_validation(process, context):
    return has_role(role=('Member',))#has_role(role=('System',))


def alert_state_validation(process, context):
    wg = context.working_group
    return 'active' in wg.state and any(s in context.state \
                                        for s in ['proofreading', 'amendable'])


class Alert(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_order = 4
    context = IProposal
    #actionType = ActionType.system
    processs_relation_id = 'proposal'
    roles_validation = alert_roles_validation
    relation_validation = alert_relation_validation
    state_validation = alert_state_validation

    def start(self, context, request, appstruct, **kw):
        members = context.working_group.members
        url = request.resource_url(context, "@@index")
        subject = ALERT_SUBJECT.format(subject_title=context.title)
        for member in members:
            message = ALERT_MESSAGE.format(
                recipient_title=getattr(member, 'user_title',''),
                recipient_first_name=getattr(member, 'first_name', member.name),
                recipient_last_name=getattr(member, 'last_name',''),
                subject_url=url
                 )
            mailer_send(subject=subject, 
                recipients=[member.email], 
                body=message)

        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def comm_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def comm_roles_validation(process, context):
    return has_role(role=('Member',))


def comm_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def comm_state_validation(process, context):
    return  not('draft' in context.state)


class CommentProposal(CommentIdea):
    isSequential = False
    context = IProposal
    processs_relation_id = 'proposal'
    roles_validation = comm_roles_validation
    processsecurity_validation = comm_processsecurity_validation
    state_validation = comm_state_validation


def edita_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def edita_roles_validation(process, context):
    return has_role(role=('Participant', context))


def edita_processsecurity_validation(process, context):
    return any(not('archived' in a.state) for a in context.amendments) and \
          global_user_processsecurity(process, context)


class EditAmendments(InfiniteCardinality):
    isSequential = False
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = edita_relation_validation
    roles_validation = edita_roles_validation
    processsecurity_validation = edita_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def present_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def present_roles_validation(process, context):
    return has_role(role=('Member',))


def present_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def present_state_validation(process, context):
    return not ('draft' in context.state) #TODO ?


class PresentProposal(PresentIdea):
    context = IProposal
    processs_relation_id = 'proposal'
    roles_validation = present_roles_validation
    processsecurity_validation = present_processsecurity_validation
    state_validation = present_state_validation


def associate_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def associate_processsecurity_validation(process, context):
    return (has_role(role=('Owner', context)) or \
           (has_role(role=('Member',)) and \
            not ('draft' in context.state))) and \
           global_user_processsecurity(process, context)


class Associate(AssociateIdea):
    context = IProposal
    processs_relation_id = 'proposal'
    processsecurity_validation = associate_processsecurity_validation
    relation_validation = associate_relation_validation


def seeideas_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def seeideas_roles_validation(process, context):
    return has_role(role=('Member',)) 


def seeideas_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context) 


def seeideas_state_validation(process, context):
    return not ('draft' in context.state) or \
           ('draft' in context.state and has_role(role=('Owner', context))) 


class SeeRelatedIdeas(InfiniteCardinality):
    context = IProposal
    processs_relation_id = 'proposal'
    processsecurity_validation = seeideas_processsecurity_validation
    roles_validation = seeideas_roles_validation
    state_validation = seeideas_state_validation
    relation_validation = seeideas_relation_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def improve_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def improve_roles_validation(process, context):
    return has_role(role=('Participant', context))


def improve_processsecurity_validation(process, context):
    #correction_in_process = any(('in process' in c.state for c in context.corrections))
    return global_user_processsecurity(process, context)


def improve_state_validation(process, context):
    wg = context.working_group
    return 'active' in wg.state and 'amendable' in context.state


class ImproveProposal(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'text-action'
    style_picto = 'glyphicon glyphicon-edit'
    style_order = 4
    isSequential = False
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = improve_relation_validation
    roles_validation = improve_roles_validation
    processsecurity_validation = improve_processsecurity_validation
    state_validation = improve_state_validation


    def start(self, context, request, appstruct, **kw):
        root = getSite()
        data = {}
        data['title'] = context.title + '_A ' + \
                        str(getattr(context, '_amendments_counter', 1))
        data['text'] = appstruct['text']
        data['description'] = appstruct['description']
        keywords_ids = appstruct.pop('keywords')
        result, newkeywords = root.get_keywords(keywords_ids)
        for nkw in newkeywords:
            root.addtoproperty('keywords', nkw)

        result.extend(newkeywords)
        data['keywords_ref'] = result
        amendment = Amendment()
        self.newcontext = amendment
        amendment.set_data(data)
        context.addtoproperty('amendments', amendment)
        amendment.state.append('draft')
        grant_roles(roles=(('Owner', amendment), ))
        amendment.setproperty('author', get_current())
        context._amendments_counter = getattr(context, '_amendments_counter', 1) + 1
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def correctitem_relation_validation(process, context):
    return process.execution_context.has_relation(context.proposal, 'proposal')


def correctitem_roles_validation(process, context):
    return has_role(role=('Participant', context.proposal))


def correctitem_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def correctitem_state_validation(process, context):
    return 'active' in context.proposal.working_group.state and \
           'proofreading' in context.proposal.state


class CorrectItem(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    isSequential = True
    context = ICorrection
    relation_validation = correctitem_relation_validation
    roles_validation = correctitem_roles_validation
    processsecurity_validation = correctitem_processsecurity_validation
    state_validation = correctitem_state_validation

    def _include_to_proposal(self, context, text_to_correct, request, content):
        corrections = [item for item in context.corrections.keys() \
                       if not('included' in context.corrections[item])]
        text = self._include_items(text_to_correct, request, corrections)
        if content == 'description':
            text = text.replace('<p>', '').replace('</p>', '')

        setattr(context.proposal, content, text)

    def _include_items(self, text, request, items, to_add=False):
        text_analyzer = get_current_registry().getUtility(ITextAnalyzer,
                                                          'text_analyzer')
        todel = "ins"
        toins = "del"
        if to_add:
            todel = "del"
            toins = "ins"

        soup = BeautifulSoup(text)
        corrections = []
        for item in items:
            corrections.extend(soup.find_all('span', {'id':'correction', 
                                                      'data-item': item}))

        blocstodel = ('span', {'id':'correction_actions'})
        soup = text_analyzer.include_diffs(soup, corrections,
                        todel, toins, blocstodel)
        return text_analyzer.soup_to_text(soup)

    def start(self, context, request, appstruct, **kw):
        item = appstruct['item']
        content = appstruct['content']
        vote = (appstruct['vote'].lower() == 'true')
        user = get_current()
        user_oid = get_oid(user)
        correction_data = context.corrections[item]
        text_to_correct = getattr(context, content,'')
        if not(user_oid in correction_data['favour']) and \
               not(user_oid in correction_data['against']):
            if vote:
                context.corrections[item]['favour'].append(get_oid(user))
                if (len(context.corrections[item]['favour'])-1) >= \
                    DEFAULT_NB_CORRECTORS:
                    text = self._include_items(text_to_correct, 
                                   request, [item], True)
                    setattr(context, content, text)
                    text_to_correct = getattr(context, content,'')
                    context.corrections[item]['included'] = True
                    if not any(not('included' in context.corrections[c]) \
                               for c in context.corrections.keys()):
                        context.state.remove('in process')
                        context.state.append('processed')

                    self._include_to_proposal(context, text_to_correct, 
                                              request, content)
            else:
                context.corrections[item]['against'].append(get_oid(user))
                if len(context.corrections[item]['against']) >= \
                   DEFAULT_NB_CORRECTORS:
                    text = self._include_items(text_to_correct, request, [item])
                    setattr(context, content, text)
                    text_to_correct = getattr(context, content,'')
                    context.corrections[item]['included'] = True
                    if not any(not('included' in context.corrections[c]) \
                               for c in context.corrections.keys()):
                        context.state.remove('in process')
                        context.state.append('processed')

                    self._include_to_proposal(context, text_to_correct,
                                              request, content)
            
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def correct_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def correct_roles_validation(process, context):
    return has_role(role=('Participant', context))


def correct_processsecurity_validation(process, context):
    correction_in_process = any(('in process' in c.state for c in context.corrections))
    return not correction_in_process and \
           not getattr(process, 'first_decision', True) and \
           global_user_processsecurity(process, context)


def correct_state_validation(process, context):
    return 'active' in context.working_group.state and 'proofreading' in context.state


class CorrectProposal(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'text-action'
    style_picto = 'glyphicon glyphicon-check'
    style_order = 2
    isSequential = True
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = correct_relation_validation
    roles_validation = correct_roles_validation
    processsecurity_validation = correct_processsecurity_validation
    state_validation = correct_state_validation

    def _add_vote_actions(self, tag, correction, request):
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,'dace_ui_api')
        if not hasattr(self, 'correctitemaction'):
            correctitemnode = self.process['correctitem']
            correctitem_wis = [wi for wi in correctitemnode.workitems \
                               if wi.node is correctitemnode]
            if correctitem_wis:
                self.correctitemaction = correctitem_wis[0].actions[0]

        if hasattr(self, 'correctitemaction'):
            actionurl_update = dace_ui_api.updateaction_viewurl(
                               request=request, 
                               action_uid=str(get_oid(self.correctitemaction)), 
                               context_uid=str(get_oid(correction)))
            values = {'favour_action_url': actionurl_update,
                     'against_action_url': actionurl_update}
            template = 'novaideo:views/proposal_management/templates/correction_item.pt'
            body = renderers.render(template, values, request)
            correction_item_soup = BeautifulSoup(body)
            tag.append(correction_item_soup.body)
            tag.body.unwrap()

    def _add_actions(self, correction, request, soup):
        corrections_tags = soup.find_all('span', {'id':'correction'})
        for correction_tag in corrections_tags:
            self._add_vote_actions(correction_tag, correction, request)

    def _identify_corrections(self, soup, correction, descriminator, content):
        correction_tags = soup.find_all('span', {'id': "correction"})
        correction_oid = str(get_oid(correction))
        user = get_current()
        user_oid = get_oid(user)
        for correction_tag in correction_tags:
            correction_tag['data-correction'] = correction_oid
            correction_tag['data-item'] = str(descriminator)
            correction_tag['data-content'] = content
            init_vote = {'favour':[user_oid], 'against':[]}
            correction.corrections[str(descriminator)] = init_vote
            descriminator += 1

        return descriminator      

    def start(self, context, request, appstruct, **kw):
        user = get_current()
        correction = appstruct['_object_data']
        correction.setproperty('author', user)
        context.addtoproperty('corrections', correction)
        text_analyzer = get_current_registry().getUtility(
                                                ITextAnalyzer,
                                                'text_analyzer')
        souptextdiff, textdiff = text_analyzer.render_html_diff(
                                       getattr(context, 'text', ''), 
                                       getattr(correction, 'text', ''),
                                       "correction")
        soupdescriptiondiff, descriptiondiff = text_analyzer.render_html_diff(
                                        getattr(context, 'description', ''), 
                                        getattr(correction, 'description', ''), 
                                        "correction")
        descriminator = 0
        descriminator = self._identify_corrections(soupdescriptiondiff, 
                                                   correction, 
                                                   descriminator, 
                                                   'description')
        self._add_actions(correction, request, soupdescriptiondiff)
        self._identify_corrections(souptextdiff, correction, 
                                   descriminator, 'text')
        self._add_actions(correction, request, souptextdiff)
        correction.text = text_analyzer.soup_to_text(souptextdiff)
        context.originaltext = correction.text
        correction.description = text_analyzer.soup_to_text(soupdescriptiondiff)
        if souptextdiff.find_all("span", id="correction"):
            correction.state.append('in process')

        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def addp_state_validation(process, context):
    return False


class AddParagraph(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'text-action'
    style_order = 3
    isSequential = False
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = correct_relation_validation
    roles_validation = correct_roles_validation
    processsecurity_validation = correct_processsecurity_validation
    state_validation = addp_state_validation#correct_state_validation

    def start(self, context, request, appstruct, **kw):
        #TODO
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def decision_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def decision_roles_validation(process, context):
    return has_role(role=('Member',))#has_role(role=('System',))


def decision_state_validation(process, context):
    return 'active' in context.working_group.state and \
           any(s in context.state for s in ['proofreading', 'amendable'])


class VotingPublication(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_order = 5
    context = IProposal
    processs_relation_id = 'proposal'
    #actionType = ActionType.system
    relation_validation = decision_relation_validation
    roles_validation = decision_roles_validation
    state_validation = decision_state_validation

    def start(self, context, request, appstruct, **kw):
        state = context.state[0] 
        context.state.remove(state)
        context.state.append('votes for publishing')
        context.reindex()
        members = context.working_group.members
        url = request.resource_url(context, "@@index")
        subject = VOTINGPUBLICATION_SUBJECT.format(subject_title=context.title)
        for member in members:
            message = VOTINGPUBLICATION_MESSAGE.format(
                recipient_title=getattr(member, 'user_title',''),
                recipient_first_name=getattr(member, 'first_name', member.name),
                recipient_last_name=getattr(member, 'last_name',''),
                subject_title=context.title,
                subject_url=url
                 )
            mailer_send(subject=subject, 
                recipients=[member.email], 
                body=message)

        self.process.iteration = getattr(self.process, 'iteration', 0) + 1
        return True


    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def withdraw_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def withdraw_roles_validation(process, context):
    return has_role(role=('Member',))


def withdraw_processsecurity_validation(process, context):
    user = get_current()
    return user in context.working_group.wating_list and \
           global_user_processsecurity(process, context)


def withdraw_state_validation(process, context):
    return  any(s in context.state for s in ['proofreading', 'amendable'])


class Withdraw(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'wg-action'
    style_order = 3
    style_css_class = 'btn-warning'
    isSequential = False
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = withdraw_relation_validation
    roles_validation = withdraw_roles_validation
    processsecurity_validation = withdraw_processsecurity_validation
    state_validation = withdraw_state_validation

    def start(self, context, request, appstruct, **kw):
        user = get_current()
        wg = context.working_group
        wg.delproperty('wating_list', user)
        subject = WITHDRAW_SUBJECT.format(subject_title=context.title)
        message = WITHDRAW_MESSAGE.format(
                recipient_title=getattr(user, 'user_title',''),
                recipient_first_name=getattr(user, 'first_name', user.name),
                recipient_last_name=getattr(user, 'last_name',''),
                subject_title=context.title,
                subject_url=request.resource_url(context, "@@index")
                 )
        mailer_send(subject=subject, 
            recipients=[user.email], 
            body=message)
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def resign_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def resign_roles_validation(process, context):
    return has_role(role=('Participant', context))


def resign_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def resign_state_validation(process, context):
    return  any(s in context.state for s in \
                ['proofreading', 'amendable', 'open to a working group'])


class Resign(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'wg-action'
    style_order = 2
    style_css_class = 'btn-danger'
    isSequential = False
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = resign_relation_validation
    roles_validation = resign_roles_validation
    processsecurity_validation = resign_processsecurity_validation
    state_validation = resign_state_validation

    def _get_next_user(self, users, root):
        for user in users:
            wgs = user.active_working_groups
            if 'active' in user.state and len(wgs) < root.participations_maxi:
                return user

        return None 

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        user = get_current()
        wg = context.working_group
        wg.delproperty('members', user)
        #ajouter le user a demission..
        revoke_roles(user, (('Participant', context),))
        url = request.resource_url(context, "@@index")
        if wg.wating_list:
            next_user = self._get_next_user(wg.wating_list, root)
            if next_user is not None:
                wg.delproperty('wating_list', next_user)
                wg.addtoproperty('members', next_user)
                grant_roles(next_user, (('Participant', context),))
                subject = PARTICIPATE_SUBJECT.format(subject_title=context.title)
                message = PARTICIPATE_MESSAGE.format(
                        recipient_title=getattr(next_user, 'user_title',''),
                        recipient_first_name=getattr(next_user, 
                                               'first_name', next_user.name),
                        recipient_last_name=getattr(next_user, 'last_name',''),
                        subject_title=context.title,
                        subject_url=url
                 )
                mailer_send(subject=subject, recipients=[next_user.email], body=message)

        participants = wg.members
        len_participants = len(participants)
        if len_participants < root.participants_mini and \
            not ('open to a working group' in context.state):
            context.state = PersistentList(['open to a working group'])
            wg.state = PersistentList(['deactivated'])
            wg.reindex()
            context.reindex()

        subject = RESIGN_SUBJECT.format(subject_title=context.title)
        message = RESIGN_MESSAGE.format(
                recipient_title=getattr(user, 'user_title',''),
                recipient_first_name=getattr(user, 'first_name', user.name),
                recipient_last_name=getattr(user, 'last_name',''),
                subject_title=context.title,
                subject_url=url
                 )
        mailer_send(subject=subject, 
             recipients=[user.email], 
             body=message)

        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def participate_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def participate_roles_validation(process, context):
    return has_role(role=('Member',)) and not has_role(role=('Participant', context))


def participate_processsecurity_validation(process, context):
    user = get_current()
    root = getSite()
    wgs = user.active_working_groups
    return not(user in context.working_group.wating_list) and \
           len(wgs) < root.participations_maxi and \
           global_user_processsecurity(process, context)


def participate_state_validation(process, context):
    wg = context.working_group
    return  not('closed' in wg.state) and \
            any(s in context.state for s in \
                ['proofreading', 'amendable', 'open to a working group']) 


class Participate(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'wg-action'
    style_order = 1
    style_css_class = 'btn-success'
    isSequential = False
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = participate_relation_validation
    roles_validation = participate_roles_validation
    processsecurity_validation = participate_processsecurity_validation
    state_validation = participate_state_validation

    def _send_mail_to_user(self, subject_template, message_template, user, context, request):
        subject = subject_template.format(subject_title=context.title)
        message = message_template.format(
                recipient_title=getattr(user, 'user_title',''),
                recipient_first_name=getattr(user, 'first_name', user.name),
                recipient_last_name=getattr(user, 'last_name',''),
                subject_title=context.title,
                subject_url=request.resource_url(context, "@@index")
                 )
        mailer_send(subject=subject, recipients=[user.email], body=message)

    def _call_votingpublication(self, context, request):
        try:
            action = self.process.getWorkItems()['proposalmanagement.votingpublication'].actions[0]
            action.execute(context, request, {})
        except Exception:
            pass

    def start(self, context, request, appstruct, **kw):
        root = getSite()
        user = get_current()
        wg = context.working_group
        participants = wg.members
        len_participants = len(participants)
        first_decision = False
        if len_participants < root.participants_maxi:
            wg.addtoproperty('members', user)
            grant_roles(user, (('Participant', context),))
            if (len_participants+1) == root.participants_mini:
                context.state = PersistentList()#.remove('open to a working group')
                wg.state = PersistentList(['active'])
                if not hasattr(self.process, 'first_decision'):
                    self.process.first_decision = True
                    first_decision = True

                if any(not('archived' in a.state) for a in context.amendments):
                    context.state.append('amendable')
                else:
                    context.state.append('proofreading')

                wg.reindex()
                context.reindex()

            self._send_mail_to_user(PARTICIPATE_SUBJECT, PARTICIPATE_MESSAGE,
                 user, context, request)
            if first_decision:
                self._call_votingpublication(context, request)
        else:
            wg.addtoproperty('wating_list', user)
            wg.reindex()
            self._send_mail_to_user(WATINGLIST_SUBJECT, WATINGLIST_MESSAGE,
                 user, context, request)


        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def va_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def va_roles_validation(process, context):
    return has_role(role=('Member',))#has_role(role=('System',))


def va_state_validation(process, context):
    return 'active' in context.working_group.state and \
           'amendable' in context.state


class VotingAmendments(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_order = 6
    context = IProposal
    processs_relation_id = 'proposal'
    #actionType = ActionType.system
    relation_validation = va_relation_validation
    roles_validation = va_roles_validation
    state_validation = va_state_validation

    def start(self, context, request, appstruct, **kw):
        context.state = PersistentList(['votes for amendments'])
        context.working_group.state.append('closed')
        context.reindex()
        members = context.working_group.members
        url = request.resource_url(context, "@@index")
        subject = VOTINGAMENDMENTS_SUBJECT.format(subject_title=context.title)
        for member in members:
            message = VOTINGAMENDMENTS_MESSAGE.format(
                recipient_title=getattr(member, 'user_title',''),
                recipient_first_name=getattr(member, 'first_name', member.name),
                recipient_last_name=getattr(member, 'last_name',''),
                subject_title=context.title,
                subject_url=url
                 )
            mailer_send(subject=subject, 
                 recipients=[member.email], 
                 body=message)
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def ar_state_validation(process, context):
    return 'active' in context.working_group.state and \
           'votes for amendments' in context.state


class AmendmentsResult(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_order = 7
    amendments_group_result_template = 'novaideo:views/proposal_management/templates/amendments_group_result.pt'
    amendments_vote_result_template = 'novaideo:views/proposal_management/templates/amendments_vote_result.pt'
    context = IProposal
    processs_relation_id = 'proposal'
    #actionType = ActionType.system
    relation_validation = va_relation_validation
    roles_validation = va_roles_validation
    state_validation = ar_state_validation

    def _get_copy(self, context, root, wg):
        copy_of_proposal = copy(context, (root, 'proposals'), 
                             omit=('created_at','modified_at'),roles=True)
        copy_keywords, newkeywords = root.get_keywords(context.keywords)
        copy_of_proposal.setproperty('keywords_ref', copy_keywords)
        copy_of_proposal.setproperty('version', context)
        copy_of_proposal.state = PersistentList(['proofreading'])
        copy_of_proposal.setproperty('author', context.author)
        copy_of_proposal.setproperty('comments', context.comments)
        self.process.execution_context.add_created_entity('proposal', 
                                           copy_of_proposal)
        wg.setproperty('proposal', copy_of_proposal)
        return copy_of_proposal

    def _send_ballot_result(self, context, request, electeds, members):
        group_nb = 0
        amendments_vote_result = []
        for ballot in self.process.amendments_ballots: 
            group_nb += 1
            values = {'group_nb': group_nb,
                      'report': ballot.report,
                      'get_obj': get_obj}
            group_body = renderers.render(
                self.amendments_group_result_template, values, request)
            amendments_vote_result.append(group_body)

        values = {'amendments_vote_result': amendments_vote_result,
                  'electeds': electeds,
                  'subject': context}
        result_body = renderers.render(self.amendments_vote_result_template,
                                 values, request)
        subject = RESULT_VOTE_AMENDMENT_SUBJECT.format(
                        subject_title=context.title)
        import pdb; pdb.set_trace()
        for member in members:
            message = RESULT_VOTE_AMENDMENT_MESSAGE.format(
                recipient_title=getattr(member, 'user_title',''),
                recipient_first_name=getattr(member, 'first_name', member.name),
                recipient_last_name=getattr(member, 'last_name',''),
                message_result=result_body
                 )
            mailer_send(subject=subject, 
                 recipients=[member.email], 
                 html=message)
        

    def start(self, context, request, appstruct, **kw):
        result = set()
        for ballot in self.process.amendments_ballots:
            electeds = ballot.report.get_electeds()
            if electeds is not None:
                result.update(electeds)

        amendments = [a for a in result if isinstance(a, Amendment)]
        wg = context.working_group
        root = getSite()
        self.newcontext = context 
        if amendments:
            self._send_ballot_result(context, request, result, wg.members)
            text_analyzer = get_current_registry().getUtility(
                                            ITextAnalyzer,'text_analyzer')
            merged_text = text_analyzer.merge(context.text, 
                                 [a.text for a in amendments])
            #TODO merged_keywords + merged_description
            copy_of_proposal = self._get_copy(context, root, wg)
            context.state = PersistentList(['archived'])
            copy_of_proposal.text = merged_text
            #correlation idea of replacement ideas... del replaced_idea
            added_ideas = [a.added_ideas for a in amendments]
            added_ideas = [item for sublist in added_ideas for item in sublist]
            removed_ideas = [a.removed_ideas for a in amendments]
            removed_ideas = [item for sublist in removed_ideas \
                             for item in sublist]
            not_modified_ideas = [i for i in context.related_ideas \
                                  if not (i in removed_ideas)]
            new_ideas = not_modified_ideas
            new_ideas.extend(added_ideas)
            new_ideas = list(set(new_ideas))
            associate_to_proposal(new_ideas, copy_of_proposal, False)
            self.newcontext = copy_of_proposal
            copy_of_proposal.reindex()
        else:
            context.state = PersistentList(['proofreading'])
            for amendment in context.amendments:
                amendment.state = PersistentList(['archived'])
                amendment.reindex()

        context.reindex()
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(self.newcontext, "@@index"))


def ta_state_validation(process, context):
    return 'active' in context.working_group.state and \
           'votes for publishing' in context.state


class Amendable(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_order = 8
    context = IProposal
    processs_relation_id = 'proposal'
    #actionType = ActionType.system
    relation_validation = va_relation_validation
    roles_validation = va_roles_validation
    state_validation = ta_state_validation

    def start(self, context, request, appstruct, **kw):
        context.state.remove('votes for publishing')
        wg = context.working_group
        if self.process.first_decision:
            self.process.first_decision = False
        if any(not('archived' in a.state) for a in context.amendments):
            context.state.append('amendable')
        else:
            context.state.append('proofreading')

        reopening_ballot = getattr(self.process, 
                            'reopening_configuration_ballot', None)
        if reopening_ballot is not None:
            report = reopening_ballot.report
            voters_len = len(report.voters)
            electors_len = len(report.electors)
            report.calculate_votes()
            if (voters_len == electors_len) and \
               (report.result['False'] == 0) and \
               'closed' in wg.state:
                wg.state.remove('closed')
                wg.reindex()

        context.reindex()
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def compare_processsecurity_validation(process, context):
    return getattr(context, 'version', None) is not None and \
           (has_role(role=('Owner', context)) or \
           (has_role(role=('Member',)) and\
            not ('draft' in context.state))) and \
           global_user_processsecurity(process, context)


class CompareProposal(InfiniteCardinality):
    title = _('Compare')
    context = IProposal
    relation_validation = associate_relation_validation
    processsecurity_validation = compare_processsecurity_validation

    def start(self, context, request, appstruct, **kw):
        return True

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


#TODO behaviors

VALIDATOR_BY_CONTEXT[Proposal] = CommentProposal
