#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2010-2020, Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Neotion nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NEOTION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from doctest import testmod
from os import environ
from sys import modules
from time import sleep, time as now
from unittest import TestCase, TestSuite, makeSuite, main as ut_main
from pyftdi.ftdi import Ftdi
from pyftdi.usbtools import UsbTools, UsbToolsError


class FtdiTestCase(TestCase):
    """FTDI driver test case"""

    def test_multiple_interface(self):
        # the following calls used to create issues (several interfaces from
        # the same device). The test expects an FTDI 2232H here
        ftdi1 = Ftdi()
        ftdi1.open(vendor=0x403, product=0x6010, interface=1)
        ftdi2 = Ftdi()
        ftdi2.open(vendor=0x403, product=0x6010, interface=2)
        for x in range(5):
            print("If#1: ", hex(ftdi1.poll_modem_status()))
            print("If#2: ", ftdi2.modem_status())
            sleep(0.500)
        ftdi1.close()
        ftdi2.close()


class HotplugTestCase(TestCase):

    def test_hotplug_discovery(self):
        """Demonstrate how to connect to an hotplugged FTDI device, i.e.
           an FTDI device that is connected after the initial attempt to
           enumerate it on the USB bus."""
        url = environ.get('FTDI_DEVICE', 'ftdi:///1')
        ftdi = Ftdi()
        timeout = now() + 5.0  # sanity check: bail out after 10 seconds
        while now() < timeout:
            try:
                ftdi.open_from_url(url)
                break
            except UsbToolsError:
                UsbTools.flush_cache()
                sleep(0.05)
                continue
        self.assertTrue(ftdi.is_connected, 'Unable to connect to FTDI')
        print('Connected to FTDI', url)


class ResetTestCase(TestCase):

    def test_simple_reset(self):
        """Demonstrate how to connect to an hotplugged FTDI device, i.e.
           an FTDI device that is connected after the initial attempt to
           enumerate it on the USB bus."""
        url = environ.get('FTDI_DEVICE', 'ftdi:///1')
        ftdi = Ftdi()
        ftdi.open_from_url(url)
        self.assertTrue(ftdi.is_connected, 'Unable to connect to FTDI')
        ftdi.close()
        self.assertFalse(ftdi.is_connected, 'Unable to close connection')
        ftdi.open_from_url(url)
        self.assertTrue(ftdi.is_connected, 'Unable to connect to FTDI')
        ftdi.reset(False)

    def test_dual_if_reset(self):
        """Demonstrate how to connect to an hotplugged FTDI device, i.e.
           an FTDI device that is connected after the initial attempt to
           enumerate it on the USB bus."""
        url1 = environ.get('FTDI_DEVICE', 'ftdi:///1')
        url2 = environ.get('FTDI_DEVICE', 'ftdi:///2')
        ftdi1 = Ftdi()
        ftdi2 = Ftdi()
        ftdi1.open_from_url(url1)
        self.assertTrue(ftdi1.is_connected, 'Unable to connect to FTDI')
        ftdi2.open_from_url(url2)
        # use latenty setting to set/test configuration is preserved
        ftdi2.set_latency_timer(128)
        # should be the same value
        self.assertEqual(ftdi2.get_latency_timer(), 128)
        self.assertTrue(ftdi2.is_connected, 'Unable to connect to FTDI')
        ftdi1.close()
        self.assertFalse(ftdi1.is_connected, 'Unable to close connection')
        # closing first connection should not alter second interface
        self.assertEqual(ftdi2.get_latency_timer(), 128)
        ftdi1.open_from_url(url1)
        self.assertTrue(ftdi1.is_connected, 'Unable to connect to FTDI')
        # a FTDI reset should not alter settings...
        ftdi1.reset(False)
        self.assertEqual(ftdi2.get_latency_timer(), 128)
        # ... however performing a USB reset through any interface should alter
        # any previous settings made to all interfaces
        ftdi1.reset(True)
        self.assertNotEqual(ftdi2.get_latency_timer(), 128)


def suite():
    suite_ = TestSuite()
    #suite_.addTest(makeSuite(FtdiTestCase, 'test'))
    #suite_.addTest(makeSuite(HotplugTestCase, 'test'))
    suite_.addTest(makeSuite(ResetTestCase, 'test'))
    return suite_


if __name__ == '__main__':
    testmod(modules[__name__])
    ut_main(defaultTest='suite')
