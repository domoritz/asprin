#!/usr/bin/python

#
# IMPORTS
#

from __future__ import print_function
import re
import argparse
import sys
import clingo
import os
from src.spec_parser    import    spec_parser
from src.program_parser import program_parser
from src.solver         import         solver
from src.utils          import        printer
from src.utils          import          utils
import errno

#
# DEFINES
#

VERSION       = "3.0.0"
UNKNOWN       = "UNKNOWN"
ERROR         = "*** ERROR: (asprin): {}"
ERROR_INFO    = "*** Info : (asprin): Try '--help' for usage information"
ERROR_OPEN    = "<cmd>: error: file could not be opened:\n  {}\n"
ERROR_FATAL   = "Fatal error, this should not happen.\n"
ERROR_PARSING = "parsing failed"


#
# GLOBAL VARIABLES AND FUNCTIONS
#

class MyArgumentParser(argparse.ArgumentParser):

    def print_help(self, file=None):
        if file is None:
            file = sys.stdout
        file.write("asprin version {}\n".format(VERSION))
        argparse.ArgumentParser.print_help(self, file)
       
    def error(self, message):
        raise argparse.ArgumentError(None,"In context <asprin>: " + message)


#
# class AsprinArgumentParser
#
class AsprinArgumentParser:


    clingo_help = """
Clingo Options:
  --<option>[=<value>]\t: Set clingo <option> [to <value>]

    """


    usage = "asprin [number] [options] [files]"


    epilog = """
Default command-line:
asprin --models 1

asprin is part of Potassco: https://potassco.org/labs
Get help/report bugs via : https://potassco.org/support
    """


    version_string = "asprin " + VERSION + """
Copyright (C) Javier Romero
License: The MIT License <https://opensource.org/licenses/MIT>"""


    def __init__(self):
        self.underscores  = 0
        self.__first_file = None
        self.__file_warnings = []

    def __update_underscores(self,new):
        i = 0
        while len(new)>i and new[i]=="_": i+=1
        if i>self.underscores: self.underscores = i


    def __add_file(self,files,file):
        abs_file = os.path.abspath(file) if file != "-" else "-"
        if abs_file in [i[1] for i in files]:
            self.__file_warnings.append(file)
        else:
            files.append((file,abs_file))
        if not self.__first_file:
            self.__first_file = file


    def run(self):

        # command parser
        _epilog = self.clingo_help + "\nusage: " + self.usage + self.epilog
        cmd_parser = MyArgumentParser(usage=self.usage, epilog=_epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False)

        # Basic Options
        basic = cmd_parser.add_argument_group('Basic Options')
        basic.add_argument('-h', '--help', action='help',
                           help=': Print help and exit')
        basic.add_argument('-v', '--version', dest='version',
                           action='store_true',
                           help=': Print version information and exit')
        basic.add_argument('--print-programs', dest='print-programs',
                           help=': Print translated programs and exit',
                           action='store_true')
        #basic.add_argument('-', dest='read_stdin', action='store_true',
        #                   help=argparse.SUPPRESS)
        basic.add_argument('--stats', dest='stats', action='store_true',
                           help=': Print statistics')
        basic.add_argument('--no-asprin-lib', dest='asprin-lib',
                           help=': Do not include asprin.lib',
                           action='store_false')
        basic.add_argument('-c', '--const', dest='constants', 
                           action="append", help=argparse.SUPPRESS,default=[])

        # Solving Options
        solving = cmd_parser.add_argument_group('Solving Options')
        solving.add_argument('--models', '-n',
                             help=": Compute at most <n> models (0 for all)",
                             type=int, dest='max_models', metavar='<n>',
                             default=1)
        solving.add_argument('--steps', '-s', 
                             help=": Execute at most <s> steps", type=int,
                             dest='steps', metavar='<s>', default=0)
        solving.add_argument('--project', dest='project',
                             help=': Enable projective solution enumeration',
                             action='store_true')
        solving.add_argument('--solving-mode', dest='solving_mode', 
                             metavar="<arg>",
                             #help=""": Run {normal|approx|heuristic} \
                             #          solving mode""",
                             help=argparse.SUPPRESS,
                             default="normal", 
                             choices=["normal", "approx", "heuristic"])

        options, unknown = cmd_parser.parse_known_args()
        options = vars(options)

        # print version
        if options['version']:
            print(self.version_string)
            sys.exit(0)

        # separate files, number of models and clingo options
        options['files'], clingo_options = [], []
        for i in unknown:
            if i=="-":                                   
                self.__add_file(options['files'],i)
            elif (re.match(r'^([0-9]|[1-9][0-9]+)$',i)): 
                options['max_models'] = int(i)
            elif (re.match(r'^-',i)):                    
                clingo_options.append(i)
            else:                                        
                self.__add_file(options['files'],i)

        # when no files, add stdin
        # build prologue
        if options['files'] == []:
            self.__first_file = "stdin"
            options['files'].append(("-","-"))
        if len(options['files'])>1: 
            self.__first_file += " ..."
        prologue = "asprin version " + VERSION + "\nReading from " 
        prologue += self.__first_file

        # handle constants
        constants = dict()
        for i in options['constants']:
            old, sep, new = i.partition("=")
            self.__update_underscores(new)
            if old in constants:
                raise Exception("constant defined twice")
            else:
                constants[old] = new
        options['constants'] = constants

        # statistics
        # if options['stats']:
        clingo_options.append('--stats')

        # return
        return options, clingo_options, self.underscores, prologue, \
               self.__file_warnings



#
# class Asprin
#
class Asprin:


    def __update_constants(self,options,constants):
        for i in constants:
            if i[0] not in options['constants']:
                options['constants'][i[0]] = i[1]


    def __get_control(self,clingo_options):
        try:
            return clingo.Control(clingo_options)
        except Exception as e:
            raise argparse.ArgumentError(None,e.message)

    def run_wild(self):

        # arguments parsing 
        aap = AsprinArgumentParser()
        options, clingo_options, underscores, prologue, warnings = aap.run()

        # create Control object
        control = self.__get_control(clingo_options)

        # print prologue and warnings
        print(prologue)
        for i in warnings:
            printer.Printer().warning_included_file(i)

        # specification parsing
        sp = spec_parser.Parser(underscores)
        programs, utils.underscores, base_constants, options['show'] = \
                                                 sp.parse_files(options)
        self.__update_constants(options, base_constants)

        # preference programs parsing
        program_parser.Parser(control, programs, options).parse()

        # solving
        _solver = solver.Solver(control)
        _solver.set_options(options)
        _solver.run()


    def run(self):
        try:
            self.run_wild()
        except argparse.ArgumentError as e:
            print(ERROR.format(str(e)),file=sys.stderr)
            print(ERROR_INFO,file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            if (e.errno == errno.ENOENT):
                print(ERROR_OPEN.format(e.filename),file=sys.stderr)
                print(ERROR.format(ERROR_PARSING),file=sys.stderr)
            else: 
                print(ERROR.format(str(e)),file=sys.stderr)
            print(UNKNOWN,file=sys.stdout)
            sys.exit(65)
        except utils.SilentException as e:
            pass
        except utils.FatalException as e:
            print(ERROR.format(ERROR_FATAL),file=sys.stderr)
            print(UNKNOWN,file=sys.stdout)
            sys.exit(65)
        except Exception as e:
            print(ERROR.format(str(e)),file=sys.stderr)
            print(UNKNOWN,file=sys.stdout)
            sys.exit(65)

