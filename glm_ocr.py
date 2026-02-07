from transformers import AutoProcessor, AutoModelForImageTextToText
import torch
import os
from datetime import datetime

MODEL_PATH = "zai-org/GLM-OCR"
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "url": "test_image.png"
            },
            {
                "type": "text",
                "text": "Text Recognition:"
            }
        ],
    }
]
processor = AutoProcessor.from_pretrained(MODEL_PATH, cache_dir="./model_folder")
model = AutoModelForImageTextToText.from_pretrained(
    pretrained_model_name_or_path=MODEL_PATH,
    torch_dtype="auto",
    device_map="auto",
)
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

# Save output to temp folder
temp_folder = "temp"
os.makedirs(temp_folder, exist_ok=True)

# Create filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"ocr_output_{timestamp}.txt"
output_path = os.path.join(temp_folder, output_filename)

# Save the output
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(output_text)

print(f"OCR output saved to: {output_path}")
print(f"Output text:\n{output_text}")
