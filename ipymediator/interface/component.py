from operator import itemgetter
from typing import Optional, Union

from ipymediator.enumerations import Options, Value
from ipymediator.interface.mediator import Mediator
from ipymediator.interface.metaclass import ABCTraits

from ipywidgets import widgets
from traitlets import Bool, HasTraits


class Component(ABCTraits):
    """Concrete Component class for communication between a concrete Mediator
    class and a DOMWidget, based on trait changes."""

    def __new__(cls, **kwargs):
        """Add a bool value trait to any Button widgets and assigns an on_click
        function to toggle the Button value."""
        if isinstance(kwargs["widget"], widgets.Button):
            def on_click(w) -> None:
                w.value = not w.value
            # ipywidgets overwrites HasTraits.add_traits and uses depreciated
            # trait.get_metadata. The metadata of a trait type instance should
            # be directly accessed via the metadata attribute.
            # Issue: https://github.com/jupyter-widgets/ipywidgets/pull/3894

            # pytest depreciation warning:
            # kwargs["widget"].add_traits(value=Bool(False))

            # NOTE: HasTraits.add_traits avoids depreciation warning.
            HasTraits.add_traits(kwargs["widget"], value=Bool(False))
            kwargs["widget"].on_click(on_click)
        return super(Component, cls).__new__(cls)

    def __init__(
        self,
        mediator: Mediator,
        widget: widgets.DOMWidget,
        widget_name: Optional[str] = None,
        names: tuple[str, ...] = ("value",),
        notify_self: bool = False,
    ):
        """Initialse Component class.

        Params:
            mediator (Mediator): Reference to a concrete Mediator

            widget (widgets.DOMWidget): Any widget from ipywidgets

            widget_name (str): Optional name for the Component's widget.
                If None, the default value of the widget property's class
                name + "Component" is used

            names (tuple[str, ...]): Trait names of the widget passed to
                the widget property

            notify_self (bool): Determines the reference value passed to
                Mediator's notify function - self (True) or widget_name (False)

        Raises:
            ValueError: Names param contains trait names not held by widget

            AttributeError: Access trait name not held by widget property
        """
        super(Component, self).__init__()
        self.__mediator = mediator
        self.widget = widget
        try:
            # returns widget trait values referenced by names (__call__)
            self(*names)
        except AttributeError as e:
            raise ValueError(f"check 'names' parameter: {names}") from e
        self.widget.observe(self.observe_handler, names=names)  # type: ignore
        self.widget_name = widget_name or f"{type(widget).__name__}Component"
        self.__reference = self if notify_self else self.widget_name

    @property
    def _mediator(self) -> Mediator:
        """Property with a reference to this Component's Mediator"""
        return self.__mediator

    @property
    def _reference(self) -> Union[str, "Component"]:
        """Store reference paramater value passed to Mediator notify method"""
        return self.__reference

    def observe_handler(self, change: Union[Value, Options]) -> None:
        """Observe callback function, passing trait changes to the Mediator"""
        self._mediator.notify(self._reference, change)

    def __call__(self, trait: str, *args):
        """Return widget trait values by leveraging __getitem__, which directs
        the call to the Component's DOMWidget properties"""
        return itemgetter(trait, *args)(self)

    def __contains__(self, trait) -> bool:
        """"""
        return self.widget.has_trait(trait)

    def __getitem__(self, trait: str):
        """Subscriptable interface of Component passed to DOMWidget"""
        return getattr(self.widget, trait)

    def __setitem__(self, trait: str, value) -> None:
        """Facilitate trait value assignment with bracket notation"""
        self.widget.set_trait(trait, value)

    def __str__(self) -> str:
        """Return widget_name property value on str(object)"""
        return self.widget_name
