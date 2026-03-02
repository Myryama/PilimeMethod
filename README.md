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

### `sample_members.csv`
```csv
name
Alice
Bob
Carol
```

List of all team members available for assignment (one name per row).

### `sample_projects.csv`
```csv
name
Project Alpha
Project Beta
Project Gamma
```

List of all active projects requiring teams (one name per row).

The sample_members.csv and sample_projects.csv files are entirely fake, having been created by Anthropic Claude. No relation to real people is intended or expected

## Running the Script

```bash
python3 pilime_method.py
```

The script will:
1. Read `sample_members.csv` and `sample_projects.csv`
2. Generate a 4-quarter circulation schedule
3. Display constraint verification results
4. Output a Markdown table to `team_schedule.md`

## Output

The `team_schedule.md` file contains a table showing:
- **Quarter**: Which quarter (Q1-Q4)
- **Project**: Project name
- **Team Members**: People assigned to that project
- **Leader**: The designated leader for that quarter

Example output:
```markdown
## Quarter 1

| Project | Team Members | Leader |
|---------|--------------|--------|
| Project Alpha | Alice, Bob, Carol, David, Emma | Alice |
| Project Beta | Frank, Grace, Henry | Henry |
```

## Customization

To modify the script, you can adjust:

- **Number of quarters**: Change `quarters=4` in the `TeamCirculation` initialization
- **Team size range**: Modify `team_size_min` and `team_size_max` (default: 3-5)
- **Max concurrent projects**: Adjust `max_projects_per_person` in `_assign_people_to_project()` (default: 3)
- **Input file names**: Change the filenames in the `main()` function

## Example

Run with the included sample data to generate a schedule for 8 team members and 4 projects:

```bash
python3 pilime_method.py
```

Output shows all 16 assignments (4 projects × 4 quarters) with team members and leaders balanced across the year.

## Requirements

- Python 3.7+
- No external dependencies required

## Verification

The script automatically verifies:
- ✓ Each person leads at least 2 projects per year
- ✓ Each project has 3-5 team members per quarter
- ✓ Team members rotate appropriately
- ✓ Leadership is balanced across the team
