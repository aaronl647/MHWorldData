from collections.abc import Sequence
import struct
import inspect
from typing import get_type_hints

import mhw_armor_edit.ftypes as ft

class Readable:
    def __init__(self):
        self._initialized = False
        self._value = None

    def read(self, reader: 'StructReader'):
        raise Exception("Read not implemented")

class StructReader:
    """Class used to read  mhw_armor_edit struct types, when a file contains multiple of them"""
    
    def __init__(self, data):
        self.offset = 0
        self.data = data

    def read_struct(self, struct_class):
        if isinstance(struct_class, Readable):
            return struct_class.read(self)
        if issubclass(struct_class, Readable):
            obj = struct_class()
            return obj.read(self)
        elif issubclass(struct_class, ft.Struct):
            obj = struct_class(None, 0, self.data, offset=self.offset)
            self.offset += struct_class.STRUCT_SIZE
            return obj
        else:
            raise Exception('Unknown struct value: ' + str(struct_class))

    def read_structs(self, struct_class, count):
        results = []
        for i in range(count):
            results.append(self.read_struct(struct_class))
        return results

    def read_structs_block(self, struct_class):
        "Reads a count uint value and then reads that many blocks. Called mod3 in some codebases"
        count = self.read_field('<I')
        return read_structs(struct_class, count)
        
    def read_field(self, fmt):
        result = struct.unpack_from(fmt, self.data, self.offset)[0]
        self.offset += struct.calcsize(fmt)
        return result

class ReadablePrimitive(Readable):
    def __init__(self, fmt):
        self.fmt = fmt
    
    def read(self, reader: StructReader):
        return reader.read_field(self.fmt)

class uint(ReadablePrimitive):
    def __init__(self):
        super().__init__("<I")


class ushort(ReadablePrimitive):
    def __init__(self):
        super().__init__("<H")


class ubyte(ReadablePrimitive):
    def __init__(self):
        super().__init__("<B")


class int(ReadablePrimitive):
    def __init__(self):
        super().__init__("i")


class short(ReadablePrimitive):
    def __init__(self):
        super().__init__("<h")


class byte(ReadablePrimitive):
    def __init__(self):
        super().__init__("<b")


class long(ReadablePrimitive):
    def __init__(self):
        super().__init__("<q")

class blist(Readable):
    def __init__(self, base, count):
        self.base = base
        self.count = count

        if inspect.isclass(self.base):
            self.base = self.base()

    @property
    def size(self):
        return self.base.size * self.count
    
    def read(self, reader):
        results = []
        for i in range(self.count):
            value = self.base.read(reader)
            results.append(value)

        return results

class AnnotatedStruct(Readable):
    def __init__(self):
        self.fields = []

        hints = get_type_hints(self.__class__)
        for name, readable in hints.items():
            self.fields.append(name)

    def read(self, reader: StructReader):
        hints = get_type_hints(self.__class__)
        for name, readable in hints.items():
            value = reader.read_struct(readable)
            setattr(self, name, value)

        return self

    def as_dict(self):
        return {
            attr: getattr(self, attr)
            for attr in self.fields
        }

    def values(self):
        return tuple(
            getattr(self, attr)
            for attr in self.fields
        )
