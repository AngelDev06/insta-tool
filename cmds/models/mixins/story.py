from typing import Iterable, Self, Optional, overload
from datetime import datetime

from ...utils.constants import ChangesType, CHANGES
from ..update import Update, SingleUpdate, RenamedUser
from ..viewer import Viewer


class Story:
    timestamp: datetime
    viewers: dict[int, Viewer]

    def added_from(self, other: Self) -> dict[int, Viewer]:
        return {
            uid: self.viewers[uid]
            for uid in self.viewers.keys() - other.viewers.keys()
        }

    def removed_from(self, other: Self) -> dict[int, Viewer]:
        return other.added_from(self)

    def renamed_from(self, other: Self) -> dict[int, RenamedUser]:
        return {
            uid: RenamedUser(other.viewers[uid], self.viewers[uid])
            for uid in self.viewers.keys() & other.viewers.keys()
            if self.viewers[uid].name != other.viewers[uid].name
        }

    def user_added_from(
        self, other: Self, username: str
    ) -> Optional[tuple[int, Viewer]]:
        for uid, viewer in self.viewers.items():
            if viewer.name == username:
                if uid not in other.viewers:
                    return uid, viewer
                return None
        return None

    def user_removed_from(
        self, other: Self, username: str
    ) -> Optional[tuple[int, Viewer]]:
        return other.user_added_from(self, username)

    def user_renamed_from(
        self, other: Self, username: str
    ) -> Optional[tuple[int, RenamedUser]]:
        for current_viewers, other_viewers in (
            (self.viewers, other.viewers),
            (other.viewers, self.viewers),
        ):
            for uid, viewer in current_viewers.items():
                if viewer.name == username:
                    other_viewer = other_viewers.get(uid)
                    if (
                        other_viewer is not None
                        and other_viewer.name != viewer.name
                    ):
                        return uid, RenamedUser(other_viewer, viewer)
                    return None
        return None

    @overload
    def updates_from(
        self,
        other: Self,
        username: str,
        changes: Iterable[ChangesType],
    ) -> SingleUpdate: ...

    @overload
    def updates_from(
        self,
        other: Self,
        username: None,
        changes: Iterable[ChangesType],
    ) -> Update: ...

    def updates_from(self, other, username=None, changes=CHANGES):
        if username is None:
            return Update(
                **{
                    change_type: getattr(self, f"{change_type}_from")(other)
                    for change_type in changes
                }
            )

        for change_type in changes:
            result = getattr(self, f"user_{change_type}_from")(other, username)
            if result is not None:
                return SingleUpdate(change_type, result[0], result[1])
        return SingleUpdate()

    @property
    def viewers_strings(self) -> Iterable[str]:
        return (str(viewer) for viewer in self.viewers.values())

    @property
    def viewers_usernames(self) -> Iterable[str]:
        return (viewer.name for viewer in self.viewers.values())
