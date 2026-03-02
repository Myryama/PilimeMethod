#!/usr/bin/env python3
"""
Pilime Method - Team Rotation Scheduler

This script implements the Pilime Method for creating temporary work teams across projects,
ensuring knowledge distribution and continuity of expertise.
"""

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
    
    # Tracking data
    assignments: Dict[int, List[Assignment]] = field(default_factory=dict)
    leadership_count: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    project_teams: Dict[Tuple[int, str], List[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the circulation tracker."""
        for member in self.members:
            self.leadership_count[member] = 0
    
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
        """
        if not candidates:
            raise ValueError("Cannot select leader from empty candidates list")
        
        # Sort by leadership count (ascending) and randomize within same count
        candidates_sorted = sorted(candidates, key=lambda x: self.leadership_count[x])
        min_count = self.leadership_count[candidates_sorted[0]]
        eligible = [c for c in candidates_sorted if self.leadership_count[c] == min_count]
        return random.choice(eligible)
    
    def _get_previous_team(self, quarter: int, project: str) -> Set[str]:
        """Get the team members from the previous quarter for a project."""
        if quarter == 0:
            return set()
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
        
        team = []
        
        # Prefer to keep some previous team members (but allow new ones too)
        for member in previous_team:
            if len(team) < max(1, team_size // 2):  # Keep ~half from previous team
                team.append(member)
        
        # Fill remaining slots, balancing workload
        # Calculate max projects per person based on team and project sizes
        avg_team_size = (self.team_size_min + self.team_size_max) // 2
        total_slots_needed = len(self.projects) * avg_team_size
        max_projects_per_person = max(2, -(-total_slots_needed // len(self.members)))  # Ceiling division
        
        candidates = [
            m for m in self.members 
            if m not in team and assigned_this_quarter.get(m, 0) < max_projects_per_person
        ]
        
        # Prefer people with lighter workloads
        candidates.sort(key=lambda x: assigned_this_quarter.get(x, 0))
        
        while len(team) < team_size and candidates:
            person = candidates.pop(0)
            team.append(person)
        
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
        
        # Verify constraints
        self._verify_constraints()
    
    def _verify_constraints(self) -> None:
        """Verify that all constraints are met."""
        print("Constraint Verification:")
        print("-" * 50)
        
        # Check leadership distribution
        print("\nLeadership assignments per person:")
        for member in sorted(self.members):
            count = self.leadership_count[member]
            print(f"  {member}: {count} projects")
        
        # Check that each person leads at least 2 projects per year (if possible)
        min_leadership = min(self.leadership_count.values())
        max_leadership = max(self.leadership_count.values())
        print(f"\nLeadership range: {min_leadership} to {max_leadership}")
        
        if min_leadership < 2:
            print(f"⚠️  Warning: Some people lead fewer than 2 projects per year")
        else:
            print(f"✓ All people lead at least 2 projects per year")
        
        # Check team sizes
        print("\nTeam sizes:")
        for quarter in range(self.quarters):
            for project in self.projects:
                team_size = len(self.project_teams.get((quarter, project), []))
                if team_size < self.team_size_min or team_size > self.team_size_max:
                    print(f"  ⚠️  Q{quarter + 1} {project}: {team_size} people (expected {self.team_size_min}-{self.team_size_max})")
                else:
                    print(f"  ✓ Q{quarter + 1} {project}: {team_size} people")
    
    def generate_markdown_table(self) -> str:
        """Generate a Markdown table showing all assignments."""
        output = []
        output.append("# Pilime Method - Team Circulation Schedule\n")
        
        for quarter in range(self.quarters):
            output.append(f"## Quarter {quarter + 1}\n")
            output.append("| Project | Team Members | Leader |")
            output.append("|---------|--------------|--------|")
            
            for project in self.projects:
                team = self.project_teams.get((quarter, project), [])
                leader = next((a.person for a in self.assignments[quarter] 
                             if a.project == project and a.is_leader), "—")
                
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


def main():
    """Main entry point."""
    # Read input files
    members = read_csv("members.csv", "name")
    projects = read_csv("projects.csv", "name")
    
    if not members:
        print("Error: No team members found in sample_members.csv")
        exit(1)
    if not projects:
        print("Error: No projects found in sample_projects.csv")
        exit(1)
    
    print(f"Team Members ({len(members)}): {', '.join(members)}")
    print(f"Projects ({len(projects)}): {', '.join(projects)}")
    print()
    
    # Generate schedule
    # Set use_initials=True to display initials instead of full names
    circulation = TeamCirculation(members, projects, quarters=4, use_initials=True)
    circulation.generate_schedule()
    
    # Print verification
    print("\n" + "=" * 50)
    circulation._verify_constraints()
    
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
