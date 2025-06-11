import re
import os

class CharacterPromptGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "organization": (["lovehent", "vixmavis", "violetjoi", "teste"], {}),
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
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("character_prompt", "scene_prompts", "hiresfix_prompts","base_savepath", "savepath_high_quality", 
                   "savepath_low_quality", "savepath_watermarked", "source", "logo", "title")
    OUTPUT_IS_LIST = (False, False, True, False, False, False, False, False, False)
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
    
    def get_node_directory(self):
        """Get the directory where this node file is located"""
        return os.path.dirname(os.path.abspath(__file__))
    
    def generate_prompts(self, organization, project_type, workspace, character_name, character_base, 
                        character_scene_details, background, final_details_quality_tags,
                        prompt_scenes, max_prompts_enabled, max_prompts):
        
        # Map organization selection to its corresponding value
        org_mapping = {
            "lovehent": "by mdf_an, ratatatat74",
            "vixmavis": "Anime screencap,Koyorin",
            "violetjoi":"_style0",
            "teste":"_style0"
        }
        
        # Organization-specific tags for hiresfix_prompts
        hiresfix_org_mapping = {
            "teste": "_style0",
            "vixmavis": "fake_screenshot,Koyorin,by free_style_\(yohan1754\)",
            "violetjoi":"_style0",
            "lovehent":"by mdf_an,tomu_\(tomubobu\),"
        }
        
        # Organization-specific source and logo mapping
        org_info_mapping = {
            "lovehent": {
                "source": "https://www.patreon.com/lovehent",
                "logo": "lovehent_watermark.png"
            },
            "vixmavis": {
                "source": "https://www.patreon.com/vixmavis",
                "logo": "vixmavis_watermark.png"
            },
            "violetjoi": {
                "source": "https://www.patreon.com/violetjoi",
                "logo": "violetjoi_watermark.png"
            },
            "teste": {
                "source": "",
                "logo": ""
            }
        }
        
        org_value = org_mapping.get(organization, "")
        hiresfix_org_value = hiresfix_org_mapping.get(organization, "")
        org_info = org_info_mapping.get(organization, {"source": "", "logo": ""})
        
        # Map workspace selection to its corresponding file path
        workspace_paths = {
            "lightning": "/teamspace/studios/this_studio/Packreator/",
            "runpod": "/workspace/Packreator/",
            "sagemaker": "/workspace/sage/Packreator/"
        }
        
        workspace_path = workspace_paths[workspace]
        
        # Generate title
        title = f"{character_name} {project_type}"
        
        # Generate source and logo paths
        source = org_info["source"]
        
        if org_info["logo"]:
            node_dir = self.get_node_directory()
            logo = os.path.join(node_dir, "files", org_info["logo"]).replace("\\", "/")
        else:
            logo = ""
        
        # Generate base savepath
        base_savepath = f"{workspace_path}{organization}/{project_type}/{character_name}"
        
        # Generate the three savepaths
        savepath_high_quality = f"{base_savepath}/high_quality"
        savepath_low_quality = f"{base_savepath}/lowquality"
        savepath_watermarked = f"{base_savepath}/watermarked"
        
        # Generate character prompt
        character_prompt = f"[{character_name}], {org_value}, {character_base}, {background}"
        #character_prompt = self.clean_text(character_prompt)
        
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
                #full_prompt = self.clean_text(full_prompt)
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
        
        return (character_prompt, scene_prompts, hiresfix_prompts_list,base_savepath, savepath_high_quality, 
                savepath_low_quality, savepath_watermarked, source, logo, title)
