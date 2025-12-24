import os
import zipfile
import io
import re

def format_number(number: str):
    if "." in number:
        inteiro, decimal = number.split(".")
        formatted = f"{int(inteiro):02}.{decimal}"
    elif "," in number:
        inteiro, decimal = number.split(".")
        formatted = f"{int(inteiro):02}.{decimal}"
    else:
        formatted = f"{int(number):02}"
    
    return formatted

def file_exists_with_regex(directory, pattern):
    """
    Checks if any file in the given directory matches the provided regex pattern.

    Args:
        directory (str): The path to the directory to search.
        pattern (str): The regular expression pattern to match filenames against.

    Returns:
        bool: True if at least one file matches the pattern, False otherwise.
    """
    try:
        # Compile the regex pattern for efficiency
        regex = re.compile(pattern)
        if pattern == r'.*Ch\.02.5\.cbz':
            pass
        
        # List all files and directories in the given directory
        for filename in os.listdir(directory):
            # Check if the filename matches the regex pattern
            if regex.match(filename):
                return True
        return False
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def save_cbz(images, chapter_number, output_folder, manga_name, volume_number=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    cbz_filename = f"{manga_name} {f'Vol.{volume_number} ' if volume_number != None else ''}Ch.{chapter_number}.cbz"
    cbz_path = os.path.join(output_folder, cbz_filename)
    with zipfile.ZipFile(cbz_path, 'w') as cbz:
        for idx, img in enumerate(images):
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            cbz.writestr(f"{idx+1:03d}.jpg", img_bytes.read())
    return cbz_filename
