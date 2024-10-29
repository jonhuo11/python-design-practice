class FileSystemObject:
    def __init__(self, name: str):
        self.name = name

class File(FileSystemObject):
    def __init__(self, name: str, content: str):
        super().__init__(name)
        self.content = content

    def add_content(self, new_content: str) -> None:
        self.content += new_content

class Directory(FileSystemObject):
    def __init__(self, name):
        super().__init__(name)
        self.subdirs: Dict[str, Directory] = {}
        self.files: Dict[str, File] = {}

    def add_subdir(self, name: str):
        self.subdirs[name] = Directory(name)

    def add_file(self, name: str, content: str):
        self.files[name] = File(name, content)


class FileSystem:

    def __init__(self):
        self.root: Directory = Directory("root")

    def goto_dir(self, path: str) -> Directory | File:
        # parses path, traverses it, and returns the Directory or file
        if path == "/":
            return self.root

        dirs = path.split("/")[1:]
        current_dir = self.root
        for dir_ in dirs:
            if dir_ not in current_dir.subdirs:
                return current_dir.files[dir_]
            current_dir = current_dir.subdirs[dir_]
        return current_dir

    def ls(self, path: str) -> List[str]:
        dest: Directory | File = self.goto_dir(path)
        if isinstance(dest, Directory):
            output = []
            for file_name in dest.files.keys():
                output.append(file_name)
            for subdir_name in dest.subdirs.keys():
                output.append(subdir_name)
            output.sort()
            return output
        else:  # file
            return [dest.name]

    def mkdir(self, path: str) -> None:
        parsed_path = path.split("/")[1:]
        current_dir = self.root
        for dir_ in parsed_path:
            if dir_ not in current_dir.subdirs:
                current_dir.subdirs[dir_] = Directory(dir_)
            current_dir = current_dir.subdirs[dir_]

    def addContentToFile(self, filePath: str, content: str) -> None:
        # remove the filename from the path, go to its parent directory, and check if file exists
        split_path = filePath.split("/")
        file_name = split_path[-1]
        parent_path = "/".join(split_path[:-1])
        parent_dir = self.goto_dir(parent_path)
        if isinstance(parent_dir, Directory):
            if file_name not in parent_dir.files:
                parent_dir.add_file(file_name, content)
            else:
                parent_dir.files[file_name].add_content(content)

    def readContentFromFile(self, filePath: str) -> str:
        file = self.goto_dir(filePath)
        if isinstance(file, File):
            return file.content
        return "" # should never happen


# Your FileSystem object will be instantiated and called as such:
# obj = FileSystem()
# param_1 = obj.ls(path)
# obj.mkdir(path)
# obj.addContentToFile(filePath,content)
# param_4 = obj.readContentFromFile(filePath)