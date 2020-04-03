import keyword
import argparse
import os
from parser.SolidityLexer import *
from parser.SolidityParser import *


def main(args):
    classname = os.path.basename(args.src).split('.')[0]
    file = FileStream(args.src)
    lexer = SolidityLexer(file)
    stream = CommonTokenStream(lexer)
    parser = SolidityParser(stream)

    # Initialize files

    if not os.path.isdir(args.dst):
        os.mkdir(args.dst)

    with open(args.dst + '/Enums.py', 'w+') as enums:
        enums.write('from enum import Enum\n\n')

    with open(args.dst + '/' + classname + 'Contract.py', 'w+') as contract_file:
        contract_file.write('from .Contract import Contract\n' +
                            'from .Enums import *\n' +
                            'import datetime\n' +
                            'from .. import helper\n\n\n')

    # Parsing
    tree = parser.sourceUnit()

    for i in range(0, len(tree.contractDefinition())):
        contract: SolidityParser.ContractDefinitionContext = tree.contractDefinition()[i]

        contract_name: str = contract.identifier().Identifier().getText()

        with open(args.dst + '/' + contract_name + 'Contract.py', 'a+') as contract_file:
            contract_file.write(f'class {contract_name}Contract(Contract):\n\n')

        events = {}

        # print('contract: ' + contract_name)
        for j in range(0, len(contract.contractPart())):
            part: SolidityParser.ContractPartContext = contract.contractPart()[j]

            if part.structDefinition() is not None:  # it is a struct definition.
                struct: SolidityParser.StructDefinitionContext = part.structDefinition()
                struct_name: str = struct.identifier().Identifier().getText()
                for k in range(0, len(struct.variableDeclaration())):
                    variable: SolidityParser.VariableDeclarationContext = struct.variableDeclaration()[k]
                    variable_name: str = variable.identifier().Identifier().getText()
                    type: SolidityParser.TypeNameContext = variable.typeName()
                    type_text = parse_type(type)

            if part.eventDefinition() is not None:  # Guess what? It's an event!
                event: SolidityParser.EventDefinitionContext = part.eventDefinition()
                event_name: str = event.identifier().Identifier().getText()
                params = []
                for k in range(0, len(event.eventParameterList().eventParameter())):
                    event_param: SolidityParser.EventParameterContext = event.eventParameterList().eventParameter()[k]
                    param_name: str = event_param.identifier().Identifier().getText()
                    param_type = parse_type(event_param.typeName())
                    params.append((param_name, param_type))
                events[event_name] = params

            if part.enumDefinition() is not None:  # it is an enum definition.
                enum: SolidityParser.EnumDefinitionContext = part.enumDefinition()
                enum_name = enum.identifier().Identifier().getText()
                with open(args.dst + '/Enums.py', 'a+') as enums:
                    enums.write(f'\nclass {enum_name}(Enum):\n')
                for k in range(0, len(enum.enumValue())):
                    enum_value: SolidityParser.EnumValueContext = enum.enumValue()[k]
                    value: str = enum_value.identifier().Identifier().getText()
                    value = value if not keyword.iskeyword(value) else '_' + value
                    with open(args.dst + '/Enums.py', 'a+') as enums:
                        enums.write(f'\t{value} = {k}\n')

                with open(args.dst + '/Enums.py', 'a+') as enums:
                    enums.write('\n')

            if part.functionDefinition() is not None:  # of course it's a function!
                func: SolidityParser.FunctionDefinitionContext = part.functionDefinition()
                if func.identifier() is None:  # It is the `fallback` method.
                    continue
                func_name: str = func.identifier().Identifier().getText()
                param_list: SolidityParser.ParameterListContext = func.parameterList()

                is_payable: bool = False
                modifiers: SolidityParser.ModifierListContext = func.modifierList()
                for k in range(0, len(modifiers.stateMutability())):
                    state_mutability: SolidityParser.StateMutabilityContext = modifiers.stateMutability()[k]
                    if state_mutability.getText() == 'payable':
                        is_payable = True

                params = []
                has_oid: bool = False
                has_joid: bool = False
                has_ijoid: bool = False
                for k in range(0, len(param_list.parameter())):
                    param: SolidityParser.ParameterContext = param_list.parameter()[k]
                    param_name: str = param.identifier().Identifier().getText()
                    param_type = parse_type(param.typeName())
                    params.append((param_name, param_type))

                 
                    if param_name == "offerId":
                        has_oid = True
                    if param_name == "jobOfferId":
                        has_joid = True
                    if param_name == "ijoid":
                        has_ijoid = True


                with open(args.dst + '/' + contract_name + 'Contract.py', 'a+') as contract_file:
                    contract_file.write(f'\tdef {func_name}(self, from_account, getReceipt%s%s' % (', ' if len(params) != 0 else '',
                                                                'price, ' if is_payable else '') + ', '.join([p[0] for p in params]) + 
                                                                '):\n'+
                                        f'\t\tevent = "{func_name}"\n'+
                                        f'\t\tself.helper.logTxn(self.aix, event%s%s%s)\n' %(', joid=offerId' if has_oid else '', ', joid=jobOfferId' if has_joid else '', ', ijoid=ijoid' if has_ijoid else '') +
                                        f'\t\treturn self.call_func(from_account, getReceipt, %s, event%s\n' % ('price' if is_payable else '0', ', ' if len(params) != 0 else '') +
                                        f'\t\t\t' + ',\n\t\t\t'.join([f'"{p[1]}", {p[0]}' for p in params]) + '\n' +
                                        f'\t\t)\n\n')  # I couldn't make it anymore ugly!

                # # TRYING TO GET PARAMS FOR BETTER LOGGING
                # with open(args.dst + '/' + contract_name + 'Contract.py', 'a+') as contract_file:
                #     contract_file.write(f'\tdef {func_name}(self, from_account, getReceipt%s%s' % (', ' if len(params) != 0 else '',
                #                                                 'price, ' if is_payable else '') + ', '.join([p[0] for p in params]) + 
                #                                                 ', oid=-1, ijoid=-1'
                #                                                 '):\n'+
                #                         f'\t\treturn self.call_func(from_account, getReceipt, %s, "{func_name}"%s self.aix, oid, ijoid,\n' % ('price' if is_payable else '0', ', ' if len(params) != 0 else '') +
                #                         f'\t\t\t' + ',\n\t\t\t'.join([f'"{p[1]}", {p[0]}' for p in params]) + '\n' +
                #                         f'\t\t)\n\n')  # I couldn't make it anymore ugly!

        # INIT PART ###
        # with open(args.dst + '/' + contract_name + 'Contract.py', 'a+') as contract_file:
        #     contract_file.write(f'\tdef __init__(self, client, address):\n' +
        #                         f'\t\tsuper().__init__(client, address, {events})\n')

        # TRYING TO GET PARAMS FOR BETTER LOGGING
        with open(args.dst + '/' + contract_name + 'Contract.py', 'a+') as contract_file:
            contract_file.write(f'\tdef __init__(self, aix, client, address):\n' +
                                f'\t\tself.aix = aix \n' +
                                f'\t\tself.helper=helper.helper()\n' +
                                f'\t\tsuper().__init__(client, address, {events})\n')


def parse_type(type: SolidityParser.TypeNameContext) -> str:  # if it's an array, it will end with '[]'

    if type.typeName() is not None:  # it is definition of an array '[]'.
        type_name: SolidityParser.TypeNameContext = type.typeName()
        if type_name.elementaryTypeName() is not None:  # type is elementary
            elementary_name: SolidityParser.ElementaryTypeNameContext = type_name.elementaryTypeName()
            type_text: str = elementary_name.getText()
        elif type_name.userDefinedTypeName() is not None:  # maybe user_defined?
            user_defined_name: SolidityParser.UserDefinedTypeNameContext = type_name.userDefinedTypeName()
            type_text: str = user_defined_name.getText()
        else:
            raise NotImplementedError
        type_text = type_text + '[]'

    else:
        if type.elementaryTypeName() is not None:  # type is elementary
            elementary_name: SolidityParser.ElementaryTypeNameContext = type.elementaryTypeName()
            type_text: str = elementary_name.getText()
        elif type.userDefinedTypeName() is not None:  # maybe user_defined?
            user_defined_name: SolidityParser.UserDefinedTypeNameContext = type.userDefinedTypeName()
            type_text: str = user_defined_name.getText()
        else:
            raise NotImplementedError

    return type_text


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Process a Solidity source file and generate a Python class for Contract.py.')
    parser.add_argument('src', metavar='src', type=str,
                        help='Path to Solidity source file')
    parser.add_argument('dst', metavar='dst', type=str,
                        help='Path to output directory')

    main(parser.parse_args())
