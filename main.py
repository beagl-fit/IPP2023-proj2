#   David Novak
#   xnovak2r
#   IPP proj 2 - Python interpreter
#   april 2023

import fileinput
import argparse
import sys
import textwrap
import xml.etree.ElementTree as Tree


class Counter:
    """
    Object serves as a program counter. Current value is stored in the `_Count` variable.
    """
    def __init__(self) -> None:
        self._Count = 0

    def get_count(self) -> int:
        """
        Method which returns current count
        :return: _Count
        """
        return self._Count

    def increment_count(self) -> None:
        """
        Method which adds 1 to current count
        """
        self._Count += 1

    def reset_count(self) -> None:
        """
        Method which resets current count back to 0
        """
        self._Count = 0

class Argument:
    """
    some text
    """
    # GF/LF/TF@var_name, int/string/bool/nil/type/label => value
    _Types = {
        'int': int,
        'string': str,
        'bool': bool,
        'type': type,
        'nil': 'nil',
        'label': 'label',
        'var': 'var'
    }

    def __init__(self, arg_type: str, arg_value: str):
        self._VarType = None
        self._Type = self._Types[arg_type]
        self._Frame = None
        self._Name: str
        self._Value: str

        if self._Type == "var":
            self._Frame = arg_value.split('@')[0]
            self._Name = arg_value.split('@')[1]
        elif self._Type in (int, str, bool, type):
            try:
                self._Value = self._Type(arg_value)
            except ValueError:
                exit(53)

    def get_type(self):
        return self._Type

    def get_value(self):
        try:
            return self._Value
        except AttributeError:
            sys.stderr.write("ERROR: Argument get_value(): Empty value\n")
            exit(56)

    def set_value(self, value):
        if self._Type == "var":
            if value is None:
                self._VarType = str
                self._Value = ""
            elif value == "True" or value == "False":
                self._Value = bool(value)
                self._VarType = bool
            elif value.isnumeric():
                self._VarType = int
                self._Value = int(value)
            elif value == "nil":
                self._VarType = "nil"
                self._Value = value
            else:
                self._VarType = "string"
                self._Value = value
        else:
            sys.stderr.write("ERROR: Argument set_value(): setting value to non-variable argument\n")
            exit(53)

    def get_frame(self):
        try:
            return self._Frame
        except AttributeError:
            return "NONE"

    def get_name(self):
        try:
            return self._Name
        # TODO: mby change from sys err to: return None ???
        except AttributeError:
            sys.stderr.write("ERROR: Argument get_name(): argument is not variable\n")
            exit(53)

    # TODO: no idea what this is
    def set_frame(self, frame):
        if self.get_frame() == "LF" and frame == "TF":
            self._Frame = frame
        elif self.get_frame() == "TF" and frame == "LF":
            self._Frame = frame
        else:
            sys.stderr.write("ERROR: Argument set_frame(): can't set frame\n")
            exit(57)

    def is_variable(self):
        return True if self._Type == 'var' else False

    def get_var_type(self):
        return self._VarType

    # TODO: dont think this is necessary
    def has_value(self):
        try:
            return self._Value
        except AttributeError:
            return False


class Instruction:
    """
    The Instruction object contains IPPcode23 instruction. Each IPPcode23 instruction has opcode and 0-3 arguments.
    :param opcode: instruction code
    :param arg1: positional argument 1
    :param arg2: positional argument 2
    :param arg3: positional argument 3
    """
    _InstructionList = []

    def __init__(self, opcode: str, arg1: Argument | None = None,
                 arg2: Argument | None = None, arg3: Argument | None = None) -> None:
        self._Opcode = opcode
        self._arg1 = arg1
        self._arg2 = arg2
        self._arg3 = arg3
        self._InstructionList.append(self)

    def get_opcode(self) -> str:
        """
        Method which returns the IPPcode23 instruction code
        :return: Opcode
        """
        return self._Opcode

    def get_list(self) -> list:
        """
        Method which returns list of all instructions in current program.
        :return: InstructionList
        """
        return self._InstructionList

    def get_arg(self, arg_num: int) -> Argument:
        """
        Method which returns argument specified by the arg_num parameter.
        :param arg_num: 1 | 2 | 3
        :return: arg1 | arg2 | arg3
        """
        if arg_num == 1:
            return self._arg1
        else:
            return self._arg2 if (arg_num == 2) else self._arg3



#   class for 3 stacks - label, data and call
##  label stack (functions LABEL, JUMP,...)
##  data stack (functions PUSHS, POPS)
##  call stack (functions CALL, RETURN)
### has methods pop, push and pop_all
class Stack:
    _LabelStack = []
    _DataStack = []
    _CallStack = []

    # pushes value to stack
    def push(self, val, stack):
        if stack == "label":
            for num in range(len(self._LabelStack)):
                if val[0] in self._LabelStack[num][0]:
                    sys.stderr.write("ERROR: Stack push(): label already exists\n")
                    exit(52)
            self._LabelStack.append(val)
        elif stack == "data":
            self._DataStack.append(val)
        elif stack == "call":
            self._CallStack.append(val)
        else:
            sys.stderr.write("ERROR: Stack push(): unknown 'stack'\n")
            exit(99)

    # pops value from stack
    def pop(self, stack):
        if stack == "call":
            if len(self._CallStack):
                return self._CallStack.pop()
        elif stack == "data":
            if len(self._DataStack):
                return self._DataStack.pop()
            return "nil"
        else:
            sys.stderr.write("ERROR: Stack pop(): unknown 'stack'\n")
            exit(99)
        sys.stderr.write("ERROR: Stack pop(): empty 'stack'\n")
        exit(56)

    # returns all variables present in stack
    def pop_all(self, stack):
        ret = ""
        if stack == "label":
            length = len(self._LabelStack)
            for ln in range(length):
                ret += self._LabelStack[ln]
                ret += " "
        elif stack == "data":
            length = len(self._DataStack)
            for ln in range(length):
                ret += self._DataStack[ln]
                ret += " "
        else:
            sys.stderr.write("ERROR: Stack pop_all(): unknown 'stack'\n")
            exit(99)
        return ret

    # _LabelStack = [[LABEL,NUMBER],[LABEL2,NUMBER2],...]
    # returns NUMBER that will be set as global COUNT to execute next instruction
    def jump(self, name):
        for num in range(len(self._LabelStack)):
            if name in self._LabelStack[num][0]:
                return self._LabelStack[num][1]
        sys.stderr.write("ERROR: Stack jump(): label doesn't exists\n")
        exit(52)


#   class to keep global, local and temporary frame, to know where variables are defined
##  methods return_frame, push_frame, add_var_to_frame, get_var, pop_frame, is_in_frame, clear_temp_frame
class Frame:
    _GlobalFrame = []
    _FrameStack = []
    _TemporaryFrame = []

    # return all variables in chosen frame
    def return_frame(self, frame: str):
        if frame == "LF":
            if len(self._FrameStack):
                return self._FrameStack[-1]
            sys.stderr.write("ERROR: return_frame(): local frame doesn't exist\n")
            exit(55)
        elif frame == "GF":
            return self._GlobalFrame
        elif frame == "TF":
            return self._TemporaryFrame
        sys.stderr.write("ERROR: return_frame(): frame doesn't exist\n")
        exit(55)

    # appends temporary frame to stack of frame and changes frames of appended variables
    def push_frame(self):
        for arg in self._TemporaryFrame:
            arg.set_frame("LF")
        self._FrameStack.append(self._TemporaryFrame)
        self._TemporaryFrame.clear()

    # adds variable to chosen frame
    def add_var_to_frame(self, var: Argument, frame):
        if frame == "GF":
            self._GlobalFrame.append(var)
        elif frame == "TF":
            self._TemporaryFrame.append(var)
        else:
            sys.stderr.write("ERROR: add_var_to_frame(): frame doesn't exist\n")
            exit(55)

    # returns variable if variable with chosen name and frame exists
    def get_var(self, name, frame):
        if frame == "GF":
            for var in self._GlobalFrame:
                if var.get_name() == name:
                    return var
        elif frame == "LF":
            for var in self._FrameStack[-1]:
                if var.get_name() == name:
                    return var
        elif frame == "TF":
            for var in self._TemporaryFrame:
                if var.get_name() == name:
                    return var
        else:
            sys.stderr.write("ERROR: get_var(): frame doesn't exist\n")
            exit(55)
        sys.stderr.write("ERROR: get_var(): non-existing variable access\n")
        exit(54)

    # pops local frame to temporary frame and changes frames of popped variables
    def pop_frame(self):
        if len(self._FrameStack):
            self._TemporaryFrame = self._FrameStack.pop()
            for arg in self._TemporaryFrame:
                arg.set_frame("TF")
        else:
            sys.stderr.write("ERROR: pop_frame(): stack is empty\n")
            exit(55)

    # returns True if variable with given name and frame is already in frame and False if it isn't
    def is_in_frame(self, arg, frame: str):
        for variable in self.return_frame(frame):
            if arg == variable:
                return True
        return False

    # clears temporary frame
    def clear_temp_frame(self):
        self._TemporaryFrame.clear()


#################################
#################################
#################################
# TODO: check - arg_value is from arg_type, arg_value OK for instruction
# TODO: check - correct type??

class MOVE(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction MOVE got " + arg_num + "arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        super().__init__("MOVE", arg1, arg2)

    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class CREATEFRAME(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction CREATEFRAME got " + arg_num + "arguments, 0 arguments expected")
            exit(52)

        super().__init__("CREATEFRAME")

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class PUSHFRAME(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction PUSHFRAME got " + arg_num + "arguments, 0 arguments expected")
            exit(52)

        super().__init__("PUSHFRAME")

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class POPFRAME(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction POPFRAME got " + arg_num + "arguments, 0 arguments expected")
            exit(52)

        super().__init__("POPFRAME")

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class DEFVAR(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction DEFVAR got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("DEFVAR", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class CALL(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction CALL got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("CALL", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class RETURN(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction RETURN got " + arg_num + "arguments, 0 arguments expected")
            exit(52)

        super().__init__("RETURN")

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class PUSHS(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction PUSHS got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("PUSHS", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class POPS(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction POPS got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("POPS", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class ADD(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction ADD got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("ADD", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class SUB(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction SUB got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("SUB", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class MUL(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction MUL got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("MUL", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class IDIV(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction IDIV got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("IDIV", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class LT(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction LT got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("LT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class GT(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction GT got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("GT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class EQ(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction EQ got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("EQ", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class AND(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction AND got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("AND", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class OR(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction OR got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("OR", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class NOT(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction NOT got " + arg_num + "arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        super().__init__("NOT", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class INT2CHAR(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction INT2CHAR got " + arg_num + "arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        super().__init__("INT2CHAR", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class STRI2INT(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction STRI2INT got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("STRI2INT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class READ(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction READ got " + arg_num + "arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        super().__init__("READ", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class WRITE(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction WRITE got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("WRITE", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class CONCAT(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction CONCAT got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("CONCAT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class STRLEN(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction STRLEN got " + arg_num + "arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        super().__init__("STRLEN", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class GETCHAR(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction GETCHAR got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("GETCHAR", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class SETCHAR(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction SETCHAR got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("SETCHAR", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class TYPE(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction TYPE got " + arg_num + "arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        super().__init__("TYPE", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class LABEL(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction LABEL got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("LABEL", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class JUMP(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction JUMP got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("JUMP", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class JUMPIFEQ(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction JUMPIFEQ got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("JUMPIFEQ", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class JUMPIFNEQ(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction JUMPIFNEQ got " + arg_num + "arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])
        super().__init__("JUMPIFNEQ", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class EXIT(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction EXIT got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("EXIT", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class DPRINT(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction DPRINT got " + arg_num + "arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        super().__init__("DPRINT", arg1)

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class BREAK(Instruction):
    def __init__(self, arg_num, arguments, types):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction BREAK got " + arg_num + "arguments, 0 arguments expected")
            exit(52)

        super().__init__("BREAK")

    @classmethod
    def execute(cls, arg1: Argument, arg2: Argument, arg3: Argument):
        pass


class Factory:
    @classmethod
    def resolve(cls, opcode: str, num_of_args: int, value_list: list, type_list: list) -> Instruction:
        if opcode.upper() == 'MOVE':
            return MOVE(num_of_args, value_list, type_list)
        elif opcode.upper() == 'CREATEFRAME':
            return CREATEFRAME(num_of_args, value_list, type_list)
        elif opcode.upper() == 'PUSHFRAME':
            return PUSHFRAME(num_of_args, value_list, type_list)
        elif opcode.upper() == 'POPFRAME':
            return POPFRAME(num_of_args, value_list, type_list)
        elif opcode.upper() == 'DEFVAR':
            return DEFVAR(num_of_args, value_list, type_list)
        elif opcode.upper() == 'CALL':
            return CALL(num_of_args, value_list, type_list)
        elif opcode.upper() == 'RETURN':
            return RETURN(num_of_args, value_list, type_list)

        elif opcode.upper() == 'PUSHS':
            return PUSHS(num_of_args, value_list, type_list)
        elif opcode.upper() == 'POPS':
            return POPS(num_of_args, value_list, type_list)

        elif opcode.upper() == 'ADD':
            return ADD(num_of_args, value_list, type_list)
        elif opcode.upper() == 'SUB':
            return SUB(num_of_args, value_list, type_list)
        elif opcode.upper() == 'MUL':
            return MUL(num_of_args, value_list, type_list)
        elif opcode.upper() == 'IDIV':
            return IDIV(num_of_args, value_list, type_list)
        elif opcode.upper() == 'LT':
            return LT(num_of_args, value_list, type_list)
        elif opcode.upper() == 'GT':
            return GT(num_of_args, value_list, type_list)
        elif opcode.upper() == 'EQ':
            return EQ(num_of_args, value_list, type_list)
        elif opcode.upper() == 'AND':
            return AND(num_of_args, value_list, type_list)
        elif opcode.upper() == 'OR':
            return OR(num_of_args, value_list, type_list)
        elif opcode.upper() == 'NOT':
            return NOT(num_of_args, value_list, type_list)
        elif opcode.upper() == 'INT2CHAR':
            return INT2CHAR(num_of_args, value_list, type_list)
        elif opcode.upper() == 'STRI2INT':
            return STRI2INT(num_of_args, value_list, type_list)

        elif opcode.upper() == 'READ':
            return READ(num_of_args, value_list, type_list)
        elif opcode.upper() == 'WRITE':
            return WRITE(num_of_args, value_list, type_list)

        elif opcode.upper() == 'CONCAT':
            return CONCAT(num_of_args, value_list, type_list)
        elif opcode.upper() == 'STRLEN':
            return STRLEN(num_of_args, value_list, type_list)
        elif opcode.upper() == 'GETCHAR':
            return GETCHAR(num_of_args, value_list, type_list)
        elif opcode.upper() == 'SETCHAR':
            return SETCHAR(num_of_args, value_list, type_list)

        elif opcode.upper() == 'TYPE':
            return TYPE(num_of_args, value_list, type_list)
        elif opcode.upper() == 'LABEL':
            return LABEL(num_of_args, value_list, type_list)
        elif opcode.upper() == 'JUMP':
            return JUMP(num_of_args, value_list, type_list)
        elif opcode.upper() == 'JUMPIFEQ':
            return JUMPIFEQ(num_of_args, value_list, type_list)
        elif opcode.upper() == 'JUMPIFNEQ':
            return JUMPIFNEQ(num_of_args, value_list, type_list)
        elif opcode.upper() == 'EXIT':
            return EXIT(num_of_args, value_list, type_list)

        elif opcode.upper() == 'DPRINT':
            return DPRINT(num_of_args, value_list, type_list)
        elif opcode.upper() == 'BREAK':
            return BREAK(num_of_args, value_list, type_list)
        else:
            sys.stderr.write('ERROR: unknown instruction\n')
            exit(52)


### ERROR
##  py ERROR
#   31 - XML file is not well-formed
#   32 - unexpected XML structure   (dupes)

#   2  - most argparse errors

##  project ERROR
#   10      - missing parameter
#   11      - error when opening input files    - argparse errno 13
#   12      - error when opening output files
#   99      - internal error

##  Interpreter ERROR
#   52      - semantic ERROR in input   (unknown instruction, undef label or var redef)
#   53      - wrong operand types
#   54      - non-existing variable access (within existing frame)
#   55      - non-existing frame
#   56      - missing value
#   57      - wrong operand value (div by 0)
#   58      - wrong string operation


#   parameters
#   --help
#   --source=FILE   - XML code
#   --input=FILE    - input of instructions

if __name__ == '__main__':
    c = Counter()
    #   Parsing arguments
    parser = argparse.ArgumentParser(
        description='Python interpreter of IPPcode22',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
        Either '--source' or '--input' argument required
            - STDIN will then be regarded as the other one
        '''))
    parser.add_argument("--source", metavar='file', type=argparse.FileType('r'), help='file containing XML code')
    parser.add_argument("--input", metavar='file', type=argparse.FileType('r'),
                        help='input of XML instructions (e.g. READ)')
    args = parser.parse_args()

    ### Check availability of source and input files
    root: Tree.Element
    InputFile: str
    #   No file
    if args.source is None and args.input is None:
        sys.stderr.write('at least one of --source and --input required\n')  # parser.error()    <- error 2
        exit(10)

    #   Only input file
    elif args.source is None:
        SourceString = ""
        with fileinput.input('-') as f:
            for line in f:
                SourceString += line
        root = Tree.fromstring(SourceString)

        with open(args.input.name, encoding=args.input.encoding) as In:
            InputFile = In.read()

    #   Only source file
    elif args.input is None:
        # noinspection PyUnresolvedReferences
        with open(args.source.name, encoding=args.source.encoding) as SourceFile:
            tree = Tree.parse(SourceFile)
            root = tree.getroot()

        InputFile = ""
        with fileinput.input('-') as f:
            for line in f:
                InputFile += line

    #   Both files
    else:
        with open(args.source.name, encoding=args.source.encoding) as SourceFile:
            tree = Tree.parse(SourceFile)
            root = tree.getroot()

        with open(args.input.name, encoding=args.input.encoding) as In:
            InputFile = In.read()

    # noinspection PyUnboundLocalVariable
    if root.tag != 'program':
        sys.stderr.write('ERROR: No "program" root of XML\n')
        exit(31)

    # noinspection PyUnboundLocalVariable
    Input = list(InputFile.splitlines())
    Input.reverse()
    for element in Input:
        Stack().push(element, 'input')

    ######  Sort Instructions
    ##   https://devdreamz.com/question/931441-python-sort-xml-elements-by-and-tag-and-attributes-recursively
    root[:] = sorted(root, key=lambda child: (child.tag, int(child.get('order'))))
    ##

    for instr in root:
        attrib = instr.attrib
        if len(attrib) > 1:
            attribs = sorted(attrib.items())
            attrib.clear()
            # noinspection PyTypeChecker
            attrib.update(attribs)
    ######

    orderStack = []

    i: Instruction
    instrCount = 0
    for instr in root:
        numOfArgs = len(instr)
        typeList = []
        valueList = []
        order = instr.attrib['order']
        if order in orderStack:
            sys.stderr.write('ERROR: duplicate instruction order')
            exit(32)
        orderStack.append(instr.attrib['order'])
        for x in range(numOfArgs):
            typeList.append(instr[x].attrib['type'])
            valueList.append(instr[x].text)

        i = Factory.resolve(instr.attrib['opcode'], numOfArgs, valueList, typeList)
        instrCount += 1

    if instrCount:
        # noinspection PyUnboundLocalVariable
        for instr in i.get_list():
            if instr.get_opcode() == "LABEL":
                instr.execute(instr.get_arg(0))
            c.increment_count()
        c.reset_count()

        InstrList = i.get_list()
        while c.get_count() < instrCount:
            instr = InstrList[c.get_count()]
            instr.execute(instr.get_arg(0), instr.get_arg(1), instr.get_arg(2))
            c.increment_count()
            # TODO: remove prints
            print(instr.get_opcode(), ':', instr.get_arg(1), instr.get_arg(2), instr.get_arg(3))
