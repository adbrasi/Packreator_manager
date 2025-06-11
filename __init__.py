from .custom_prompt_manager import CharacterPromptGenerator
from .scene_prompt_node import ScenePromptNode

# Node registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "CharacterPromptGenerator": CharacterPromptGenerator,
    "ScenePromptNode": ScenePromptNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CharacterPromptGenerator": "packreator manager",
    "ScenePromptNode": "Scene Prompt Generator 🎨"
}