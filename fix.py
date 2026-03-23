import glob

for f in glob.glob('app/routes/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if r"\'" in content:
        new_content = content.replace(r"\'", "'")
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Fixed {f}")
