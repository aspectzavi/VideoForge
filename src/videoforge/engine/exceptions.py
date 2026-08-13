"""
VideoForge Exceptions

Central exception hierarchy for the entire project.

Every custom exception should inherit from VideoForgeError so callers
can catch all application-specific failures with a single except block.
"""

from __future__ import annotations

# =====================================================================
# Base Exception
# =====================================================================


class VideoForgeError(Exception):
    """
    Base class for all VideoForge exceptions.
    """

    default_message = "VideoForge error."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# =====================================================================
# Validation
# =====================================================================


class ValidationError(VideoForgeError):
    """
    Invalid user input or configuration.
    """

    default_message = "Validation failed."


class ConfigurationError(VideoForgeError):
    """
    Invalid application configuration.
    """

    default_message = "Configuration error."


# =====================================================================
# Files
# =====================================================================


class FileError(VideoForgeError):
    """
    Base file-related exception.
    """

    default_message = "File error."


class FileNotFoundError(FileError):
    """
    Input file could not be located.
    """

    default_message = "File not found."


class OutputExistsError(FileError):
    """
    Output already exists.
    """

    default_message = "Output file already exists."


class UnsupportedMediaError(FileError):
    """
    Unsupported media format.
    """

    default_message = "Unsupported media format."


# =====================================================================
# FFmpeg
# =====================================================================


class FFmpegError(VideoForgeError):
    """
    Base FFmpeg exception.
    """

    default_message = "FFmpeg error."


class FFmpegNotFoundError(FFmpegError):
    """
    FFmpeg executable missing.
    """

    default_message = "FFmpeg executable not found."


class FFprobeNotFoundError(FFmpegError):
    """
    FFprobe executable missing.
    """

    default_message = "FFprobe executable not found."


class FFmpegExecutionError(FFmpegError):
    """
    FFmpeg process failed.
    """

    default_message = "FFmpeg execution failed."


class FFprobeError(FFmpegError):
    """
    FFprobe failed.
    """

    default_message = "FFprobe failed."


class FFmpegTimeoutError(FFmpegError):
    """
    FFmpeg exceeded timeout.
    """

    default_message = "FFmpeg timed out."


# =====================================================================
# Pipeline
# =====================================================================


class PipelineError(VideoForgeError):
    """
    Pipeline execution failed.
    """

    default_message = "Pipeline error."


class PipelineCancelledError(PipelineError):
    """
    Pipeline cancelled by user.
    """

    default_message = "Pipeline cancelled."


class OperationError(PipelineError):
    """
    Operation execution failed.
    """

    default_message = "Operation failed."


class RollbackError(PipelineError):
    """
    Rollback failed.
    """

    default_message = "Rollback failed."


# =====================================================================
# AI
# =====================================================================


class AIError(VideoForgeError):
    """
    Base AI exception.
    """

    default_message = "AI error."


class ModelNotLoadedError(AIError):
    """
    AI model unavailable.
    """

    default_message = "Model not loaded."


class TranscriptionError(AIError):
    """
    Speech transcription failed.
    """

    default_message = "Transcription failed."


class CaptionGenerationError(AIError):
    """
    Caption generation failed.
    """

    default_message = "Caption generation failed."


class TranslationError(AIError):
    """
    Translation failed.
    """

    default_message = "Translation failed."


class ThumbnailGenerationError(AIError):
    """
    Thumbnail generation failed.
    """

    default_message = "Thumbnail generation failed."


# =====================================================================
# Plugins
# =====================================================================


class PluginError(VideoForgeError):
    """
    Plugin system error.
    """

    default_message = "Plugin error."


class PluginLoadError(PluginError):
    """
    Failed to load plugin.
    """

    default_message = "Plugin failed to load."


class PluginExecutionError(PluginError):
    """
    Plugin execution failed.
    """

    default_message = "Plugin execution failed."


# =====================================================================
# Export
# =====================================================================


class ExportError(VideoForgeError):
    """
    Export failed.
    """

    default_message = "Export failed."


# =====================================================================
# Network
# =====================================================================


class NetworkError(VideoForgeError):
    """
    Network communication failed.
    """

    default_message = "Network error."


# =====================================================================
# Licensing
# =====================================================================


class LicenseError(VideoForgeError):
    """
    Licensing or activation error.
    """

    default_message = "License error."


# =====================================================================
# Internal
# =====================================================================


class InternalError(VideoForgeError):
    """
    Unexpected internal error.
    """

    default_message = "Internal VideoForge error."


class InvalidMediaError(Exception):
    """Raised when media is invalid."""

    pass


class InvalidCodecError(Exception):
    """Raised when an unsupported codec is encountered."""

    pass
