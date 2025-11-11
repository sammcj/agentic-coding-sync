"""Tests for utils module."""



from sync_agentic_tools.utils import (
    find_files,
    format_size,
    get_machine_id,
    matches_pattern,
    matches_patterns,
)


class TestMatchesPattern:
    """Test pattern matching functionality."""

    def test_simple_glob(self, tmp_path):
        """Test simple glob pattern matching."""
        test_file = tmp_path / "test.txt"
        assert matches_pattern(test_file, "*.txt", tmp_path)
        assert not matches_pattern(test_file, "*.log", tmp_path)

    def test_recursive_glob(self, tmp_path):
        """Test recursive glob pattern matching."""
        test_file = tmp_path / "dir1" / "dir2" / "test.py"
        assert matches_pattern(test_file, "**/*.py", tmp_path)
        assert matches_pattern(test_file, "**/dir2/*.py", tmp_path)

    def test_directory_pattern(self, tmp_path):
        """Test directory-based pattern matching."""
        test_file = tmp_path / "src" / "main.py"
        assert matches_pattern(test_file, "src/*.py", tmp_path)
        assert not matches_pattern(test_file, "lib/*.py", tmp_path)


class TestMatchesPatterns:
    """Test multiple pattern matching."""

    def test_no_patterns_includes_all(self):
        """Test that no include patterns means include everything."""
        assert matches_patterns("any/file.txt", [], [])
        assert matches_patterns("another/file.py", [], [])

    def test_include_patterns(self):
        """Test include patterns."""
        include = ["*.py", "*.md"]
        exclude = []
        assert matches_patterns("main.py", include, exclude)
        assert matches_patterns("README.md", include, exclude)
        assert not matches_patterns("test.txt", include, exclude)

    def test_exclude_patterns(self):
        """Test exclude patterns override includes."""
        include = ["**/*.py"]
        exclude = ["**/test_*.py"]
        assert matches_patterns("main.py", include, exclude)
        assert not matches_patterns("test_main.py", include, exclude)

    def test_recursive_patterns(self):
        """Test recursive pattern matching."""
        include = ["**/*.py"]
        exclude = ["**/node_modules/**"]
        assert matches_patterns("src/main.py", include, exclude)
        assert not matches_patterns("node_modules/pkg/file.py", include, exclude)

    def test_multiple_includes(self):
        """Test multiple include patterns."""
        include = ["*.py", "*.md", "*.txt"]
        exclude = []
        assert matches_patterns("file.py", include, exclude)
        assert matches_patterns("README.md", include, exclude)
        assert matches_patterns("notes.txt", include, exclude)
        assert not matches_patterns("image.png", include, exclude)


class TestFindFiles:
    """Test file finding functionality."""

    def test_find_all_files(self, tmp_path):
        """Test finding all files with no patterns."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file3.md").touch()

        files = find_files(tmp_path, [], [], respect_gitignore=False)
        assert len(files) == 3
        assert tmp_path / "file1.txt" in files
        assert tmp_path / "file2.py" in files
        assert tmp_path / "dir1" / "file3.md" in files

    def test_find_with_include_pattern(self, tmp_path):
        """Test finding files with include patterns."""
        (tmp_path / "test.py").touch()
        (tmp_path / "test.txt").touch()
        (tmp_path / "main.py").touch()

        files = find_files(tmp_path, ["*.py"], [], respect_gitignore=False)
        assert len(files) == 2
        assert tmp_path / "test.py" in files
        assert tmp_path / "main.py" in files
        assert tmp_path / "test.txt" not in files

    def test_find_with_exclude_pattern(self, tmp_path):
        """Test finding files with exclude patterns."""
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "utils.py").touch()

        files = find_files(tmp_path, ["*.py"], ["test_*.py"], respect_gitignore=False)
        assert len(files) == 2
        assert tmp_path / "main.py" in files
        assert tmp_path / "utils.py" in files
        assert tmp_path / "test_main.py" not in files

    def test_find_recursive(self, tmp_path):
        """Test finding files recursively."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").touch()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test.py").touch()

        files = find_files(tmp_path, ["**/*.py"], [], respect_gitignore=False)
        assert len(files) == 2
        assert tmp_path / "src" / "main.py" in files
        assert tmp_path / "tests" / "test.py" in files

    def test_find_with_gitignore(self, tmp_path):
        """Test finding files respecting gitignore."""
        (tmp_path / ".gitignore").write_text("*.log\n.env\n")
        (tmp_path / "main.py").touch()
        (tmp_path / "test.log").touch()
        (tmp_path / ".env").touch()

        files = find_files(tmp_path, [], [], respect_gitignore=True)
        assert tmp_path / "main.py" in files
        assert tmp_path / "test.log" not in files
        assert tmp_path / ".env" not in files

    def test_nonexistent_path(self, tmp_path):
        """Test finding files in nonexistent path."""
        nonexistent = tmp_path / "does_not_exist"
        files = find_files(nonexistent, [], [], respect_gitignore=False)
        assert len(files) == 0

    def test_symlinks(self, tmp_path):
        """Test symlink handling."""
        (tmp_path / "real.txt").touch()
        (tmp_path / "link.txt").symlink_to(tmp_path / "real.txt")

        # Without following symlinks
        files = find_files(tmp_path, [], [], follow_symlinks=False, respect_gitignore=False)
        # Should only get real.txt, not the symlink
        assert tmp_path / "real.txt" in files

        # With following symlinks
        files = find_files(tmp_path, [], [], follow_symlinks=True, respect_gitignore=False)
        assert tmp_path / "real.txt" in files


class TestFormatSize:
    """Test file size formatting."""

    def test_bytes(self):
        """Test byte formatting."""
        assert format_size(100) == "100.0 B"
        assert format_size(512) == "512.0 B"

    def test_kilobytes(self):
        """Test kilobyte formatting."""
        assert format_size(1024) == "1.0 KB"
        assert format_size(2048) == "2.0 KB"

    def test_megabytes(self):
        """Test megabyte formatting."""
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(5 * 1024 * 1024) == "5.0 MB"

    def test_gigabytes(self):
        """Test gigabyte formatting."""
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_size(2 * 1024 * 1024 * 1024) == "2.0 GB"


class TestGetMachineId:
    """Test machine ID generation."""

    def test_machine_id_format(self):
        """Test that machine ID has expected format."""
        machine_id = get_machine_id()
        assert isinstance(machine_id, str)
        assert "-" in machine_id
        # Last part should be 8 character hex (hostname can have hyphens)
        parts = machine_id.split("-")
        assert len(parts) >= 2
        # Last part should be 8 character hex
        assert len(parts[-1]) == 8
        # Verify it's valid hex
        int(parts[-1], 16)  # Will raise if not valid hex

    def test_machine_id_consistent(self):
        """Test that machine ID is consistent across calls."""
        id1 = get_machine_id()
        id2 = get_machine_id()
        assert id1 == id2
