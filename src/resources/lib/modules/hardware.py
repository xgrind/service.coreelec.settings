# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2018-present Team CoreELEC (https://coreelec.org)

import os
import re
import glob
import xbmc
import xbmcgui
import oeWindows
import threading
import subprocess
import shutil


class hardware:

    ENABLED = False
    menu = {'8': {
        'name': 32004,
        'menuLoader': 'load_menu',
        'listTyp': 'list',
        'InfoText': 780,
        }}

    def __init__(self, oeMain):
        try:
            oeMain.dbg_log('hardware::__init__', 'enter_function', 0)
            self.oe = oeMain
            self.struct = {
                'fan': {
                    'order': 1,
                    'name': 32400,
                    'not_supported': [],
                    'settings': {
                        'fan_mode': {
                            'order': 1,
                            'name': 32410,
                            'InfoText': 781,
                            'value': 'off',
                            'action': 'initialize_fan',
                            'type': 'multivalue',
                            'values': ['off', 'auto', 'manual'],
                            },
                        'fan_level': {
                            'order': 2,
                            'name': 32411,
                            'InfoText': 782,
                            'value': '0',
                            'action': 'set_fan_level',
                            'type': 'multivalue',
                            'values': ['0','1','2','3'],
                            'parent': {
                                'entry': 'fan_mode',
                                'value': ['manual'],
                                },
                            },

                        },
                    },

                }

            self.oe.dbg_log('hardware::__init__', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::__init__', 'ERROR: (' + repr(e) + ')')

    def start_service(self):
        try:
            self.oe.dbg_log('hardware::start_service', 'enter_function', 0)
            self.load_values()
            self.initialize_fan()
            self.oe.dbg_log('hardware::start_service', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::start_service', 'ERROR: (' + repr(e) + ')')

    def stop_service(self):
        try:
            self.oe.dbg_log('hardware::stop_service', 'enter_function', 0)
            self.oe.dbg_log('hardware::stop_service', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::stop_service', 'ERROR: (' + repr(e) + ')')

    def do_init(self):
        try:
            self.oe.dbg_log('hardware::do_init', 'enter_function', 0)
            self.load_values()
            self.oe.dbg_log('hardware::do_init', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::do_init', 'ERROR: (' + repr(e) + ')')

    def exit(self):
        self.oe.dbg_log('hardware::exit', 'enter_function', 0)
        self.oe.dbg_log('hardware::exit', 'exit_function', 0)
        pass

    def load_values(self):
        try:
            self.oe.dbg_log('connman::load_values', 'enter_function', 0)

            value = self.oe.read_setting('hardware', 'fan_mode')
            if not value is None:
                self.struct['fan']['settings']['fan_mode']['value'] = value
            value = self.oe.read_setting('hardware', 'fan_level')
            if not value is None:
                self.struct['fan']['settings']['fan_level']['value'] = value


            self.oe.dbg_log('hardware::load_values', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::load_values', 'ERROR: (' + repr(e) + ')')


    def initialize_fan(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::initialize_fan', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)
            if os.access('/sys/class/fan/enable', os.W_OK) and os.access('/sys/class/fan/mode', os.W_OK):
                if self.struct['fan']['settings']['fan_mode']['value'] == 'off':
                    fan_enable = open('/sys/class/fan/enable', 'w')
                    fan_enable.write('0')
                    fan_enable.close()
                if self.struct['fan']['settings']['fan_mode']['value'] == 'manual':
                    fan_enable = open('/sys/class/fan/enable', 'w')
                    fan_enable.write('1')
                    fan_enable.close()
                    fan_mode_ctl = open('/sys/class/fan/mode', 'w')
                    fan_mode_ctl.write('0')
                    fan_mode_ctl.close()
                    self.set_fan_level()
                if self.struct['fan']['settings']['fan_mode']['value'] == 'auto':
                    fan_enable = open('/sys/class/fan/enable', 'w')
                    fan_enable.write('1')
                    fan_enable.close()
                    fan_mode_ctl = open('/sys/class/fan/mode', 'w')
                    fan_mode_ctl.write('1')
                    fan_mode_ctl.close()
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::initialize_fan', 'exit_function', 0)
        except Exception, e:
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::initialize_fan', 'ERROR: (%s)' % repr(e), 4)

    def set_fan_level(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_fan_level', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)
            if os.access('/sys/class/fan/level', os.W_OK):
                if not self.struct['fan']['settings']['fan_level']['value'] is None and not self.struct['fan']['settings']['fan_level']['value'] == '':
                    fan_level_ctl = open('/sys/class/fan/level', 'w')
                    fan_level_ctl.write(self.struct['fan']['settings']['fan_level']['value'])
                    fan_level_ctl.close()
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_fan_level', 'exit_function', 0)
        except Exception, e:
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_fan_level', 'ERROR: (%s)' % repr(e), 4)

    def load_menu(self, focusItem):
        try:
            self.oe.dbg_log('hardware::load_menu', 'enter_function', 0)
            self.oe.winOeMain.build_menu(self.struct)
            self.oe.dbg_log('hardware::load_menu', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::load_menu', 'ERROR: (' + repr(e) + ')')

    def set_value(self, listItem):
        try:
            self.oe.dbg_log('hardware::set_value', 'enter_function', 0)
            self.struct[listItem.getProperty('category')]['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')
            self.oe.write_setting('hardware', listItem.getProperty('entry'), unicode(listItem.getProperty('value')))
            self.oe.dbg_log('hardware::set_value', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_value', 'ERROR: (' + repr(e) + ')')
