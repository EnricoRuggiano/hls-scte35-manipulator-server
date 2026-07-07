def get_line_and_newline(line:str):
    if line.endswith("\r\n"):
        line = line[:-2]
        newline = "\r\n"
    elif line.endswith("\n"):
        line = line[:-1]
        newline = "\n"
    else:
        newline = ""
    return line, newline