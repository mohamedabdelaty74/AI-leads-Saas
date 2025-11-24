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

# إعدادات CUDA
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

# تحميل النموذج - DISABLED to prevent duplicate 14GB model loading
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
print("[INFO] Qwen model disabled in generate_mail.py - model loaded in main app only")

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

def generate_emails_from_excel(input_file, output_file, user_company_info=None, custom_instruction=None):
    df = pd.read_excel(input_file, engine='openpyxl')
    required_columns = ["Title", "Email", "Description"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"❌ الملف لا يحتوي على العمود المطلوب: {col}")

    if "First Name" not in df.columns:
        df["First Name"] = ""

    df['Elite_Creatif_Email'] = ""

    if user_company_info and user_company_info.strip():
        company_info = user_company_info.strip()
    else:
        raise ValueError("❌ Company information is missing. Please provide it in the Company Info section.")

    sig = extract_signature_info(company_info)
    name_line = f"{sig['name']} | " if sig['name'] else ""

    base_instruction = f"""
You are an expert business email copywriter.
Your task: Write a professional, customized outreach email to a potential client, introducing the company and inviting them to collaborate or learn more about our services.

**Instructions:**
- Focus on the client's pain points and what makes our company unique.
- Be specific—no empty claims or clichés.
- End with a clear call to action (e.g., request a meeting, a reply, or a demo).
- The email must be ready to send with no placeholders or generic text.
- If a first name is provided, use it in the greeting; otherwise, use the company name.
- Maintain a friendly, engaging, and professional tone.
- End with your contact details from the info below.

## 📌 Example 1: (With First Name)
**Description:** "James Smith is the founder of SmithTech, a startup specializing in AI-powered business automation solutions."
**Generated Email:**  
```
Subject: Let’s Scale SmithTech with Smart Marketing

Dear James,

Your work in AI-driven business automation is truly exciting! At [Your Agency Name], we help innovative startups like SmithTech gain the visibility they deserve. Through SEO, strategic ad buying, and social media management, we ensure your solutions reach the right businesses.

Let’s set up a quick call to explore how we can accelerate your brand’s growth. Looking forward to collaborating!

Best regards,  
[Your Name] | [Your Agency Name]  
[Your Email] | [Your Website] | [Your Phone]
```

## 📌 Example 2: (Company Name Only)
**Description:** "Urban Trends is a modern fashion brand specializing in streetwear for young adults. They focus on sustainability and ethical production."
**Generated Email:**  
```
Subject: Elevate Urban Trends’ Online Presence

Dear Urban Trends Team,

We admire your commitment to sustainability and ethical fashion! At [Your Agency Name], we specialize in branding, social media management, and targeted advertising to help fashion brands reach their ideal audience.

With our expertise in SEO, PR, and influencer collaborations, we can amplify Urban Trends’ presence and drive real engagement. Let’s connect to discuss how we can grow your brand’s impact!

Best regards,  
[Your Name] | [Your Agency Name]  
[Your Email] | [Your Website] | [Your Phone]
"""

    instructions = base_instruction + "\n\n" + custom_instruction.strip() if custom_instruction and custom_instruction.strip() else base_instruction

    total = len(df)
    generated = 0
    start_time = time.time()

    for index, row in df.iterrows():
        description = row['Description'] if pd.notna(row['Description']) else row['Title']
        first_name = row['First Name'] if pd.notna(row['First Name']) else None
        company_title = row['Title'] if pd.notna(row['Title']) else "there"
        greeting = f"Dear {first_name}," if first_name else f"Dear {company_title} Team,"

        messages = [
            {"role": "system", "content": "You are an AI assistant specializing in crafting professional business emails for marketing purposes."},
            {"role": "user", "content": f"""
🔹 **Our Company Info:**
{company_info}

🔹 **Instructions:**
{instructions}

🔹 **Company Description:**
{description}

🔹 **Greeting:**
{greeting}

Please follow the above instructions carefully and return only the generated email.
"""}
        ]

        text_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer([text_prompt], return_tensors="pt").to(model.device)

        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.9
            )

        generated_text = tokenizer.batch_decode(generated_ids[:, model_inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]

        final_email = generated_text.strip()
        df.at[index, 'Elite_Creatif_Email'] = final_email
        generated += 1
        print(f"✅ Email generated for company {index+1}/{total}")

    df.to_excel(output_file, index=False)
    duration = time.time() - start_time

    summary = f"""
✅ Email Generation Completed!
📦 Total Companies: {total}
📧 Emails Generated: {generated}
⏱️ Time Taken: {duration:.2f} seconds
"""
    print(summary)
    return summary.strip()
