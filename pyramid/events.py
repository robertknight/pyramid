import venusian

from zope.interface import implements

from pyramid.interfaces import IContextFound
from pyramid.interfaces import INewRequest
from pyramid.interfaces import INewResponse
from pyramid.interfaces import IApplicationCreated
from pyramid.interfaces import IBeforeRender

class subscriber(object):
    """ Decorator activated via a :term:`scan` which treats the
    function being decorated as an event subscriber for the set of
    interfaces passed as ``*ifaces`` to the decorator constructor.

    For example:

    .. code-block:: python
    
       from pyramid.events import NewRequest
       from pyramid.events import subscriber

       @subscriber(NewRequest)
       def mysubscriber(event):
           event.request.foo = 1

    More than one event type can be passed as a construtor argument:
        
    .. code-block:: python
    
       from pyramid.events import NewRequest, NewResponse
       from pyramid.events import subscriber

       @subscriber(NewRequest, NewResponse)
       def mysubscriber(event):
           print event

    When the ``subscriber`` decorator is used without passing an arguments,
    the function it decorates is called for every event sent:

    .. code-block:: python
    
       from pyramid.events import subscriber

       @subscriber()
       def mysubscriber(event):
           print event

    This method will have no effect until a :term:`scan` is performed
    against the package or module which contains it, ala:

    .. code-block:: python
    
       from pyramid.configuration import Configurator
       config = Configurator()
       config.scan('somepackage_containing_subscribers')

    """
    venusian = venusian # for unit testing

    def __init__(self, *ifaces):
        self.ifaces = ifaces

    def register(self, scanner, name, wrapped):
        config = scanner.config
        config.add_subscriber(wrapped, self.ifaces)

    def __call__(self, wrapped):
        self.venusian.attach(wrapped, self.register, category='pyramid')
        return wrapped

class NewRequest(object):
    """ An instance of this class is emitted as an :term:`event`
    whenever :app:`Pyramid` begins to process a new request.  The
    even instance has an attribute, ``request``, which is a
    :term:`request` object.  This event class implements the
    :class:`pyramid.interfaces.INewRequest` interface."""
    implements(INewRequest)
    def __init__(self, request):
        self.request = request

class NewResponse(object):
    """ An instance of this class is emitted as an :term:`event`
    whenever any :app:`Pyramid` :term:`view` or :term:`exception
    view` returns a :term:`response`.

    The instance has two attributes:``request``, which is the request
    which caused the response, and ``response``, which is the response
    object returned by a view or renderer.

    If the ``response`` was generated by an :term:`exception view`,
    the request will have an attribute named ``exception``, which is
    the exception object which caused the exception view to be
    executed.  If the response was generated by a 'normal' view, the
    request will not have this attribute.

    This event will not be generated if a response cannot be created
    due to an exception that is not caught by an exception view (no
    response is created under this circumstace).

    This class implements the
    :class:`pyramid.interfaces.INewResponse` interface.

    .. note::

       Postprocessing a response is usually better handled in a WSGI
       :term:`middleware` component than in subscriber code that is
       called by a :class:`pyramid.interfaces.INewResponse` event.
       The :class:`pyramid.interfaces.INewResponse` event exists
       almost purely for symmetry with the
       :class:`pyramid.interfaces.INewRequest` event.
    """
    implements(INewResponse)
    def __init__(self, request, response):
        self.request = request
        self.response = response

class ContextFound(object):
    """ An instance of this class is emitted as an :term:`event` after
    the :app:`Pyramid` :term:`router` finds a :term:`context`
    object (after it performs traversal) but before any view code is
    executed.  The instance has an attribute, ``request``, which is
    the request object generated by :app:`Pyramid`.

    Notably, the request object will have an attribute named
    ``context``, which is the context that will be provided to the
    view which will eventually be called, as well as other attributes
    attached by context-finding code.

    This class implements the
    :class:`pyramid.interfaces.IContextFound` interface.

    .. note:: As of :app:`Pyramid` 1.0, for backwards compatibility
       purposes, this event may also be imported as
       :class:`pyramid.events.AfterTraversal`.
    """
    implements(IContextFound)
    def __init__(self, request):
        self.request = request

AfterTraversal = ContextFound # b/c as of 1.0
    
class ApplicationCreated(object):    
    """ An instance of this class is emitted as an :term:`event` when
    the :meth:`pyramid.configuration.Configurator.make_wsgi_app` is
    called.  The instance has an attribute, ``app``, which is an
    instance of the :term:`router` that will handle WSGI requests.
    This class implements the
    :class:`pyramid.interfaces.IApplicationCreated` interface.

    .. note:: For backwards compatibility purposes, this class can
       also be imported as
       :class:`pyramid.events.WSGIApplicationCreatedEvent`.  This
       was the name of the event class before :app:`Pyramid` 1.0.

    """
    implements(IApplicationCreated)
    def __init__(self, app):
        self.app = app
        self.object = app

WSGIApplicationCreatedEvent = ApplicationCreated # b/c (as of 1.0)

class BeforeRender(dict):
    implements(IBeforeRender)
    """
    Subscribers to this event may introspect the and modify the set of
    :term:`renderer globals` before they are passed to a :term:`renderer`.
    This event object iself has a dictionary-like interface that can be used
    for this purpose.  For example::

      from repoze.events import subscriber
      from pyramid.interfaces import IBeforeRender

      @subscriber(IBeforeRender)
      def add_global(event):
          event['mykey'] = 'foo'

    An object of this type is sent as an event just before a :term:`renderer`
    is invoked (but *after* the application-level renderer globals factory
    added via
    :class:`pyramid.configuration.Configurator.set_renderer_globals_factory`,
    if any, has injected its own keys into the renderer globals dictionary).

    If a subscriber attempts to add a key that already exist in the renderer
    globals dictionary, a :exc:`KeyError` is raised.  This limitation is
    enforced because event subscribers do not possess any relative ordering.
    The set of keys added to the renderer globals dictionary by all
    :class:`pyramid.events.BeforeRender` subscribers and renderer globals
    factories must be unique.  """

    def __init__(self, system):
        self._system = system

    def __setitem__(self, name, value):
        """ Set a name/value pair into the dictionary which is passed to a
        renderer as the renderer globals dictionary.  If the ``name`` already
        exists in the target dictionary, a :exc:`KeyError` will be raised."""
        if name in self._system:
            raise KeyError('%s is already a renderer globals value' % name)
        self._system[name] = value

    def update(self, d):
        """ Update the renderer globals dictionary with another dictionary
        ``d``.  If any of the key names in the source dictionary already exist
        in the target dictionary, a :exc:`KeyError` will be raised"""
        for k, v in d.items():
            self[k] = v

    def __contains__(self, k):
        """ Return ``True`` if ``k`` exists in the renderer globals
        dictionary."""
        return k in self._system

    def __getitem__(self, k):
        """ Return the value for key ``k`` from the renderer globals
        dictionary."""
        return self._system[k]

    def get(self, k, default=None):
        """ Return the value for key ``k`` from the renderer globals
        dictionary, or the default if no such value exists."""
        return self._system.get(k)
            
