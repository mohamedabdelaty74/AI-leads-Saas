"""
Download Qwen2.5-1.5B Model
Quick script to download the 1.5B model to your HuggingFace cache

USAGE:
    python download_1.5b_model.py
"""

import os
from huggingface_hub import snapshot_download, login
from pathlib import Path

def download_model():
    """Download Qwen2.5-1.5B-Instruct model"""

    print("=" * 70)
    print("Qwen2.5-1.5B Model Downloader")
    print("=" * 70)
    print()

    # HuggingFace token from .env
    hf_token = "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"

    # Login
    print("[1/3] Logging in to HuggingFace...")
    login(token=hf_token)
    print("      Logged in successfully!")
    print()

    # Model details
    model_id = "Qwen/Qwen2.5-1.5B-Instruct"
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    print(f"[2/3] Downloading {model_id}")
    print(f"      Size: ~3 GB")
    print(f"      Cache location: {cache_dir}")
    print(f"      This will take 5-10 minutes depending on internet speed...")
    print()

    try:
        # Download model
        model_path = snapshot_download(
            repo_id=model_id,
            token=hf_token,
            resume_download=True  # Resume if interrupted
        )

        print()
        print("[3/3] Download complete!")
        print(f"      Model saved to: {model_path}")
        print()

        print("=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Your .env is already configured (AI_MODEL_PATH=Qwen/Qwen2.5-1.5B-Instruct)")
        print("  2. Start backend: python backend/main.py")
        print("  3. Test email generation")
        print("  4. Delete old 7B model to free 14GB (optional)")
        print()
        print("Old 7B model location:")
        print("  C:\\Users\\Q\\.cache\\huggingface\\hub\\models--Qwen--Qwen2.5-7B-Instruct\\")
        print()

        return True

    except Exception as e:
        print()
        print("ERROR: Download failed!")
        print(f"       {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Check internet connection")
        print("  2. Verify HuggingFace token is valid")
        print("  3. Ensure enough disk space (~3GB)")
        print("  4. Try running as administrator")
        print()
        return False

if __name__ == "__main__":
    success = download_model()

    if success:
        print("You can now start your backend!")
        print()
        input("Press Enter to exit...")
    else:
        print("Download failed. Please check the error above.")
        print()
        input("Press Enter to exit...")
