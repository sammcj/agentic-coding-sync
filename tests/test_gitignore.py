"""Tests for gitignore module."""



from sync_agentic_tools.gitignore import (
    _gitignore_to_glob,
    collect_gitignore_patterns,
    get_gitignore_excludes,
    parse_gitignore,
)


class TestGitignoreToGlob:
    """Test gitignore pattern conversion to glob patterns."""

    def test_simple_pattern(self):
        """Test simple filename pattern."""
        assert _gitignore_to_glob("*.log") == "**/*.log"
        assert _gitignore_to_glob(".DS_Store") == "**/.DS_Store"

    def test_root_relative_pattern(self):
        """Test root-relative pattern with leading slash."""
        assert _gitignore_to_glob("/build") == "build"
        assert _gitignore_to_glob("/dist/") == "dist/**"

    def test_directory_pattern(self):
        """Test directory pattern with trailing slash."""
        assert _gitignore_to_glob("node_modules/") == "**/node_modules/**"
        assert _gitignore_to_glob("__pycache__/") == "**/__pycache__/**"

    def test_path_with_separator(self):
        """Test pattern with directory separator."""
        assert _gitignore_to_glob("build/output") == "**/build/output"
        assert _gitignore_to_glob("src/*.pyc") == "**/src/*.pyc"

    def test_root_relative_with_separator(self):
        """Test root-relative pattern with separator."""
        assert _gitignore_to_glob("/src/cache") == "src/cache"


class TestParseGitignore:
    """Test gitignore file parsing."""

    def test_empty_file(self, tmp_path):
        """Test parsing empty gitignore file."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("")
        patterns = parse_gitignore(gitignore)
        assert patterns == []

    def test_comments_ignored(self, tmp_path):
        """Test that comments are ignored."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# This is a comment\n*.log\n# Another comment\n")
        patterns = parse_gitignore(gitignore)
        assert patterns == ["**/*.log"]

    def test_blank_lines_ignored(self, tmp_path):
        """Test that blank lines are ignored."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("\n*.log\n\n\n.env\n\n")
        patterns = parse_gitignore(gitignore)
        assert patterns == ["**/*.log", "**/.env"]

    def test_negation_patterns_skipped(self, tmp_path):
        """Test that negation patterns are skipped."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n!important.log\n")
        patterns = parse_gitignore(gitignore)
        assert patterns == ["**/*.log"]
        assert "!important.log" not in patterns

    def test_mixed_patterns(self, tmp_path):
        """Test parsing file with mixed patterns."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            """# Build outputs
/build/
/dist/

# Dependencies
node_modules/
.venv/

# Logs
*.log
*.tmp

# Environment
.env
"""
        )
        patterns = parse_gitignore(gitignore)
        assert "build/**" in patterns
        assert "dist/**" in patterns
        assert "**/node_modules/**" in patterns
        assert "**/.venv/**" in patterns
        assert "**/*.log" in patterns
        assert "**/*.tmp" in patterns
        assert "**/.env" in patterns

    def test_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent gitignore file."""
        gitignore = tmp_path / ".gitignore"
        patterns = parse_gitignore(gitignore)
        assert patterns == []


class TestCollectGitignorePatterns:
    """Test collecting gitignore patterns from directory tree."""

    def test_single_gitignore(self, tmp_path):
        """Test collecting patterns from single gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n.env\n")
        patterns = collect_gitignore_patterns(tmp_path)
        assert "**/*.log" in patterns
        assert "**/.env" in patterns

    def test_nested_gitignore(self, tmp_path):
        """Test collecting patterns from nested gitignore files."""
        # Root gitignore
        root_gitignore = tmp_path / ".gitignore"
        root_gitignore.write_text("*.log\n")

        # Nested gitignore
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        nested_gitignore = subdir / ".gitignore"
        nested_gitignore.write_text("*.tmp\n")

        patterns = collect_gitignore_patterns(tmp_path, respect_nested=True)

        assert "**/*.log" in patterns
        # Nested pattern should be prefixed or kept as global
        assert any("*.tmp" in p for p in patterns)

    def test_no_gitignore(self, tmp_path):
        """Test collecting patterns when no gitignore exists."""
        patterns = collect_gitignore_patterns(tmp_path)
        assert patterns == []


class TestGetGitignoreExcludes:
    """Test main entry point for gitignore support."""

    def test_get_gitignore_excludes(self, tmp_path):
        """Test getting gitignore excludes."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            """*.log
/build/
node_modules/
.env
"""
        )
        excludes = get_gitignore_excludes(tmp_path)

        assert "**/*.log" in excludes
        assert "build/**" in excludes
        assert "**/node_modules/**" in excludes
        assert "**/.env" in excludes
