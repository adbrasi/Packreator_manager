import re

class CharacterPromptGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "organization": (["lovehent", "meitabu", "project3"], {}),
                "project_type": (["comic", "pack", "extra"], {}),
                "workspace": (["lightning", "runpod", "sagemaker"], {}),
                "character_name": ("STRING", {"multiline": True}),
                "character_base": ("STRING", {"multiline": True}),
                "character_scene_details": ("STRING", {"multiline": True}),
                "background": ("STRING", {"multiline": True}),
                "final_details_quality_tags": ("STRING", {"multiline": True}),
                "prompt_scenes": ("STRING", {"multiline": True}),
                "max_prompts_enabled": (["yes", "no"], {}),
                "max_prompts": ("INT", {"default": 1, "min": 1, "max": 250})
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING",)
    RETURN_NAMES = ("character_prompt", "scene_prompts", "hiresfix_prompts", "savepath")
    OUTPUT_IS_LIST = (False, False, True, False)
    FUNCTION = "generate_prompts"
    CATEGORY = "text/prompt"
    
    def sanitize_path(self, text):
        """Sanitize text for use in filepath"""
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', text.replace(' ', '_'))
        return sanitized
    
    def clean_text(self, text):
        """Clean up text by removing double spaces, double commas, and other formatting issues"""
        # Replace underline with space
        text = text.replace('_', ' ')
        # Remove double spaces
        text = re.sub(r"\s{2,}", " ", text)
        # Remove spaces before commas
        text = text.replace(" ,", ",")
        # Remove double commas
        text = re.sub(r",{2,}", ",", text)
        # Remove double bars
        text = re.sub(r"\|{2,}", "|", text)
        # Trim whitespace
        text = text.strip()
        return text
    
    def generate_prompts(self, organization, project_type,workspace, character_name, character_base, 
                        character_scene_details, background, final_details_quality_tags,
                        prompt_scenes, max_prompts_enabled, max_prompts):
        
        # Map organization selection to its corresponding value
        org_mapping = {
            "lovehent": "mdf_an,ratatatat74",
            "meitabu": "(suyasuyabi,ratatatat74)",
            "project3": "proj3 patreon"
        }
        
        # Organization-specific tags for hiresfix_prompts
        hiresfix_org_mapping = {
            "lovehent": "mdf_an,artist:quasarcake",
            "meitabu": "(suyasuyabi,dross,(ratatatat74:0.5))",
            "project3": ""
        }
        
        org_value = org_mapping[organization]
        hiresfix_org_value = hiresfix_org_mapping[organization]
        
        # Map workspace selection to its corresponding file path
        workspace_paths = {
            "lightning": "/teamspace/studios/this_studio/outputParagonCreator/",
            "runpod": "/workspace/outputParagonCreator/",
            "sagemaker": "/workspace/sage/outputParagonCreator/"
        }
        
        workspace_path = workspace_paths[workspace]
        
        # Generate savepath
        sanitized_character_name = self.sanitize_path(character_name)
        savepath = f"{workspace_path}{organization}/{project_type}/{self.clean_text(sanitized_character_name)}"
        
        # Generate character prompt
        character_prompt = f"[{character_name}], {org_value}, {character_base}, {background}"
        character_prompt = self.clean_text(character_prompt)
        
        # Process prompt scenes
        prompt_segments = prompt_scenes.split("/")
        
        # Limit number of prompt segments if max_prompts is enabled
        if max_prompts_enabled == "yes":
            prompt_segments = prompt_segments[:max_prompts]
        
        # Generate scene prompts and hiresfix prompts
        scene_prompts_list = []
        hiresfix_prompts_list = []
        
        for segment in prompt_segments:
            segment = segment.strip()
            if segment:  # Skip empty segments
                # Construct full prompt for scene_prompts
                full_prompt = f"[{character_name}], {segment}, {character_scene_details}, {final_details_quality_tags}"
                full_prompt = self.clean_text(full_prompt)
                scene_prompts_list.append(full_prompt)
                
                # Construct hiresfix prompt with different format and organization-specific tags
                if hiresfix_org_value:
                    hiresfix_prompt = f"{hiresfix_org_value}, {character_base}, {segment}, {character_scene_details}, {background}, {final_details_quality_tags}"
                else:
                    hiresfix_prompt = f"{character_base}, {segment}, {character_scene_details}, {background}, {final_details_quality_tags}"
                
                hiresfix_prompt = self.clean_text(hiresfix_prompt)
                hiresfix_prompts_list.append(hiresfix_prompt)
        
        # Join scene prompts into a multi-line string
        scene_prompts = "\n".join(scene_prompts_list)
        
        return (character_prompt, scene_prompts, hiresfix_prompts_list, savepath)