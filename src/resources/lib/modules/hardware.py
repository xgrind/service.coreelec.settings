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

    remotes = [
        {
            "name": "Hardkernel",
            "remotewakeup": "0x23dc4db2",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Minix",
            "remotewakeup": "0xe718fe01",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Beelink",
            "remotewakeup": "0xa659ff00",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Beelink 2",
            "remotewakeup": "0xae517f80",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Khadas",
            "remotewakeup": "0xeb14ff00",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "Khadas VTV",
            "remotewakeup": "0xff00fe01",
            "decode_type": "0x0",
            "remotewakeupmask": "0xffffffff"
        },
        {
            "name": "MCE",
            "remotewakeup": "0x800f040c",
            "decode_type": "0x5",
            "remotewakeupmask": "0xffff7fff"
        },
    ]

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
                'power': {
                    'order': 1,
                    'name': 32401,
                    'not_supported': [],
                    'settings': {
                        'inject_bl301': {
                            'order': 1,
                            'name': 32415,
                            'InfoText': 785,
                            'value': '0',
                            'action': 'set_bl301',
                            'type': 'button',
                            },
                        'remote_power': {
                            'order': 2,
                            'name': 32416,
                            'InfoText': 786,
                            'value': '',
                            'action': 'set_remote_power',
                            'type': 'multivalue',
                            'values': ['Unkown'],
                            },
                        'wol': {
                            'order': 3,
                            'name': 32417,
                            'InfoText': 787,
                            'value': '0',
                            'action': 'set_wol',
                            'type': 'bool',
                            },
                        'usbpower': {
                            'order': 4,
                            'name': 32418,
                            'InfoText': 788,
                            'value': '0',
                            'action': 'set_usbpower',
                            'type': 'bool',
                            },
                        },
                    },
                'display': {
                    'order': 3,
                    'name': 32402,
                    'not_supported': [],
                    'settings': {
                        'vesa_enable': {
                            'order': 1,
                            'name': 32420,
                            'InfoText': 790,
                            'value': '0',
                            'action': 'set_vesa_enable',
                            'type': 'bool',
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

            if not os.path.exists('/usr/sbin/inject_bl301'):
                self.struct['power']['settings']['inject_bl301']['hidden'] = 'true'
                self.struct['power']['settings']['inject_bl301']['value'] = '0'


            remotewakeup = self.oe.get_config_ini('remotewakeup')

            remote_names = []
            remote_is_known = 0
            for remote in self.remotes:
              remote_names.append(remote["name"])
              if remote["remotewakeup"] in remotewakeup:
                self.struct['power']['settings']['remote_power']['value'] = remote["name"]
                remote_is_known = 1

            if remotewakeup == '':
                self.struct['power']['settings']['remote_power']['value'] = ''
            if remotewakeup != '' and remote_is_known == 0:
                self.struct['power']['settings']['remote_power']['value'] = 'Custom'

            self.struct['power']['settings']['remote_power']['values'] = remote_names

            wol = self.oe.get_config_ini('wol', '0')
            if wol == '' or "0" in wol:
                self.struct['power']['settings']['wol']['value'] = '0'
            if "1" in wol:
                self.struct['power']['settings']['wol']['value'] = '1'

            usbpower = self.oe.get_config_ini('usbpower', '0')
            if usbpower == '' or "0" in usbpower:
                self.struct['power']['settings']['usbpower']['value'] = '0'
            if "1" in usbpower:
                self.struct['power']['settings']['usbpower']['value'] = '1'

            if os.path.exists('/flash/vesa.enable'):
                self.struct['display']['settings']['vesa_enable']['value'] = '1'
            else:
                self.struct['display']['settings']['vesa_enable']['value'] = '0'

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

    def set_remote_power(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_remote_power', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)

            for remote in self.remotes:
                if self.struct['power']['settings']['remote_power']['value'] == remote["name"]:
                    self.oe.set_config_ini("remotewakeup", "\'" + remote["remotewakeup"] + "\'")
                    self.oe.set_config_ini("decode_type", "\'" + remote["decode_type"] + "\'")
                    self.oe.set_config_ini("remotewakeupmask" , "\'" + remote["remotewakeupmask"] + "\'")

            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_remote_power', 'exit_function', 0)
        except Exception, e:
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_remote_power', 'ERROR: (%s)' % repr(e), 4)

    def set_bl301(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_bl301', 'enter_function', 0)
            self.oe.set_busy(1)

            xbmcDialog = xbmcgui.Dialog()
            ynresponse = xbmcDialog.yesno(self.oe._(33415).encode('utf-8'), self.oe._(33416).encode('utf-8'), yeslabel=self.oe._(33411).encode('utf-8'), nolabel=self.oe._(32212).encode('utf-8'))

            if ynresponse == 1:
              IBL = subprocess.Popen(["/usr/sbin/inject_bl301", "-Y"], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
              IBL.wait()
              IBL_Code = IBL.returncode
              f = open("/storage/inject_bl301.log",'w')
              f.writelines(IBL.stdout.readlines())
              f.close()

              if IBL_Code == 0:
                response = xbmcDialog.ok(self.oe._(33412).encode('utf-8'), self.oe._(33417).encode('utf-8'))
              elif IBL_Code == 1:
                xbmcDialog = xbmcgui.Dialog()
                response = xbmcDialog.ok(self.oe._(33413).encode('utf-8'), self.oe._(33420).encode('utf-8'))
              elif IBL_Code == (-2 & 0xff):
                xbmcDialog = xbmcgui.Dialog()
                response = xbmcDialog.ok(self.oe._(33414).encode('utf-8'), self.oe._(33419).encode('utf-8'))
              else:
                xbmcDialog = xbmcgui.Dialog()
                response = xbmcDialog.ok(self.oe._(33414).encode('utf-8'), self.oe._(33418).encode('utf-8') % IBL_Code)

              if IBL_Code != 0:
                self.oe.dbg_log('hardware::set_bl301', 'ERROR: (%d)' % IBL_Code, 4)

            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_bl301', 'exit_function', 0)
        except Exception, e:
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_bl301', 'ERROR: (%s)' % repr(e), 4)

    def set_wol(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_wol', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)

                if self.struct['power']['settings']['wol']['value'] == '1':
                    self.oe.set_config_ini("wol", "1")
                else:
                    self.oe.set_config_ini("wol", "0")


            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_wol', 'exit_function', 0)
        except Exception, e:
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_wol', 'ERROR: (%s)' % repr(e), 4)

    def set_usbpower(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_usbpower', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)

                if self.struct['power']['settings']['usbpower']['value'] == '1':
                    self.oe.set_config_ini("usbpower", "1")
                else:
                    self.oe.set_config_ini("usbpower", "0")


            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_usbpower', 'exit_function', 0)
        except Exception, e:
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_usbpower', 'ERROR: (%s)' % repr(e), 4)

    def set_vesa_enable(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_vesa_enable', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)

                if self.struct['display']['settings']['vesa_enable']['value'] == '1':
                  ret = subprocess.call("mount -o remount,rw /flash", shell=True)
                  ret = subprocess.call("touch /flash/vesa.enable", shell=True)
                  ret = subprocess.call("mount -o remount,ro /flash", shell=True)
                else:
                  if os.path.exists("/flash/vesa.enable"):
                    ret = subprocess.call("mount -o remount,rw /flash", shell=True)
                    os.remove("/flash/vesa.enable")
                    ret = subprocess.call("mount -o remount,ro /flash", shell=True)

            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_vesa_enable', 'exit_function', 0)
        except Exception, e:
            self.oe.set_busy(0)
            self.oe.dbg_log('hardware::set_vesa_enable', 'ERROR: (%s)' % repr(e), 4)


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
