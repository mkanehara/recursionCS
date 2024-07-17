import markdown
import sys

class InvalidInputExeption(Exception):
    def __init__(self, arg=""):
        self.arg = arg

    def __str__(self):
        return (
            f"{self.arg}は指定されたコマンドではありません"
        )
    
def markdownToHtml(inputfile, outputfile):
    contents = ""
    html = ""
    with open(inputfile) as f:
        contents = f.read()
        html = markdown.markdown(contents)
    
    with open(outputfile, 'w') as f:
        f.write(html)


def main():
    command = None

    try:
        command = sys.argv[1]
    except IndexError as e:
        print("正しい引数を入力してください")

    try:
        if command != "markdown":
            raise InvalidInputExeption(command)
    except InvalidInputExeption as e:
        print(f"{e.arg}は指定されたコマンドではありません")

    markdownToHtml(sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    main()
    