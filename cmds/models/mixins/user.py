from typing import Iterable, Optional, Self, Type, cast

from ...utils.constants import (
    CHANGES,
    DIFFS,
    LISTS,
    ChangesType,
    DiffsType,
    ListsType,
)
from ..diff import Diff, SingleDiff, UserDiff
from ..update import RenamedUser, SingleUpdate, Update, UserUpdate


class User:
    followers: dict[int, str]
    followings: dict[int, str]

    def diff(self, reverse: bool) -> frozenset[str]:
        return (
            self.followings_usernames - self.followers_usernames
            if not reverse
            else self.followers_usernames - self.followings_usernames
        )

    def renamed_from_as_tuples(
        self, other: Self, list_name: ListsType
    ) -> dict[int, tuple[str, str]]:
        return {
            uid: (cast(str, renamed.old), cast(str, renamed.new))
            for uid, renamed in self.renamed_from(other, list_name).items()
        }

    def renamed_from(self, other: Self, list_name: ListsType) -> dict[int, RenamedUser]:
        current_list: dict[int, str] = getattr(self, list_name)
        other_list: dict[int, str] = getattr(other, list_name)
        return {
            uid: RenamedUser(other_list[uid], current_list[uid])
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
        username: Optional[str] = None,
        lists: Iterable[ListsType] = LISTS,
        changes: Iterable[ChangesType] = CHANGES,
    ) -> UserUpdate:
        if username is None:
            return UserUpdate(  # type: ignore
                **{
                    list_name: Update(  # type: ignore
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

        return UserUpdate(  # type: ignore
            **{
                list_name: self._lookup_change_for(
                    SingleUpdate, other, username, list_name, changes
                )
                for list_name in lists
            }
        )

    def diffs_from(
        self,
        other: Self,
        username: Optional[str] = None,
        lists: Iterable[ListsType] = LISTS,
        diffs: Iterable[DiffsType] = DIFFS,
    ) -> UserDiff:
        table = {"user1": "added", "user2": "removed", "mutuals": "mutuals"}
        if username is None:
            return UserDiff(  # type: ignore
                **{
                    list_name: Diff(  # type: ignore
                        **{
                            diff_type: getattr(self, f"{table[diff_type]}_from")(
                                other, list_name
                            )
                            for diff_type in diffs
                        }
                    )
                    for list_name in lists
                }
            )

        return UserDiff(  # type: ignore
            **{
                list_name: self._lookup_change_for(
                    SingleDiff,
                    other,
                    username,
                    list_name,
                    (table[diff_type] for diff_type in diffs),  # type: ignore
                )
                for list_name in lists
            }
        )

    def _lookup_change_for[T](
        self,
        updatecls: Type[T],
        other: Self,
        username: str,
        list_name: ListsType,
        changes: Iterable[ChangesType],
    ) -> T:
        for change_type in changes:
            updates = getattr(self, f"{change_type}_from")(other, list_name)

            if change_type == "renamed":
                for uid, renamed in updates.items():
                    if username == renamed.old or username == renamed.new:
                        return updatecls(change_type, uid, renamed)  # type: ignore
                continue

            for uid, name in updates.items():
                if username == name:
                    return updatecls(change_type, uid, name)  # type: ignore
        return updatecls()

    @property
    def followers_usernames(self) -> frozenset[str]:
        return frozenset(self.followers.values())

    @property
    def followings_usernames(self) -> frozenset[str]:
        return frozenset(self.followings.values())
