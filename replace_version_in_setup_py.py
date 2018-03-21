import re

with open('setup.py') as setup_file:
    content = setup_file.read()
    res = re.search('version=\'\d+\.\d+\.(\d+)\'', content)
    if res is not None:
        matched_text = res.group()
        new_version = int(res.group(1)) + 1
        new_text = matched_text.replace('.{}\''.format(res.group(1)), '.{}\''.format(new_version))
        content = content.replace(matched_text, new_text)

with open('setup.py', 'w') as setup_file:
    setup_file.write(content)
