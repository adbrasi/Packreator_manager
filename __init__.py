from .custom_prompt_manager import CharacterPromptGenerator

# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "CharacterPromptGenerator": CharacterPromptGenerator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CharacterPromptGenerator": "Character Prompt Generator 📝"
}