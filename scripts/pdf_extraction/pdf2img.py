import os
from pdf2image import convert_from_path

def pdf_to_images(pdf_path, output_base_dir, poppler_path=None, image_format='jpeg', dpi=300):
    # Extract base name without extension
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Create a dedicated subfolder for this PDF
    output_folder = os.path.join(output_base_dir, base_filename)
    os.makedirs(output_folder, exist_ok=True)

    # Convert PDF pages to images
    images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)

    # Save images with naming: <filename>_1.jpeg, <filename>_2.jpeg, ...
    for i, img in enumerate(images):
        img_name = f"{base_filename}_{i+1}.{image_format}"
        img_path = os.path.join(output_folder, img_name)
        img.save(img_path, image_format.upper())
        print(f"Saved: {img_path}")

def process_pdfs_in_directory(root_dir, output_dir, poppler_path=None):
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(subdir, file)
                try:
                    print(f"\nProcessing: {pdf_path}")
                    pdf_to_images(pdf_path, output_base_dir=output_dir, poppler_path=poppler_path)
                except Exception as e:
                    print(f"❌ Failed to process {pdf_path}: {e}")

# Example usage
if __name__ == '__main__':
    input_pdf_root = r'C:\Users\Scry\Downloads\Scanned RL Docs'  # Folder with nested PDFs
    output_dir = r'C:\Users\Scry\Documents\pdf_images'           # Where images should be saved
    poppler_path = r'C:\Users\Scry\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin'

    process_pdfs_in_directory(input_pdf_root, output_dir, poppler_path)
