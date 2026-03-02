# Pilime Method - Team Circulation Scheduler

A Python script to implement the Pilime Method, a systematic approach to team rotation across long-running projects to distribute knowledge and ensure continuity.

## Overview

The Pilime Method ensures:
- **Knowledge Distribution**: Team members rotate through projects, spreading expertise
- **Continuity**: Experienced members remain on projects as leaders step down
- **Balanced Workload**: Each person leads multiple projects per year
- **Team Flexibility**: Changing team composition each quarter while maintaining stability

## How It Works

The algorithm:
1. Assigns **3-5 people** to each project per quarter
2. Designates **one person as leader** for each project
3. Allows people to work on **multiple projects** in the same quarter
4. Ensures members **rotate while maintaining continuity** (previous leaders stay but step down)
5. Guarantees each person **leads at least 2 projects per year**

## Input Files

You need two CSV files:

### `members.csv`
```csv
name
Alice
Bob
Carol
```

List of all team members available for assignment (one name per row).

### `projects.csv`
```csv
name
Project Alpha
Project Beta
Project Gamma
```

List of all active projects requiring teams (one name per row).

The included `members.csv` and `projects.csv` files contain sample data for demonstration purposes.

## Running the Script

```bash
python3 pilime_method.py
```

The script will:
1. Read `members.csv` and `projects.csv`
2. Generate a 4-quarter circulation schedule
3. Display constraint verification results
4. Output a Markdown table to `team_schedule.md`

## Output

The `team_schedule.md` file contains a table showing:
- **Quarter**: Which quarter (Q1-Q4)
- **Project**: Project name
- **Team Members**: People assigned to that project (full names or initials)
- **Leader**: The designated leader for that quarter

Example output with full names:
```markdown
## Quarter 1

| Project | Team Members | Leader |
|---------|--------------|--------|
| Project Alpha | Alice, Bob, Carol, David, Emma | Alice |
| Project Beta | Frank, Grace, Henry | Henry |
```

Example output with initials:
```markdown
## Quarter 1

| Project | Team Members | Leader |
|---------|--------------|--------|
| Project Alpha | AB, BY, CD, DE, EF | AB |
| Project Beta | FG, GH, HI | HI |
```

## Customization

To modify the script, you can adjust parameters in the `TeamCirculation` initialization:

```python
circulation = TeamCirculation(
    members=members,
    projects=projects,
    quarters=4,              # Number of quarters to plan (default: 4)
    team_size_min=3,         # Minimum team size per project (default: 3)
    team_size_max=5,         # Maximum team size per project (default: 5)
    use_initials=False       # Use initials instead of full names (default: False)
)
```

### Parameter Details

- **`quarters`**: Number of quarters to plan (e.g., 4 for one year, 8 for two years)
- **`team_size_min` / `team_size_max`**: Adjusts the range of people per project team
- **`use_initials`**: When `True`, displays initials (e.g., "Alice Brown" → "AB") in the output table
- **Max concurrent projects**: Automatically calculated based on number of people and projects to ensure fair workload distribution (default minimum: 2, typically 3-4)
- **Input file names**: Change the filenames in the `main()` function if using different file names

## Example

Run with the included sample data to generate a schedule for the team members and projects:

```bash
python3 pilime_method.py
```

This will generate a comprehensive schedule with team members and leaders balanced across quarters, along with constraint verification showing leadership distribution and team sizes.

### Using Initials

To generate a schedule with initials instead of full names, create a custom script:

```python
from pilime_method import read_csv, TeamCirculation

members = read_csv("members.csv", "name")
projects = read_csv("projects.csv", "name")

# Generate schedule with initials
circulation = TeamCirculation(
    members=members,
    projects=projects,
    quarters=4,
    use_initials=True  # Enable initials in output
)
circulation.generate_schedule()

# Save schedule
markdown = circulation.generate_markdown_table()
with open("team_schedule.md", "w") as f:
    f.write(markdown)
```

## Requirements

- Python 3.7+
- No external dependencies required

## Verification

The script automatically verifies:
- ✓ Each person leads at least 2 projects per year
- ✓ Each project has 3-5 team members per quarter
- ✓ Team members rotate appropriately
- ✓ Leadership is balanced across the team
