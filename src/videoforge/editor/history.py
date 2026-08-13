"""
VideoForge History

Undo/Redo manager for VideoForge.

The history system stores commands instead of snapshots, making it
memory efficient and similar to professional NLEs.

Every editing operation should be wrapped in a HistoryCommand.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

# ==========================================================
# Base Command
# ==========================================================


class HistoryCommand(ABC):
    """
    Base undoable command.
    """

    def __init__(
        self,
        description: str = "",
    ) -> None:

        self.description = description

    @abstractmethod
    def execute(self) -> None:
        """
        Execute the command.
        """

    @abstractmethod
    def undo(self) -> None:
        """
        Undo the command.
        """


# ==========================================================
# History Manager
# ==========================================================


class History:
    """
    Undo / Redo stack.

    Example
    -------
    history.execute(AddClipCommand(...))

    history.undo()

    history.redo()
    """

    def __init__(
        self,
        max_history: int = 500,
    ) -> None:

        self.max_history = max_history

        self._undo_stack: list[HistoryCommand] = []

        self._redo_stack: list[HistoryCommand] = []

    # ======================================================
    # Execute
    # ======================================================

    def execute(
        self,
        command: HistoryCommand,
    ) -> None:
        """
        Execute a command and push it
        onto the undo stack.
        """

        command.execute()

        self._undo_stack.append(command)

        self._redo_stack.clear()

        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)

    # ======================================================
    # Undo
    # ======================================================

    def undo(self) -> bool:

        if not self._undo_stack:
            return False

        command = self._undo_stack.pop()

        command.undo()

        self._redo_stack.append(command)

        return True

    # ======================================================
    # Redo
    # ======================================================

    def redo(self) -> bool:

        if not self._redo_stack:
            return False

        command = self._redo_stack.pop()

        command.execute()

        self._undo_stack.append(command)

        return True

    # ======================================================
    # Stack Management
    # ======================================================

    def clear(self) -> None:

        self._undo_stack.clear()

        self._redo_stack.clear()

    # ======================================================
    # Queries
    # ======================================================

    @property
    def can_undo(self) -> bool:

        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:

        return bool(self._redo_stack)

    @property
    def undo_count(self) -> int:

        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:

        return len(self._redo_stack)

    @property
    def last_command(self) -> HistoryCommand | None:

        if not self._undo_stack:
            return None

        return self._undo_stack[-1]

    # ======================================================
    # Peek
    # ======================================================

    def peek_undo(self) -> HistoryCommand | None:

        if not self._undo_stack:
            return None

        return self._undo_stack[-1]

    def peek_redo(self) -> HistoryCommand | None:

        if not self._redo_stack:
            return None

        return self._redo_stack[-1]

    # ======================================================
    # Representation
    # ======================================================

    def __len__(self) -> int:

        return self.undo_count

    def __repr__(self) -> str:

        return f"History(undo={self.undo_count}, redo={self.redo_count})"


# ==========================================================
# Generic Lambda Command
# ==========================================================


class LambdaCommand(HistoryCommand):
    """
    Convenience command for simple actions.

    Example
    -------
    history.execute(
        LambdaCommand(
            do=lambda: track.add_clip(clip),
            undo=lambda: track.remove_clip(clip),
            description="Add Clip",
        )
    )
    """

    def __init__(
        self,
        do,
        undo,
        description: str = "",
    ) -> None:

        super().__init__(description)

        self._do = do

        self._undo = undo

    def execute(self) -> None:

        self._do()

    def undo(self) -> None:

        self._undo()
