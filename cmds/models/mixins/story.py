from typing import Self

from ..viewer import Viewer


class Story:
    viewers: dict[int, Viewer]

    def added_from(self, other: Self) -> dict[int, Viewer]:
        return {
            uid: self.viewers[uid] for uid in self.viewers.keys() - other.viewers.keys()
        }

    def removed_from(self, other: Self) -> dict[int, Viewer]:
        return other.added_from(self)

    def renamed_from(self, other: Self) -> dict[int, tuple[Viewer, Viewer]]:
        return {
            uid: (other.viewers[uid], self.viewers[uid])
            for uid in self.viewers.keys() & other.viewers.keys()
            if self.viewers[uid].name != other.viewers[uid].name
        }

    @property
    def viewers_usernames(self) -> frozenset[str]:
        return frozenset(viewer.name for viewer in self.viewers.values())
