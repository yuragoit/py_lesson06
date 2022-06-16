from pathlib import Path
import sys
import re
import shutil

from pkg_resources import split_sections


def handle_image(path: Path, root_folder: Path):
    target_folder = root_folder / "images"
    target_folder.mkdir(exist_ok=True)
    path.replace(target_folder / path.name)


def handle_video(path: Path, root_folder: Path):
    target_folder = root_folder / "video"
    target_folder.mkdir(exist_ok=True)
    path.replace(target_folder / path.name)


def handle_audio(path: Path, root_folder: Path):
    target_folder = root_folder / "audio"
    target_folder.mkdir(exist_ok=True)
    path.replace(target_folder / path.name)


def handle_document(path: Path, root_folder: Path):
    target_folder = root_folder / "documents"
    target_folder.mkdir(exist_ok=True)
    path.replace(target_folder / path.name)


def handle_archive(path: Path, root_folder: Path):
    target_folder = root_folder / "archives"
    name, _ = split_extension(path.name)
    target_folder.mkdir(exist_ok=True)
    archive_folder = target_folder / name
    archive_folder.mkdir(exist_ok=True)
    try:
        shutil.unpack_archive(str(path.absolute()),
                              str(archive_folder.absolute()))
    except shutil.ReadError:
        archive_folder.rmdir()
        return
    path.unlink()


def handle_folder(path: Path):
    try:
        path.rmdir()
    except OSError:
        pass


IMAGES = []
AUDIO = []
VIDEO = []
DOCUMENTS = []
ARCHIVES = []
FOLDERS = []
UNKNOWN_EXTENSIONS = set()
LINKED_KNOWN_EXTENSIONS = set()
KNOWN_EXTENSIONS = {
    'JPEG': IMAGES, 'PNG': IMAGES, 'JPG': IMAGES, 'SVG': IMAGES,
    'AVI': VIDEO, 'MP4': VIDEO, 'MOV': VIDEO, 'MKV': VIDEO,
    'DOC': DOCUMENTS, 'DOCX': DOCUMENTS, 'TXT': DOCUMENTS,
    'XLSX': DOCUMENTS, 'PPTX': DOCUMENTS, 'PDF': DOCUMENTS,
    'MP3': AUDIO, 'OGG': AUDIO, 'WAW': AUDIO, 'AMR': AUDIO,
    'ZIP': ARCHIVES, 'TAR': ARCHIVES, 'GZ': ARCHIVES
}

CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")

TRANS_DIC = {}
for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS_DIC[ord(c)] = l
    TRANS_DIC[ord(c.upper())] = l.upper()


def normalize(name: str) -> str:
    t_name = name.translate(TRANS_DIC)
    t_name = re.sub(r'\W', "_", t_name)
    return t_name


def split_extension(file_name: str):
    ext_start = 0
    for idx, char in enumerate(file_name):
        if char == ".":
            ext_start = idx
    name = file_name[:ext_start]
    extension = file_name[ext_start + 1:].upper()
    if not ext_start:
        return file_name, ""
    return name, extension


def scan(folder: Path):
    for item in folder.iterdir():
        if item.is_dir():
            new_dir_name = normalize(item.name)
            new_dir_item = item.parent / new_dir_name
            item = item.rename(new_dir_item)
            if item.name not in ("images", "video", "audio", "documents", "archives"):
                FOLDERS.append(item)
                scan(item)
            continue
        name, extension = split_extension(file_name=item.name)
        new_name = normalize(name)
        new_item = folder / ".".join([new_name, extension.lower()])
        item.rename(new_item)
        if extension:
            try:
                container = KNOWN_EXTENSIONS[extension]
                container.append(new_item)
                LINKED_KNOWN_EXTENSIONS.add(extension)

            except KeyError:
                UNKNOWN_EXTENSIONS.add(extension)
                continue


def main() -> None:
    path = sys.argv[1]
    print(f'Start scanning in {path} ...')
    folder = Path(path)
    scan(folder)
    for file in IMAGES:
        handle_image(file, folder)
    for file in VIDEO:
        handle_video(file, folder)
    for file in AUDIO:
        handle_audio(file, folder)
    for file in DOCUMENTS:
        handle_document(file, folder)
    for file in ARCHIVES:
        handle_archive(file, folder)
    for fold in FOLDERS[::-1]:
        handle_folder(fold)
    lst_image = [elem.name for elem in IMAGES]
    lst_video = [elem.name for elem in VIDEO]
    lst_audio = [elem.name for elem in AUDIO]
    lst_doc = [elem.name for elem in DOCUMENTS]
    lst_arch = [elem.name for elem in ARCHIVES]
    print("Image-files list: ", lst_image)
    print("Video-files list: ", lst_video)
    print("Audio-files list: ", lst_audio)
    print("Document-files list: ", lst_doc)
    print("Archive-files list: ", lst_arch)
    print("Unknown extensions list: ", UNKNOWN_EXTENSIONS)
    print("Matched extensions list: ", LINKED_KNOWN_EXTENSIONS)


if __name__ == "__main__":
    main()
