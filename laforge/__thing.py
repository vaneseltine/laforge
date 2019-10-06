import sys


class FilteredPrint(object):
    def __init__(self, stream, default_sep=" ", default_end="\n"):
        self.stdout = stream
        self.default_sep = default_sep
        self.default_end = default_end
        self.continuing_same_print = False
        self.file = open("log.txt", "a")

    def __getattr__(self, name):
        return getattr(self.stdout, name)

    def write(self, text):
        if text is self.default_end:
            self.continuing_same_print = False
        elif text is self.default_sep:
            self.continuing_same_print = True

        new_text = text
        if text in {self.default_sep, self.default_end}:
            pass
        elif self.continuing_same_print:
            pass
        else:
            new_text = f"| {new_text}"

        self.stdout.write(new_text)
        self.flush()


_stdout = sys.stdout
sys.stdout = FilteredPrint(sys.stdout)
print("Test", "  ", "log", sep="  ")
print("Another test log")
sys.stdout = _stdout
print("and we're out")
