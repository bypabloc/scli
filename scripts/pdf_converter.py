#!/usr/bin/env python3
"""
PDF Converter - Convert PDF files to different formats (TXT, Images)
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from menu_utils import confirm, interactive_menu, text_input
from output_manager import OutputManager

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

DESCRIPTION = "PDF Converter - Convert PDF files to TXT or image formats"


def get_pdf_libraries_status() -> Dict[str, bool]:
    """Check which PDF processing libraries are available"""
    libraries = {
        "PyPDF2": False,
        "pymupdf": False,
        "pdf2image": False,
        "Pillow": False,
        "pdfplumber": False,
    }

    try:
        pass

        libraries["PyPDF2"] = True
    except ImportError:
        pass

    try:
        import fitz  # PyMuPDF

        libraries["pymupdf"] = True
    except ImportError:
        pass

    try:
        pass

        libraries["pdf2image"] = True
    except ImportError:
        pass

    try:
        pass

        libraries["Pillow"] = True
    except ImportError:
        pass

    try:
        pass

        libraries["pdfplumber"] = True
    except ImportError:
        pass

    return libraries


def install_missing_dependencies():
    """Suggest installation of missing dependencies"""
    libraries = get_pdf_libraries_status()
    missing = [lib for lib, available in libraries.items() if not available]

    if not missing:
        print("✅ All PDF processing libraries are available!")
        return True

    print(f"❌ Missing dependencies: {', '.join(missing)}")
    print("\n💡 To install missing dependencies, run:")

    if "PyPDF2" in missing:
        print("   uv add PyPDF2")
    if "pymupdf" in missing:
        print("   uv add PyMuPDF")
    if "pdf2image" in missing:
        print("   uv add pdf2image")
    if "Pillow" in missing:
        print("   uv add Pillow")
    if "pdfplumber" in missing:
        print("   uv add pdfplumber")

    return len(missing) == 0


def pdf_to_text_pypdf2(pdf_path: str) -> str:
    """Convert PDF to text using PyPDF2"""
    try:
        import PyPDF2

        text_content = []
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"--- Page {page_num} ---\n{page_text}\n")
                except Exception as e:
                    text_content.append(f"--- Page {page_num} (Error: {e}) ---\n")

        return "\n".join(text_content)
    except ImportError:
        raise Exception("PyPDF2 not available. Install with: uv add PyPDF2")


def pdf_to_text_pdfplumber(pdf_path: str) -> str:
    """Convert PDF to text using pdfplumber (better text extraction)"""
    try:
        import pdfplumber

        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(f"--- Page {page_num} ---\n{page_text}\n")
                    else:
                        text_content.append(
                            f"--- Page {page_num} (No text found) ---\n"
                        )
                except Exception as e:
                    text_content.append(f"--- Page {page_num} (Error: {e}) ---\n")

        return "\n".join(text_content)
    except ImportError:
        raise Exception("pdfplumber not available. Install with: uv add pdfplumber")


def pdf_to_text_pymupdf(pdf_path: str) -> str:
    """Convert PDF to text using PyMuPDF"""
    try:
        import fitz  # PyMuPDF

        text_content = []
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
                else:
                    text_content.append(
                        f"--- Page {page_num + 1} (No text found) ---\n"
                    )
            except Exception as e:
                text_content.append(f"--- Page {page_num + 1} (Error: {e}) ---\n")

        doc.close()
        return "\n".join(text_content)
    except ImportError:
        raise Exception("PyMuPDF not available. Install with: uv add PyMuPDF")


def convert_pdf_to_text(pdf_path: str, output_path: str) -> bool:
    """Convert PDF to text using the best available library"""
    libraries = get_pdf_libraries_status()

    # Try libraries in order of preference
    extraction_methods = [
        ("pdfplumber", pdf_to_text_pdfplumber, libraries["pdfplumber"]),
        ("pymupdf", pdf_to_text_pymupdf, libraries["pymupdf"]),
        ("PyPDF2", pdf_to_text_pypdf2, libraries["PyPDF2"]),
    ]

    for method_name, method_func, available in extraction_methods:
        if available:
            try:
                print(f"📖 Extracting text using {method_name}...")
                text_content = method_func(pdf_path)

                # Write to file
                with open(output_path, "w", encoding="utf-8") as output_file:
                    output_file.write(text_content)

                print(f"✅ Text extracted successfully using {method_name}")
                return True

            except Exception as e:
                print(f"❌ Failed with {method_name}: {e}")
                continue

    print("❌ No suitable PDF text extraction library available")
    return False


def pdf_to_images_pdf2image(
    pdf_path: str, output_dir: str, format: str = "PNG"
) -> List[str]:
    """Convert PDF to images using pdf2image"""
    try:
        from pdf2image import convert_from_path

        print(f"🖼️  Converting PDF to {format} images...")

        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=200)

        image_paths = []
        base_name = Path(pdf_path).stem

        for i, image in enumerate(images, 1):
            image_filename = f"{base_name}_page_{i:03d}.{format.lower()}"
            image_path = os.path.join(output_dir, image_filename)

            # Save image
            image.save(image_path, format)
            image_paths.append(image_path)
            print(f"📄 Saved page {i}: {image_filename}")

        return image_paths

    except ImportError:
        raise Exception("pdf2image not available. Install with: uv add pdf2image")


def pdf_to_images_pymupdf(
    pdf_path: str, output_dir: str, format: str = "PNG"
) -> List[str]:
    """Convert PDF to images using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        from PIL import Image

        print(f"🖼️  Converting PDF to {format} images using PyMuPDF...")

        doc = fitz.open(pdf_path)
        image_paths = []
        base_name = Path(pdf_path).stem

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page as image (matrix for higher resolution)
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            pix.tobytes("ppm")
            pil_image = Image.open(
                tempfile.NamedTemporaryFile(suffix=".ppm", delete=False)
            )
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Save image
            image_filename = f"{base_name}_page_{page_num + 1:03d}.{format.lower()}"
            image_path = os.path.join(output_dir, image_filename)
            pil_image.save(image_path, format)

            image_paths.append(image_path)
            print(f"📄 Saved page {page_num + 1}: {image_filename}")

        doc.close()
        return image_paths

    except ImportError:
        raise Exception(
            "PyMuPDF or Pillow not available. Install with: uv add PyMuPDF Pillow"
        )


def convert_pdf_to_images(
    pdf_path: str, output_dir: str, format: str = "PNG"
) -> List[str]:
    """Convert PDF to images using the best available library"""
    libraries = get_pdf_libraries_status()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Try libraries in order of preference
    conversion_methods = [
        ("pdf2image", pdf_to_images_pdf2image, libraries["pdf2image"]),
        (
            "pymupdf",
            pdf_to_images_pymupdf,
            libraries["pymupdf"] and libraries["Pillow"],
        ),
    ]

    for method_name, method_func, available in conversion_methods:
        if available:
            try:
                image_paths = method_func(pdf_path, output_dir, format)
                print(f"✅ Images converted successfully using {method_name}")
                return image_paths

            except Exception as e:
                print(f"❌ Failed with {method_name}: {e}")
                continue

    print("❌ No suitable PDF to image conversion library available")
    return []


def browse_for_pdf_file() -> Optional[str]:
    """Browse for PDF file using interactive menu"""
    current_dir = os.getcwd()

    while True:
        # Get directory contents
        items = []

        # Add parent directory option
        if current_dir != os.path.dirname(current_dir):
            items.append(
                {
                    "name": "📁 ..",
                    "value": "..",
                    "description": "Parent directory",
                    "type": "parent",
                }
            )

        try:
            entries = sorted(os.listdir(current_dir))

            # Add directories
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isdir(full_path):
                    items.append(
                        {
                            "name": f"📁 {entry}",
                            "value": entry,
                            "description": "Directory",
                            "type": "dir",
                        }
                    )

            # Add PDF files
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isfile(full_path) and entry.lower().endswith(".pdf"):
                    file_size = get_file_size_str(os.path.getsize(full_path))
                    items.append(
                        {
                            "name": f"📄 {entry}",
                            "value": entry,
                            "description": f"PDF File ({file_size})",
                            "type": "file",
                        }
                    )

            # Add manual entry option
            items.append(
                {
                    "name": "✏️  Enter path manually",
                    "value": "manual",
                    "description": "Type the full file path",
                    "type": "manual",
                }
            )

            # Add cancel option
            items.append(
                {
                    "name": "❌ Cancel",
                    "value": "cancel",
                    "description": "Cancel file selection",
                    "type": "cancel",
                }
            )

            # Show current directory and menu
            print(f"\n📂 Current directory: {current_dir}")
            selected = interactive_menu("Select PDF file:", items)

            if not selected or selected["type"] == "cancel":
                return None

            if selected["type"] == "manual":
                manual_path = text_input("Enter full path to PDF file:")
                if manual_path and manual_path.strip():
                    manual_path = manual_path.strip()
                    if os.path.exists(manual_path) and manual_path.lower().endswith(
                        ".pdf"
                    ):
                        return os.path.abspath(manual_path)
                    else:
                        print(f"❌ Invalid PDF file: {manual_path}")
                        continue
                continue

            elif selected["type"] == "parent":
                current_dir = os.path.dirname(current_dir)

            elif selected["type"] == "dir":
                current_dir = os.path.join(current_dir, selected["value"])

            elif selected["type"] == "file":
                file_path = os.path.join(current_dir, selected["value"])
                return os.path.abspath(file_path)

        except PermissionError:
            print(f"❌ Permission denied: {current_dir}")
            current_dir = os.path.dirname(current_dir)
        except Exception as e:
            print(f"❌ Error browsing directory: {e}")
            return None


def select_output_format() -> Optional[str]:
    """Select output format for conversion"""
    format_options = [
        {
            "name": "📝 Text (TXT)",
            "value": "txt",
            "description": "Extract text content from PDF",
        },
        {
            "name": "🖼️  PNG Images",
            "value": "png",
            "description": "Convert each page to PNG image",
        },
        {
            "name": "📸 JPEG Images",
            "value": "jpg",
            "description": "Convert each page to JPEG image",
        },
        {"name": "❌ Cancel", "value": "cancel", "description": "Cancel conversion"},
    ]

    selected = interactive_menu("Select output format:", format_options)

    if not selected or selected["value"] == "cancel":
        return None

    return selected["value"]


def get_file_size_str(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def convert_pdf_file():
    """Main PDF conversion function"""
    print("📄 PDF File Converter")
    print("-" * 30)

    # Check dependencies
    print("🔍 Checking PDF processing libraries...")
    if not any(get_pdf_libraries_status().values()):
        print("❌ No PDF processing libraries found!")
        install_missing_dependencies()
        return

    # Browse for PDF file
    pdf_file = browse_for_pdf_file()
    if not pdf_file:
        print("❌ PDF file selection cancelled")
        return

    print(f"✅ Selected PDF file: {os.path.basename(pdf_file)}")

    # Get PDF info
    try:
        file_size = get_file_size_str(os.path.getsize(pdf_file))
        print(f"📊 File size: {file_size}")
    except Exception as e:
        print(f"⚠️  Could not get file info: {e}")

    # Select output format
    output_format = select_output_format()
    if not output_format:
        print("❌ Conversion cancelled")
        return

    # Setup output
    output_manager = OutputManager()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_name = Path(pdf_file).stem

    print(f"\n🔄 Converting to {output_format.upper()}...")

    if output_format == "txt":
        # Convert to text
        output_filename = f"{base_name}_{timestamp}.txt"
        output_path = output_manager.get_output_path("pdf_converter", output_filename)

        if convert_pdf_to_text(pdf_file, output_path):
            file_size = get_file_size_str(os.path.getsize(output_path))
            print("✅ Text conversion completed!")
            print(f"📁 Output file: {output_path}")
            print(f"📊 Output size: {file_size}")
        else:
            print("❌ Text conversion failed")

    elif output_format in ["png", "jpg"]:
        # Convert to images
        output_dir = output_manager.get_output_path(
            "pdf_converter", f"{base_name}_{timestamp}"
        )

        image_paths = convert_pdf_to_images(pdf_file, output_dir, output_format.upper())

        if image_paths:
            total_size = sum(os.path.getsize(path) for path in image_paths)
            print("✅ Image conversion completed!")
            print(f"📁 Output directory: {output_dir}")
            print(f"🖼️  Generated {len(image_paths)} images")
            print(f"📊 Total size: {get_file_size_str(total_size)}")
        else:
            print("❌ Image conversion failed")


def main():
    print("📄 PDF Converter")
    print("=" * 50)

    # Check if libraries are available
    libraries = get_pdf_libraries_status()
    available_libs = [lib for lib, status in libraries.items() if status]

    if not available_libs:
        print("❌ No PDF processing libraries found!")
        print("📦 This tool requires at least one of the following libraries:")
        install_missing_dependencies()
        return

    print(f"✅ Available libraries: {', '.join(available_libs)}")

    # Define menu options
    menu_options = [
        {
            "name": "🔄 Convert PDF file",
            "value": "convert",
            "description": "Convert PDF to TXT or image formats",
            "action": convert_pdf_file,
        },
        {
            "name": "🔍 Check dependencies",
            "value": "check_deps",
            "description": "Check available PDF processing libraries",
            "action": install_missing_dependencies,
        },
        {
            "name": "👋 Exit",
            "value": "exit",
            "description": "Quit the PDF converter",
            "action": None,
        },
    ]

    while True:
        try:
            print("\n" + "=" * 50)
            selected = interactive_menu("Select an option:", menu_options)

            if not selected or selected["value"] == "exit":
                print("👋 Goodbye!")
                break

            # Execute the selected action
            if selected["action"]:
                print(f"\n🔧 Running: {selected['name']}")
                print("-" * 40)
                selected["action"]()

                # Ask if user wants to continue
                if not confirm(
                    "\nWould you like to perform another action?", default=True
                ):
                    print("👋 Goodbye!")
                    break

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if not confirm("Would you like to continue?", default=True):
                break
