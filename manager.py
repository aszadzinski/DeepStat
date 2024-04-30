import os
from ai import AI
import shutil
from pandas import DataFrame
from subprocess import check_output
from ai import Responses
from typing import Callable

from addons import fm
from commands import (CommandTemplate, FileCommand, DescTableCommand, DescCommand, CustomCommand, CountTableCommand, CrossTableCommand,ExpandTableCommand,
                      PlotCommand, AICommand,
                      QueryCommand, StatisticCommand,
                      UnsupportedCommand)
from conf import structure, tex_config
from texbuilder import TeXbuilder


class CommandManager():
    """Loader class."""

    def __init__(self, responses: Responses, data : DataFrame, ai):
        self.df = data
        self.ai = ai
        self.commands : list[CommandTemplate] = []
        self.queue : list[CommandTemplate] = []
        self.last_id : int = 0
        self.responses = responses
        self.command_map = {
            'file' : {
                'desc' : FileCommand,
                'table': FileCommand,
                'plot': UnsupportedCommand,
                'stat': UnsupportedCommand,
            },
            'gen' : {
                'desc' : DescCommand,
                'desctable': DescTableCommand,
                'counttable': CountTableCommand,
                'crosstable': CrossTableCommand,
                'expandtable': ExpandTableCommand,
                'plot': PlotCommand,
                'stat': StatisticCommand,
            },
            'load' : {
                'desc' : QueryCommand,
                'table': QueryCommand,
                'plot': QueryCommand,
                'stat': QueryCommand,
            },
            "gendesc" : {
                'desc' : DescCommand,
            },
            'static' : {
                'desc' : CustomCommand,
            }
        }

    def create_id(self):
        self.last_id += 1
        return self.last_id

    def register(self, flg: str, kind: str, ctx: str, silent = False, mode: str = 'static', paraphrase: bool = False, loc: str = 'inline', alias='NoName', *args, **kwargs) -> None:
        print("\t- Registering {} as {} for {} in {} mode p{}".format(
            fm(kind),
            fm(flg, 'yellow'),
            fm(ctx, 'cyan'),
            fm(mode, 'red'),
            fm(paraphrase),
        ))
        orderID = self.create_id()
        # runtime_data =   TODO
        params = {
            "id" : orderID,
            "flg" : flg,
            "kind" : kind,
            "ai" : self.ai,
            "ctx" : ctx,
            "mode" : mode,
            "loc" : loc,
            "alias" : alias,
            'kwargs' : kwargs,
            'silent' : silent,
            "paraphrase" : paraphrase,
            "data" : self.df,
            "responses" : self.responses,
        }

        # SET METHOD TODO

        command : CommandTemplate = self.command_map[flg][kind](**params)
        self.commands.append(command)
        return command

    def create_queue(self):
        """Define priority of instructions."""
        print("\t- Sorting instructions list")
        hierarchy = ['file', 'gen', 'load', 'static', 'gendesc']
        self.queue = sorted(self.commands, key=lambda obj: hierarchy.index(obj.flg))

    def execute_queue(self):
        print("\t- Executing analysis command")
        for command in self.queue:
            try:
                print("\t\t- Executing command: {}: ".format(command.id), end='')
                command.execute()
            except Exception as e:
                print(fm("Fail", 'red'), end='')
                print(" {}".format(e))
            else:
                print(fm("Pass", 'green'))


class Analysis:
    """Session analysis builder."""

    def __init__(self, tex_config: dict, data : DataFrame, doc_type: str = "latex"):
        """Session manager for analysis session."""
        self.structure : Callable
        self.ai =  AI()
        self.responses : Responses = Responses.init(tex_config['responses_file'])
        self.df = data
        self.command_manager : CommandManager = CommandManager(self.responses, self.df, self.ai)
        self.document : TeXbuilder = TeXbuilder("Report", config=tex_config, init=True)
        self.create_folders()

    def create_folders(self):
        print("- Creating folders..")
        print("\t- picture folder", end='')
        try:
            os.mkdir(os.path.join(tex_config['folder'], 'pics'))
        except Exception as e:
            print("folder exists, {}".format(fm('skip', 'red')))
        else:
            print(fm('Done'))

    def register_commands(self):
        self.structure = structure(self.command_manager)

    def create_table_of_content(self):
        """Wrap tex build."""
        print('\t- Creating table of content')
        print('\t=====================================================')
        self.document.build(self.structure, self.document)
        print('\t=====================================================')

    def boost_commands(self):
        self.command_manager.create_queue()
        self.command_manager.execute_queue()

    def build_document(self):
        print('\t- Applying payloads & building document')
        self.document.apply_payloads()  # self.command_manager.commands)

    def queue_organizer(self, queue):
        """Organize analysis instruction based on priority of funcions."""

    def compile(self):
        try:
            print("- Compiling document... ", end='')
            compile_config = tex_config['compile']
            filename = tex_config['filename']
            file_path = os.path.join(tex_config['folder'], filename + ".tex")
            command = "{} {} {}".format(
                compile_config['executable'],
                compile_config['options'],
                file_path,
            )
            for n in range(2):
                _ = check_output(command + " 1 > /dev/null", shell=True)

            shutil.copy(filename + ".pdf", file_path + ".pdf")
            ext2del = [
                ".log",
                ".aux",
                ".lof",
                ".lot",
                ".out",
                ".toc",
                ".pdf",
            ]
            for file in ext2del:
                os.remove(filename + file)

        except Exception as e:
            print("{} {}".format(fm("FAIL", "red"), e))
        else:
            print(fm('DONE'))
