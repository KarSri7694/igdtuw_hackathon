import os
import logging
from pathlib import Path
from typing import List, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_files_by_extension(
    directory: Union[str, Path],
    extensions: List[str],
    recursive: bool = False
) -> List[str]:
    """
    Retrieve a list of files from a directory based on given file extensions.
    
    Args:
        directory: Path to the directory to search
        extensions: List of file extensions (e.g., ['.py', '.txt', '.jpg'])
                   Extensions can be with or without the leading dot
        recursive: If True, search subdirectories as well (default: True)
    
    Returns:
        List of absolute file paths matching the given extensions
    
    Example:
        files = get_files_by_extension('/path/to/dir', ['.py', '.txt'])
        files = get_files_by_extension('C:\\folder', ['py', 'txt'], recursive=False)
    """
    directory = Path(directory)
    
    logger.debug(f"Searching for files in: {directory}")
    logger.debug(f"Extensions: {extensions}, Recursive: {recursive}")
    
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        raise ValueError(f"Directory does not exist: {directory}")
    
    if not directory.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        raise ValueError(f"Path is not a directory: {directory}")
    
    # Normalize extensions to include the leading dot
    normalized_extensions = []
    for ext in extensions:
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized_extensions.append(ext.lower())
    
    logger.debug(f"Normalized extensions: {normalized_extensions}")
    
    matching_files = []
    
    if recursive:
        # Walk through directory tree
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in normalized_extensions:
                    matching_files.append(str(file_path.absolute()))
    else:
        # Only search top-level directory
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() in normalized_extensions:
                matching_files.append(str(item.absolute()))
    
    logger.info(f"Found {len(matching_files)} matching file(s)")
    return matching_files


def get_files_by_extension_grouped(
    directory: Union[str, Path],
    extensions: List[str],
    recursive: bool = True
) -> dict:
    """
    Retrieve files grouped by extension.
    
    Args:
        directory: Path to the directory to search
        extensions: List of file extensions
        recursive: If True, search subdirectories as well
    
    Returns:
        Dictionary with extensions as keys and lists of file paths as values
    
    Example:
        files = get_files_by_extension_grouped('/path/to/dir', ['.py', '.txt'])
        # Returns: {'.py': ['file1.py', 'file2.py'], '.txt': ['notes.txt']}
    """
    logger.debug(f"Grouping files by extension for directory: {directory}")
    
    all_files = get_files_by_extension(directory, extensions, recursive)
    
    grouped = {ext if ext.startswith('.') else '.' + ext: [] for ext in extensions}
    
    for file_path in all_files:
        ext = Path(file_path).suffix.lower()
        if ext in grouped:
            grouped[ext].append(file_path)
    
    logger.info(f"Grouped {len(all_files)} files into {len([g for g in grouped.values() if g])} extension category(ies)")
    return grouped


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Set logging level to INFO for demo
    logger.setLevel(logging.INFO)
    
    # Get all files with specified extension
    current_dir = "C:\\Users\\Kartikeya Srivastava\\Downloads"
    logger.info(f"Searching in: {current_dir}")
    
    # Get files
    files = get_files_by_extension(current_dir, ['.md', '.txt', '.jpg', '.png', '.pdf'], recursive=False)
    
    # Save output to text file
    output_folder = "temp"
    os.makedirs(output_folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"file_list.txt"
    output_path = os.path.join(output_folder, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for file in files:
            f.write(f"{file}\n")
    
    print(f"\nFound {len(files)} files:")
    for file in files:
        print(f"  - {file}")
    print(f"\nOutput saved to: {output_path}")
