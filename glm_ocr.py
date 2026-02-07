from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig
import torch
import os
import gc
from datetime import datetime
from pathlib import Path

MODEL_PATH = "zai-org/GLM-OCR"
temp_folder = "temp"

# Read image paths from file_list.txt
file_list_path = os.path.join(temp_folder, "file_list.txt")

if not os.path.exists(file_list_path):
    print(f"Error: {file_list_path} not found!")
    exit(1)

# Read all file paths and filter for images
image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
image_paths = []

with open(file_list_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if Path(line).suffix.lower() in image_extensions:
            if os.path.exists(line):
                image_paths.append(line)

print(f"Found {len(image_paths)} image(s) to process")

if len(image_paths) == 0:
    print("No valid images found in file list!")
    exit(0)

# Load model and processor
print("Loading model with int8 quantization...")
processor = AutoProcessor.from_pretrained(MODEL_PATH, cache_dir="./model_folder")

# Configure int8 quantization
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0  
)

model = AutoModelForImageTextToText.from_pretrained(
    pretrained_model_name_or_path=MODEL_PATH,
    quantization_config=quantization_config,
    device_map="auto",
)
print("Model loaded successfully with int8 quantization\n")

# Create output folder
os.makedirs(temp_folder, exist_ok=True)

# Process each image
for idx, image_path in enumerate(image_paths, 1):
    print(f"Processing image {idx}/{len(image_paths)}: {Path(image_path).name}")
    
    # Prepare messages for this image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "url": image_path
                },
                {
                    "type": "text",
                    "text": "Text Recognition:"
                }
            ],
        }
    ]
    
    # Process image
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt"
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    
    generated_ids = model.generate(**inputs, max_new_tokens=32000)
    output_text = processor.decode(generated_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)
    
    # Create output filename based on the image name
    image_name = Path(image_path).stem
    output_filename = f"ocr_{image_name}.txt"
    output_path = os.path.join(temp_folder, output_filename)
    
    # Save to individual file
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(f"OCR Result for: {Path(image_path).name}\n")
        output_file.write(f"Source: {image_path}\n")
        output_file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_file.write("=" * 80 + "\n\n")
        output_file.write(output_text + "\n")
    
    print(f"  ✓ Saved to: {output_filename}")
    
    # Clear memory after each image to prevent CUDA OOM
    del inputs
    del generated_ids
    del output_text
    
    # Clear CUDA cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Force garbage collection
    gc.collect()
    
    print(f"  ✓ Memory cleared\n")

print(f"\n{'='*80}")
print(f"Processed {len(image_paths)} image(s) successfully")
print(f"Output files saved in: {temp_folder}/")
