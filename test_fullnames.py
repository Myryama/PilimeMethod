from pilime_method import read_csv, TeamCirculation

members = read_csv('members.csv', 'name')
projects = read_csv('projects.csv', 'name')

# Change use_initials to False and test
circulation = TeamCirculation(members, projects, quarters=4, use_initials=False)
circulation.generate_schedule()

# Generate and save markdown
markdown = circulation.generate_markdown_table()

with open("test_schedule_fullnames.md", "w", encoding="utf-8") as f:
    f.write(markdown)

print("✓ Schedule with full names saved to test_schedule_fullnames.md")

# Show a preview
lines = markdown.split('\n')
for i, line in enumerate(lines):
    if i >= 4 and i <= 12:
        print(line)
