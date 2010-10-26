import os

def getfiles(path, extensions = None):
    """
    Builds a generator that recursively searches a directory for files that
    end with the extensions.
    """
    stack = [path]
    while stack:
        dir = stack[-1]
        for file in os.listdir(dir):
            filepath = dir + '/' + file
            if os.path.isdir(filepath):
                stack.append(filepath)
            elif not extensions or filepath.endswith(extensions):
                yield filepath
        stack.remove(dir)
