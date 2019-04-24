#!/usr/bin/env python
# coding=utf-8
"""skrevo
Usage:
  skrevo [--config FILE] [-o SKREVOFILE]
  skrevo (-h | --help)
  skrevo --version
  skrevo --show-default-bindings
Options:
  -o FILE                             Path to the file where skrevo will save your content [default: ~/skrevo.txt]
  -c FILE --config=FILE               Path to your skrevo configuraton file [default: ~/.skrevorc]
  -h --help                           Show this screen.
  --version                           Show version.
  --show-default-bindings             Show default keybindings in config parser format
                                      Add this to your config file and edit to customize
"""

import sys
import os
import random
import threading
from collections import OrderedDict
from docopt import docopt

import skrevo as SKR
from skrevo.urwid_ui import UrwidUI
from skrevo.keys import KeyBindings
from skrevo.skrevo import Skrevo

import configparser
config_parser_module = configparser

autosave_lock = threading.Lock()


def autosave():
    if not enable_autosave:
        return

    # print "autosaving..."
    with autosave_lock:
        # view.save_todos() # TODO: Saved message isn't displayed, need to force redraw urwid ui?
        view.todos.save()

    # Check the flag once again, as the flag may have been set
    # after the last check but before this statement is executed.
    if enable_autosave:
        global timer
        timer = threading.Timer(30.0, autosave)
        timer.start()


timer = threading.Timer(30.0, autosave)


def exit_with_error(message):
    sys.stderr.write(message.strip(' \n') + '\n')
    print(__doc__.split('\n\n')[1])
    exit(1)


def get_real_path(filename, description):
    # expand enviroment variables and username, get canonical path
    file_path = os.path.realpath(os.path.expanduser(os.path.expandvars(filename)))

    if os.path.isdir(file_path):
        exit_with_error("ERROR: Specified {0} file is a directory.".format(description))

    if not os.path.exists(file_path):
        directory = os.path.dirname(file_path)
        if os.path.isdir(directory):
            # directory exists, but no todo.txt file - create an empty one
            open(file_path, 'a').close()
        else:
            exit_with_error("ERROR: The directory: '{0}' does not exist\n\nPlease create the directory or specify a different\n{0} file on the command line.".format(directory, description))

    return file_path


def get_boolean_config_option(cfg, section, option, default=False):
    value = dict(cfg.items(section)).get(option, default)
    if (type(value) != bool and
        (str(value).lower() == 'true' or
         str(value).lower() == '1')):
        value = True
    else:
        # If present but is not True or 1
        value = False
    return value


def main():
    random.seed()

    # Parse command line
    arguments = docopt(__doc__, version=SKR.version)
    config_file_path = os.path.expanduser(arguments['--config'][0])
    # print(arguments) ; exit(0)

    # Validate readline editing mode option (docopt doesn't handle this)
    # if arguments['--readline-editing-mode'] not in ['vi', 'emacs']:
    #     exit_with_error("--readline-editing-mode must be set to either vi or emacs\n")

    # Parse config file
    cfg = config_parser_module.ConfigParser(allow_no_value=True)
    cfg.read(config_file_path)

    cfg.add_section('keys')
    cfg.add_section('settings')

    if arguments['--show-default-bindings']:
        d = {k: ", ".join(v) for k, v in KeyBindings({}).key_bindings.items()}
        cfg._sections['keys'] = OrderedDict(sorted(d.items(), key=lambda t: t[0]))
        cfg.write(sys.stdout)
        exit(0)

    # Load keybindings specified in the [keys] section of the config file
    keyBindings = KeyBindings(dict(cfg.items('keys')))

    # load the colorscheme defined in the user config, else load the default scheme
    # colorscheme = ColorScheme(dict(cfg.items('settings')).get('colorscheme', 'default'), cfg)

    # Get auto-saving setting (defaults to False)
    global enable_autosave
    enable_autosave = get_boolean_config_option(cfg, 'settings', 'auto-save', default=False)

    # Load the skrevo.txt file specified in the [settings] section of the config file
    # a skrevo.txt file on the command line takes precedence
    skrevo_file = dict(cfg.items('settings')).get('content-file', arguments['-o'])
    if arguments['-o']:
        skrevo_file = os.path.expanduser(arguments['-o'])

    if skrevo_file is None:
        exit_with_error("ERROR: No skrevo file specified. Either specify one as an argument on the command line or set it in your configuration file ({0}).".format(config_file_path))

    skrevo_file_path = get_real_path(skrevo_file, 'skrevo.txt')

    try:
        with open(skrevo_file_path, "w+") as skrevo_file:
            skrevo = Skrevo(skrevo_file.readlines(), skrevo_file_path)
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        exit_with_error("ERROR: unable to open {0}\n\nEither specify one as an argument on the command line or set it in your configuration file ({1}).".format(skrevo_file_path, config_file_path))
        skrevo = Skrevo([], skrevo_file_path)

    show_toolbar = get_boolean_config_option(cfg, 'settings', 'show-toolbar')
    enable_word_wrap = get_boolean_config_option(cfg, 'settings', 'enable-word-wrap')

    global view
    view = UrwidUI(skrevo)

    timer.start()

    view.main(  # start up the urwid UI event loop
        enable_word_wrap,
        show_toolbar)

    # UI is now shut down

    # Shut down the auto-saving thread.
    enable_autosave = False
    timer.cancel()

    # Final save
    with autosave_lock:
        # print("Writing: {0}".format(skrevo_file_path))
        view.skrevo.save()

    exit(0)


if __name__ == '__main__':
    main()