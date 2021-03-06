# -*- coding: utf-8 -*-
"""
Copyright (C) 2016 Korcan Karaokçu <korcankaraokcu@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import gdb
import struct
import sys

# This is some retarded hack
gdbvalue = gdb.parse_and_eval("$PINCE_PATH")
PINCE_PATH = gdbvalue.string()
sys.path.append(PINCE_PATH)  # Adds the PINCE directory to PYTHONPATH to import libraries from PINCE

from libPINCE import SysUtils
from libPINCE import type_defs

INDEX_BYTE = type_defs.VALUE_INDEX.INDEX_BYTE
INDEX_2BYTES = type_defs.VALUE_INDEX.INDEX_2BYTES
INDEX_4BYTES = type_defs.VALUE_INDEX.INDEX_4BYTES
INDEX_8BYTES = type_defs.VALUE_INDEX.INDEX_8BYTES
INDEX_FLOAT = type_defs.VALUE_INDEX.INDEX_FLOAT
INDEX_DOUBLE = type_defs.VALUE_INDEX.INDEX_DOUBLE
INDEX_STRING = type_defs.VALUE_INDEX.INDEX_STRING
INDEX_AOB = type_defs.VALUE_INDEX.INDEX_AOB

index_to_valuetype_dict = type_defs.index_to_valuetype_dict
index_to_struct_pack_dict = type_defs.index_to_struct_pack_dict

inferior = gdb.selected_inferior()
pid = inferior.pid
mem_file = "/proc/" + str(pid) + "/mem"


# This function is used to avoid errors in gdb scripts, because gdb scripts stop working when encountered an error
def issue_command(command, error_message=""):
    try:
        gdb.execute(command)
    except:
        if error_message:
            error_message = str(error_message)
            gdb.execute('echo ' + error_message + '\n')


def read_single_address(address, value_type, length=0, unicode=False, zero_terminate=True):
    try:
        value_type = int(value_type)
    except:
        print(str(value_type) + " is not a valid value index")
        return ""
    try:
        address = int(address, 16)
    except:
        print(str(address) + " is not a valid address")
        return ""
    packed_data = index_to_valuetype_dict.get(value_type, -1)
    if value_type is INDEX_STRING:
        try:
            expected_length = int(length)
        except:
            print(str(length) + " is not a valid length")
            return ""
        if unicode:
            expected_length = length * 2
    elif value_type is INDEX_AOB:
        try:
            expected_length = int(length)
        except:
            print(str(length) + " is not a valid length")
            return ""
    else:
        expected_length = packed_data[0]
        data_type = packed_data[1]
    FILE = open(mem_file, "rb")
    try:
        FILE.seek(address)
        data_read = FILE.read(expected_length)
    except IOError:
        FILE.close()
        print("Can't access the memory at address " + hex(address) + " or offset " + hex(address + expected_length))
        return ""
    FILE.close()
    if value_type is INDEX_STRING:
        if unicode:
            returned_string = data_read.decode("utf-8", "replace")
        else:
            returned_string = data_read.decode("ascii", "replace")
        if zero_terminate:
            if returned_string.startswith('\x00'):
                returned_string = '\x00'
            else:
                returned_string = returned_string.split('\x00')[0]
        return returned_string[0:length]
    elif value_type is INDEX_AOB:
        return " ".join(format(n, '02x') for n in data_read)
    else:
        return struct.unpack_from(data_type, data_read)[0]


def set_single_address(address, value_index, value):
    try:
        address = int(address, 16)
    except:
        print(str(address) + " is not a valid address")
        return
    write_data = SysUtils.parse_string(value, value_index)
    if write_data is None:
        return
    if value_index is INDEX_STRING:
        write_data = bytearray(write_data, "utf-8", "replace")
    elif value_index is INDEX_AOB:
        write_data = bytearray(write_data)
    else:
        data_type = index_to_struct_pack_dict.get(value_index, -1)
        write_data = struct.pack(data_type, write_data)
    FILE = open(mem_file, "rb+")

    # Check SetMultipleAddresses class in GDBCommandExtensions.py to see why we moved away the try/except block
    FILE.seek(address)
    FILE.write(write_data)
    FILE.close()
