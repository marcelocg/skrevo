#!/usr/bin/env python
# coding=utf-8

import urwid
import collections

# Modified from http://wiki.goffi.org/wiki/Urwid-satext/en

class UrwidUI:

    def __init__(self, skrevo):
        self.wrapping = collections.deque(['clip', 'space'])
        self.border = collections.deque(['no border', 'bordered'])

        self.skrevo = skrevo
        # self.key_bindings = key_bindings

        # self.colorscheme = colorscheme
        # self.palette = [(key, '', '', '', value['fg'], value['bg']) for key, value in self.colorscheme.colors.items()]

        self.toolbar_is_open = False
        self.help_panel_is_open = False
        # self.filter_panel_is_open = False
        # self.filtering = False
        # self.searching = False
        # self.search_string = ''
        # self.yanked_text = ''

    def visible_lines(self):
        lines = self.loop.screen_size[1] - 1  # minus one for the header
        if self.toolbar_is_open:
            lines -= 1
        # if self.searching:
        #     lines -= 1
        return lines

    def move_selection_down(self):
        self.listbox.keypress((0, self.visible_lines()), 'down')

    def move_selection_up(self):
        self.listbox.keypress((0, self.visible_lines()), 'up')

    def move_selection_top(self):
        self.listbox.set_focus(0)

    def move_selection_bottom(self):
        self.listbox.set_focus(len(self.listbox.body) - 1)

    def toggle_help_panel(self, button=None):
        if self.help_panel_is_open:
            self.view.contents.pop()
            self.help_panel_is_open = False
            # set header line to word-wrap contents
            # for header_column in self.frame.header.original_widget.contents:
            #     header_column[0].set_wrap_mode('space')
        else:
            self.help_panel = self.create_help_panel()
            self.view.contents.append((self.help_panel, self.view.options(width_type='weight', width_amount=3)))
            self.view.set_focus(1)
            self.help_panel_is_open = True
            # set header line to clip contents
            # for header_column in self.frame.header.original_widget.contents:
            #     header_column[0].set_wrap_mode('clip')


    def toggle_wrapping(self, checkbox=None, state=None):
        self.wrapping.rotate(1)
        for widget in self.listbox.body:
            widget.wrapping = self.wrapping[0]
            widget.update_todo()
        if self.toolbar_is_open:
            self.update_header()

    def toggle_border(self, checkbox=None, state=None):
        self.border.rotate(1)
        for widget in self.listbox.body:
            widget.border = self.border[0]
            widget.update_todo()
        if self.toolbar_is_open:
            self.update_header()

    def toggle_toolbar(self):
        self.toolbar_is_open = not self.toolbar_is_open
        self.update_header()

    def save_skrevo(self, button=None):
        self.skrevo.save()
        self.update_header("Saved")

    def reload_skrevo_from_file(self, button=None):
        self.clear_skrevo_content()
        self.skrevo.reload_from_file()
        self.update_header("Reloaded")

    def keystroke(self, input):
        focus, focus_index = self.listbox.get_focus()

        if self.key_bindings.is_binded_to(input, 'quit'):
            raise urwid.ExitMainLoop()

        # Movement
        elif self.key_bindings.is_binded_to(input, 'top'):
            self.move_selection_top()
        elif self.key_bindings.is_binded_to(input, 'bottom'):
            self.move_selection_bottom()
        elif self.key_bindings.is_binded_to(input, 'swap-down'):
            self.swap_down()
        elif self.key_bindings.is_binded_to(input, 'swap-up'):
            self.swap_up()
        elif self.key_bindings.is_binded_to(input, 'change-focus'):
            current_focus = self.frame.get_focus()
            if current_focus == 'body':

                if self.filter_panel_is_open and self.toolbar_is_open:

                    if self.view.focus_position == 1:
                        self.view.focus_position = 0
                        self.frame.focus_position = 'header'
                    elif self.view.focus_position == 0:
                        self.view.focus_position = 1

                elif self.toolbar_is_open:
                    self.frame.focus_position = 'header'

                elif self.filter_panel_is_open:
                    if self.view.focus_position == 1:
                        self.view.focus_position = 0
                    elif self.view.focus_position == 0:
                        self.view.focus_position = 1

            elif current_focus == 'header':
                self.frame.focus_position = 'body'

        # View options
        elif self.key_bindings.is_binded_to(input, 'toggle-help'):
            self.toggle_help_panel()
        elif self.key_bindings.is_binded_to(input, 'toggle-toolbar'):
            self.toggle_toolbar()
        elif self.key_bindings.is_binded_to(input, 'toggle-filter'):
            self.toggle_filter_panel()
        elif self.key_bindings.is_binded_to(input, 'clear-filter'):
            self.clear_filters()
        elif self.key_bindings.is_binded_to(input, 'toggle-wrapping'):
            self.toggle_wrapping()
        elif self.key_bindings.is_binded_to(input, 'toggle-borders'):
            self.toggle_border()
        elif self.key_bindings.is_binded_to(input, 'toggle-sorting'):
            self.toggle_sorting()

        elif self.key_bindings.is_binded_to(input, 'search'):
            self.start_search()
        elif self.key_bindings.is_binded_to(input, 'search-clear'):
            if self.searching:
                self.clear_search_term()

        # Editing
        elif self.key_bindings.is_binded_to(input, 'toggle-complete'):
            if focus.todo.is_complete():
                focus.todo.incomplete()
            else:
                focus.todo.complete()
            focus.update_todo()
            self.update_header()

        elif self.key_bindings.is_binded_to(input, 'archive'):
            self.archive_done_todos()

        elif self.key_bindings.is_binded_to(input, 'delete'):
            if self.todos.todo_items:
                i = focus.todo.raw_index
                self.todos.delete(i)
                del self.listbox.body[focus_index]
                self.update_header()

        elif self.key_bindings.is_binded_to(input, 'append'):
            self.add_new_todo(position='append')
        elif self.key_bindings.is_binded_to(input, 'insert-before'):
            self.add_new_todo(position='insert_before')
        elif self.key_bindings.is_binded_to(input, 'insert-after'):
            self.add_new_todo(position='insert_after')

        elif self.key_bindings.is_binded_to(input, 'priority-up'):
            self.adjust_priority(focus, up=True)

        elif self.key_bindings.is_binded_to(input, 'priority-down'):
            self.adjust_priority(focus, up=False)

        # Save current file
        elif self.key_bindings.is_binded_to(input, 'save'):
            self.save_todos()

        # Reload original file
        elif self.key_bindings.is_binded_to(input, 'reload'):
            self.reload_todos_from_file()

    def adjust_priority(self, focus, up=True):
            priorities = ['', 'A', 'B', 'C', 'D', 'E', 'F']
            if up:
                new_priority = priorities.index(focus.todo.priority) + 1
            else:
                new_priority = priorities.index(focus.todo.priority) - 1

            if new_priority < 0:
                focus.todo.change_priority(priorities[len(priorities) - 1])
            elif new_priority < len(priorities):
                focus.todo.change_priority(priorities[new_priority])
            else:
                focus.todo.change_priority(priorities[0])

            focus.update_todo()

    def add_new_todo(self, position=False):
        if len(self.listbox.body) == 0:
            position = 'append'
        else:
            focus_index = self.listbox.get_focus()[1]

        if self.filtering:
            position = 'append'

        if position is 'append':
            new_index = self.todos.append('', add_creation_date=False)
            self.listbox.body.append(TodoWidget(self.todos[new_index], self.key_bindings, self.colorscheme, self, editing=True, wrapping=self.wrapping[0], border=self.border[0]))
        else:
            if position is 'insert_after':
                new_index = self.todos.insert(focus_index + 1, '', add_creation_date=False)
            elif position is 'insert_before':
                new_index = self.todos.insert(focus_index, '', add_creation_date=False)

            self.listbox.body.insert(new_index, TodoWidget(self.todos[new_index], self.key_bindings, self.colorscheme, self, editing=True, wrapping=self.wrapping[0], border=self.border[0]))

        if position:
            if self.filtering:
                self.listbox.set_focus(len(self.listbox.body) - 1)
            else:
                self.listbox.set_focus(new_index)
            # edit_widget = self.listbox.body[new_index]._w
            # edit_widget.edit_text += ' '
            # edit_widget.set_edit_pos(len(self.todos[new_index].raw) + 1)
            self.update_header()

    def create_header(self, message=""):
        return urwid.AttrMap(
            urwid.Columns([
                urwid.Text([
                    ('header_word_count', "{0} Words ".format(self.skrevo.word_count())),
                    ('header_char_count', " {0} Chars ".format(self.skrevo.__len__())),
                    ('header_line_count', " {0} Lines ".format(self.skrevo.line_count())),
                ]),
                # urwid.Text( " skrevo ", align='center' ),
                urwid.Text(('header_file', "{0}  {1} ".format(message, self.skrevo.file_path)), align='right')
            ]), 'header')

    def create_toolbar(self):
        return urwid.AttrMap(urwid.Columns([
            urwid.Padding(
                urwid.AttrMap(
                    urwid.CheckBox([('header_file', 'w'), 'ord wrap'], state=(self.wrapping[0] == 'space'), on_state_change=self.toggle_wrapping),
                    'header', 'plain_selected'), right=2),

            urwid.Padding(
                urwid.AttrMap(
                    urwid.Button([('header_file', 'R'), 'eload'], on_press=self.reload_todos_from_file),
                    'header', 'plain_selected'), right=2),

            urwid.Padding(
                urwid.AttrMap(
                    urwid.Button([('header_file', 'S'), 'ave'], on_press=self.save_todos),
                    'header', 'plain_selected'), right=2),

        ]), 'header')

    def create_footer(self):
        w = None
        return w

    def update_header(self, message=""):
        if self.toolbar_is_open:
            self.frame.header = urwid.Pile([self.create_header(message), self.create_toolbar()])
        else:
            self.frame.header = self.create_header(message)

    def update_footer(self, message=""):
        self.frame.footer = self.create_footer()

    def main(self,
             enable_word_wrap=False,
             show_toolbar=False):

        self.header = self.create_header()
        self.footer = self.create_footer()

        self.listbox = ViListBox(self.key_bindings, urwid.SimpleListWalker(
            [TodoWidget(t, self.key_bindings, self.colorscheme, self) for t in self.todos.todo_items]
        ))

        self.frame = urwid.Frame(urwid.AttrMap(self.listbox, 'plain'), header=self.header, footer=self.footer)

        self.view = ViColumns(self.key_bindings,
                              [
                                  ('weight', 2, self.frame)
                              ])

        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.keystroke)
        self.loop.screen.set_terminal_properties(colors=256)

        if enable_word_wrap:
            self.toggle_wrapping()
        if show_toolbar:
            self.toggle_toolbar()

        self.loop.run()