#   David Novak
#   xnovak2r
#   IPP proj 2 - Python interpreter
#   april 2023

import fileinput
import argparse
import re
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

    def set_count(self, num: int) -> None:
        """
        Method which sets program counter to a specific number. It is used by all jump instructions.
        :param num: number used as the new counter count
        """
        self._Count = num


class Argument:
    # TODO: docstrings
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

    def __init__(self, arg_type: str, arg_value: str) -> None:
        self._VarType = None
        self._Type = self._Types[arg_type]
        self._Frame = None
        self._Name = None
        self._Value = None

        if self._Type == "var":
            self._Frame = arg_value.split('@')[0]
            self._Name = arg_value.split('@')[1]
        elif self._Type == int:
            try:
                self._Value = int(arg_value)
            except ValueError:
                sys.stderr.write('ERROR: Argument init: wrong int argument value')
                exit(53)
        elif self._Type == str:
            if arg_value is None:
                self._Value = ''
            else:
                for ch in set(re.findall(r'\\\d{3}', arg_value)):
                    arg_value = arg_value.replace(ch, chr(int(ch[1:])))
                self._Value = arg_value
        elif self._Type == "nil":
            self._Value = 'nil'
        elif self._Type == bool:
            if arg_value.upper() == 'TRUE':
                self._Value = True
            elif arg_value.upper() == 'FALSE':
                self._Value = False
            else:
                sys.stderr.write("ERROR: Argument init: wrong bool argument value\n")
                exit(53)
        elif self._Type == type:
            if arg_value in ('int', 'string', 'bool', 'nil'):
                self._Value = self._Types[arg_value]
            else:
                sys.stderr.write("ERROR: Argument init: wrong type argument value\n")
                exit(53)
        elif self._Type == 'label':
            self._Value = arg_value

    def get_type(self):
        return self._Type

    def get_value(self) -> _Types:
        val = self._Value
        if val is None:
            sys.stderr.write("ERROR: Argument get_value(): Empty value\n")
            exit(56)
        return self._Value

    def set_value(self, value):
        if self._Type == "var":
            if value is None:
                self._VarType = str
                self._Value = ""
            elif type(value) is bool:
                self._Value = value
                self._VarType = bool
            elif type(value) == int:
                self._VarType = int
                self._Value = int(value)
            elif value == "nil":
                self._VarType = "nil"
                self._Value = "nil"
            else:
                self._VarType = str
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
        except AttributeError:
            sys.stderr.write("ERROR: Argument get_name(): argument is not variable\n")
            exit(53)

    def set_frame(self, frame: str) -> None:
        """
        Changes scope of variable from LF to TF or from TF to LF. Used when pushing or popping a frame.
        :param frame: TF | LF
        """
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

    def is_symbol(self):
        return True if self.is_variable() or self._Type in (int, str, bool, 'nil') else False


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


class Stack:
    """
    Stack is a class containing 3 different stack. Stacks are implemented as lists and are needed for correct
    function of different IPPcode23 instructions.
    :var _LabelStack: LABEL, JUMP(s)
    :var _DataStack: PUSHS, POPS
    :var _CallStack: CALL, RETURN
    """
    _LabelStack = []  # _LabelStack = [[LABEL,NUMBER],[LABEL2,NUMBER2],...]
    _DataStack = []
    _CallStack = []
    _InputStack = []

    def push(self, val, stack: str) -> None:
        """
        Method adds a value to a stack specified by the `stack` param.
        :param val: value to be added
        :param stack: L | D | C
        """
        if stack == "L":  # stack().push([arg1.getvalue(), c.get_count()]
            for num in range(len(self._LabelStack)):
                if val[0] in self._LabelStack[num][0]:
                    sys.stderr.write("ERROR: Stack push(): label already exists\n")
                    exit(52)
            self._LabelStack.append(val)
        elif stack == "D":
            self._DataStack.append(val)
        elif stack == "C":
            self._CallStack.append(val)
        elif stack == "I":
            self._InputStack.append(val)
        else:
            sys.stderr.write("ERROR: Stack push(): unknown 'stack'\n")
            exit(99)

    def pop(self, stack: str):
        """
        Method pop returns and removes the last value from a stack specified by the `stack` param. Labels from
        label stack can't be popped. May result in error if it is called on an empty call stack.
        :param stack: D | C
        :return: last value on stack
        """
        if stack == "C":
            if len(self._CallStack):
                return self._CallStack.pop()
            sys.stderr.write("ERROR: Stack pop(): empty call stack\n")
            exit(56)
        elif stack == "D":
            if len(self._DataStack):
                return self._DataStack.pop()
            sys.stderr.write("ERROR: Stack pop(): empty data stack\n")
            exit(56)
        else:
            sys.stderr.write("ERROR: Stack pop(): unknown 'stack'\n")
            exit(99)

    def ret_all(self, stack: str) -> str:
        """
        Ret_all method returns all everything on a stack specified by the stack param
        :param stack: L | D
        :return: stack elements
        """
        # TODO: do DATA stack
        ret = ''
        if stack == "L":
            if len(self._LabelStack):
                ret += 'name:count:: '
                for label in self._LabelStack:
                    ret += label[0]
                    ret += ':'
                    ret += str(label[1])
                    ret += '; '
            else:
                ret = 'EMPTY; '
        elif stack == "D":
            if len(self._DataStack):
                for label in self._DataStack:
                    ret += label[0]
                    ret += ':'
                    ret += str(label[1])
                    ret += '; '
            else:
                ret = 'EMPTY;'
        else:
            if len(self._CallStack):
                ret += 'B->T:: '
                for label in self._CallStack:
                    ret += str(label)
                    ret += '; '
            else:
                ret = 'EMPTY;'
        return ret

    def jump(self, name: str) -> int:
        """
        Method jump returns a number that will be used by the program counter to execute correct
        instruction after a JUMP instruction.
        :param name: name of the label program jumps to
        :return: number for counter
        """
        for num in range(len(self._LabelStack)):
            if name in self._LabelStack[num][0]:
                return self._LabelStack[num][1]
        sys.stderr.write("ERROR: Stack jump(): label doesn't exists\n")
        exit(52)


#   class to keep global, local and temporary frame, to know where variables are defined
##  methods return_frame, push_frame, add_var_to_frame, get_var, pop_frame, is_in_frame, clear_temp_frame
class Frame:
    # TODO: docstrings
    # TODO: local + temp frame init to None
    _GlobalFrame = []
    _FrameStack = []
    _TemporaryFrame = None

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
        if self._TemporaryFrame is not None:
            for arg in self._TemporaryFrame:
                arg.set_frame("LF")
            self._FrameStack.append(self._TemporaryFrame)
            self._TemporaryFrame = None
        else:
            sys.stderr.write("ERROR: push(): frame undefined\n")
            exit(55)

    # adds variable to chosen frame
    def add_var_to_frame(self, var: Argument, frame: str):
        if frame == "GF":
            self._GlobalFrame.append(var)
        elif frame == "TF":
            self._TemporaryFrame.append(var)
        else:
            sys.stderr.write("ERROR: add_var_to_frame(): frame doesn't exist\n")
            exit(55)

    # returns variable if variable with chosen name and frame exists
    def get_var(self, name: str, frame: str):
        if frame == "GF":
            for var in self._GlobalFrame:
                if var.get_name() == name:
                    return var
        elif frame == "LF":
            for var in self._FrameStack[-1]:
                if var.get_name() == name:
                    return var
        elif frame == "TF":
            try:
                for var in self._TemporaryFrame:
                    if var.get_name() == name:
                        return var
            except TypeError:
                sys.stderr.write("ERROR: get_var(): frame doesn't exist\n")
                exit(55)
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
        try:
            for variable in self.return_frame(frame):
                if arg == variable:
                    return True
            return False
        except TypeError:
            print(arg, frame, sep='\n')
            sys.stderr.write("ERROR: is_in_frame(): frame doesn't exist")
            exit(55)

    # clears temporary frame
    def clear_temp_frame(self):
        self._TemporaryFrame = []


# TODO: check - arg_value is from arg_type, arg_value OK for instruction
# TODO: check - correct type??
# TODO: string ab\032cd => ab cd (write)
class MOVE(Instruction):
    """
    Instruction MOVE from IPPcode23 requires 2 arguments of type variable and symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list) -> None:
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction MOVE got " + str(arg_num) + " arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction MOVE: argument 1 is not a variable")
            exit(53)

        if not arg2.is_symbol():
            sys.stderr.write("ERROR: Instruction MOVE: argument 2 is not a symbol")
            exit(53)

        super().__init__("MOVE", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Sets value of arg1 to value of arg2.
        :param arg1: var
        :param arg2: symb
        :param arg3: None
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())
        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())

        arg1.set_value(arg2.get_value())


class CREATEFRAME(Instruction):
    """
    Instruction CREATEFRAME from IPPcode23 requires 0 arguments.
    """

    def __init__(self, arg_num: int, arguments: list, types: list) -> None:
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction CREATEFRAME got " + str(arg_num) + " arguments, 0 arguments expected")
            exit(52)

        super().__init__("CREATEFRAME")

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Creates a new temporary frame and clears any content it might have had previously.
        :param arg1: None
        :param arg2: None
        :param arg3: None
        """
        f.clear_temp_frame()


class PUSHFRAME(Instruction):
    """
    Instruction PUSHFRAME from IPPcode23 requires 0 arguments.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction PUSHFRAME got " + str(arg_num) + " arguments, 0 arguments expected")
            exit(52)

        super().__init__("PUSHFRAME")

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Transfer all variables in temporary frame to the top of frame stack and changes frame of said variables
        from TF to LF.
        :param arg1: None
        :param arg2: None
        :param arg3: None
        """
        f.push_frame()


class POPFRAME(Instruction):
    """
    Instruction POPFRAME from IPPcode23 requires 0 arguments.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction POPFRAME got " + str(arg_num) + " arguments, 0 arguments expected")
            exit(52)

        super().__init__("POPFRAME")

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Transfer all variables in from the top of frame stack to temporary frame and changes frame of said variables
        from LF to LT.
        :param arg1: None
        :param arg2: None
        :param arg3: None
        """
        f.pop_frame()


class DEFVAR(Instruction):
    """
    Instruction DEFVAR from IPPcode23 requires 1 argument of type variable.
    """

    def __init__(self, arg_num: int, arguments: list, types: list) -> None:
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction DEFVAR got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction DEFVAR: argument 1 is not a variable")
            exit(53)

        super().__init__("DEFVAR", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Declares a variable specified by arg1. Local and temporary frames have to be created first.
        :param arg1: var
        :param arg2: None
        :param arg3: None
        """
        if f.is_in_frame(arg1.get_name(), arg1.get_frame()):
            sys.stderr.write("ERROR: execute DEFVAR: variable already in frame\n")
            exit(52)
        f.add_var_to_frame(arg1, arg1.get_frame())


class CALL(Instruction):
    """
    Instruction CALL from IPPcode23 requires 1 argument of type label.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction CALL got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if arg1.get_type() != 'label':
            sys.stderr.write("ERROR: Instruction CALL: argument 1 is not of type label")
            exit(53)

        super().__init__("CALL", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Jumps to the label specified by arg1 while saving the value of program counter on top of call stack.
        :param arg1: label
        :param arg2: None
        :param arg3: None
        """
        s.push(c.get_count(), 'C')  # todo: check `count + 1` vs count
        JUMP.execute(arg1, None, None)


class RETURN(Instruction):
    """
    Instruction RETURN from IPPcode23 requires 0 arguments.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction RETURN got " + str(arg_num) + " arguments, 0 arguments expected")
            exit(52)

        super().__init__("RETURN")

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Sets program counter to value on top of call stack and removes said value from call stack.
        :param arg1: None
        :param arg2: None
        :param arg3: None
        """
        c.set_count(s.pop('C'))


class PUSHS(Instruction):
    """
    Instruction PUSHS from IPPcode23 requires 1 argument of type symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction PUSHS got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if not arg1.is_symbol():
            sys.stderr.write("ERROR: Instruction PUSHS: argument 1 is not of type symbol")
            exit(53)

        super().__init__("PUSHS", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Adds value of arg1 to the top of data stack.
        :param arg1: symb
        :param arg2: None
        :param arg3: None
        """
        if arg1.is_variable():
            arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        s.push(arg1.get_value(), 'D')


class POPS(Instruction):
    """
    Instruction POPS from IPPcode23 requires 1 argument of type variable.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction POPS got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction POPS: argument 1 is not a variable")
            exit(53)

        super().__init__("POPS", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Save value from the top of data stack to a variable specified by arg1.
        :param arg1: var
        :param arg2: None
        :param arg3: None
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())
        arg1.set_value(s.pop('D'))


class ADD(Instruction):
    """
    Instruction ADD from IPPcode23 requires 3 arguments of type variable, int and int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction ADD got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction ADD: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', int) or not arg3.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction ADD: argument 2 or 3 is not a variable or an int")
            exit(53)

        super().__init__("ADD", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves the sum of arg2 and arg3 to a variable specified by arg1.
        :param arg1: var
        :param arg2: int
        :param arg3: int
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction ADD: argument 2 is not an int")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction ADD: argument 3 is not an int")
                exit(53)

        arg1.set_value(arg2.get_value() + arg3.get_value())


class SUB(Instruction):
    """
    Instruction SUB from IPPcode23 requires 3 arguments of type variable, int and int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction SUB got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction SUB: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', int) or not arg3.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction SUB: argument 2 or 3 is not a variable or an int")
            exit(53)

        super().__init__("SUB", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves the difference of arg2 and arg3 to a variable specified by arg1.
        :param arg1: var
        :param arg2: int
        :param arg3: int
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction SUB: argument 2 is not an int")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction SUB: argument 3 is not an int")
                exit(53)

        arg1.set_value(arg2.get_value() - arg3.get_value())


class MUL(Instruction):
    """
    Instruction MUL from IPPcode23 requires 3 arguments of type variable, int and int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction MUL got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction MUL: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', int) or not arg3.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction MUL: argument 2 or 3 is not a variable or an int")
            exit(53)

        super().__init__("MUL", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves the product of arg2 and arg3 to a variable specified by arg1.
        :param arg1: var
        :param arg2: int
        :param arg3: int
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction MUL: argument 2 is not an int")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction MUL: argument 3 is not an int")
                exit(53)

        arg1.set_value(arg2.get_value() * arg3.get_value())


class IDIV(Instruction):
    """
    Instruction IDIV from IPPcode23 requires 3 arguments of type variable, int and int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction IDIV got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction IDIV: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', int) or not arg3.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction IDIV: argument 2 or 3 is not a variable or an int")
            exit(53)

        super().__init__("IDIV", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves the fraction of arg2 and arg3 to a variable specified by arg1.
        :param arg1: var
        :param arg2: int
        :param arg3: int
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction IDIV: argument 2 is not an int")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction IDIV: argument 3 is not an int")
                exit(53)

        val = arg3.get_value()
        if val == 0:
            sys.stderr.write("ERROR: Instruction IDIV: zero division")
            exit(57)

        arg1.set_value(arg2.get_value() / val)


class LT(Instruction):
    """
    Instruction LT from IPPcode23 requires 3 arguments of type variable, symbol and symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction LT got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction LT: argument 1 is not a variable")
            exit(53)
        if not arg2.is_symbol():
            sys.stderr.write("ERROR: Instruction LT: argument 2 or 3 is not a symbol")
            exit(53)

        super().__init__("LT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves True to a variable specified by arg1 if arg2 < arg3 and saves False if it isn't.
        Arg2 and arg3 need to be of the same type.
        :param arg1: var
        :param arg2: symb
        :param arg3: symb
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())
        type1 = arg2.get_type()
        type2 = arg3.get_type()

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            type1 = arg2.get_var_type()
            if type1 not in (int, str, bool):
                sys.stderr.write("ERROR: Instruction LT: wrong type of argument 2")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            type2 = arg3.get_var_type()
            if type2 not in (int, str, bool):
                sys.stderr.write("ERROR: Instruction LT: wrong type of argument 3")
                exit(53)

        if type2 == 'nil' or type1 == 'nil':
            sys.stderr.write("ERROR: Instruction LT: arguments can't be of type nil")
            exit(53)

        if type1 != type2:
            sys.stderr.write("ERROR: Instruction LT: can't compare arguments of different types")
            exit(53)

        arg1.set_value(arg2.get_value() < arg3.get_value())


class GT(Instruction):
    """
    Instruction GT from IPPcode23 requires 3 arguments of type variable, symbol and symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction GT got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction GT: argument 1 is not a variable")
            exit(53)
        if not arg2.is_symbol():
            sys.stderr.write("ERROR: Instruction GT: argument 2 or 3 is not a symbol")
            exit(53)

        super().__init__("GT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves True to a variable specified by arg1 if arg2 > arg3 and saves False if it isn't.
        Arg2 and arg3 need to be of the same type.
        :param arg1: var
        :param arg2: symb
        :param arg3: symb
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())
        type1 = arg2.get_type()
        type2 = arg3.get_type()

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            type1 = arg2.get_var_type()
            if type1 not in (int, str, bool):
                sys.stderr.write("ERROR: Instruction GT: wrong type of argument 2")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            type2 = arg3.get_var_type()
            if type2 not in (int, str, bool):
                sys.stderr.write("ERROR: Instruction GT: wrong type of argument 2")
                exit(53)

        if type2 == 'nil' or type1 == 'nil':
            sys.stderr.write("ERROR: Instruction GT: arguments can't be of type nil")
            exit(53)

        if type1 != type2:
            sys.stderr.write("ERROR: Instruction GT: can't compare arguments of different types")
            exit(53)

        arg1.set_value(arg2.get_value() > arg3.get_value())


class EQ(Instruction):
    """
    Instruction GT from IPPcode23 requires 3 arguments of type variable, symbol and symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction EQ got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction EQ: argument 1 is not a variable")
            exit(53)
        if not arg2.is_symbol():
            sys.stderr.write("ERROR: Instruction EQ: argument 2 or 3 is not a symbol")
            exit(53)

        super().__init__("EQ", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves True to a variable specified by arg1 if arg2 == arg3 and saves False if it isn't.
        Arg2 and arg3 need to be of the same type or at least one of them needs to be of type nil.
        Comparing nil and value other than nil saves False to arg1.
        :param arg1: var
        :param arg2: symb
        :param arg3: symb
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())
        type1 = arg2.get_type()
        type2 = arg3.get_type()

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            type1 = arg2.get_var_type()
            if type1 not in (int, str, bool, 'nil'):
                sys.stderr.write("ERROR: Instruction EQ: wrong type of argument 2")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            type2 = arg3.get_var_type()
            if type2 not in (int, str, bool, 'nil'):
                sys.stderr.write("ERROR: Instruction EQ: wrong type of argument 3")
                exit(53)

        if type1 != type2 and type1 != 'nil' and type2 != 'nil':
            sys.stderr.write("ERROR: Instruction EQ: can't compare arguments of different types "
                             "unless one of them is of type nil")
            exit(53)

        # TODO: write about this in documentation
        # TODO: symb nil => false
        if type1 != type2:
            arg1.set_value(False)
        else:
            arg1.set_value(arg2.get_value() == arg3.get_value())


class AND(Instruction):
    """
    Instruction AND from IPPcode23 requires 3 arguments of type variable, bool and bool.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction AND got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction AND: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', bool) or not arg3.get_type() in ('var', bool):
            sys.stderr.write("ERROR: Instruction AND: argument 2 or 3 is not a variable or a bool")
            exit(53)

        super().__init__("AND", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves result of logical operation `and` between arg2 and arg3 into a variable specified by arg1.
        :param arg1: var
        :param arg2: bool
        :param arg3: bool
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != bool:
                sys.stderr.write("ERROR: Instruction AND: argument 2 is not a bool")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != bool:
                sys.stderr.write("ERROR: Instruction AND: argument 3 is not an bool")
                exit(53)

        arg1.set_value(arg2.get_value() and arg3.get_value())


class OR(Instruction):
    """
    Instruction OR from IPPcode23 requires 3 arguments of type variable, bool and bool.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction OR got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction OR: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', bool) or not arg3.get_type() in ('var', bool):
            sys.stderr.write("ERROR: Instruction OR: argument 2 or 3 is not a variable or a bool")
            exit(53)

        super().__init__("OR", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves result of logical operation `or` between arg2 and arg3 into a variable specified by arg1.
        :param arg1: var
        :param arg2: bool
        :param arg3: bool
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != bool:
                sys.stderr.write("ERROR: Instruction OR: argument 2 is not a bool")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != bool:
                sys.stderr.write("ERROR: Instruction OR: argument 3 is not an bool")
                exit(53)

        arg1.set_value(arg2.get_value() or arg3.get_value())


class NOT(Instruction):
    """
    Instruction NOT from IPPcode23 requires 2 arguments of type variable and bool.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction NOT got " + str(arg_num) + " arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction NOT: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', bool):
            sys.stderr.write("ERROR: Instruction NOT: argument 2 is not a variable or a bool")
            exit(53)

        super().__init__("NOT", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves result of logical operation `not` arg2 into a variable specified by arg1.
        :param arg1: var
        :param arg2: bool
        :param arg3: None
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != bool:
                sys.stderr.write("ERROR: Instruction NOT: argument 2 is not a bool")
                exit(53)

        arg1.set_value(not arg2.get_value())


class INT2CHAR(Instruction):
    """
    Instruction INT2CHAR from IPPcode23 requires 2 arguments of type variable and int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction INT2CHAR got " + str(arg_num) + " arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction INT2CHAR: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction INT2CHAR: argument 2 is not a variable or an int")
            exit(53)

        super().__init__("INT2CHAR", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Transforms value of arg2 to a char and saves said value to arg1.
        :param arg1: var
        :param arg2: int
        :param arg3: None
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction INT2CHAR: argument 2 is not an int")
                exit(53)

        try:
            arg1.set_value(chr(arg2.get_value()))
        except ValueError:
            sys.stderr.write("ERROR: Instruction INT2CHAR: invalid value or arg2")
            exit(58)


class STRI2INT(Instruction):
    """
    Instruction STRI2INT from IPPcode23 requires 3 arguments of type variable, string and int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction STRI2INT got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction INT2CHAR: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', str):
            sys.stderr.write("ERROR: Instruction INT2CHAR: argument 2 is not a variable or a string")
            exit(53)
        if not arg3.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction INT2CHAR: argument 3 is not a variable or an int")
            exit(53)

        super().__init__("STRI2INT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Transforms character from string in arg2 on position arg3 and save said character to arg1
        :param arg1: var
        :param arg2: string
        :param arg3: int
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != str:
                sys.stderr.write("ERROR: Instruction STRI2INT: argument 2 is not a string")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction STRI2INT: argument 3 is not an int")
                exit(53)

        try:
            transform = list(arg2.get_value())
            index = arg3.get_value()

            if not 0 <= index < len(transform):
                sys.stderr.write("ERROR: Instruction STRI2INT: arg3 outside of range of arg2")
                exit(58)
            arg1.set_value(ord(transform[index]))

        except ValueError:
            sys.stderr.write("ERROR: Instruction STRI2INT: invalid value to transform in arg2")
            exit(58)


class READ(Instruction):
    """
    Instruction READ from IPPcode23 requires 2 arguments of type variable and type.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction READ got " + str(arg_num) + " arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction READ: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', type):
            sys.stderr.write("ERROR: Instruction READ: argument 2 is not a variable or a type")
            exit(53)

        super().__init__("READ", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Reads a value from stdin, converts it to type arg2 and saves said value to arg1.
        In case of an invalid or empty an input saves value nil of type nil.
        :param arg1: var
        :param arg2: type
        :param arg3: None
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != type:
                sys.stderr.write("ERROR: Instruction READ: argument 2 is not a valid type")
                exit(53)

        try:
            #  get value from input  #
            if args.input is None:
                value = input()
            else:
                value = Input.pop()
            # ---------------------- #
            in_type = arg2.get_value()
            # true of any case => True; anything else => False
            if in_type == bool:
                if value.upper() == 'TRUE':
                    value = True
                else:
                    value = False
            else:
                if in_type == int:
                    value = int(value)
                elif in_type == str:
                    for ch in set(re.findall(r'\\\d{3}', value)):
                        value = value.replace(ch, chr(int(ch[1:])))
        except (KeyboardInterrupt, IndexError, ValueError):
            value = 'nil'

        arg1.set_value(value)


class WRITE(Instruction):
    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction WRITE got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if not arg1.is_symbol():
            sys.stderr.write("ERROR: Instruction WRITE: argument 1 is not a symbol")
            exit(53)

        super().__init__("WRITE", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        if arg1.is_variable():
            arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        val = arg1.get_value()
        if arg1.get_type() == 'nil' or arg1.get_var_type() == 'nil':
            val = ''

        # TODO: interpret escape sequences - \032 => whitespace
        if arg1.get_type() == str or arg1.get_var_type() == str:
            pass

        # if val is None:
        #     sys.stderr.write("ERROR: Instruction WRITE: Empty value\n")
        #     exit(56)

        print(val, end='')


class CONCAT(Instruction):
    """
    Instruction CONCAT from IPPcode23 requires 3 arguments of type variable, string and string.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction CONCAT got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction CONCAT: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', str) or not arg3.get_type() in ('var', str):
            sys.stderr.write("ERROR: Instruction CONCAT: argument 2 or 3 is not a variable or a string")
            exit(53)

        super().__init__("CONCAT", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves the concatenation of arg2 and arg3 to a variable specified by arg1.
        :param arg1: var
        :param arg2: string
        :param arg3: string
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != str:
                sys.stderr.write("ERROR: Instruction CONCAT: argument 2 is not a string")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != str:
                sys.stderr.write("ERROR: Instruction CONCAT: argument 3 is not a string")
                exit(53)

        arg1.set_value(arg2.get_value() + arg3.get_value())


class STRLEN(Instruction):
    """
    Instruction STRLEN from IPPcode23 requires 2 arguments of type variable, string.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction STRLEN got " + str(arg_num) + " arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction STRLEN: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', str):
            sys.stderr.write("ERROR: Instruction STRLEN: argument 2 is not a variable or a string")
            exit(53)

        super().__init__("CONCAT", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves the lenght of arg2 to a variable specified by arg1.
        :param arg1: var
        :param arg2: string
        :param arg3: None
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != str:
                sys.stderr.write("ERROR: Instruction CONCAT: argument 2 is not a string")
                exit(53)

        arg1.set_value(len(arg2.get_value()))


class GETCHAR(Instruction):
    """
    Instruction GETCHAR from IPPcode23 requires 3 arguments of type variable, string and int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction GETCHAR got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction GETCHAR: argument 1 is not a variable")
            exit(53)
        if not arg2.get_type() in ('var', str):
            sys.stderr.write("ERROR: Instruction GETCHAR: argument 2 is not a variable or a string")
            exit(53)
        if not arg3.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction GETCHAR: argument 3 is not a variable or a int")
            exit(53)

        super().__init__("GETCHAR", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Saves character on position arg3 from string arg2 to a variable arg1.
        :param arg1: var
        :param arg2: string
        :param arg3: int
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != str:
                sys.stderr.write("ERROR: Instruction GETCHAR: argument 2 is not a string")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction GETCHAR: argument 3 is not an int")
                exit(53)
        try:
            arg1.set_value(arg2.get_value()[arg3.get_value()])
        except IndexError:
            sys.stderr.write("ERROR: Instruction GETCHAR: index outside of string")
            exit(58)


class SETCHAR(Instruction):
    """
    Instruction SETCHAR from IPPcode23 requires 3 arguments of type variable, int and string.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction SETCHAR got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction SETCHAR: argument 1 is not a variable")
            exit(53)
        if not arg3.get_type() in ('var', str):
            sys.stderr.write("ERROR: Instruction SETCHAR: argument 3 is not a variable or a string")
            exit(53)
        if not arg2.get_type() in ('var', int):
            sys.stderr.write("ERROR: Instruction SETCHAR: argument 2 is not a variable or a int")
            exit(53)

        super().__init__("SETCHAR", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Modifies character on position arg2 in a string variable arg1 to the first character from string arg3.
        :param arg1: var(string)
        :param arg2: int
        :param arg3: string
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())
        if arg1.get_var_type() != str:
            sys.stderr.write("ERROR: Instruction SETCHAR: argument 1 is not a string")
            exit(53)

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            if arg2.get_var_type() != int:
                sys.stderr.write("ERROR: Instruction SETCHAR: argument 2 is not an int")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            if arg3.get_var_type() != str:
                sys.stderr.write("ERROR: Instruction SETCHAR: argument 3 is not a string")
                exit(53)
        try:
            string_to_change = list(arg1.get_value())
            string_to_change[arg2.get_value()] = arg3.get_value()[0]
            arg1.set_value(''.join(string_to_change))
        except IndexError:
            sys.stderr.write("ERROR: Instruction SETCHAR: index outside of arg1 or arg3 is an empty string")
            exit(58)


class TYPE(Instruction):
    """
    Instruction TYPE from IPPcode23 requires 2 arguments of type variable and symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 2:
            sys.stderr.write("ERROR: Instruction TYPE got " + str(arg_num) + " arguments, 2 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])

        if not arg1.is_variable():
            sys.stderr.write("ERROR: Instruction TYPE: argument 1 is not of type variable")
            exit(53)
        if not arg2.is_symbol():
            sys.stderr.write("ERROR: Instruction TYPE: argument 2 is not of type symbol")
            exit(53)
        super().__init__("TYPE", arg1, arg2)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Finds out type of constant (int, string, nil, bool) of arg2 and writes the result as a string to a variable
        specified by arg1.
        :param arg1: var
        :param arg2: symb
        :param arg3: None
        """
        arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        my_type = arg2.get_type()
        if my_type == 'var':
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            my_type = arg2.get_var_type()
            if my_type is None:
                my_type = ''
                arg1.set_value(my_type)
                return

        type_dict = {
            int: 'int',
            str: 'string',
            bool: 'bool',
            'nil': 'nil',
        }
        arg1.set_value(type_dict[my_type])


class LABEL(Instruction):
    """
    Instruction LABEL from IPPcode23 requires 1 argument of type label.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction LABEL got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if arg1.get_type() != 'label':
            sys.stderr.write("ERROR: Instruction LABEL: argument 1 is not of type label")
            exit(53)

        super().__init__("LABEL", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Defines a label which can be used by all jump instructions.
        :param arg1: label
        :param arg2: None
        :param arg3: None
        """
        s.push([arg1.get_value(), c.get_count()], "L")


class JUMP(Instruction):
    """
    Instruction JUMP from IPPcode23 requires 1 argument of type label.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction JUMP got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if arg1.get_type() != 'label':
            sys.stderr.write("ERROR: Instruction JUMP: argument 1 is not of type label")
            exit(53)

        super().__init__("JUMP", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Jumps to the label specified by arg1.
        :param arg1: label
        :param arg2: None
        :param arg3: None
        """
        c.set_count(s.jump(arg1.get_value()))


class JUMPIFEQ(Instruction):
    """
    Instruction JUMPIFEQ from IPPcode23 requires 3 arguments of type label, symbol and symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction JUMPIFEQ got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if arg1.get_type() != 'label':
            sys.stderr.write("ERROR: Instruction JUMPIFEQ: argument 1 is not of type label")
            exit(53)
        if not arg2.is_symbol():
            sys.stderr.write("ERROR: Instruction JUMPIFEQ: argument 2 or 3 is not a symbol")
            exit(53)

        super().__init__("JUMPIFEQ", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Jumps to a label specified by arg1 if arg2 and arg3 are equal. It doesn't utilize instruction EQ because that
        would require defining a variable in a known Frame which might cause problems if a variable of the same name
        would be used by program.
        :param arg1: label
        :param arg2: symb
        :param arg3: symb
        """
        # arg = Argument('var', 'GF@MyTinyGlobalTemporaryVariableUsedBySomeInstructionsWithSillyButUniqueEnoughName000')
        # DEFVAR.execute(arg, None, None)
        # EQ.execute(arg, arg2, arg3)
        # if arg.get_value():
        #     JUMP.execute(arg1, None, None)

        type1 = arg2.get_type()
        type2 = arg3.get_type()

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            type1 = arg2.get_var_type()
            if type1 not in (int, str, bool, 'nil'):
                sys.stderr.write("ERROR: Instruction JUMPIFEQ: wrong type of argument 2")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            type2 = arg3.get_var_type()
            if type2 not in (int, str, bool, 'nil'):
                sys.stderr.write("ERROR: Instruction JUMPIFEQ: wrong type of argument 3")
                exit(53)

        if type1 != type2 and type1 != 'nil' and type2 != 'nil':
            sys.stderr.write("ERROR: Instruction JUMPIFEQ: can't compare arguments of different types "
                             "unless one of them is of type nil")
            exit(53)

        if type1 == type2 and arg2.get_value() == arg3.get_value():
            JUMP.execute(arg1, None, None)


class JUMPIFNEQ(Instruction):
    """
    Instruction JUMPIFNEQ from IPPcode23 requires 3 arguments of type label, symbol and symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 3:
            sys.stderr.write("ERROR: Instruction JUMPIFNEQ got " + str(arg_num) + " arguments, 3 arguments expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])
        arg2 = Argument(types[1], arguments[1])
        arg3 = Argument(types[2], arguments[2])

        if arg1.get_type() != 'label':
            sys.stderr.write("ERROR: Instruction JUMPIFNEQ: argument 1 is not of type label")
            exit(53)
        if not arg2.is_symbol():
            sys.stderr.write("ERROR: Instruction JUMPIFNEQ: argument 2 or 3 is not a symbol")
            exit(53)

        super().__init__("JUMPIFNEQ", arg1, arg2, arg3)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Jumps to a label specified by arg1 if arg2 and arg3 are not equal.
        :param arg1: label
        :param arg2: symb
        :param arg3: symb
        """

        type1 = arg2.get_type()
        type2 = arg3.get_type()

        if arg2.is_variable():
            arg2 = f.get_var(arg2.get_name(), arg2.get_frame())
            type1 = arg2.get_var_type()
            if type1 not in (int, str, bool, 'nil'):
                sys.stderr.write("ERROR: Instruction JUMPIFNEQ: wrong type of argument 2")
                exit(53)

        if arg3.is_variable():
            arg3 = f.get_var(arg3.get_name(), arg3.get_frame())
            type2 = arg3.get_var_type()
            if type2 not in (int, str, bool, 'nil'):
                sys.stderr.write("ERROR: Instruction JUMPIFNEQ: wrong type of argument 3")
                exit(53)

        if type1 != type2 and type1 != 'nil' and type2 != 'nil':
            sys.stderr.write("ERROR: Instruction JUMPIFNEQ: can't compare arguments of different types "
                             "unless one of them is of type nil")
            exit(53)

        if type1 != type2 or arg2.get_value() != arg3.get_value():
            JUMP.execute(arg1, None, None)


class EXIT(Instruction):
    """
    Instruction EXIT from IPPcode23 requires 1 argument of type int.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction EXIT got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if arg1.get_type() not in ('var', int):
            sys.stderr.write("ERROR: Instruction EXIT: argument 1 is not a valid symbol")
            exit(53)

        super().__init__("EXIT", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        if arg1.is_variable():
            arg1 = f.get_var(arg1.get_name(), arg1.get_frame())
            if arg1.get_var_type != int:
                sys.stderr.write("ERROR: Instruction EXIT: argument 1 is not an int")
                exit(53)

        val = arg1.get_value()
        if 0 <= val <= 49:
            exit(val)
        else:
            sys.stderr.write("ERROR: Instruction EXIT: invalid exit value")
            exit(57)


class DPRINT(Instruction):
    """
    Instruction DPRINT from IPPcode23 requires 1 argument of type symbol.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 1:
            sys.stderr.write("ERROR: Instruction DPRINT got " + str(arg_num) + " arguments, 1 argument expected")
            exit(52)

        arg1 = Argument(types[0], arguments[0])

        if not arg1.is_symbol():
            sys.stderr.write("ERROR: Instruction DPRINT: argument 1 is not a symbol")
            exit(53)

        super().__init__("DPRINT", arg1)

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Writes value or arg1 to stderr.
        :param arg1: symb
        :param arg2: None
        :param arg3: None
        """
        if arg1.is_variable():
            arg1 = f.get_var(arg1.get_name(), arg1.get_frame())

        val = arg1.get_value()
        if arg1.get_type() == 'nil' or arg1.get_var_type() == 'nil':
            val = ''

        # TODO: interpret escape sequences - \032 => whitespace
        if arg1.get_type() == str or arg1.get_var_type() == str:
            pass

        sys.stderr.write(val)


class BREAK(Instruction):
    """
    Instruction BREAK from IPPcode23 requires 0 arguments.
    """

    def __init__(self, arg_num: int, arguments: list, types: list):
        if arg_num != 0:
            sys.stderr.write("ERROR: Instruction BREAK got " + str(arg_num) + " arguments, 0 arguments expected")
            exit(52)

        super().__init__("BREAK")

    @classmethod
    def execute(cls, arg1: Argument | None, arg2: Argument | None, arg3: Argument | None) -> None:
        """
        Writes the state of interpret to stderr.
        :param arg1: None
        :param arg2: None
        :param arg3: None
        """
        sys.stderr.write('\n' + 'Labels => ' + s.ret_all('L') + '\n')
        sys.stderr.write('Data stack => ' + s.ret_all('D') + '\n')
        sys.stderr.write('Call stack => ' + s.ret_all('C') + '\n\n')


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


# ______ERRORS______
#  py ERROR
#   31 - XML file is not well-formed
#   32 - unexpected XML structure   (dupes)

#   2  - most argparse errors

#  project ERROR
#   10      - missing parameter
#   11      - error when opening input files    - argparse errno 13
#   12      - error when opening output files
#   99      - internal error

#  Interpreter ERROR
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
    f = Frame()
    s = Stack()
    #   Parsing arguments
    parser = argparse.ArgumentParser(
        description='Python interpreter of IPPcode23',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
        Either '--source' or '--input' argument required
            - STDIN will then be regarded as the other one
        '''))
    parser.add_argument("--source", metavar='file', type=argparse.FileType('r'), help='file containing XML code')
    parser.add_argument("--input", metavar='file', type=argparse.FileType('r'),
                        help='input of XML instructions (e.g. READ)')
    args = parser.parse_args()

    # Check availability of source and input files
    root: Tree.Element
    InputFile: str
    #   No file
    if args.source is None and args.input is None:
        sys.stderr.write('at least one of --source and --input required')  # parser.error()    <- error 2
        exit(10)

    #   Only input file
    elif args.source is None:
        SourceString = ""
        with fileinput.input('-') as fil:
            for line in fil:
                SourceString += line
        root = Tree.fromstring(SourceString)

        with open(args.input.name, encoding=args.input.encoding) as In:
            InputFile = In.read()

    #  Only source file
    elif args.input is None:
        # noinspection PyUnresolvedReferences
        with open(args.source.name, encoding=args.source.encoding) as SourceFile:
            tree = Tree.parse(SourceFile)
            root = tree.getroot()

    #   Both files
    else:
        with open(args.source.name, encoding=args.source.encoding) as SourceFile:
            tree = Tree.parse(SourceFile)
            root = tree.getroot()

        with open(args.input.name, encoding=args.input.encoding) as In:
            InputFile = In.read()

    # noinspection PyUnboundLocalVariable
    if root.tag != 'program':
        sys.stderr.write('ERROR: No "program" root of XML')
        exit(31)

    if args.input:
        # noinspection PyUnboundLocalVariable
        Input = list(InputFile.splitlines())
        Input.reverse()
    # for element in Input:
    #     s.push(element, 'I')

    # Sort instructions, non-author code from:
    #    https://devdreamz.com/question/931441-python-sort-xml-elements-by-and-tag-and-attributes-recursively
    root[:] = sorted(root, key=lambda child: (child.tag, int(child.get('order'))))
    # slightly altered continuation of code from the same site

    for instr in root:
        attrib = instr.attrib
        if len(attrib) > 1:
            instr[:] = sorted(instr, key=lambda child: (child.tag, child.get('desc')))
            attribs = sorted(attrib.items())
            attrib.clear()
            # noinspection PyTypeChecker
            attrib.update(attribs)
    # end of non-author code

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
        for instr in i.get_list():  # loop through program to define labels for forward jumps
            if instr.get_opcode() == "LABEL":
                instr.execute(instr.get_arg(1), instr.get_arg(2), instr.get_arg(3))
            c.increment_count()
        c.reset_count()

        InstrList = i.get_list()
        while c.get_count() < instrCount:
            instr = InstrList[c.get_count()]
            # loop through program while skipping execution of label instructions to prevent
            # creation of labels with the same name
            if instr.get_opcode() != 'LABEL':
                instr.execute(instr.get_arg(1), instr.get_arg(2), instr.get_arg(3))
            c.increment_count()
            # TODO: remove prints
            # print(instr.get_opcode(), ':', instr.get_arg(1), instr.get_arg(2), instr.get_arg(3))
        # print(c.get_count())
