#   David Novak
#   xnovak2r
#   IPP proj 2 - Python interpreter
#   april 2023

import fileinput
import argparse
import sys
import textwrap
import xml.etree.ElementTree as ET


class Counter:
    def __init__(self):
        self._Count = 0

    def get_count(self):
        return self._Count

    def increment_count(self):
        self._Count += 1

    def reset_count(self):
        self._Count = 0


### Class definition
#   every instuction has atributes opcode to define opcode, number of instructions, argument types,
#   arguments (class Argument) and it appends itself to instruction list which is shared among all Instructions
class Instruction:
    _InstructionList = []

    def __init__(self, opcode, arg1: None, arg2: None, arg3: None):
        self._Opcode = opcode
        self._NumOfArgs = arg_num
        self._Type = t
        self._Arg = []
        self._InstructionList.append(self)

        if self._NumOfArgs < 0 or self._NumOfArgs > 3:
            sys.stderr.write("ERROR: Instruction init(): wrong number of arguments\n")
            exit(52)

        for number in range(self._NumOfArgs):
            self._Arg.append(Argument(self._Type[number], arg[number]))

    def get_opcode(self):
        return self._Opcode

    def get_list(self):
        return self._InstructionList

    def get_arg_num(self):
        return self._NumOfArgs

    def get_arg(self, arg_num):
        if 3 < arg_num < 0:
            exit(99)
        else:
            return self._Arg[arg_num]


#   every Argument of every instruction has defined type
#   if argument is variable
##      defined: frame, name
##      may be defined: value + var_type
#   other arguments
##      defined: value
class Argument:

    def __init__(self, ):
        self._VarType = ""
        self._Type = t
        self._Frame = None
        self._Name: str
        self._Value: str

        if self._Type == "var":
            self._Frame = string.split('@')[0]
            self._Name = string.split('@')[1]
        else:
            self._Value = string

    def get_type(self):
        return self._Type

    def get_value(self):
        try:
            return self._Value
        except AttributeError:
            sys.stderr.write("ERROR: Argument get_value(): empty variable\n")
            exit(56)

    def set_value(self, value):
        if self._Type == "var":
            if value is None:
                self._VarType = "string"
                self._Value = ""
            elif value == "True" or value == "False":
                self._Value = bool(value)
                self._VarType = "bool"
            elif value.isnumeric():
                self._VarType = "int"
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
        except AttributeError:
            sys.stderr.write("ERROR: Argument get_name(): argument is not variable\n")
            exit(53)

    def set_frame(self, frame):
        if self.get_frame() == "LF" and frame == "TF":
            self._Frame = frame
        elif self.get_frame() == "TF" and frame == "LF":
            self._Frame = frame
        else:
            sys.stderr.write("ERROR: Argument set_frame(): can't set frame\n")
            exit(57)

    def is_variable(self):
        if self.get_frame():
            return True
        return False

    def get_var_type(self):
        if self.is_variable():
            return self._VarType
        sys.stderr.write("ERROR: get_var_type(): argument is not a variable\n")
        exit(99)

    def has_value(self):
        try:
            return self._Value
        except AttributeError:
            return False


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
# TODO: check - order, opcode, arg_num, arg_type, arg_value is from arg_type, arg_value OK for instruction
class MOVE(Instruction):
    def __init__(self, arg_num, arg, t):
        super().__init__("MOVE", arg_num, arg, t)
class CREATEFRAME(Instruction):
class PUSHFRAME(Instruction):
class POPFRAME(Instruction):
class DEFVAR(Instruction):
class CALL(Instruction):
class RETURN(Instruction):
class PUSHS(Instruction):
class POPS(Instruction):
class ADD(Instruction):
class SUB(Instruction):
class MUL(Instruction):
class IDIV(Instruction):
class LT(Instruction):
class GT(Instruction):
class EQ(Instruction):
class AND(Instruction):
class OR(Instruction):
class NOT(Instruction):
class INT2CHAR(Instruction):
class STRI2INT(Instruction):
class READ(Instruction):
class WRITE(Instruction):
class CONCAT(Instruction):
class STRLEN(Instruction):
class GETCHAR(Instruction):
class SETCHAR(Instruction):
class TYPE(Instruction):
class LABEL(Instruction):
class JUMP(Instruction):
class JUMPIFEQ(Instruction):
class JUMPIFNEQ(Instruction):
class EXIT(Instruction):
class DPRINT(Instruction):
class BREAK(Instruction):

class Factory:
    @classmethod
    def resolve(cls, opcode: str, arg_num, value, t):
        if opcode.upper() == 'MOVE':
            return MOVE(value, )
        elif opcode.upper() == 'CREATEFRAME':
            return CREATEFRAME(value, t)
        elif opcode.upper() == 'PUSHFRAME':
            return PUSHFRAME(value, t)
        elif opcode.upper() == 'POPFRAME':
            return POPFRAME(value, t)
        elif opcode.upper() == 'DEFVAR':
            return DEFVAR(value, t)
        elif opcode.upper() == 'CALL':
            return CALL(value, t)
        elif opcode.upper() == 'RETURN':
            return RETURN(value, t)

        elif opcode.upper() == 'PUSHS':
            return PUSHS(value, t)
        elif opcode.upper() == 'POPS':
            return POPS(value, t)

        elif opcode.upper() == 'ADD':
            return ADD(value, t)
        elif opcode.upper() == 'SUB':
            return SUB(value, t)
        elif opcode.upper() == 'MUL':
            return MUL(value, t)
        elif opcode.upper() == 'IDIV':
            return IDIV(value, t)
        elif opcode.upper() == 'LT':
            return LT(value, t)
        elif opcode.upper() == 'GT':
            return GT(value, t)
        elif opcode.upper() == 'EQ':
            return EQ(value, t)
        elif opcode.upper() == 'AND':
            return AND(value, t)
        elif opcode.upper() == 'OR':
            return OR(value, t)
        elif opcode.upper() == 'NOT':
            return NOT(value, t)
        elif opcode.upper() == 'INT2CHAR':
            return INT2CHAR(value, t)
        elif opcode.upper() == 'STRI2INT':
            return STRI2INT(value, t)

        elif opcode.upper() == 'READ':
            return READ(value, t)
        elif opcode.upper() == 'WRITE':
            return WRITE(value, t)

        elif opcode.upper() == 'CONCAT':
            return CONCAT(value, t)
        elif opcode.upper() == 'STRLEN':
            return STRLEN(value, t)
        elif opcode.upper() == 'GETCHAR':
            return GETCHAR(value, t)
        elif opcode.upper() == 'SETCHAR':
            return SETCHAR(value, t)

        elif opcode.upper() == 'TYPE':
            return TYPE(value, t)
        elif opcode.upper() == 'LABEL':
            return LABEL(value, t)
        elif opcode.upper() == 'JUMP':
            return JUMP(value, t)
        elif opcode.upper() == 'JUMPIFEQ':
            return JUMPIFEQ(value, t)
        elif opcode.upper() == 'JUMPIFNEQ':
            return JUMPIFNEQ(value, t)
        elif opcode.upper() == 'EXIT':
            return EXIT(value, t)

        elif opcode.upper() == 'DPRINT':
            return DPRINT(value, t)
        elif opcode.upper() == 'BREAK':
            return BREAK(value, t)
        else:
            sys.stderr.write('ERROR: unknown instruction\n')
            exit(52)


### ERROR
##  py ERROR
#   31 - XML file is not well-formed
#   32 - unexpected XML structure   (dup)

#   2  - most argparse errors

##  project ERROR
#   10      - missing parameter
#   11      - error when opening input files    - argparse errno 13
#   12      - error when opening output files
#   99      - internal error

##  Interpreter ERROR
#   52      - semantic ERROR in input   (unknown instruction)
#   53      - wrong operand types
#   54      - non-existing variable access
#   55      - non-existing frame
#   56      - missing value
#   57      - wrong operand value   (div by 0)
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
    root: ET.Element
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
        root = ET.fromstring(SourceString)

        with open(args.input.name, encoding=args.input.encoding) as In:
            InputFile = In.read()

    #   Only source file
    elif args.input is None:
        # noinspection PyUnresolvedReferences
        with open(args.source.name, encoding=args.source.encoding) as SourceFile:
            tree = ET.parse(SourceFile)
            root = tree.getroot()

        InputFile = ""
        with fileinput.input('-') as f:
            for line in f:
                InputFile += line

    #   Both files
    else:
        with open(args.source.name, encoding=args.source.encoding) as SourceFile:
            tree = ET.parse(SourceFile)
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
