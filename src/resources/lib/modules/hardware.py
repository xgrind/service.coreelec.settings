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

# CEC Wake Up flags from u-boot(bl301)
CEC_FUNC_MASK = 0
AUTO_POWER_ON_MASK = 3
STREAMPATH_POWER_ON_MASK = 4
ACTIVE_SOURCE_MASK = 6

class hardware:
    ENABLED = False
    need_inject = False
    menu = {'8': {
        'name': 32004,
        'menuLoader': 'load_menu',
        'listTyp': 'list',
        'InfoText': 780,
        }}

    power_compatible_devices = [
        'odroid_n2',
        'odroid_c4',
    ]

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
                    'order': 2,
                    'name': 32401,
                    'not_supported': [],
                    'compatible_model': self.power_compatible_devices,
                    'settings': {
                        'inject_bl301': {
                            'order': 1,
                            'name': 32415,
                            'InfoText': 785,
                            'value': '0',
                            'action': 'set_bl301',
                            'type': 'bool',
                            },
                        'heartbeat': {
                            'order': 2,
                            'name': 32419,
                            'InfoText': 789,
                            'value': '0',
                            'action': 'set_heartbeat',
                            'type': 'bool',
                            },
                        'remote_power': {
                            'order': 3,
                            'name': 32416,
                            'InfoText': 786,
                            'value': '',
                            'action': 'set_remote_power',
                            'type': 'multivalue',
                            'values': ['Unknown'],
                            },
                        'wol': {
                            'order': 4,
                            'name': 32417,
                            'InfoText': 787,
                            'value': '0',
                            'action': 'set_wol',
                            'type': 'bool',
                            },
                        'usbpower': {
                            'order': 5,
                            'name': 32418,
                            'InfoText': 788,
                            'value': '0',
                            'action': 'set_usbpower',
                            'type': 'bool',
                            },
                        },
                    },
                'cec': {
                    'order': 3,
                    'name': 32404,
                    'not_supported': [],
                    'settings': {
                        'cec_name': {
                            'order': 1,
                            'name': 32430,
                            'InfoText': 792,
                            'value': 'CoreELEC',
                            'action': 'set_cec',
                            'type': 'text',
                            },
                        'cec_all': {
                            'order': 2,
                            'name': 32431,
                            'InfoText': 793,
                            'value': '0',
                            'bit': CEC_FUNC_MASK,
                            'action': 'set_cec',
                            'type': 'bool',
                            },
                        'cec_auto_power': {
                            'order': 3,
                            'name': 32432,
                            'InfoText': 794,
                            'value': '0',
                            'bit': AUTO_POWER_ON_MASK,
                            'action': 'set_cec',
                            'type': 'bool',
                            },
                        'cec_streaming': {
                            'order': 4,
                            'name': 32433,
                            'InfoText': 795,
                            'value': '0',
                            'bit': STREAMPATH_POWER_ON_MASK,
                            'action': 'set_cec',
                            'type': 'bool',
                            },
                        'cec_active_route': {
                            'order': 5,
                            'name': 32434,
                            'InfoText': 796,
                            'value': '0',
                            'bit': ACTIVE_SOURCE_MASK,
                            'action': 'set_cec',
                            'type': 'bool',
                            },
                        },
                    },
                'display': {
                    'order': 4,
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
                'performance': {
                    'order': 5,
                    'name': 32403,
                    'not_supported': [],
                    'settings': {
                        'cpu_governor': {
                            'order': 1,
                            'name': 32421,
                            'InfoText': 791,
                            'value': '',
                            'action': 'set_cpu_governor',
                            'type': 'multivalue',
                            'values': ['ondemand', 'performance'],
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
            if not 'hidden' in self.struct['fan']:
                self.initialize_fan()
            self.set_cpu_governor()
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
        if self.struct['power']['settings']['inject_bl301']['value'] == '1':
            self.oe.set_busy(1)
            xbmcDialog = xbmcgui.Dialog()

            if hardware.need_inject:
                IBL_Code = self.run_inject_bl301('-Y')

                if IBL_Code == 0:
                    self.load_values()
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

                hardware.need_inject = False

            self.oe.set_busy(0)
        self.oe.dbg_log('hardware::exit', 'exit_function', 0)
        pass

    def check_compatibility(self):
        try:
            self.oe.dbg_log('hardware::check_compatibility', 'enter_function', 0)
            ret = False
            dtname = self.oe.get_dtname()
            ret = any(substring in dtname for substring in self.struct['power']['compatible_model'])
            self.oe.dbg_log('hardware::check_compatibility', 'exit_function, ret: %s' % ret, 0)
        except Exception, e:
            self.oe.dbg_log('hardware::check_compatibility', 'ERROR: (' + repr(e) + ')')
        finally:
            return ret

    def run_inject_bl301(self, parameter=''):
        try:
            self.oe.dbg_log('hardware::run_inject_bl301', 'enter_function, parameter: %s' % parameter, 0)
            IBL = subprocess.Popen(["/usr/sbin/inject_bl301", parameter], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            IBL.wait()
            lines = IBL.stdout.readlines()
            if len(lines) > 0:
                f = open("/storage/inject_bl301.log",'w')
                f.writelines(lines)
                f.close()
            self.oe.dbg_log('hardware::run_inject_bl301', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::run_inject_bl301', 'ERROR: (' + repr(e) + ')')
        finally:
            return IBL.returncode

    def inject_check_compatibility(self):
        try:
            self.oe.dbg_log('hardware::inject_check_compatibility', 'enter_function', 0)
            ret = False
            if os.path.exists('/usr/sbin/inject_bl301'):
                if self.run_inject_bl301('-c') == 0:
                    ret = True
            self.oe.dbg_log('hardware::inject_check_compatibility', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::inject_check_compatibility', 'ERROR: (' + repr(e) + ')')
        finally:
            return ret

    def load_values(self):
        try:
            self.oe.dbg_log('hardware::load_values', 'enter_function', 0)

            if not os.path.exists('/sys/class/fan'):
                self.struct['fan']['hidden'] = 'true'
            else:
                value = self.oe.read_setting('hardware', 'fan_mode')
                if not value is None:
                    self.struct['fan']['settings']['fan_mode']['value'] = value
                value = self.oe.read_setting('hardware', 'fan_level')
                if not value is None:
                    self.struct['fan']['settings']['fan_level']['value'] = value

            if not os.path.exists('/sys/firmware/devicetree/base/leds/blueled'):
                self.struct['power']['settings']['heartbeat']['hidden'] = 'true'
            else:
                if 'hidden' in self.struct['power']['settings']['heartbeat']:
                    del self.struct['power']['settings']['heartbeat']['hidden']
                heartbeat = self.oe.get_config_ini('heartbeat', '1')
                if heartbeat == '' or "1" in heartbeat:
                    self.struct['power']['settings']['heartbeat']['value'] = '1'
                if "0" in heartbeat:
                    self.struct['power']['settings']['heartbeat']['value'] = '0'


            if not self.inject_check_compatibility():
                self.struct['power']['settings']['inject_bl301']['hidden'] = 'true'
                self.struct['power']['settings']['inject_bl301']['value'] = '0'
            else:
                if 'hidden' in self.struct['power']['settings']['inject_bl301']:
                    del self.struct['power']['settings']['inject_bl301']['hidden']
                if os.path.exists('/tmp/bl301_injected'):
                    self.struct['power']['settings']['inject_bl301']['value'] = '1'
                else:
                    self.struct['power']['settings']['inject_bl301']['value'] = '0'

            power_setting_visible = bool(int(self.struct['power']['settings']['inject_bl301']['value'])) or self.check_compatibility()

            if not power_setting_visible:
                self.struct['cec']['hidden'] = 'true'
            else:
                if 'hidden' in self.struct['cec']:
                    del self.struct['cec']['hidden']

                if not self.struct['power']['settings']['inject_bl301']['value'] == '1':
                    self.struct['cec']['settings']['cec_name']['hidden'] = 'true'
                else:
                    if 'hidden' in self.struct['cec']['settings']['cec_name']:
                        del self.struct['cec']['settings']['cec_name']['hidden']
                    self.struct['cec']['settings']['cec_name']['value'] = self.oe.get_config_ini('cec_osd_name', 'CoreELEC')

                cec_func_config = int(self.oe.get_config_ini('cec_func_config', '7f'), 16)
                bit = self.struct['cec']['settings']['cec_all']['bit']
                self.struct['cec']['settings']['cec_all']['value'] = str((cec_func_config & (1 << bit)) >> bit)

                if self.struct['cec']['settings']['cec_all']['value'] == '1':
                    bit = self.struct['cec']['settings']['cec_auto_power']['bit']
                    self.struct['cec']['settings']['cec_auto_power']['value'] = str((cec_func_config & (1 << bit)) >> bit)
                    bit = self.struct['cec']['settings']['cec_streaming']['bit']
                    self.struct['cec']['settings']['cec_streaming']['value'] = str((cec_func_config & (1 << bit)) >> bit)
                    bit = self.struct['cec']['settings']['cec_active_route']['bit']
                    self.struct['cec']['settings']['cec_active_route']['value'] = str((cec_func_config & (1 << bit)) >> bit)

            if not power_setting_visible:
                self.struct['power']['settings']['remote_power']['hidden'] = 'true'
            else:
                if 'hidden' in self.struct['power']['settings']['remote_power']:
                    del self.struct['power']['settings']['remote_power']['hidden']

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

            if not power_setting_visible:
                self.struct['power']['settings']['usbpower']['hidden'] = 'true'
            else:
                if 'hidden' in self.struct['power']['settings']['usbpower']:
                    del self.struct['power']['settings']['usbpower']['hidden']

                usbpower = self.oe.get_config_ini('usbpower', '0')
                if usbpower == '' or "0" in usbpower:
                    self.struct['power']['settings']['usbpower']['value'] = '0'
                if "1" in usbpower:
                    self.struct['power']['settings']['usbpower']['value'] = '1'

            if os.path.exists('/flash/vesa.enable'):
                self.struct['display']['settings']['vesa_enable']['value'] = '1'
            else:
                self.struct['display']['settings']['vesa_enable']['value'] = '0'

            cpu_clusters = ["", "cpu0/"]
            for cluster in cpu_clusters:
                sys_device = '/sys/devices/system/cpu/' + cluster + 'cpufreq/'
                if not os.path.exists(sys_device):
                    continue

                if os.path.exists(sys_device + 'scaling_available_governors'):
                    available_gov = self.oe.load_file(sys_device + 'scaling_available_governors')
                    self.struct['performance']['settings']['cpu_governor']['values'] = available_gov.split()

                value = self.oe.read_setting('hardware', 'cpu_governor')
                if value is None:
                    value = self.oe.load_file(sys_device + 'scaling_governor')

                self.struct['performance']['settings']['cpu_governor']['value'] = value

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
            self.oe.dbg_log('hardware::set_fan_level', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_fan_level', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

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

                    hardware.need_inject = True

            self.oe.dbg_log('hardware::set_remote_power', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_remote_power', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

    def set_bl301(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_bl301', 'enter_function', 0)
            self.oe.set_busy(1)

            xbmcDialog = xbmcgui.Dialog()

            if listItem.getProperty('value') == '1':
                ynresponse = xbmcDialog.yesno(self.oe._(33415).encode('utf-8'), self.oe._(33416).encode('utf-8'), yeslabel=self.oe._(33411).encode('utf-8'), nolabel=self.oe._(32212).encode('utf-8'))

                if ynresponse == 1:
                  IBL_Code = self.run_inject_bl301('-Y')

                  if IBL_Code == 0:
                    self.struct['power']['settings']['inject_bl301']['value'] = '1'
                    subprocess.call("touch /tmp/bl301_injected", shell=True)
                    self.load_values()
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
            else:
                ynresponse = xbmcDialog.yesno(self.oe._(33415).encode('utf-8'), self.oe._(33421).encode('utf-8'), yeslabel=self.oe._(33411).encode('utf-8'), nolabel=self.oe._(32212).encode('utf-8'))

                if ynresponse == 1:
                    IBL = subprocess.Popen(["cat", "/proc/cpuinfo"], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    IBL.wait()
                    serial = next((s for s in IBL.stdout if "Serial" in s), None)
                    if serial != '':
                        filename = '/flash/{0}_bl301.bin'.format([x.strip() for x in serial.split(':')][1])
                        if os.path.exists(filename) and os.path.exists('/dev/bootloader'):
                            self.oe.dbg_log('hardware::set_bl301', 'write %s to /dev/bootloader' % filename, 0)
                            with open(filename, 'rb') as fr:
                                with open('/dev/bootloader', 'wb') as fw:
                                    fw.write(fr.read())
                            self.struct['power']['settings']['inject_bl301']['value'] = '0'
                            subprocess.call("rm -rf /tmp/bl301_injected", shell=True)
                            self.load_values()
                            response = xbmcDialog.ok(self.oe._(33412).encode('utf-8'), self.oe._(33422).encode('utf-8'))

            self.oe.dbg_log('hardware::set_bl301', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_bl301', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

    def set_cec(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_cec', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                if not listItem.getProperty('entry') == 'cec_name':
                    bit = self.struct['cec']['settings'][listItem.getProperty('entry')]['bit']
                    cec_func_config = int(self.oe.get_config_ini('cec_func_config', '7f'), 16)

                    if bit == CEC_FUNC_MASK:
                        for item in self.struct['cec']['settings']:
                            if listItem.getProperty('value') == '0':
                                self.struct['cec']['settings'][item]['value'] = '0'
                            else:
                                self.struct['cec']['settings'][item]['value'] = '1'
                    else:
                        self.struct[listItem.getProperty('category')]['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')
                        if listItem.getProperty('value') == '0':
                            cec_func_config &= ~(1 << bit)
                        else:
                            cec_func_config |= 1 << bit

                    self.oe.set_config_ini("cec_func_config", hex(cec_func_config)[2:])
                else:
                    old_name = self.struct['cec']['settings'][listItem.getProperty('entry')]['value']
                    if not old_name == listItem.getProperty('value')[:14]:
                        self.struct['cec']['settings'][listItem.getProperty('entry')]['value'] = listItem.getProperty('value')[:14]
                        self.oe.set_config_ini("cec_osd_name", self.struct['cec']['settings'][listItem.getProperty('entry')]['value'])

                        hardware.need_inject = True

            self.oe.dbg_log('hardware::set_cec', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_cec', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

    def set_heartbeat(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_heartbeat', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)

                if self.struct['power']['settings']['heartbeat']['value'] == '1':
                    self.oe.set_config_ini("heartbeat", "1")
                else:
                    self.oe.set_config_ini("heartbeat", "0")

            self.oe.dbg_log('hardware::set_heartbeat', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_heartbeat', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

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

                hardware.need_inject = not hardware.need_inject

            self.oe.dbg_log('hardware::set_wol', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_wol', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

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

                hardware.need_inject = not hardware.need_inject

            self.oe.dbg_log('hardware::set_usbpower', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_usbpower', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

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

            self.oe.dbg_log('hardware::set_vesa_enable', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_vesa_enable', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

    def set_cpu_governor(self, listItem=None):
        try:
            self.oe.dbg_log('hardware::set_cpu_governor', 'enter_function', 0)
            self.oe.set_busy(1)
            if not listItem == None:
                self.set_value(listItem)

            value = self.struct['performance']['settings']['cpu_governor']['value']
            if not value is None and not value == '':
                cpu_clusters = ["", "cpu0/", "cpu4/"]
                for cluster in cpu_clusters:
                    sys_device = '/sys/devices/system/cpu/' + cluster + 'cpufreq/scaling_governor'
                    if os.access(sys_device, os.W_OK):
                        cpu_governor_ctl = open(sys_device, 'w')
                        cpu_governor_ctl.write(value)
                        cpu_governor_ctl.close()

            self.oe.dbg_log('hardware::set_cpu_governor', 'exit_function', 0)
        except Exception, e:
            self.oe.dbg_log('hardware::set_cpu_governor', 'ERROR: (%s)' % repr(e), 4)
        finally:
            self.oe.set_busy(0)

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
