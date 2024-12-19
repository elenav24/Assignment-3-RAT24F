import lexer as lexical
from parser import Parser
import re

#main function
def main():
    tokens = [] # List of tokens
    input_filename = input("Enter the input file name: ")
    output_filename = input_filename.rsplit('.', 1)[0] + '_output.txt'

    try:
        # Open files with the correct encoding
        with open(input_filename, 'r') as file, open(output_filename, 'w', encoding='utf-8') as output_file:

            comment_buffer = ""
            inside_comment = False
            # Tokenize input file line by line
            for line in file:
                if inside_comment:
                    comment_buffer += line  # Continue adding to the comment buffer
                    if "*]" in line:  # End of multi-line comment
                        line = comment_buffer
                        inside_comment = False
                        comment_buffer = ""  # Reset the comment buffer after processing
                    continue  # Skip adding this line to the token list
                
                # Check if line starts a comment
                if "[*" in line:
                    inside_comment = True
                    comment_buffer = line  # Start accumulating the comment
                    if "*]" in line:  # If the comment is on one line
                        inside_comment = False
                        comment_buffer = ""  # Reset the comment buffer after processing
                    if line[0:2] == "[*":
                        continue

                # Remove comments and other unnecessary parts here
                line = re.sub(r'\[\*\s*.*?\*\]', '', line, flags=re.DOTALL)
                line_tokens = lexical.lexer(line)
                if line_tokens:
                    tokens.extend(line_tokens)

            # Reset the index and start parsing
            parser = Parser(tokens, output_file)
            parser.parse()

    except Exception as e: # Catch any exceptions
        print(f"Error: {e}")

if __name__ == "__main__": # Run the main function
    main()
