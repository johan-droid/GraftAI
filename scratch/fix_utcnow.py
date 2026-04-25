import os
import re

def fix_utcnow(directory):
    for root, dirs, files in os.walk(directory):
        if '.venv' in dirs:
            dirs.remove('.venv')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        for file in files:
            if not file.endswith('.py'):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'datetime.utcnow()' in content:
                    # Replace datetime.utcnow() with datetime.now(timezone.utc)
                    new_content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
                    
                    # Ensure timezone is imported from datetime
                    if 'from datetime import' in new_content:
                        # check if timezone is imported
                        if not re.search(r'from datetime import.*timezone', new_content):
                            # Add timezone to an existing datetime import
                            new_content = re.sub(r'(from datetime import [^\n]+)', r'\1, timezone', new_content, count=1)
                    else:
                        # Add import if it doesn't exist
                        if 'import datetime' in new_content:
                            new_content = new_content.replace('import datetime', 'import datetime\nfrom datetime import timezone')
                        else:
                            new_content = 'from datetime import timezone\n' + new_content

                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed {path}")
            except Exception as e:
                print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    fix_utcnow('d:\\GraftAI\\backend')
