# Restaurant Description Generator with Google Enrichment
# For Google Colab
# !pip install transformers bitsandbytes accelerate openpyxl pandas smtplib email serpapi --upgrade
# import sys
# !{sys.executable} -m pip install --upgrade duckduckgo-search
import os
import time
import re
import pandas as pd
import torch
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login


# ✅ تحميل متغيرات البيئة (API Keys)
load_dotenv()
login(token=os.getenv("HUGGINGFACE_API_KEY"))

# دي أهم خطوة دلوقتي 👇
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

# Model loading - DISABLED to prevent duplicate 14GB model loading
# The Qwen model is loaded once in gradio_saas_integrated.py
# model_id = "Qwen/Qwen2.5-7B-Instruct"
# tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
# model = AutoModelForCausalLM.from_pretrained(
#     model_id,
#     trust_remote_code=True,
#     torch_dtype=torch.bfloat16,
#     device_map="auto"
# )
model_id = None
tokenizer = None
model = None
print("[INFO] Qwen model disabled in generate_whats.py - model loaded in main app only")


def extract_signature_info(company_info):
    email = re.findall(r"[\w.-]+@[\w.-]+", company_info)
    phone = re.findall(r"\+?\d[\d\s\-()]{7,}", company_info)
    website = re.findall(r"www\.[\w.-]+", company_info)
    company_name_match = re.search(r"We[’']?re an? (.+?) offering", company_info, re.IGNORECASE)
    name_match = re.search(r"Contact:\s*([^|\n]+)", company_info)

    return {
        "name": name_match.group(1).strip() if name_match else "",
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "website": website[0] if website else "",
        "company": company_name_match.group(1).strip() if company_name_match else ""
    }



def generate_whatsapp_messages_from_excel(input_file, output_file, user_company_info, custom_instruction=None):
    df = pd.read_excel(input_file, engine='openpyxl')
    required_columns = ["Title", "Phone", "Description"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"❌ الملف لا يحتوي على العمود المطلوب: {col}")

    if "First Name" not in df.columns:
        df["First Name"] = ""

    df['WhatsApp_Message'] = ""

    if user_company_info and user_company_info.strip():
        company_info = user_company_info.strip()
    else:
        raise ValueError("❌ Company information is missing. Please provide it in the Company Info section.")

    sig = extract_signature_info(company_info)
    name_line = f"{sig['name']} | " if sig['name'] else ""
    fallback_signature = f"""
\n{name_line}{sig['company']}\n{sig['email']} | {sig['website']} | {sig['phone']}"""

    base_instruction = f"""
Instructions:
- You will be provided with real company information.
- Replace placeholders like [Your Name], [Your Company], [Your Email], [Your Website], and [Your Phone] using the info provided.
- Craft a short, natural WhatsApp message introducing your service to the company.
- Use friendly, human language.
- Keep it concise: 3 to 6 lines.
- End with your name and contact (from company info).

## 📌 Example 1: (With First Name)
**Description:** "James Smith is the founder of SmithTech, a startup specializing in AI-powered business automation solutions."
**Generated Message:**
Hi James 👋  
I'm [Your Name] from [Your Company].  
I noticed your work with SmithTech in AI automation – super impressive!  
We specialize in helping SaaS startups like yours gain more visibility through strategic SEO and paid ads.  
Would love to connect for a quick chat if you're open!  
– [Your Name] | [Your Company]  
[Your Website]

## 📌 Example 2: (Company Name Only)
**Description:** "Urban Trends is a modern fashion brand specializing in streetwear for young adults. They focus on sustainability and ethical production."
**Generated Message:**
Hey Urban Trends Team 👋  
I’m [Your Name] from [Your Company].  
Loved your focus on sustainable streetwear – it’s very on trend 🌱  
We help fashion brands grow their audience through social media, influencer content, and targeted ads.  
Can we set up a quick call to explore ideas?  
– [Your Name] | [Your Company]  
[Your Website]
"""

    instructions = base_instruction + "\n\n" + custom_instruction.strip() if custom_instruction and custom_instruction.strip() else base_instruction

    total = len(df)
    generated = 0
    start_time = time.time()

    for index, row in df.iterrows():
        description = row['Description'] if pd.notna(row['Description']) else row['Title']
        first_name = row['First Name'] if pd.notna(row['First Name']) else None

        messages = [
            {"role": "system", "content": "You are an AI assistant specializing in generating short, effective WhatsApp marketing messages."},
            {"role": "user", "content": f"""
🔹 **Our Company Info:**
{company_info}

🔹 **Instructions:**
{instructions}

🔹 **Company Description:**
{description}

Please follow the above instructions carefully and return only the WhatsApp message.
"""}
        ]

        text_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer([text_prompt], return_tensors="pt").to(model.device)

        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=300,
                do_sample=True,
                temperature=0.9
            )

        generated_text = tokenizer.batch_decode(generated_ids[:, model_inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]

        final_msg = generated_text.strip()
        df.at[index, 'WhatsApp_Message'] = final_msg.strip()
        generated += 1
        print(f"✅ WhatsApp message generated for company {index+1}/{total}")

    df.to_excel(output_file, index=False)
    duration = time.time() - start_time

    summary = f"""
✅ WhatsApp Message Generation Completed!
📦 Total Companies: {total}
📩 Messages Generated: {generated}
⏱️ Time Taken: {duration:.2f} seconds
"""
    print(summary)
    return summary.strip()    
