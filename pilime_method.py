#!/usr/bin/env python3
"""
Pilime Method - Team Rotation Scheduler

This script implements the Pilime Method for creating temporary work teams across projects,
ensuring knowledge distribution and continuity of expertise.
"""

import argparse
import csv
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from collections import defaultdict


@dataclass
class Assignment:
    """Represents a person's assignment to a project in a quarter."""
    person: str
    project: str
    is_leader: bool


@dataclass
class TeamCirculation:
    """Manages team circulation across quarters."""
    members: List[str]
    projects: List[str]
    quarters: int = 4
    team_size_min: int = 3
    team_size_max: int = 5
    use_initials: bool = False
    seed_leaders: Dict[str, str] = field(default_factory=dict)

    # Tracking data
    assignments: Dict[int, List[Assignment]] = field(default_factory=dict)
    leadership_count: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    project_teams: Dict[Tuple[int, str], List[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the circulation tracker."""
        for member in self.members:
            self.leadership_count[member] = 0

        # Precompute: max projects any one person may work on in a quarter.
        # Depends only on fixed constructor args so it never changes.
        avg_team_size = (self.team_size_min + self.team_size_max) // 2
        total_slots = len(self.projects) * avg_team_size
        self._max_projects_per_person: int = max(
            2, -(-total_slots // len(self.members))  # ceiling division
        )
    
    def _get_display_name(self, person: str) -> str:
        """Get the display name for a person (full name or initials)."""
        if not self.use_initials:
            return person
        
        parts = person.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}"
        elif len(parts) == 1:
            return parts[0][0]
        return person
    
    def _get_team_size(self) -> int:
        """Get a random team size between min and max."""
        return random.randint(self.team_size_min, self.team_size_max)
    
    def _select_leader(self, candidates: List[str]) -> str:
        """
        Select a leader from candidates, prioritizing those with fewer leadership roles.
        Uses a single O(n) pass rather than sorting.
        """
        if not candidates:
            raise ValueError("Cannot select leader from empty candidates list")

        min_count = min(self.leadership_count[c] for c in candidates)
        eligible = [c for c in candidates if self.leadership_count[c] == min_count]
        return random.choice(eligible)
    
    def _get_previous_team(self, quarter: int, project: str) -> Set[str]:
        """Get the team members from the previous quarter for a project."""
        if quarter == 0:
            leader = self.seed_leaders.get(project)
            if leader and leader in self.members:
                return {leader}
            return set()
        # Convert to set; callers sort before iterating for determinism.
        return set(self.project_teams.get((quarter - 1, project), []))
    
    def _assign_people_to_project(self, quarter: int, project: str, assigned_this_quarter: Dict[str, int]) -> List[str]:
        """
        Assign people to a project in a given quarter.
        
        People can work on multiple projects, but we balance workload.
        Strategy:
        - Keep some members from the previous quarter for continuity
        - Prefer people with lighter workloads this quarter
        - Mix new and continuing members
        """
        team_size = self._get_team_size()
        previous_team = self._get_previous_team(quarter, project)

        team: List[str] = []
        team_set: Set[str] = set()  # O(1) membership checks

        # Prefer to keep some previous team members (sorted for determinism).
        for member in sorted(previous_team):
            if len(team) < max(1, team_size // 2):  # Keep ~half from previous team
                team.append(member)
                team_set.add(member)

        # Fill remaining slots using the precomputed per-person project cap.
        candidates = [
            m for m in self.members
            if m not in team_set
            and assigned_this_quarter.get(m, 0) < self._max_projects_per_person
        ]

        # Prefer people with lighter workloads
        candidates.sort(key=lambda x: assigned_this_quarter.get(x, 0))

        idx = 0
        while len(team) < team_size and idx < len(candidates):
            team.append(candidates[idx])
            idx += 1

        return team[:team_size]
    
    def generate_schedule(self) -> None:
        """Generate the team assignments for all quarters."""
        random.seed(42)  # For reproducibility
        
        for quarter in range(self.quarters):
            self.assignments[quarter] = []
            workload_this_quarter = defaultdict(int)  # Track projects per person
            
            for project in self.projects:
                # Assign team to project
                team = self._assign_people_to_project(quarter, project, workload_this_quarter)
                
                # Update workload tracking
                for person in team:
                    workload_this_quarter[person] += 1
                
                self.project_teams[(quarter, project)] = team
                
                # Select leader from the team
                if team:
                    leader = self._select_leader(team)
                    self.leadership_count[leader] += 1
                    
                    # Create assignments
                    for person in team:
                        is_leader = person == leader
                        assignment = Assignment(person, project, is_leader)
                        self.assignments[quarter].append(assignment)
        
    def _verify_constraints(self) -> dict:
        """
        Verify constraints and return a summary dict — does not print anything.

        Returns:
            {
                "min_leadership": int,
                "max_leadership": int,
                "leadership_per_member": {member: count, ...},
                "team_size_violations": [(quarter, project, actual_size), ...],
            }
        """
        leadership_per_member = {
            m: self.leadership_count[m] for m in sorted(self.members)
        }
        counts = list(leadership_per_member.values())
        min_leadership = min(counts)
        max_leadership = max(counts)

        violations = []
        for quarter in range(self.quarters):
            for project in self.projects:
                size = len(self.project_teams.get((quarter, project), []))
                if size < self.team_size_min or size > self.team_size_max:
                    violations.append((quarter, project, size))

        return {
            "min_leadership": min_leadership,
            "max_leadership": max_leadership,
            "leadership_per_member": leadership_per_member,
            "team_size_violations": violations,
        }
    
    def generate_markdown_table(self) -> str:
        """Generate a Markdown table showing all assignments."""
        output = []
        output.append("# Pilime Method - Team Circulation Schedule\n")
        
        for quarter in range(self.quarters):
            output.append(f"## Quarter {quarter + 1}\n")
            output.append("| Project | Team Members | Leader |")
            output.append("|---------|--------------|--------|")
            
            # Build O(1) leader lookup for this quarter up front.
            leader_by_project = {
                a.project: a.person
                for a in self.assignments[quarter]
                if a.is_leader
            }

            for project in self.projects:
                team = self.project_teams.get((quarter, project), [])
                leader = leader_by_project.get(project, "—")
                
                # Apply display name formatting
                team_display = ", ".join(self._get_display_name(member) for member in team)
                leader_display = self._get_display_name(leader) if leader != "—" else "—"
                
                output.append(f"| {project} | {team_display} | {leader_display} |")
            
            output.append("")
        
        # Add key if using initials
        if self.use_initials:
            output.append("## Key\n")
            for member in sorted(self.members):
                initials = self._get_display_name(member)
                output.append(f"- {initials}: {member}")
        
        return "\n".join(output)


def read_csv(filename: str, column: str = "name") -> List[str]:
    """Read a CSV file and extract a list of values from a column."""
    values = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if column in row:
                    values.append(row[column].strip())
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading '{filename}': {e}")
        exit(1)
    return values


def read_seed_leaders(filename: str) -> Dict[str, str]:
    """Read a CSV file mapping project names to their last-quarter leaders.

    Expected format (with header row):
        project,leader
        Project Alpha,Alice Adams
    """
    result = {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "project" in row and "leader" in row:
                    project = row["project"].strip()
                    leader = row["leader"].strip()
                    if project and leader:
                        result[project] = leader
    except FileNotFoundError:
        print(f"Error: Seed leaders file '{filename}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading seed leaders file '{filename}': {e}")
        exit(1)
    return result


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Pilime Method - Team Rotation Scheduler")
    parser.add_argument(
        "-q", "--quarters",
        type=int,
        default=4,
        help="Number of quarters to schedule (default: 4)",
    )
    parser.add_argument(
        "-s", "--seed-leaders",
        default=None,
        metavar="FILE",
        help="CSV file mapping projects to their last-quarter leaders for Q1 continuity",
    )

    args = parser.parse_args(argv)
    if args.quarters < 1:
        parser.error("--quarters must be a positive integer")
    return args


def main():
    """Main entry point."""
    args = parse_args()

    # Read input files
    members = read_csv("members.csv", "name")
    projects = read_csv("projects.csv", "name")
    
    if not members:
        print("Error: No team members found in members.csv")
        exit(1)
    if not projects:
        print("Error: No projects found in projects.csv")
        exit(1)
    
    print(f"Team Members ({len(members)}): {', '.join(members)}")
    print(f"Projects ({len(projects)}): {', '.join(projects)}")
    print()
    
    # Load optional seed leaders
    seed_leaders = {}
    if args.seed_leaders:
        seed_leaders = read_seed_leaders(args.seed_leaders)
        print(f"Seed leaders loaded: {seed_leaders}")

    # Generate schedule
    # Set use_initials=True to display initials instead of full names
    circulation = TeamCirculation(
        members, projects, quarters=args.quarters, use_initials=False,
        seed_leaders=seed_leaders,
    )
    circulation.generate_schedule()
    
    # Print verification
    print("\n" + "=" * 50)
    constraints = circulation._verify_constraints()
    print("Constraint Verification:")
    print("-" * 50)
    print("\nLeadership assignments per person:")
    for member, count in constraints["leadership_per_member"].items():
        print(f"  {member}: {count} projects")
    print(f"\nLeadership range: {constraints['min_leadership']} to {constraints['max_leadership']}")
    if constraints["min_leadership"] < 2:
        print("⚠️  Warning: Some people lead fewer than 2 projects per year")
    else:
        print("✓ All people lead at least 2 projects per year")
    print("\nTeam sizes:")
    violation_set = {(q, p) for q, p, _ in constraints["team_size_violations"]}
    for quarter in range(circulation.quarters):
        for project in circulation.projects:
            size = len(circulation.project_teams.get((quarter, project), []))
            if (quarter, project) in violation_set:
                print(f"  ⚠️  Q{quarter + 1} {project}: {size} people "
                      f"(expected {circulation.team_size_min}-{circulation.team_size_max})")
            else:
                print(f"  ✓ Q{quarter + 1} {project}: {size} people")
    
    # Generate and save markdown
    print("\n" + "=" * 50)
    markdown = circulation.generate_markdown_table()
    
    with open("team_schedule.md", "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print("\n✓ Schedule generated and saved to team_schedule.md")
    print("\nPreview:")
    print("=" * 50)
    print(markdown)


if __name__ == "__main__":
    main()
