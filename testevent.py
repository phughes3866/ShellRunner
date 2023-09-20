import sublime
import sublime_plugin

class EventDoEversoCommandCommand(sublime_plugin.WindowCommand):

    def run(self, event=None, **kwargs):
        self.myargs = kwargs
        self.eventy = event
        print('we run man: {}, kwargs: {}'.format(self.eventy, self.myargs))
        return

    def want_event(self):
        return True

    def input(self, args):
        return None
