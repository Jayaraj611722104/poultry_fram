import glob, re

for file_path in glob.glob('app/routes/*.py'):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace single queries
    content = re.sub(r"\(Farm\.query\.filter_by\(id=([^\)]+)\) if getattr\(current_user, 'role', 'user'\) == 'admin' else Farm\.query\.filter_by\(id=\1, user_id=current_user\.id\)\)", r"Farm.query.filter_by(id=\1)", content)
    
    # Replace global queries
    content = content.replace("(Farm.query if getattr(current_user, 'role', 'user') == 'admin' else Farm.query.filter_by(user_id=current_user.id))", "Farm.query")

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Updated {file_path}")
