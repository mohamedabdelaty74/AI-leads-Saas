import os
import time
import random
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# ✅ تحميل متغيرات البيئة (API Keys)
load_dotenv()

def send_emails_from_excel(input_file, sender_email, app_password):

    df = pd.read_excel(input_file)

    # Find email column (flexible naming)
    possible_email_columns = ['Email', 'email', 'E-mail', 'e-mail', 'EMAIL', 'Contact Email', 'contact_email',
                            'ContactEmail', 'Email Address', 'email_address', 'EmailAddress']
    email_column = None
    for col in possible_email_columns:
        if col in df.columns:
            email_column = col
            break

    if email_column is None:
        available_columns = ', '.join(df.columns.tolist())
        return {
            "sent": 0, "failed": 0, "total": 0, "failed_emails": [],
            "error": f"❌ No email column found. Available columns: {available_columns}"
        }

    # Rename columns consistently
    df.rename(columns={email_column: "receiver_email"}, inplace=True)
    df.rename(columns={"Elite_Creatif_Email": "Email"}, inplace=True)
    
    # ✅ فلترة الصفوف بدون إيميل
    df = df[df["receiver_email"].notna() & (df["receiver_email"].str.strip() != "")]

    required_columns = ["receiver_email", "Email"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return {
            "sent": 0,
            "failed": 0,
            "total": 0,
            "failed_emails": [],
            "error": f"❌ Missing columns: {missing_columns}"
        }

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    total_emails = len(df)
    sent_count = 0
    failed_count = 0
    failed_emails = []

    max_emails_limit = 1000  # ✅ الحد الأقصى للإيميلات
    start_time = time.time()  # 🕰️ بداية حساب الوقت

    for index, row in df.iterrows():
        if sent_count >= max_emails_limit:
            print(f"🛑 Reached the maximum limit of {max_emails_limit} emails. Stopping sending.")
            break

        receiver_email = row["receiver_email"]
        email_content = row["Email"]

        lines = email_content.split("\n", 1)
        if len(lines) < 2:
            failed_count += 1
            failed_emails.append(receiver_email)
            continue

        subject = lines[0].replace("Subject: ", "").strip()
        body = lines[1].strip()

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            sent_count += 1
            print(f"✅ Email {sent_count}/{total_emails} sent successfully to {receiver_email}")

        except Exception as e:
            failed_count += 1
            failed_emails.append(receiver_email)
            print(f"❌ Failed to send Email {index+1}/{total_emails} to {receiver_email}: {e}")

        # ✅ تأخير عشوائي بين الإيميلات
        sleep_time = random.uniform(5, 15)
        print(f"⏳ Waiting for {sleep_time:.2f} seconds before sending the next email...")
        time.sleep(sleep_time)
        
        #sleep_time = random.randint(10, 20) * 60  # من 10 لـ 20 دقيقة
        #print(f"⏳ Waiting for {sleep_time // 60:.0f} minutes before sending the next email...")
        #time.sleep(sleep_time)


        # ✅ كل 50 إيميل بريك 5 دقائق
        if sent_count % 50 == 0 and sent_count % 100 != 0 and sent_count != 0:
            print(f"🛑 Sent {sent_count} emails! Taking a 5-minute break...")
            time.sleep(5 * 60)
            print("✅ Break finished. Resuming sending emails...")

        # ✅ كل 100 إيميل بريك 10 دقائق
        if sent_count % 100 == 0 and sent_count != 0:
            print(f"🛑 Sent {sent_count} emails! Taking a 10-minute break...")
            time.sleep(10 * 60)
            print("✅ Break finished. Resuming sending emails...")

    end_time = time.time()  # 🕰️ نهاية حساب الوقت
    total_duration = end_time - start_time

    # ✅ طباعة السامري الكامل
    print("\n🎯 Final Summary:")
    print(f"✅ Emails sent successfully: {sent_count}")
    print(f"❌ Emails failed to send: {failed_count}")
    print(f"🕰️ Total time taken: {total_duration/60:.2f} minutes")
    print(f"⚡ Average sending speed: {sent_count / (total_duration/60):.2f} emails per minute")

    return {
        "sent": sent_count,
        "failed": failed_count,
        "total": total_emails,
        "failed_emails": failed_emails,
        "duration_seconds": total_duration
    }
