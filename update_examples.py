import re
import os

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to find callout-tip examples with manual numbering
    # e.g., ::: {.callout-tip} \n ## Ejemplo 1.1.1: Title
    pattern = r'::: \{\.callout-tip\}\n## Ejemplo [\d\.]+: (.*?)\n'
    
    def replacement(match):
        title = match.group(1)
        # Create a clean label from the title
        label = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())
        return f'::: {{#exm-{label} .callout-tip}}\n## Ejemplo: {title}\n'

    new_content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

chapters_dir = 'chapters'
for filename in os.listdir(chapters_dir):
    if filename.endswith('.qmd'):
        process_file(os.path.join(chapters_dir, filename))
