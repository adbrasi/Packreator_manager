import os
import json
import random
import subprocess
import time
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

class PromptSceneGenerator:
    """
    Generates scene prompts by combining texts from different files and appending
    additional information from a JSON configuration and character tags.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the PromptSceneGenerator with path configuration.
        
        Args:
            base_path: Base path where all input files are located. Defaults to './files' relative to this script.
        """
        if base_path is None:
            base_path = Path(__file__).parent / "files"
        self.base_path = Path(base_path)
        self.files = {
            "start": self.base_path / "start.txt",
            "middle": self.base_path / "middle.txt",
            "end": self.base_path / "end.txt",
            "clothing": self.base_path / "clothing.json",
            "characters": self.base_path / "440028Already29.txt",
            "scraper": self.base_path / "danbooru_scraper.py"
        }
        
        # Validate paths
        for name, path in self.files.items():
            if not path.exists():
                raise FileNotFoundError(f"Required file not found: {path}")
        
        # Load configuration
        self.clothing_config = self._load_json(self.files["clothing"])
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load and parse a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_text_lines(self, file_path: Path) -> List[str]:
        """Load lines from a text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    
    def _get_context_lines(self, lines: List[str], index: int, context_size: int) -> List[str]:
        """
        Get lines around the specified index to provide context.
        
        Args:
            lines: List of all text lines
            index: Center index for context
            context_size: Total number of lines to return (including center)
            
        Returns:
            List of context lines
        """
        if not lines:
            return []
        
        # If context_size is 1, just return the selected line
        if context_size <= 1:
            return [lines[index]]
        
        # Calculate how many lines we need before and after
        total_lines = len(lines)
        
        # Try to distribute context evenly (prefer more lines after than before if uneven)
        lines_before = min((context_size - 1) // 2, index)
        lines_after = min(context_size - 1 - lines_before, total_lines - index - 1)
        
        # Readjust lines_before if we couldn't get enough lines_after
        lines_before = min(context_size - 1 - lines_after, index)
        
        # Extract the context
        start_idx = index - lines_before
        end_idx = index + lines_after + 1  # +1 because slices are exclusive at end
        
        return lines[start_idx:end_idx]
    
    def _select_random_lines_with_context(self, file_type: str, count: int) -> List[str]:
        """
        Select random lines with context from the specified file.
        
        Args:
            file_type: The type of file to read from ('start', 'middle', or 'end')
            count: How many lines to select (including context)
            
        Returns:
            List of selected lines
        """
        if count <= 0:
            return []
            
        lines = self._load_text_lines(self.files[file_type])
        if not lines:
            return []
        
        # If we need less or equal lines than available, just return random ones
        if count >= len(lines):
            return lines
        
        result = []
        remaining = count
        
        while remaining > 0:
            # How many lines to select in this iteration
            # This helps handle cases where count is small
            batch_size = min(remaining, max(1, remaining // 2))
            
            # Select a random line and get context around it
            random_index = random.randint(0, len(lines) - 1)
            context_lines = self._get_context_lines(lines, random_index, batch_size)
            
            # Add to result and update remaining
            result.extend(context_lines)
            remaining -= len(context_lines)
        
        # Trim if we somehow got too many lines
        return result[:count]
    
    def _get_character_tags(self, timeout: int = 10) -> str:
        """
        Get character tags by running the danbooru scraper script.
        
        Args:
            timeout: Maximum time in seconds to wait for the script
            
        Returns:
            Character tags as a string
        """
        characters = self._load_text_lines(self.files["characters"])
        if not characters:
            return ""
        
        max_attempts = 3
        for attempt in range(max_attempts):
            # Select random character
            self.selected_character = random.choice(characters)
            print(self.selected_character)
            
            try:
                # Run scraper script
                start_time = time.time()
                process = subprocess.Popen(
                    [sys.executable, str(self.files["scraper"]), self.selected_character],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for completion or timeout
                while time.time() - start_time < timeout:
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
                
                # Check if process is still running (timeout occurred)
                if process.poll() is None:
                    process.terminate()
                    print(f"Scraper timed out for character: {self.selected_character}")
                    continue  # Try another character
                
                # Check output
                stdout, _ = process.communicate()
                tags = stdout.strip()
                
                # Validate the number of tags
                tag_count = len([t for t in tags.split(',') if t.strip()])
                if tag_count <= 3:
                    print(f"Insufficient tags ({tag_count}) for character: {self.selected_character}")
                    continue  # Try another character
                
                return tags
                
            except Exception as e:
                print(f"Error running scraper for character {self.selected_character}: {e}")
        
        # If all attempts failed, return a simple default
        return "character"
    
    def _enhance_prompt_with_clothing(self, 
                                      start_prompts: List[str], 
                                      mid_prompts: List[str], 
                                      end_prompts: List[str],
                                      partner: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Enhance prompts with clothing information from the JSON configuration.
        
        Args:
            start_prompts: List of start prompts
            mid_prompts: List of middle prompts
            end_prompts: List of end prompts
            partner: Partner string to include in prompts (can include multiple options separated by /)
            
        Returns:
            Tuple of enhanced (start_prompts, mid_prompts, end_prompts)
        """
        # Split partner string into multiple options if they exist
        partner_options = [p.strip() for p in partner.split("/")] if partner else []
        
        # Generate random clothing combination
        color = random.choice(self.clothing_config["start"]["colors"]) if self.clothing_config["start"]["colors"] else ""
        clothing = random.choice(self.clothing_config["start"]["clothing"]) if self.clothing_config["start"]["clothing"] else ""
        outfit = f"{color}, {clothing}" if color and clothing else color or clothing
        
        # Enhanced start prompts with colors and clothing
        enhanced_start = []
        if start_prompts:
            # Apply to all start prompts
            for i, prompt in enumerate(start_prompts):
                # Add partner to 1/4 of start prompts (at the end)
                partner_text = ""
                if i >= len(start_prompts) - max(1, len(start_prompts) // 4) and partner_options:
                    # Randomly select one partner option
                    selected_partner = random.choice(partner_options)
                    partner_text = f", {selected_partner}" if selected_partner else ""
                
                enhanced_start.append(f"{outfit}{partner_text}, {prompt}")
        
        # Enhance middle prompts with part1 and part2
        enhanced_mid = []
        if mid_prompts:
            # Calculate split point for part1 and part2
            part1_count = max(1, len(mid_prompts) // 4) if len(mid_prompts) > 0 else 0
            
            # Calculate how many mid prompts should have the outfit (half of them)
            outfit_count = max(1, len(mid_prompts) // 2) if len(mid_prompts) > 0 else 0
            
            # Process part1 prompts
            for i in range(min(part1_count, len(mid_prompts))):
                part1_item = random.choice(self.clothing_config["Mid"]["part1"]) if self.clothing_config["Mid"]["part1"] else ""
                
                partner_text = ""
                if partner_options:
                    # Randomly select one partner option
                    selected_partner = random.choice(partner_options)
                    partner_text = f", {selected_partner}" if selected_partner else ""
                
                # Add outfit to half of middle prompts
                outfit_text = f"{outfit}, " if i < outfit_count else ""
                
                enhanced_mid.append(f"{outfit_text}{part1_item}{partner_text}, {mid_prompts[i]}")
            
            # Process part2 prompts
            for i in range(part1_count, len(mid_prompts)):
                part2_item = random.choice(self.clothing_config["Mid"]["part2"]) if self.clothing_config["Mid"]["part2"] else ""
                
                partner_text = ""
                if partner_options:
                    # Randomly select one partner option
                    selected_partner = random.choice(partner_options)
                    partner_text = f", {selected_partner}" if selected_partner else ""
                
                # Add outfit to half of middle prompts (continuing count from part1)
                outfit_text = f"{outfit}, " if i - part1_count + part1_count < outfit_count else ""
                
                enhanced_mid.append(f"{outfit_text}{part2_item}{partner_text}, {mid_prompts[i]}")
        
        # Enhance end prompts
        enhanced_end = []
        if end_prompts:
            end_tag = self.clothing_config["end"].get("tag", "")
            
            for i, prompt in enumerate(end_prompts):
                # Add partner to 1/4 of end prompts (at the beginning)
                partner_text = ""
                if i < max(1, len(end_prompts) // 4) and partner_options:
                    # Randomly select one partner option
                    selected_partner = random.choice(partner_options)
                    partner_text = f", {selected_partner}" if selected_partner else ""
                
                enhanced_end.append(f"{end_tag}{partner_text}, {prompt}")
        
        return enhanced_start, enhanced_mid, enhanced_end
    
    def generate_scene_prompt(self, start: int, middle: int, end: int, partner: str = "") -> Dict[str, Any]:
        """
        Generate a complete scene prompt based on input parameters.
        
        Args:
            start: Number of lines to select from start.txt
            middle: Number of lines to select from middle.txt
            end: Number of lines to select from end.txt
            partner: Partner string to include in prompts (can include multiple options separated by /)
            
        Returns:
            Dictionary with scenePrompt and characterTags
        """
        # Ensure parameters are valid
        start = max(0, start)
        middle = max(0, middle)
        end = max(0, end)
        
        # Select random lines with context
        start_prompts = self._select_random_lines_with_context('start', start)
        mid_prompts = self._select_random_lines_with_context('middle', middle)
        end_prompts = self._select_random_lines_with_context('end', end)
        
        # Enhance prompts with clothing information
        enhanced_start, enhanced_mid, enhanced_end = self._enhance_prompt_with_clothing(
            start_prompts, mid_prompts, end_prompts, partner
        )
        
        # Combine all parts with / separator
        all_prompts = enhanced_start + enhanced_mid + enhanced_end
        scene_prompt = "/".join(all_prompts)
        
        # Get character tags
        character_tags = self._get_character_tags()
        
        return {
            "scenePrompt": scene_prompt,
            "characterTags": character_tags,
            "character": self.selected_character
        }