from kivy.uix.screenmanager import Screen

from mc.core.mode import Mode
from mc.core.utils import set_position, get_insert_index


class Slide(Screen):
    next_id = 0

    @classmethod
    def get_id(cls):
        Slide.next_id += 1
        return Slide.next_id

    def __init__(self, mc, name, config, target='default', mode=None,
                 priority=None, show=True, force=False, **kwargs):
        self.mc = mc
        self.name = name
        self.priority = None
        self.creation_order = Slide.get_id()
        self.pending_widgets = set()

        if priority is None:
            try:
                self.priority = mode.priority
            except AttributeError:
                self.priority = 0
        else:
            self.priority = int(priority)

        if mode:
            if isinstance(mode, Mode):
                self.mode = mode
            else:
                self.mode = self.mc.modes[mode]
        else:
            self.mode = None

        if self.mode:
            self.priority += self.mode.priority

        target = mc.targets[target]

        self.size_hint = (None, None)
        super().__init__(**kwargs)
        self.size = target.native_size
        self.orig_w, self.orig_h = self.size

        try:
            self.add_widgets_from_config(config)
        except KeyError:
            pass

        self.mc.active_slides[name] = self
        target.add_widget(slide=self, show=show, force=force)

    def __repr__(self):
        return '<Slide name={}, priority={}>'.format(self.name, self.priority)

    def add_widgets_from_library(self, name, mode=None):
        if name not in self.mc.widget_configs:
            return

        return self.add_widgets_from_config(self.mc.widget_configs[name], mode)

    def add_widgets_from_config(self, config, mode=None):
        if type(config) is not list:
            config = [config]
        widgets_added = list()

        for widget in config:
            widget_obj = widget['widget_cls'](mc=self.mc, config=widget,
                                              slide=self, mode=mode)

            top_widget = widget_obj

            while top_widget.parent:
                top_widget = top_widget.parent

            self.add_widget(top_widget)
            try:  # text only? Need to change this. TODO
                widget_obj.texture_update()
                widget_obj.size = widget_obj.texture_size
            except AttributeError:
                widget_obj.size = (widget['width'], widget['height'])

            widget_obj.pos = set_position(self.width,
                                          self.height,
                                          widget_obj.width,
                                          widget_obj.height,
                                          widget['x'],
                                          widget['y'],
                                          widget['h_pos'],
                                          widget['v_pos'])

            widgets_added.append(widget_obj)

        return widgets_added

    def add_widget(self, widget):
        """Adds a widget to this slide.

        Args:
            widget: An MPF-enhanced widget (which will include details like z
                order and what mode created it.

        This method respects the z-order of the widget it's adding and inserts
        it into the proper position in the widget tree. Higher numbered z order
        values will be inserted after (so they draw on top) of existing ones.

        If the new widget has the same priority of existing widgets, the new
        one is inserted after the widgets of that priority, meaning the newest
        widget will be displayed on top of existing ones with the same
        priority.

        """
        z = widget.config['z']

        if z < 0:
            self.add_widget_to_parent_frame(widget)
            return

        super().add_widget(widget, get_insert_index(z=z, target_widget=self))

        widget.pos = set_position(self.size[0], self.size[1],
                                  widget.width, widget.height,
                                  widget.config['x'], widget.config[
                                      'y'], widget.config['h_pos'],
                                  widget.config['v_pos'])

    def remove_widgets_by_mode(self, mode):
        for widget in [x for x in self.children if x.mode == mode]:
            self.remove_widget(widget)

    def add_widget_to_parent_frame(self, widget):
        """Adds this widget to this slide's parent frame instead of to this
        slide.

        Args:
            widget:
                The widget object.

        Widgets added to the parent slide_frame stay active and visible even
        if the slide in the frame changes.

        Note that negative z-order values tell the widget it should be applied
        to the parent frame instead of the slide, but the absolute value of the
        values is used to control their z-order. e.g. -100 widget shows on top
        of a -50 widget.

        """
        self.parent.parent.add_widget(widget)

    def prepare_for_removal(self, widget=None):
        pass

        # TODO what do we have to do here? I assume something? Remove from
        # active slide list?
