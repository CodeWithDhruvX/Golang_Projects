import zipfile
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
from tqdm import tqdm  # For progress bar
import io

# Define text-based file extensions to process
TEXT_EXTENSIONS = {
    '.go': 'go',
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.c': 'c',
    '.html': 'html',
    '.css': 'css',
    '.md': 'markdown',
    '.json': 'json',
    '.xml': 'xml',
    '.sql': 'sql',
    '.sh': 'bash',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.txt': 'text'
}

def is_text_file(filename):
    """Check if the file has a text-based extension."""
    return any(filename.lower().endswith(ext) for ext in TEXT_EXTENSIONS)

def get_language_from_extension(filename):
    """Get the language for syntax highlighting based on file extension."""
    ext = Path(filename).suffix.lower()
    return TEXT_EXTENSIONS.get(ext, 'text')

def process_zip_to_markdown(zip_path, output_md_path):
    """Process a ZIP file and combine text-based files into a single Markdown file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of all files in the ZIP, filter text files upfront
            file_list = [f for f in sorted(zip_ref.namelist()) if not f.endswith('/') and is_text_file(f)]
            
            # Use a buffered writer to reduce I/O overhead
            with open(output_md_path, 'w', encoding='utf-8', buffering=8192) as md_file:
                # Progress bar for large file counts
                for file_path in tqdm(file_list, desc="Processing files", unit="file"):
                    try:
                        with zip_ref.open(file_path, 'r') as file:
                            # Read file in chunks to handle large files
                            content = io.StringIO()
                            try:
                                while chunk := file.read(8192):  # Read 8KB chunks
                                    content.write(chunk.decode('utf-8', errors='ignore'))
                            except UnicodeDecodeError:
                                # Skip files that can't be decoded as text
                                md_file.write(f"## {file_path}\n")
                                md_file.write("**Error**: File could not be decoded as text\n\n")
                                continue
                            
                            # Write file path as heading
                            md_file.write(f"## {file_path}\n")
                            
                            # Write content in fenced code block with language
                            language = get_language_from_extension(file_path)
                            md_file.write(f"```{language}\n")
                            content_str = content.getvalue()
                            md_file.write(content_str)
                            # Ensure code block is properly closed
                            if not content_str.endswith('\n'):
                                md_file.write('\n')
                            md_file.write("```\n\n")
                            
                            # Clean up to free memory
                            content.close()
                            
                    except Exception as e:
                        # Log error and continue with next file
                        md_file.write(f"## {file_path}\n")
                        md_file.write(f"**Error**: Could not process file: {str(e)}\n\n")
                        
        return True, f"Markdown file generated successfully: {output_md_path}"
    except Exception as e:
        return False, f"Error processing ZIP file: {str(e)}"

class ZipToMarkdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ZIP to Markdown Converter")
        self.zip_path = None
        
        # Default output folder
        self.default_output_folder = os.path.join(os.getcwd(), "requirement")
        self.output_folder = self.default_output_folder
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # ZIP file selection
        tk.Label(self.root, text="Select ZIP File:").pack(pady=5)
        self.zip_label = tk.Label(self.root, text="No file selected")
        self.zip_label.pack()
        tk.Button(self.root, text="Browse ZIP", command=self.browse_zip).pack(pady=5)
        
        # Output folder selection
        tk.Label(self.root, text="Output Folder:").pack(pady=5)
        self.folder_label = tk.Label(self.root, text=f"Default: {self.default_output_folder}")
        self.folder_label.pack()
        tk.Button(self.root, text="Choose Folder", command=self.choose_folder).pack(pady=5)
        
        # Generate button
        tk.Button(self.root, text="Generate Markdown", command=self.generate_markdown).pack(pady=10)
        
    def browse_zip(self):
        self.zip_path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if self.zip_path:
            self.zip_label.config(text=f"Selected: {os.path.basename(self.zip_path)}")
        
    def choose_folder(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.output_folder = selected_folder
            self.folder_label.config(text=f"Selected: {self.output_folder}")
        else:
            self.output_folder = self.default_output_folder
            self.folder_label.config(text=f"Default: {self.default_output_folder}")
        
    def generate_markdown(self):
        if not self.zip_path:
            messagebox.showerror("Error", "Please select a ZIP file.")
            return
        
        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)
        output_md_path = os.path.join(self.output_folder, "all_files.md")
        
        # Disable generate button during processing
        self.root.config(cursor="wait")
        self.root.update()
        
        # Process the ZIP file
        success, message = process_zip_to_markdown(self.zip_path, output_md_path)
        
        # Re-enable cursor
        self.root.config(cursor="")
        
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

def main():
    # Check if running in CLI mode
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
        output_folder = "requirement"
        
        # Check for optional output folder argument
        if len(sys.argv) > 2:
            output_folder = sys.argv[2]
            
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        output_md_path = os.path.join(output_folder, "all_files.md")
        
        # Validate ZIP file
        if not os.path.exists(zip_path):
            print(f"Error: ZIP file '{zip_path}' does not exist.")
            return
            
        # Process ZIP file with progress feedback
        success, message = process_zip_to_markdown(zip_path, output_md_path)
        print(message)
    else:
        # Run GUI mode
        root = tk.Tk()
        app = ZipToMarkdownApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()