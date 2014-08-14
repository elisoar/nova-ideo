import re
import colander
from pyramid.view import view_config
from pyramid.threadlocal import get_current_registry

from dace.util import find_catalog
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.util import getSite, allSubobjectsOfType
from dace.objectofcollaboration.principal.util import get_current
from pontus.view import BasicView, ViewError, merge_dicts
from pontus.dace_ui_extension.interfaces import IDaceUIAPI
from pontus.widget import CheckboxChoiceWidget, RichTextWidget
from pontus.schema import Schema
from pontus.form import FormView
from pontus.view_operation import MultipleView

from novaideo.content.processes.idea_management.behaviors import  SeeIdea
from novaideo.content.idea import Idea
from novaideo import _
from novaideo.views.novaideo_view_manager.search import SearchResultView
from .present_idea import PresentIdeaView
from .duplicate_idea import DuplicateIdeaView
from .comment_idea import CommentIdeaView
from .associate import AssociateView
from .compare_idea import CompareIdeaView
from add_to_proposals import AddToProposalsView



class DetailIdeaView(BasicView):
    title = _('Details')
    name = 'seeIdea'
    behaviors = [SeeIdea]
    template = 'novaideo:views/idea_management/templates/see_idea.pt'
    item_template = 'pontus:templates/subview_sample.pt'
    viewid = 'seeidea'


    def update(self):
        self.execute(None) 
        user = get_current()
        files = getattr(self.context, 'attached_files', [])
        files_urls = []
        for f in files:
            files_urls.append({'title':f.title, 'url':f.url(self.request)})

        actions = [a for a in self.context.actions if getattr(a.action, 'style', '') == 'button']
        actions_urls = []
        for action in actions:
            actions_urls.append({'title':action.title, 'url':action.url})

        result = {}
        values = {
                'idea': self.context,
                'current_user': user,
                'files': files_urls,
                'actions': actions_urls
               }
        body = self.content(result=values, template=self.template)['body']
        item = self.adapt_item(body, self.viewid)
        result['coordinates'] = {self.coordinates:[item]}
        return result


class SeeIdeaActionsView(MultipleView):
    title = _('actions')
    name = 'seeiactionsdea'
    template = 'novaideo:views/idea_management/templates/panel_group.pt'
    views = (AddToProposalsView, AssociateView, PresentIdeaView, CommentIdeaView, CompareIdeaView)


@view_config(
    name='seeidea',
    context=Idea,
    renderer='pontus:templates/view.pt',
    )
class SeeIdeaView(MultipleView):
    title = _('Details')
    name = 'seeidea'
    template = 'pontus.dace_ui_extension:templates/sample_mergedmultipleview.pt'
    views = (DetailIdeaView, SeeIdeaActionsView)


DEFAULTMAPPING_ACTIONS_VIEWS.update({SeeIdea:SeeIdeaView})

