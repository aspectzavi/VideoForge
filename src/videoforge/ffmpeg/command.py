
"""
Build FFmpeg commands from FFmpegJob objects.
"""

from __future__ import annotations

from videoforge.ffmpeg.binaries import BINARIES
from videoforge.ffmpeg.job import FFmpegJob


class FFmpegCommandBuilder:
    """
    Translate an FFmpegJob into an FFmpeg command.

    This class is responsible only for command construction.

    It does not:

    - Validate jobs
    - Execute FFmpeg
    - Modify the FFmpegJob
    - Inspect files
    - Add implicit inputs
    - Invent filters

    Validation is handled by JobValidator.
    Execution is handled by FFmpegRunner.
    """

    @staticmethod
    def build(job: FFmpegJob) -> list[str]:
        """
        Build the FFmpeg command for ``job``.

        The output file is always the final command argument.
        """

        command: list[str] = [
            str(BINARIES.ffmpeg),
        ]

        # =========================================================
        # Global options
        # =========================================================

        command.append(
            "-y"
            if job.overwrite
            else "-n"
        )

        # =========================================================
        # Hardware acceleration
        # =========================================================

        if job.hwaccel is not None:
            command.extend(
                [
                    "-hwaccel",
                    job.hwaccel,
                ]
            )

        if job.hwaccel_output_format is not None:
            command.extend(
                [
                    "-hwaccel_output_format",
                    job.hwaccel_output_format,
                ]
            )

        # =========================================================
        # Input files
        #
        # Inputs are supplied explicitly by the operation through
        # FFmpegJob.inputs.
        # =========================================================

        for input_file in job.inputs:
            command.extend(
                [
                    "-i",
                    str(input_file),
                ]
            )

        # =========================================================
        # Stream mapping
        #
        # Mapping must be emitted before codec configuration.
        # =========================================================

        for stream in job.map_streams:
            command.extend(
                [
                    "-map",
                    stream,
                ]
            )

        # =========================================================
        # Complex filter graph
        # =========================================================

        if job.filter_complex is not None:
            command.extend(
                [
                    "-filter_complex",
                    job.filter_complex,
                ]
            )

        # =========================================================
        # Video filters
        #
        # Operations are responsible for constructing the filter
        # chain. The command builder only serializes it.
        # =========================================================

        elif job.video_filters:
            command.extend(
                [
                    "-vf",
                    ",".join(job.video_filters),
                ]
            )

        # =========================================================
        # Audio filters
        # =========================================================

        if job.audio_filters:
            command.extend(
                [
                    "-af",
                    ",".join(job.audio_filters),
                ]
            )

        # =========================================================
        # Video codec
        # =========================================================

        if job.copy_video:
            command.extend(
                [
                    "-c:v",
                    "copy",
                ]
            )

        elif job.video_codec is not None:
            command.extend(
                [
                    "-c:v",
                    job.video_codec,
                ]
            )

        # =========================================================
        # Audio codec
        # =========================================================

        if job.copy_audio:
            command.extend(
                [
                    "-c:a",
                    "copy",
                ]
            )

        elif job.audio_codec is not None:
            command.extend(
                [
                    "-c:a",
                    job.audio_codec,
                ]
            )

        # =========================================================
        # Subtitle codec
        # =========================================================

        if job.subtitle_codec is not None:
            command.extend(
                [
                    "-c:s",
                    job.subtitle_codec,
                ]
            )

        # =========================================================
        # Encoding options
        # =========================================================

        if job.preset is not None:
            command.extend(
                [
                    "-preset",
                    job.preset,
                ]
            )

        if job.crf is not None:
            command.extend(
                [
                    "-crf",
                    str(job.crf),
                ]
            )

        if job.video_bitrate is not None:
            command.extend(
                [
                    "-b:v",
                    job.video_bitrate,
                ]
            )

        if job.audio_bitrate is not None:
            command.extend(
                [
                    "-b:a",
                    job.audio_bitrate,
                ]
            )

        if job.pixel_format is not None:
            command.extend(
                [
                    "-pix_fmt",
                    job.pixel_format,
                ]
            )

        if job.profile is not None:
            command.extend(
                [
                    "-profile:v",
                    job.profile,
                ]
            )

        if job.level is not None:
            command.extend(
                [
                    "-level",
                    job.level,
                ]
            )

        if job.tune is not None:
            command.extend(
                [
                    "-tune",
                    job.tune,
                ]
            )

        # =========================================================
        # Resolution
        #
        # width / height are serialized as explicit FFmpeg
        # output options only when supplied.
        #
        # Operations that require a filter-based resize should
        # place their scale expression in video_filters instead.
        # =========================================================

        if job.width is not None:
            command.extend(
                [
                    "-width",
                    str(job.width),
                ]
            )

        if job.height is not None:
            command.extend(
                [
                    "-height",
                    str(job.height),
                ]
            )

        # =========================================================
        # Timing
        # =========================================================

        if job.start_time is not None:
            command.extend(
                [
                    "-ss",
                    str(job.start_time),
                ]
            )

        if job.duration is not None:
            command.extend(
                [
                    "-t",
                    str(job.duration),
                ]
            )

        elif job.end_time is not None:
            command.extend(
                [
                    "-to",
                    str(job.end_time),
                ]
            )

        # =========================================================
        # Frame rate
        # =========================================================

        if job.frame_rate is not None:
            command.extend(
                [
                    "-r",
                    str(job.frame_rate),
                ]
            )

        # =========================================================
        # Audio configuration
        # =========================================================

        if job.sample_rate is not None:
            command.extend(
                [
                    "-ar",
                    str(job.sample_rate),
                ]
            )

        if job.channels is not None:
            command.extend(
                [
                    "-ac",
                    str(job.channels),
                ]
            )

        if job.volume is not None:
            command.extend(
                [
                    "-af",
                    f"volume={job.volume}",
                ]
            )

        # =========================================================
        # Subtitle configuration
        # =========================================================

        if job.burn_subtitles:
            if job.subtitle_file is None:
                raise ValueError(
                    "burn_subtitles=True requires subtitle_file."
                )

            subtitle_path = (
                str(job.subtitle_file)
                .replace("\\", "/")
                .replace(":", r"\:")
            )

            subtitle_filter = (
                f"subtitles='{subtitle_path}'"
            )

            style = job.metadata.get(
                "subtitle_force_style"
            )

            if style:
                subtitle_filter += (
                    f":force_style='{style}'"
                )

            # If existing video filters are present, append the
            # subtitle filter rather than emitting another -vf.
            if job.filter_complex is None:
                existing_filters = list(
                    job.video_filters
                )

                existing_filters.append(
                    subtitle_filter
                )

                # Remove an already-emitted -vf by rebuilding
                # this section is unnecessary because filters
                # are emitted above only when burn_subtitles is
                # false.
                #
                # Therefore this branch replaces the previous
                # video-filter representation in the command.
                filter_index = _find_option(
                    command,
                    "-vf",
                )

                if filter_index is not None:
                    command[filter_index + 1] = ",".join(
                        existing_filters
                    )
                else:
                    command.extend(
                        [
                            "-vf",
                            ",".join(existing_filters),
                        ]
                    )

        # =========================================================
        # Metadata
        # =========================================================

        for key, value in job.metadata.items():
            if key == "subtitle_force_style":
                continue

            command.extend(
                [
                    "-metadata",
                    f"{key}={value}",
                ]
            )

        # =========================================================
        # Threads
        # =========================================================

        if job.threads is not None:
            command.extend(
                [
                    "-threads",
                    str(job.threads),
                ]
            )

        # =========================================================
        # Extra FFmpeg arguments
        # =========================================================

        if job.extra_args:
            command.extend(
                job.extra_args
            )

        # =========================================================
        # Output
        #
        # IMPORTANT:
        # FFmpegRunner relies on the output being the final
        # argument when it adds progress options.
        # =========================================================

        command.append(
            str(job.output)
        )

        return command


def _find_option(
    command: list[str],
    option: str,
) -> int | None:
    """
    Find the index of an option in an FFmpeg command.
    """

    try:
        return command.index(option)
    except ValueError:
        return None
