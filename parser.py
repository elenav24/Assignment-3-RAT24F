"""Assignment 2 - Compilers CPSC 323
Team Members: Elena Marquez
Date: 11/5/2024
Description: This assignment involves creating a syntax analyzer using a top-down parser, 
and it's structured into several steps to ensure that you can parse an input program 
according to a specified grammar (Rat24F) while handling errors and generating detailed outputs
"""

class Parser: 
    def __init__(self, tokens, output_file): 
        self.tokens = tokens  
        self.current_index = 0
        self.current_token = self.tokens[self.current_index]
        self.output_file = output_file
        self.symbol_table = SymbolTable(output_file) # Create a symbol table
        self.assembly_code = AssemblyCode(output_file) # Create an assembly code object

    def write_output(self, message): 
        self.output_file.write(message + '\n')

    def advance(self):  
        self.current_index += 1
        if self.current_index < len(self.tokens):
            self.current_token = self.tokens[self.current_index]

    def match(self, expected_type):  
        if self.current_token.token_type == expected_type:
            # self.write_output(f"Token: {str(self.current_token.token_type):<15} Lexeme: {str(self.current_token.lexeme):<20}")
            self.advance()
        else:  
            raise SyntaxError(f"Unexpected token {self.current_token.token_type}, expected {expected_type}, lexeme: {self.current_token.lexeme}")

    def parse(self): 
        self.rat24f()
        self.assembly_code.resolve_jumpz()  # Resolve any JUMPZ placeholders
        self.assembly_code.print_code()
        self.symbol_table.print_table()

    def rat24f(self): 
        self.match("separator")  
        self.opt_declaration_list()
        self.statement_list()
        self.match("separator")  

    def opt_declaration_list(self): 
        while self.current_token.token_type == "keyword" and self.current_token.lexeme in ["integer", "boolean"]:
            self.declaration()

    def declaration(self):
        var_type = self.current_token.lexeme
        self.match("keyword")
        while True:
            identifier = self.current_token.lexeme
            self.symbol_table.insert(identifier, var_type)
            self.match("identifier")
            if self.current_token.lexeme == ";":
                self.match("separator")
                break
            elif self.current_token.lexeme == ",":
                self.match("separator")

    def statement_list(self):  
        self.statement()
        while self.current_token.token_type in ["identifier", "keyword"]:
            self.statement()

    def statement(self):  
        if self.current_token.token_type == "identifier":
            self.assign()
        elif self.current_token.lexeme == "if":
            self.if_statement()
        elif self.current_token.lexeme == "return":
            self.return_statement()
        elif self.current_token.lexeme == "put":
            self.print_statement()
        elif self.current_token.lexeme == "get":
            self.scan_statement()
        elif self.current_token.lexeme == "while":
            self.while_statement()
        elif self.current_token.token_type == "separator" and self.current_token.lexeme == "{":
            self.compound_statement()
        else:
            raise SyntaxError(f"Unexpected statement: {self.current_token.lexeme}")

    def if_statement(self):  
        self.match("keyword")  
        self.match("separator")  
        self.condition()  
        self.match("separator")  

        # Placeholder for JUMPZ to skip the `if` body if false
        jump_else = self.assembly_code.add_placeholder_instruction("JUMPZ")
        self.statement()  # If block body
        self.assembly_code.add_instruction("LABEL")

        # Handle optional `else` branch
        if self.current_token.lexeme == "else":
            jump_end = self.assembly_code.add_placeholder_instruction("JUMPZ")
            self.assembly_code.update_placeholder(jump_else, self.assembly_code.instruction_counter)
            self.match("keyword")  
            self.statement()  # Else block body
            self.assembly_code.update_placeholder(jump_end, self.assembly_code.instruction_counter)
        else:
            self.assembly_code.update_placeholder(jump_else, self.assembly_code.instruction_counter)

        self.match("keyword")  

    def return_statement(self):  
        self.match("keyword")  
        if self.current_token.lexeme != ";":
            self.expression()  
        self.match("separator")  

    def print_statement(self):  
        self.match("keyword")  
        self.match("separator")  
        self.expression()  
        self.assembly_code.add_instruction("STDOUT")
        self.match("separator")  
        self.match("separator")  

    def scan_statement(self):  
        self.match("keyword")  
        self.match("separator")  
        while True:
            identifier = self.current_token.lexeme
            entry = self.symbol_table.lookup(identifier)
            self.assembly_code.add_instruction("STDIN")
            self.assembly_code.add_instruction(f"POPM {entry['address']}")
            self.match("identifier")
            if self.current_token.lexeme == ")":
                self.match("separator")
                break
            elif self.current_token.lexeme == ",":
                self.match("separator")
        self.match("separator")  

    def while_statement(self):  
        loop_start = self.assembly_code.instruction_counter  # Start of the loop
        self.match("keyword")  
        self.match("separator")  
        self.condition()  
        self.match("separator")  
        self.assembly_code.add_instruction("LABEL")  # Label to mark the beginning of the loop

        # Placeholder for JUMPZ to exit the loop if condition is false
        jump_end = self.assembly_code.add_placeholder_instruction("JUMPZ")
        self.statement()  # Loop body

        # Jump back to start of the loop if condition is true
        self.assembly_code.add_instruction(f"JUMP {loop_start}")
        self.assembly_code.update_placeholder(jump_end, self.assembly_code.instruction_counter)


    def compound_statement(self):  
        self.match("separator")  
        self.statement_list()  
        self.match("separator")  

    def condition(self):  
        self.expression()  
        relop = self.current_token.lexeme
        self.relop()       
        self.expression()  
        if relop == "==":
            self.assembly_code.add_instruction("EQU")
        elif relop == "!=":
            self.assembly_code.add_instruction("NEQ")
        elif relop == "<":
            self.assembly_code.add_instruction("LES")
        elif relop == "<=":
            self.assembly_code.add_instruction("LEQ")
        elif relop == ">":
            self.assembly_code.add_instruction("GRT")
        elif relop == ">=":
            self.assembly_code.add_instruction("GEQ")

    def assign(self):  
        identifier = self.current_token.lexeme
        entry = self.symbol_table.lookup(identifier)
        self.match("identifier")
        self.match("operator")  
        self.expression()
        self.assembly_code.add_instruction(f"POPM {entry['address']}")
        self.match("separator")  

    def expression(self):
        self.term()
        self.expression_prime()

    def expression_prime(self):  
        if self.current_token.lexeme in ("+", "-"):
            operator = self.current_token.lexeme
            self.match("operator")  
            self.term()
            if operator == "+":
                self.assembly_code.add_instruction("ADD")
            elif operator == "-":
                self.assembly_code.add_instruction("SUB")
            self.expression_prime()

    def term(self):  
        self.factor()
        self.term_prime()

    def term_prime(self):  
        if self.current_token.lexeme in ("*", "/"):
            operator = self.current_token.lexeme
            self.match("operator")  
            self.factor()
            if operator == "*":
                self.assembly_code.add_instruction("MUL")
            elif operator == "/":
                self.assembly_code.add_instruction("DIV")
            self.term_prime()

    def factor(self):
        if self.current_token.token_type == "keyword":
            value = 1 if self.current_token.lexeme == "true" else 0
            self.match("keyword")
            self.assembly_code.add_instruction(f"PUSHI {value}")
        elif self.current_token.token_type == "integer":
            value = self.current_token.lexeme
            self.match("integer")
            self.assembly_code.add_instruction(f"PUSHI {value}")
        elif self.current_token.token_type == "identifier":
            entry = self.symbol_table.lookup(self.current_token.lexeme)
            self.match("identifier")
            self.assembly_code.add_instruction(f"PUSHM {entry['address']}")
        elif self.current_token.lexeme == "(":
            self.match("separator")
            self.expression()
            self.match("separator")
        else:
            raise ValueError(f"Syntax Error: Unexpected token {self.current_token.lexeme}")

    def relop(self):  
        if self.current_token.lexeme in ["==", "!=", ">", "<", "<=", ">="]:
            self.match("operator") 
        else:
            raise SyntaxError(f"Unexpected token {self.current_token.lexeme}, expected a relational operator")

class SymbolTable:
    def __init__(self, output_file):
        self.output_file = output_file
        self.table = {}
        self.memory_address = 9000

    def insert(self, identifier, var_type):
        if identifier in self.table:
            raise ValueError(f"Identifier '{identifier}' already declared.")
        self.table[identifier] = {"address": self.memory_address, "type": var_type}
        self.memory_address += 1

    def lookup(self, identifier):
        if identifier not in self.table:
            raise ValueError(f"Identifier '{identifier}' used without declaration.")
        return self.table[identifier]

    def print_table(self):
        self.output_file.write("Symbol Table:" + '\n')
        for identifier, info in self.table.items():
            self.output_file.write(f"{identifier}: Address = {info['address']}, Type = {info['type']}")

class AssemblyCode:
    def __init__(self, output_file):
        self.output_file = output_file
        self.instructions = []
        self.instruction_counter = 1
        self.placeholders = {}
        self.labels = {}

    def add_instruction(self, instruction):
        self.instructions.append(f"{self.instruction_counter} {instruction}")
        self.instruction_counter += 1

    def add_placeholder_instruction(self, instruction):
        placeholder = self.instruction_counter
        self.instructions.append(f"{placeholder} {instruction} ???")  # ??? as placeholder
        self.instruction_counter += 1
        return placeholder

    def add_label(self, label):
        if label in self.labels:
            raise ValueError(f"Label '{label}' already defined.")
        self.labels[label] = self.instruction_counter

    def update_placeholder(self, placeholder, target):
        if placeholder < 1 or placeholder > len(self.instructions):
            raise ValueError(f"Invalid placeholder reference: {placeholder}")
        self.instructions[placeholder - 1] = self.instructions[placeholder - 1].replace("???", str(target))

    def resolve_jumpz(self):
    # Update all jump placeholders
        for placeholder, label in self.placeholders.items():
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label}")
            self.update_placeholder(placeholder, self.labels[label])


    def print_code(self):
        self.output_file.write("Assembly Code:" + '\n')
        for line in self.instructions:
            self.output_file.write(line + '\n')
