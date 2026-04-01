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
5. Aims for each person to **lead at least 2 projects per year**

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
python3 pilime_method.py [options]
```

### Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--quarters N` | `-q N` | `4` | Number of quarters to schedule |
| `--seed-leaders FILE` | `-s FILE` | _(none)_ | CSV file of last quarter's project leaders, used to seed Q1 continuity |

### Examples

Default run — four quarters, no seed data:
```bash
python3 pilime_method.py
```

Schedule two quarters:
```bash
python3 pilime_method.py --quarters 2
```

Schedule eight quarters using last quarter's leaders for continuity:
```bash
python3 pilime_method.py --quarters 8 --seed-leaders last_quarter_leaders.csv
```

The script will:
1. Read `members.csv` and `projects.csv`
2. Optionally load seed leaders from `--seed-leaders FILE`
3. Generate the requested number of quarters of assignments
4. Display a constraint verification summary
5. Output a Markdown table to `team_schedule.md`

## Seed Leaders File

To carry forward the leaders from a previous run into Q1 of the new schedule, provide a CSV file with `project` and `leader` columns:

```csv
project,leader
Project Alpha,Alice Adams
Project Beta,Bob Brown
Project Gamma,Carol Chen
```

Each named leader is treated as the sole returning member of their project team when building Q1 assignments, giving them continuity priority. Leaders not found in `members.csv` are silently ignored.

A sample file `last_quarter_leaders.csv` is included for reference.

## Output

The `team_schedule.md` file contains a table showing:
- **Quarter**: Which quarter (Q1–QN)
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

When using initials, a `## Key` section is automatically added at the end of the document showing the mapping of initials to full names.

## Customisation

Adjust parameters when constructing `TeamCirculation` in the script:

```python
circulation = TeamCirculation(
    members=members,
    projects=projects,
    quarters=4,              # Number of quarters to plan (default: 4)
    team_size_min=3,         # Minimum team size per project (default: 3)
    team_size_max=5,         # Maximum team size per project (default: 5)
    use_initials=False,      # Use initials instead of full names (default: False)
    seed_leaders={},         # Dict mapping project → last-quarter leader (default: {})
)
```

### Parameter Details

- **`quarters`**: Number of quarters to plan (e.g., `4` for one year, `8` for two years). Also settable via `--quarters` on the command line.
- **`team_size_min` / `team_size_max`**: Adjusts the range of people per project team.
- **`use_initials`**: When `True`, displays initials (e.g., `"Alice Brown"` → `"AB"`) in the output table.
- **`seed_leaders`**: A `{project: leader}` dict pre-populating Q1 continuity. Populated automatically when `--seed-leaders FILE` is passed on the command line.
- **Max concurrent projects**: Automatically calculated from the number of people and projects to ensure fair workload distribution (minimum 2).
- **Input file names**: Change the filenames in the `main()` function if using different file names.

### Using Initials via a Custom Script

```python
from pilime_method import read_csv, TeamCirculation

members = read_csv("members.csv", "name")
projects = read_csv("projects.csv", "name")

circulation = TeamCirculation(
    members=members,
    projects=projects,
    quarters=4,
    use_initials=True,
)
circulation.generate_schedule()

markdown = circulation.generate_markdown_table()
with open("team_schedule.md", "w") as f:
    f.write(markdown)
```

### Using Seed Leaders via a Custom Script

```python
from pilime_method import read_csv, read_seed_leaders, TeamCirculation

members = read_csv("members.csv", "name")
projects = read_csv("projects.csv", "name")
seed = read_seed_leaders("last_quarter_leaders.csv")

circulation = TeamCirculation(
    members=members,
    projects=projects,
    quarters=4,
    seed_leaders=seed,
)
circulation.generate_schedule()

markdown = circulation.generate_markdown_table()
with open("team_schedule.md", "w") as f:
    f.write(markdown)
```

## Requirements

- Python 3.7+
- No external dependencies required

## Verification

After generating the schedule, the script prints a constraint summary:
- Leadership assignments per person
- Leadership range (min to max across the team)
- ✓ / ⚠️ status for every project team size

Programmatic access to the same data is available via `_verify_constraints()`, which returns a dict:

```python
constraints = circulation._verify_constraints()
# {
#   "min_leadership": int,
#   "max_leadership": int,
#   "leadership_per_member": {"Alice Adams": 3, ...},
#   "team_size_violations": [(quarter_index, project, actual_size), ...],
# }
```
