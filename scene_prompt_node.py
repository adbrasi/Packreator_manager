from .prompt_scene_generator import PromptSceneGenerator
import random
import re

class ScenePromptNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "start_count": ("INT", {"default": 5, "min": 0, "max": 100}),
                "middle_count": ("INT", {"default": 10, "min": 0, "max": 100}),
                "end_count": ("INT", {"default": 3, "min": 0, "max": 100}),
                "partner_text": ("STRING",{"multiline": True, "default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 9999999999}),
            },
            "optional": {
                "characterName": ("STRING", {"multiline": True, "default": ""}),
                "characterTags": ("STRING", {"multiline": True, "default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("character", "characterTags", "scenePrompt")
    FUNCTION = "generate_scene_prompt"
    CATEGORY = "text/prompt"
    
    def clean_character_name(self, character_name: str) -> str:
        """
        Remove caracteres indesejados do nome do personagem, como '.', '/', '()', espaços, etc.
        """
        # Remove tudo que não for letra ou número
        cleaned_name = re.sub(r'[^\w]', '', character_name)
        return cleaned_name
    
    def remove_duplicate_commas(self, text: str) -> str:
        """
        Remove vírgulas duplicadas do texto, mantendo apenas uma vírgula entre os termos.
        """
        # Substitui múltiplas vírgulas por uma única vírgula
        cleaned_text = re.sub(r',+', ',', text)
        # Remove vírgulas no início ou fim
        cleaned_text = cleaned_text.strip(',')
        return cleaned_text
    
    def escape_parentheses_in_tags(self, tags: str) -> str:
        """
        Escapa parênteses em tags adicionando uma barra invertida antes de '(' e ')'.
        """
        # Divide as tags por vírgula
        tag_list = [tag.strip() for tag in tags.split(',')]
        corrected_tags = []
        for tag in tag_list:
            # Escapa '(' e ')'
            corrected_tag = tag.replace('(', '\\(').replace(')', '\\)')
            corrected_tags.append(corrected_tag)
        # Junta as tags corrigidas em uma string
        return ', '.join(corrected_tags)
    
    def generate_scene_prompt(self, start_count, middle_count, end_count, partner_text, seed, characterName="", characterTags=""):
        """
        Gera o prompt da cena e as tags do personagem, com limpezas e correções aplicadas.
        """
        # Define a semente para resultados diferentes com sementes diferentes
        random.seed(seed)
        
        generator = PromptSceneGenerator()
        result = generator.generate_scene_prompt(start_count, middle_count, end_count, partner_text)
        
        # Usa o characterName fornecido se não estiver vazio, senão usa o gerado
        final_character = characterName if characterName.strip() else result["character"]
        # Limpa o nome do personagem
        final_character = self.clean_character_name(final_character)
        
        # Usa as characterTags fornecidas se não estiverem vazias, senão usa as geradas
        final_characterTags = characterTags if characterTags.strip() else result["characterTags"]
        # Corrige os parênteses nas tags
        final_characterTags = self.escape_parentheses_in_tags(final_characterTags)
        
        final_scenePrompt = result["scenePrompt"]
        # Remove vírgulas duplicadas do prompt
        final_scenePrompt = self.remove_duplicate_commas(final_scenePrompt)
        
        return (final_character, final_characterTags, final_scenePrompt)