from pilime_method import read_csv, TeamCirculation

members = read_csv('members.csv', 'name')
projects = read_csv('projects.csv', 'name')

print("Testing use_initials parameter")
print("=" * 60)

# Test with initials=False
print("\nWith use_initials=False:")
c_false = TeamCirculation(members, projects, quarters=1, use_initials=False)
c_false.generate_schedule()
md_false = c_false.generate_markdown_table()
for line in md_false.split('\n'):
    if 'Meridian' in line and '|' in line:
        print(line[:100])
        break

# Test with initials=True
print("\nWith use_initials=True:")
c_true = TeamCirculation(members, projects, quarters=1, use_initials=True)
c_true.generate_schedule()
md_true = c_true.generate_markdown_table()
for line in md_true.split('\n'):
    if 'Meridian' in line and '|' in line:
        print(line[:100])
        break

print("\nKey section present in use_initials=True?", "## Key" in md_true)
print("Key section present in use_initials=False?", "## Key" in md_false)
