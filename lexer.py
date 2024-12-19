""" Assignment 1 - Compilers CPSC 323
Team Members: Lupita Jimenez, Lucero Matamoros, and Elena Marquez
Date: 09/24/2024
Description: This program is a lexical analyzer for the language RAT24F. 
The lexer will read through the RAT24F source code file,
identify the tokens, and output the tokens to a file USING FSM. 
"""



import re  # Regular expression library

# Token Types
class TokenType:
    #keyword 
    KEYWORD = "keyword"
    #identifier 
    IDENTIFIER = "identifier"
    #operator
    OPERATOR = "operator"
    #integer 
    INTEGER = "integer"
    #separator 
    SEPARATOR = "separator"
    #invaild
    INVALID = "invalid"

# Token class includes the token type and lexeme
class Token: 
    def __init__(self, token_type, lexeme):
        # type of token 
        self.token_type = token_type
        # the string associated with the token 
        self.lexeme = lexeme
        
    def __str__(self):
        # This will define how the token is represented a string 
        return f"{self.token_type:<10} {self.lexeme}"

# Defining keywords
keywords = ["integer", "boolean", "if", "else", "fi", "return", "put", "get", "while", "true", "false"]

# DFSM Transition Table for Identifiers
identifier_transition_table = {
    "q0": {"letter": "q1"}, # Start state; move to q1 if a letter is encountered
    "q1": {"letter": "q1", "digit": "q1"},# Stay in q1 for letters or digits (valid identifier parts)
    "qInvalid": {} # invails states for incorrect inputs 
}

# DFSM Transition Table for Integers and Floats
int_float_transition_table = {
    "q0": {"digit": "q1", ".": "qInvalid"},# Start state; move to q1 for digit, invalid for just a '.'
    "q1": {"digit": "q1", ".": "q2"}, # State for integer part; move to q2 for a dot (start of float)
    "q2": {"digit": "q3"}, # After dot; move to q3 only if followed by digits (valid float)
    "q3": {"digit": "q3"},# Valid float state; stay in q3 if more digits follow
    "qInvalid": {}
} # Invalid state for incorrect inputs

# Utility Functions

"""
    This function checks if a given character is a separator.
    Separators are common punctuation marks or symbols used to separate parts of code.
"""
def is_separator(char):
    return char in ('(', ')', ';', ':', ',', '{', '}', '$', '@')
"""
    This function checks if a given character is part of an operator.
    Operators are symbols that perform operations on variables and values.
"""
def is_operator_char(char):
    return char in ('+', '-', '*', '/', '<', '>', '=', '!')
"""
    This function checks if the provided lexeme (a sequence of characters) is a keyword.
    Keywords are reserved words in programming languages (e.g., 'if', 'else', 'while').
    The 'keywords' variable is assumed to be a predefined list or set of keywords.  
"""
def is_keyword(lexeme):
    return lexeme in keywords
"""
    This function determines the type of character provided.
    It classifies the character as either a letter, digit, dot ('.'), or other.
    This is useful for state transitions in a DFSM.
"""
def get_char_type(char):
    if char.isalpha():
        return "letter" # (a-z and A-Z)
    elif char.isdigit():
        return "digit" #(0-9)
    elif char == ".":
        return "."  # (floats)
    else:
        return "other"

# Generic FSM processor to validate a lexeme based on a finite state machine (FSM)
"""
    This function processes a lexeme (a string of characters) through a finite state machine (FSM).
    
    Parameters:
    - lexeme: The string to process (e.g., identifier, number).
    - transition_table: The FSM's transition table, which dictates state changes.
    - start_state: The state where the FSM starts processing (default is "q0").
    - accepting_states: A tuple of states that are considered valid (default is ("q1", "q3")).
    
    Returns:
    - True if the lexeme ends in an accepting state (i.e., valid lexeme).
    - False if the lexeme encounters an invalid transition or ends in a non-accepting state.
"""
def fsm_process(lexeme, transition_table, start_state="q0", accepting_states=("q1", "q3")):
    current_state = start_state
    for char in lexeme:
        char_type = get_char_type(char)
        if char_type not in transition_table.get(current_state, {}):
            return False  # Invalid character for this state
        current_state = transition_table[current_state][char_type]
    
    return current_state in accepting_states  # Return True if in accepting state

# Lexer function that calls appropriate FSM based on the token
def lexer(line):
    tokens = []
    current_lexeme = ''
    current_state = "q0"

    i = 0
    while i < len(line):
        ch = line[i]

        if current_state == "q0":
            if ch.isspace():
                i += 1
                continue
            elif is_separator(ch):
                tokens.append(Token(TokenType.SEPARATOR, ch))
                i += 1
            elif is_operator_char(ch):
                # Handle operators
                current_lexeme = ch
                if i + 1 < len(line) and line[i + 1] == '=':  # Check for multi-character operator like <= or >=
                    current_lexeme += line[i + 1]
                    i += 2
                else:
                    i += 1
                tokens.append(Token(TokenType.OPERATOR, current_lexeme))
            elif ch.isalpha():  # Start of identifier or keyword
                current_lexeme = ch
                current_state = "identifier"
                i += 1
            elif ch.isdigit():  # Start of integer or float
                current_lexeme = ch
                current_state = "number"
                i += 1
            else:
                tokens.append(Token(TokenType.INVALID, ch))
                i += 1
        elif current_state == "identifier":
            if ch.isalnum():
                current_lexeme += ch
                i += 1
            else:
                # Check if it's a keyword or identifier
                if is_keyword(current_lexeme):
                    tokens.append(Token(TokenType.KEYWORD, current_lexeme))
                else:
                    if fsm_process(current_lexeme, identifier_transition_table):
                        tokens.append(Token(TokenType.IDENTIFIER, current_lexeme))
                    else:
                        tokens.append(Token(TokenType.INVALID, current_lexeme))
                current_lexeme = ''
                current_state = "q0"
        elif current_state == "number":
            if ch.isdigit():
                current_lexeme += ch
                i += 1
            elif ch == '.':
                current_lexeme += ch
                current_state = "float"
                i += 1
            else:
                # Process as an integer
                if fsm_process(current_lexeme, int_float_transition_table):
                    tokens.append(Token(TokenType.INTEGER, current_lexeme))
                else:
                    tokens.append(Token(TokenType.INVALID, current_lexeme))
                current_lexeme = ''
                current_state = "q0"
        elif current_state == "float":
            if ch.isdigit():
                current_lexeme += ch
                i += 1
            else:
                # Process as a float
                tokens.append(Token(TokenType.INVALID, current_lexeme))
                current_lexeme = ''
                current_state = "q0"

    # Handle any remaining lexeme after the loop
    if current_lexeme:
        if current_state == "identifier":
            if is_keyword(current_lexeme):
                tokens.append(Token(TokenType.KEYWORD, current_lexeme))
            else:
                if fsm_process(current_lexeme, identifier_transition_table):
                    tokens.append(Token(TokenType.IDENTIFIER, current_lexeme))
                else:
                    tokens.append(Token(TokenType.INVALID, current_lexeme))
        elif current_state == "number":
            if fsm_process(current_lexeme, int_float_transition_table):
                tokens.append(Token(TokenType.INTEGER, current_lexeme))
            else:
                tokens.append(Token(TokenType.INVALID, current_lexeme))
        elif current_state == "float":
                tokens.append(Token(TokenType.INVALID, current_lexeme))

    return tokens

# Main function to handle file I/O
"""
    Main function that reads an input file, processes it line by line using the lexer,
    and writes the tokenized output to an output file.
    
    The output file is created by appending '_output.txt' to the input file's base name.
"""
# def main():
#     input_filename = input("Enter the input file name: ")
#     output_filename = input_filename.rsplit('.', 1)[0] + '_output.txt'

#     try:
#         with open(input_filename, 'r') as file, open(output_filename, 'w') as output_file:
#             # Writing the header for the output
#             output_file.write(f"{'Token':<12} {'Lexeme'}\n")
#             output_file.write("-" * 25 + "\n")
            
#             for line in file:
#                 tokens = lexer(line)
#                 for token in tokens:
#                     output_file.write(f"{token}\n")
#         print(f"Output file '{output_filename}' created successfully.")
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     main()
