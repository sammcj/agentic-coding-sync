"""Tests for files module."""


import pytest

from sync_agentic_tools.files import (
    FileMetadata,
    compute_checksum,
    count_lines,
    files_are_identical,
    is_text_file,
    read_file_lines,
    safe_copy_file,
    safe_delete_file,
)


class TestComputeChecksum:
    """Test checksum computation."""

    def test_same_content_same_checksum(self, tmp_path):
        """Test that same content produces same checksum."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "Hello, World!"
        file1.write_text(content)
        file2.write_text(content)

        checksum1 = compute_checksum(file1)
        checksum2 = compute_checksum(file2)
        assert checksum1 == checksum2

    def test_different_content_different_checksum(self, tmp_path):
        """Test that different content produces different checksum."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")

        checksum1 = compute_checksum(file1)
        checksum2 = compute_checksum(file2)
        assert checksum1 != checksum2

    def test_checksum_format(self, tmp_path):
        """Test checksum format."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        checksum = compute_checksum(test_file)
        assert checksum.startswith("sha256:")
        # SHA256 hex digest is 64 characters
        assert len(checksum.split(":")[1]) == 64

    def test_binary_file_checksum(self, tmp_path):
        """Test checksum of binary file."""
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

        checksum = compute_checksum(binary_file)
        assert checksum.startswith("sha256:")


class TestFilesAreIdentical:
    """Test file identity comparison."""

    def test_identical_files(self, tmp_path):
        """Test that identical files are detected."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "Same content"
        file1.write_text(content)
        file2.write_text(content)

        assert files_are_identical(file1, file2)

    def test_different_files(self, tmp_path):
        """Test that different files are detected."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")

        assert not files_are_identical(file1, file2)

    def test_different_sizes(self, tmp_path):
        """Test quick size check optimization."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Short")
        file2.write_text("Much longer content")

        # Should return False quickly based on size difference
        assert not files_are_identical(file1, file2)

    def test_nonexistent_file(self, tmp_path):
        """Test comparison with nonexistent file."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content")

        assert not files_are_identical(file1, file2)
        assert not files_are_identical(file2, file1)


class TestSafeCopyFile:
    """Test safe file copying."""

    def test_basic_copy(self, tmp_path):
        """Test basic file copy."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        content = "Test content"
        source.write_text(content)

        safe_copy_file(source, dest)
        assert dest.exists()
        assert dest.read_text() == content

    def test_copy_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "subdir" / "nested" / "dest.txt"
        source.write_text("Content")

        safe_copy_file(source, dest, create_parents=True)
        assert dest.exists()
        assert dest.read_text() == "Content"

    def test_copy_preserves_metadata(self, tmp_path):
        """Test that file metadata is preserved."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("Content")
        original_mtime = source.stat().st_mtime

        safe_copy_file(source, dest)
        # mtime should be preserved (within reasonable tolerance)
        assert abs(dest.stat().st_mtime - original_mtime) < 1

    def test_copy_nonexistent_source(self, tmp_path):
        """Test copying nonexistent source file."""
        source = tmp_path / "nonexistent.txt"
        dest = tmp_path / "dest.txt"

        with pytest.raises(FileNotFoundError):
            safe_copy_file(source, dest)

    def test_copy_to_directory(self, tmp_path):
        """Test copying to directory raises error."""
        source = tmp_path / "source.txt"
        source.write_text("Content")
        dest_dir = tmp_path / "destdir"
        dest_dir.mkdir()

        with pytest.raises(IsADirectoryError):
            safe_copy_file(source, dest_dir)

    def test_overwrite_existing(self, tmp_path):
        """Test overwriting existing file."""
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("New content")
        dest.write_text("Old content")

        safe_copy_file(source, dest)
        assert dest.read_text() == "New content"


class TestSafeDeleteFile:
    """Test safe file deletion."""

    def test_delete_file(self, tmp_path):
        """Test deleting a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        safe_delete_file(test_file)
        assert not test_file.exists()

    def test_delete_with_backup(self, tmp_path):
        """Test deleting file with backup."""
        test_file = tmp_path / "test.txt"
        content = "Important content"
        test_file.write_text(content)

        safe_delete_file(test_file, backup=True)
        assert not test_file.exists()
        # Backup should exist
        backup_file = test_file.with_suffix(test_file.suffix + ".deleted")
        assert backup_file.exists()

    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            safe_delete_file(test_file)


class TestReadFileLines:
    """Test reading file lines."""

    def test_read_text_file(self, tmp_path):
        """Test reading text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        lines = read_file_lines(test_file)
        assert len(lines) == 3
        assert lines[0] == "Line 1\n"
        assert lines[1] == "Line 2\n"
        assert lines[2] == "Line 3\n"

    def test_read_empty_file(self, tmp_path):
        """Test reading empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        lines = read_file_lines(test_file)
        assert len(lines) == 0

    def test_read_binary_file(self, tmp_path):
        """Test reading binary file."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\xff\xfe")

        lines = read_file_lines(test_file)
        assert len(lines) == 0  # Binary files return empty list


class TestCountLines:
    """Test line counting."""

    def test_count_lines_text_file(self, tmp_path):
        """Test counting lines in text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        count = count_lines(test_file)
        assert count == 3

    def test_count_lines_empty_file(self, tmp_path):
        """Test counting lines in empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        count = count_lines(test_file)
        assert count == 0

    def test_count_lines_binary_file(self, tmp_path):
        """Test counting lines in binary file."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02")

        # Binary files may return 0 or small number of lines depending on content
        count = count_lines(test_file)
        assert count <= 1  # Binary files should return 0 or minimal lines


class TestIsTextFile:
    """Test text file detection."""

    def test_text_file(self, tmp_path):
        """Test detecting text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is text content")

        assert is_text_file(test_file)

    def test_binary_file(self, tmp_path):
        """Test detecting binary file."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

        assert not is_text_file(test_file)

    def test_utf8_file(self, tmp_path):
        """Test detecting UTF-8 text file."""
        test_file = tmp_path / "utf8.txt"
        test_file.write_text("Hello 世界 🌍", encoding="utf-8")

        assert is_text_file(test_file)


class TestFileMetadata:
    """Test FileMetadata class."""

    def test_from_file(self, tmp_path):
        """Test creating metadata from file."""
        test_file = tmp_path / "test.txt"
        content = "Test content"
        test_file.write_text(content)

        metadata = FileMetadata.from_file(test_file, tmp_path)

        assert metadata.path == test_file
        assert metadata.relative_path == "test.txt"
        assert metadata.size == len(content.encode())
        assert metadata.checksum.startswith("sha256:")
        assert metadata.mtime is not None

    def test_from_nested_file(self, tmp_path):
        """Test creating metadata from nested file."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("Content")

        metadata = FileMetadata.from_file(test_file, tmp_path)

        assert metadata.relative_path == "subdir/test.txt"
