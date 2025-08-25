from typing import Callable, Iterable, Self

from ...utils.constants import (
    CHANGES,
    DIFFS,
    LISTS,
    ChangesType,
    DiffsType,
    ListsType,
)
from ..diff import Diff, UserDiff
from ..update import Update, UserUpdate


class User:
    followers: dict[int, str]
    followings: dict[int, str]

    def diff(self, reverse: bool) -> frozenset[str]:
        return (
            self.followings_usernames - self.followers_usernames
            if not reverse
            else self.followers_usernames - self.followings_usernames
        )

    def renamed_from(self, other: Self, list_name: ListsType):
        current_list: dict[int, str] = getattr(self, list_name)
        other_list: dict[int, str] = getattr(other, list_name)
        return {
            uid: (other_list[uid], current_list[uid])
            for uid in current_list.keys() & other_list.keys()
            if other_list[uid] != current_list[uid]
        }

    def added_from(self, other: Self, list_name: ListsType) -> dict[int, str]:
        current_list: dict[int, str] = getattr(self, list_name)
        other_list: dict[int, str] = getattr(other, list_name)
        return {
            uid: current_list[uid] for uid in current_list.keys() - other_list.keys()
        }

    def removed_from(self, other: Self, list_name: ListsType) -> dict[int, str]:
        return other.added_from(self, list_name)

    def mutuals_from(self, other: Self, list_name: ListsType) -> dict[int, str]:
        current_list: dict[int, str] = getattr(self, list_name)
        other_list: dict[int, str] = getattr(other, list_name)
        return {
            uid: current_list[uid] for uid in current_list.keys() & other_list.keys()
        }

    def updates_from(
        self,
        other: Self,
        lists: Iterable[ListsType] = LISTS,
        changes: Iterable[ChangesType] = CHANGES,
    ):
        return UserUpdate(
            **{
                list_name: Update(
                    **{
                        change_type: getattr(self, f"{change_type}_from")(
                            other, list_name
                        )
                        for change_type in changes
                    }
                )
                for list_name in lists
            }
        )

    def diffs_from(
        self,
        other: Self,
        lists: Iterable[ListsType] = LISTS,
        diffs: Iterable[DiffsType] = DIFFS,
    ):
        method_table: dict[DiffsType, Callable[[Self, ListsType], dict[int, str]]] = {
            "user1": self.added_from,
            "user2": self.removed_from,
            "mutuals": self.mutuals_from,
        }
        return UserDiff(
            **{
                list_name: Diff(
                    **{
                        diff_type: method_table[diff_type](other, list_name)
                        for diff_type in diffs
                    }
                )
                for list_name in lists
            }
        )

    @property
    def followers_usernames(self) -> frozenset[str]:
        return frozenset(self.followers.values())

    @property
    def followings_usernames(self) -> frozenset[str]:
        return frozenset(self.followings.values())
