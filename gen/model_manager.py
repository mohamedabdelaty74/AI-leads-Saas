"""
Shared Model Manager - Load AI models once and share across modules
This prevents loading 56GB of models (4x 14GB)
"""

# Global model storage
_shared_models = {
    "qwen_model": None,
    "qwen_tokenizer": None,
    "bart_summarizer": None
}

def set_models(qwen_model=None, qwen_tokenizer=None, bart_summarizer=None):
    """Set the shared AI models (called from main Gradio app)"""
    global _shared_models
    if qwen_model is not None:
        _shared_models["qwen_model"] = qwen_model
        print("[MODEL MANAGER] Qwen model registered")
    if qwen_tokenizer is not None:
        _shared_models["qwen_tokenizer"] = qwen_tokenizer
        print("[MODEL MANAGER] Qwen tokenizer registered")
    if bart_summarizer is not None:
        _shared_models["bart_summarizer"] = bart_summarizer
        print("[MODEL MANAGER] BART summarizer registered")

def get_qwen_model():
    """Get the shared Qwen model"""
    return _shared_models["qwen_model"]

def get_qwen_tokenizer():
    """Get the shared Qwen tokenizer"""
    return _shared_models["qwen_tokenizer"]

def get_bart_summarizer():
    """Get the shared BART summarizer"""
    return _shared_models["bart_summarizer"]

def models_available():
    """Check if models are loaded"""
    return {
        "qwen": _shared_models["qwen_model"] is not None,
        "tokenizer": _shared_models["qwen_tokenizer"] is not None,
        "bart": _shared_models["bart_summarizer"] is not None
    }

def clear_models():
    """Clear all model references (for cleanup)"""
    global _shared_models
    _shared_models = {
        "qwen_model": None,
        "qwen_tokenizer": None,
        "bart_summarizer": None
    }
    print("[MODEL MANAGER] All models cleared")
