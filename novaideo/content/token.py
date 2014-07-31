from zope.interface import implementer

from substanced.content import content
from substanced.schema import NameSchemaNode
from substanced.util import renamer

from dace.objectofcollaboration.entity import Entity
from dace.descriptors import SharedUniqueProperty
from pontus.core import VisualisableElement, VisualisableElementSchema

from .interface import IToken


def context_is_a_token(context, request):
    return request.registry.content.istype(context, 'token')


class TokenSchema(VisualisableElementSchema):

    name = NameSchemaNode(
        editing=context_is_a_token,
        )


@content(
    'token',
    icon='glyphicon glyphicon-align-left',
    )
@implementer(IToken)
class Token(VisualisableElement, Entity):
    name = renamer()
    owner = SharedUniqueProperty('owner', 'tokens')

    def __init__(self, **kwargs):
        super(Token, self).__init__(**kwargs)

    def setowner(self, owner):
        self.setproperty('owner', owner)

