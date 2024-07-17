import sys

class InvalidInputExeption(Exception):
    def __init__(self, arg=""):
        self.arg = arg

    def __str__(self):
        return (
            f"{self.arg}は指定されたコマンドではありません"
        )
    
def reverse(inputfile, outputfile):
    inputfile = open(inputfile)
    contents = inputfile.read()
    inputfile.close()

    outputContents = ""
    contents_length = len(contents)
    for i in range(contents_length-1, 0, -1):
        outputContents += contents[i]

    outputfile = open(outputfile, 'w')
    outputfile.write(outputContents + contents[0])
    outputfile.close()

def copy(inputfile, outputfile):
    inputfile=open(inputfile)
    contents = inputfile.read()
    inputfile.close()

    outputfile = open(outputfile, 'w')
    outputfile.write(contents)
    outputfile.close()

def duplicate_n(inputfile, outputfile, n):
    inputfile = open(inputfile)
    contents = inputfile.read()
    inputfile.close()

    outputContents = ""
    for i in range(n):
        outputContents += contents

    outputfile = open(outputfile, 'w')
    outputfile.write(outputContents)
    outputfile.close()

def replace(inputfile, needle, newstring):
    with open(inputfile, 'r+') as file:
        contents = file.read()

        # Replace the needle with the new string
        newcontents = contents.replace(needle, newstring)

        # Truncate the file and write the new contents
        file.seek(0)  # Move the cursor to the beginning of the file
        file.truncate(0)  # Clear the file contents
        file.write(newcontents)  # Write the new contents
        file.seek(0)  # Move the cursor back to the beginning


def main():
    command = None

    try:
        command = sys.argv[1]
    except IndexError as e:
        print("正しい引数を入力してください")

    try:
        if command != "reverse" and command != "copy" and command != "duplicate-contents" and command != "replace":
            raise InvalidInputExeption(command)
    except InvalidInputExeption as e:
        print(f"{e.arg}は指定されたコマンドではありません")

    if command == "reverse":
        reverse(sys.argv[2], sys.argv[3])
    if command == "copy":
        copy(sys.argv[2], sys.argv[3])
    if command == "duplicate-contents":
        duplicate_n(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    if command == "replace":
        replace(sys.argv[2], sys.argv[3], sys.argv[4])

if __name__ == "__main__":
    main()
