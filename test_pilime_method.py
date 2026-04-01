"""
Tests for pilime_method.py — written with red/green TDD.
Each test targets a specific behaviour described in the README.
"""
import csv
import os
import sys
import tempfile
import pytest
from collections import defaultdict
from unittest.mock import patch

from pilime_method import Assignment, TeamCirculation, read_csv, read_seed_leaders, parse_args


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MEMBERS = [
    "Alice Adams",
    "Bob Brown",
    "Carol Chen",
    "David Diaz",
    "Emma Evans",
    "Frank Ford",
    "Grace Green",
    "Henry Hall",
]

PROJECTS = ["Project Alpha", "Project Beta", "Project Gamma"]


@pytest.fixture
def circulation():
    tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=4)
    tc.generate_schedule()
    return tc


@pytest.fixture
def circulation_initials():
    tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=4, use_initials=True)
    tc.generate_schedule()
    return tc


# ---------------------------------------------------------------------------
# Team size constraints (README: "3-5 people per project per quarter")
# ---------------------------------------------------------------------------

class TestTeamSizeConstraints:
    def test_every_project_team_has_at_least_min_members(self, circulation):
        for quarter in range(circulation.quarters):
            for project in circulation.projects:
                team = circulation.project_teams[(quarter, project)]
                assert len(team) >= circulation.team_size_min, (
                    f"Q{quarter+1} '{project}' has only {len(team)} members "
                    f"(min {circulation.team_size_min})"
                )

    def test_every_project_team_has_at_most_max_members(self, circulation):
        for quarter in range(circulation.quarters):
            for project in circulation.projects:
                team = circulation.project_teams[(quarter, project)]
                assert len(team) <= circulation.team_size_max, (
                    f"Q{quarter+1} '{project}' has {len(team)} members "
                    f"(max {circulation.team_size_max})"
                )

    def test_custom_team_size_bounds_respected(self):
        tc = TeamCirculation(
            members=MEMBERS, projects=PROJECTS, quarters=2,
            team_size_min=2, team_size_max=3,
        )
        tc.generate_schedule()
        for quarter in range(tc.quarters):
            for project in tc.projects:
                team = tc.project_teams[(quarter, project)]
                assert 2 <= len(team) <= 3


# ---------------------------------------------------------------------------
# Leadership constraints
# ---------------------------------------------------------------------------

class TestLeadershipConstraints:
    def test_each_project_has_exactly_one_leader_per_quarter(self, circulation):
        for quarter in range(circulation.quarters):
            for project in circulation.projects:
                leaders = [
                    a for a in circulation.assignments[quarter]
                    if a.project == project and a.is_leader
                ]
                assert len(leaders) == 1, (
                    f"Q{quarter+1} '{project}' has {len(leaders)} leaders (expected 1)"
                )

    def test_leader_is_always_a_member_of_the_team(self, circulation):
        for quarter in range(circulation.quarters):
            for project in circulation.projects:
                team = set(circulation.project_teams[(quarter, project)])
                leader_assignment = next(
                    a for a in circulation.assignments[quarter]
                    if a.project == project and a.is_leader
                )
                assert leader_assignment.person in team, (
                    f"Leader {leader_assignment.person!r} is not in the team for "
                    f"Q{quarter+1} '{project}'"
                )

    def test_leadership_count_tracks_total_lead_roles(self, circulation):
        """leadership_count[member] == number of times they led any project."""
        expected = defaultdict(int)
        for quarter in range(circulation.quarters):
            for assignment in circulation.assignments[quarter]:
                if assignment.is_leader:
                    expected[assignment.person] += 1
        for member in MEMBERS:
            assert circulation.leadership_count[member] == expected[member]

    def test_select_leader_prefers_member_with_fewest_prior_leads(self):
        """_select_leader always picks from the lowest leadership-count group."""
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS)
        # Artificially inflate counts for all but one member
        for m in MEMBERS[1:]:
            tc.leadership_count[m] = 5
        tc.leadership_count[MEMBERS[0]] = 0
        # Run many times to check randomness doesn't pick a high-count member
        for _ in range(20):
            chosen = tc._select_leader(MEMBERS)
            assert chosen == MEMBERS[0]

    def test_select_leader_raises_on_empty_candidates(self):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS)
        with pytest.raises(ValueError):
            tc._select_leader([])


# ---------------------------------------------------------------------------
# All projects scheduled in every quarter
# ---------------------------------------------------------------------------

class TestScheduleCoverage:
    def test_all_projects_have_assignments_every_quarter(self, circulation):
        for quarter in range(circulation.quarters):
            assigned_projects = {a.project for a in circulation.assignments[quarter]}
            assert set(circulation.projects) == assigned_projects

    def test_assignments_dict_has_entry_for_every_quarter(self, circulation):
        assert set(circulation.assignments.keys()) == set(range(circulation.quarters))


# ---------------------------------------------------------------------------
# Continuity — some previous-quarter members are retained
# ---------------------------------------------------------------------------

class TestContinuity:
    def test_at_least_one_member_retained_from_previous_quarter(self, circulation):
        """From Q2 onward, each project team shares at least one member with the prior team."""
        for quarter in range(1, circulation.quarters):
            for project in circulation.projects:
                current = set(circulation.project_teams[(quarter, project)])
                previous = set(circulation.project_teams[(quarter - 1, project)])
                overlap = current & previous
                assert len(overlap) >= 1, (
                    f"Q{quarter+1} '{project}' shares no members with Q{quarter} team"
                )


# ---------------------------------------------------------------------------
# Display name formatting
# ---------------------------------------------------------------------------

class TestDisplayNames:
    def test_full_name_returned_when_initials_disabled(self):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, use_initials=False)
        assert tc._get_display_name("Alice Adams") == "Alice Adams"

    def test_initials_returned_for_two_part_name(self):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, use_initials=True)
        assert tc._get_display_name("Alice Adams") == "AA"

    def test_initials_returned_for_three_part_name(self):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, use_initials=True)
        # Only first two parts contribute to the two-letter initial
        assert tc._get_display_name("Alice Beth Chen") == "AB"

    def test_single_word_name_returns_first_letter(self):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, use_initials=True)
        assert tc._get_display_name("Alice") == "A"


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

class TestMarkdownOutput:
    def test_markdown_contains_header(self, circulation):
        md = circulation.generate_markdown_table()
        assert "# Pilime Method - Team Circulation Schedule" in md

    def test_markdown_contains_all_quarter_headings(self, circulation):
        md = circulation.generate_markdown_table()
        for q in range(1, circulation.quarters + 1):
            assert f"## Quarter {q}" in md

    def test_markdown_contains_all_project_names(self, circulation):
        md = circulation.generate_markdown_table()
        for project in PROJECTS:
            assert project in md

    def test_markdown_table_rows_include_leader(self, circulation):
        """Every data row must contain a non-empty leader cell."""
        md = circulation.generate_markdown_table()
        for line in md.splitlines():
            if line.startswith("|") and not line.startswith("| Project") and "-----" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) == 3:
                    _project, _team, leader = parts
                    assert leader and leader != "—", (
                        f"Missing leader in row: {line}"
                    )

    def test_markdown_no_key_section_without_initials(self, circulation):
        md = circulation.generate_markdown_table()
        assert "## Key" not in md

    def test_markdown_key_section_present_with_initials(self, circulation_initials):
        md = circulation_initials.generate_markdown_table()
        assert "## Key" in md

    def test_markdown_key_lists_all_members(self, circulation_initials):
        md = circulation_initials.generate_markdown_table()
        for member in MEMBERS:
            assert member in md  # full name must appear in the key

    def test_markdown_initials_used_in_team_column(self, circulation_initials):
        md = circulation_initials.generate_markdown_table()
        # Full names should NOT appear in table rows (only in Key section)
        lines_before_key = md.split("## Key")[0].splitlines()
        data_lines = [
            l for l in lines_before_key
            if l.startswith("|") and "-----" not in l and not l.startswith("| Project")
        ]
        for line in data_lines:
            for member in MEMBERS:
                assert member not in line, (
                    f"Full name {member!r} found in data row when initials expected: {line}"
                )


# ---------------------------------------------------------------------------
# read_csv helper
# ---------------------------------------------------------------------------

class TestReadCsv:
    def _make_csv(self, rows: list[str]) -> str:
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name"])
            for row in rows:
                writer.writerow([row])
        return path

    def test_reads_names_from_csv(self):
        path = self._make_csv(["Alice", "Bob", "Carol"])
        try:
            result = read_csv(path, "name")
            assert result == ["Alice", "Bob", "Carol"]
        finally:
            os.unlink(path)

    def test_strips_whitespace_from_values(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("name\n  Alice  \n Bob \n")
        try:
            result = read_csv(path, "name")
            assert result == ["Alice", "Bob"]
        finally:
            os.unlink(path)

    def test_missing_column_returns_empty_list(self):
        path = self._make_csv(["Alice", "Bob"])
        try:
            result = read_csv(path, "nonexistent_column")
            assert result == []
        finally:
            os.unlink(path)

    def test_file_not_found_exits(self):
        with pytest.raises(SystemExit):
            read_csv("/nonexistent/path/to/file.csv", "name")


# ---------------------------------------------------------------------------
# Reproducibility (fixed seed)
# ---------------------------------------------------------------------------

class TestReproducibility:
    def test_same_seed_produces_identical_schedule(self):
        tc1 = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=4)
        tc2 = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=4)
        tc1.generate_schedule()
        tc2.generate_schedule()
        assert tc1.project_teams == tc2.project_teams
        assert tc1.leadership_count == tc2.leadership_count


# ---------------------------------------------------------------------------
# Variable quarters — CLI argument parsing
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_default_quarters_is_4(self):
        args = parse_args([])
        assert args.quarters == 4

    def test_quarters_flag_sets_value(self):
        args = parse_args(["--quarters", "6"])
        assert args.quarters == 6

    def test_quarters_short_flag(self):
        args = parse_args(["-q", "2"])
        assert args.quarters == 2

    def test_quarters_must_be_positive(self):
        with pytest.raises(SystemExit):
            parse_args(["--quarters", "0"])

    def test_quarters_must_be_integer(self):
        with pytest.raises(SystemExit):
            parse_args(["--quarters", "four"])


class TestVariableQuarters:
    def test_schedule_has_correct_number_of_quarters(self):
        for n in (1, 2, 6, 8):
            tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=n)
            tc.generate_schedule()
            assert len(tc.assignments) == n

    def test_markdown_has_correct_number_of_quarter_headings(self):
        for n in (1, 3, 6):
            tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=n)
            tc.generate_schedule()
            md = tc.generate_markdown_table()
            for q in range(1, n + 1):
                assert f"## Quarter {q}" in md
            assert f"## Quarter {n + 1}" not in md

    def test_main_uses_quarters_from_cli(self, tmp_path):
        """main() reads --quarters and generates the right number of quarters."""
        members_file = tmp_path / "members.csv"
        projects_file = tmp_path / "projects.csv"
        members_file.write_text("name\n" + "\n".join(MEMBERS))
        projects_file.write_text("name\n" + "\n".join(PROJECTS))

        captured_quarters = {}

        original_init = TeamCirculation.__init__

        def mock_init(self, *args, **kwargs):
            captured_quarters["quarters"] = kwargs.get("quarters", args[2] if len(args) > 2 else 4)
            original_init(self, *args, **kwargs)

        from pilime_method import main
        with patch("pilime_method.TeamCirculation.__init__", mock_init), \
             patch("pilime_method.read_csv", side_effect=[MEMBERS, PROJECTS]), \
             patch("builtins.open", side_effect=lambda *a, **kw: tempfile.NamedTemporaryFile(
                 mode="w", suffix=".md", delete=False
             )), \
             patch("sys.argv", ["pilime_method.py", "--quarters", "6"]):
            try:
                main()
            except Exception:
                pass  # We only care that TeamCirculation was called with quarters=6

        assert captured_quarters.get("quarters") == 6


# ---------------------------------------------------------------------------
# Seed leaders — loading prior-quarter leaders from a file
# ---------------------------------------------------------------------------

def _write_seed_csv(tmp_path, rows: list[tuple[str, str]]) -> str:
    """Helper: write a seed-leaders CSV and return its path."""
    path = tmp_path / "seed_leaders.csv"
    path.write_text("project,leader\n" + "\n".join(f"{p},{l}" for p, l in rows))
    return str(path)


class TestReadSeedLeaders:
    def test_returns_project_to_leader_mapping(self, tmp_path):
        path = _write_seed_csv(tmp_path, [
            ("Project Alpha", "Alice Adams"),
            ("Project Beta", "Bob Brown"),
        ])
        result = read_seed_leaders(path)
        assert result == {"Project Alpha": "Alice Adams", "Project Beta": "Bob Brown"}

    def test_strips_whitespace(self, tmp_path):
        path = tmp_path / "seed.csv"
        path.write_text("project,leader\n  Project Alpha  ,  Alice Adams  \n")
        result = read_seed_leaders(str(path))
        assert result == {"Project Alpha": "Alice Adams"}

    def test_empty_file_returns_empty_dict(self, tmp_path):
        path = tmp_path / "seed.csv"
        path.write_text("project,leader\n")
        result = read_seed_leaders(str(path))
        assert result == {}

    def test_missing_file_raises_system_exit(self):
        with pytest.raises(SystemExit):
            read_seed_leaders("/nonexistent/seed_leaders.csv")

    def test_rows_missing_leader_column_are_skipped(self, tmp_path):
        path = tmp_path / "seed.csv"
        path.write_text("project,other_col\nProject Alpha,something\n")
        result = read_seed_leaders(str(path))
        assert result == {}


class TestSeedLeadersIntegration:
    def test_seed_leader_is_included_in_q1_team(self, tmp_path):
        """A person named as last quarter's leader should appear in Q1's team."""
        seed = {"Project Alpha": "Alice Adams"}
        tc = TeamCirculation(
            members=MEMBERS, projects=PROJECTS, quarters=1,
            seed_leaders=seed,
        )
        tc.generate_schedule()
        q1_team = tc.project_teams[(0, "Project Alpha")]
        assert "Alice Adams" in q1_team

    def test_no_seed_leaders_behaviour_unchanged(self):
        """Without seed data, Q1 previous-team is empty (original behaviour)."""
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=1)
        assert tc._get_previous_team(0, "Project Alpha") == set()

    def test_seed_leader_treated_as_sole_prior_team_member(self):
        """_get_previous_team for Q1 (quarter index 0) returns the seed leader."""
        seed = {"Project Alpha": "Bob Brown", "Project Beta": "Carol Chen"}
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, seed_leaders=seed)
        assert tc._get_previous_team(0, "Project Alpha") == {"Bob Brown"}
        assert tc._get_previous_team(0, "Project Beta") == {"Carol Chen"}

    def test_project_without_seed_entry_still_gets_empty_prior_team(self):
        seed = {"Project Alpha": "Alice Adams"}
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, seed_leaders=seed)
        assert tc._get_previous_team(0, "Project Beta") == set()

    def test_q2_plus_continuity_unaffected_by_seed(self):
        """Seed only influences Q1; Q2 onward uses the normal generated history."""
        seed = {"Project Alpha": "Alice Adams"}
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=3, seed_leaders=seed)
        tc.generate_schedule()
        for quarter in range(1, 3):
            previous = set(tc.project_teams[(quarter - 1, "Project Alpha")])
            assert tc._get_previous_team(quarter, "Project Alpha") == previous

    def test_seed_leader_not_in_members_list_is_excluded_from_team(self):
        """A seed leader who isn't in members cannot be added to the team."""
        seed = {"Project Alpha": "Unknown Person"}
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=1, seed_leaders=seed)
        tc.generate_schedule()
        q1_team = tc.project_teams[(0, "Project Alpha")]
        assert "Unknown Person" not in q1_team


class TestSeedLeadersCLI:
    def test_seed_leaders_flag_default_is_none(self):
        args = parse_args([])
        assert args.seed_leaders is None

    def test_seed_leaders_long_flag(self, tmp_path):
        path = _write_seed_csv(tmp_path, [("Project Alpha", "Alice Adams")])
        args = parse_args(["--seed-leaders", path])
        assert args.seed_leaders == path

    def test_seed_leaders_short_flag(self, tmp_path):
        path = _write_seed_csv(tmp_path, [("Project Alpha", "Alice Adams")])
        args = parse_args(["-s", path])
        assert args.seed_leaders == path


# ---------------------------------------------------------------------------
# Optimisation tests
# ---------------------------------------------------------------------------

class TestGenerateScheduleSideEffects:
    def test_generate_schedule_produces_no_stdout(self, capsys):
        """generate_schedule() must not print anything — side effects belong to the caller."""
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=2)
        tc.generate_schedule()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_generate_schedule_produces_no_stderr(self, capsys):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS, quarters=2)
        tc.generate_schedule()
        captured = capsys.readouterr()
        assert captured.err == ""


class TestVerifyConstraintsReturnsData:
    def test_verify_constraints_returns_dict_not_none(self, circulation):
        result = circulation._verify_constraints()
        assert result is not None

    def test_verify_constraints_result_has_min_leadership(self, circulation):
        result = circulation._verify_constraints()
        assert "min_leadership" in result

    def test_verify_constraints_result_has_max_leadership(self, circulation):
        result = circulation._verify_constraints()
        assert "max_leadership" in result

    def test_verify_constraints_result_has_team_size_violations(self, circulation):
        result = circulation._verify_constraints()
        assert "team_size_violations" in result

    def test_verify_constraints_min_max_values_are_correct(self, circulation):
        result = circulation._verify_constraints()
        counts = list(circulation.leadership_count.values())
        assert result["min_leadership"] == min(counts)
        assert result["max_leadership"] == max(counts)

    def test_verify_constraints_no_violations_when_constraints_met(self, circulation):
        result = circulation._verify_constraints()
        assert result["team_size_violations"] == []

    def test_verify_constraints_produces_no_stdout(self, circulation, capsys):
        """_verify_constraints must not print — callers decide what to display."""
        circulation._verify_constraints()
        captured = capsys.readouterr()
        assert captured.out == ""


class TestMaxProjectsPerPersonCached:
    def test_max_projects_per_person_attribute_exists(self):
        """Should be precomputed at init, not recalculated on every assignment call."""
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS)
        assert hasattr(tc, "_max_projects_per_person")

    def test_max_projects_per_person_value_is_correct(self):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS,
                             team_size_min=3, team_size_max=5)
        avg_team_size = (3 + 5) // 2  # 4
        total_slots = len(PROJECTS) * avg_team_size  # 3 * 4 = 12
        expected = max(2, -(-total_slots // len(MEMBERS)))  # ceil(12/8) = 2
        assert tc._max_projects_per_person == expected

    def test_max_projects_per_person_unchanged_after_generate(self):
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS)
        before = tc._max_projects_per_person
        tc.generate_schedule()
        assert tc._max_projects_per_person == before


class TestSelectLeaderEfficiency:
    def test_select_leader_never_picks_higher_count_when_lower_exists(self):
        """Correctness property — holds regardless of whether sort or min() is used."""
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS)
        tc.leadership_count["Alice Adams"] = 0
        for m in MEMBERS[1:]:
            tc.leadership_count[m] = 3
        for _ in range(50):
            assert tc._select_leader(MEMBERS) == "Alice Adams"

    def test_select_leader_picks_uniformly_among_tied_candidates(self):
        """All members tied at 0 — each should be chosen sometimes over many draws."""
        tc = TeamCirculation(members=MEMBERS, projects=PROJECTS)
        chosen = {tc._select_leader(MEMBERS) for _ in range(200)}
        assert len(chosen) > 1  # randomness means more than one person is picked


class TestMarkdownLeaderLookupCorrectness:
    def test_leader_in_markdown_matches_assignment(self, circulation):
        """After optimising the lookup, the leader shown must still match the record."""
        md = circulation.generate_markdown_table()

        # Split markdown into per-quarter sections
        sections: dict[int, list[str]] = {}
        current_quarter = None
        for line in md.splitlines():
            if line.startswith("## Quarter "):
                current_quarter = int(line.split()[-1]) - 1
                sections[current_quarter] = []
            elif current_quarter is not None:
                sections[current_quarter].append(line)

        for quarter in range(circulation.quarters):
            leader_map = {
                a.project: a.person
                for a in circulation.assignments[quarter]
                if a.is_leader
            }
            for line in sections.get(quarter, []):
                for project, leader in leader_map.items():
                    if line.startswith(f"| {project} |"):
                        assert leader in line, (
                            f"Q{quarter+1}: expected leader {leader!r} in row: {line}"
                        )
