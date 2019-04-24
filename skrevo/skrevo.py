#!/usr/bin/env python
# coding=utf-8
import re
import random
from datetime import date

class Skrevo:

    def __init__(self, skrevo, file_path):
        self.file_path = file_path
        self.update(skrevo)

    def reload_from_file(self):
        with open(self.file_path, "r") as skrevo_file:
            self.update(skrevo_file.readlines())

    def save(self):
        with open(self.file_path, "w") as skrevo_file:
            skrevo_file.write(self.skrevo.content + '\n')
    
    def update(self, skrevo_content):
        self.skrevo.content = skrevo_content
