from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import ClassVar, Iterable, Optional, Self, overload
from sys import stdout

from pydantic import BaseModel, Field, field_serializer

from ...utils.constants import CHANGES, LISTS, ChangesType, ListsType
from ...utils.streams import ColoredOutput
from ...utils.uids import UIDMap
from .. import fetched, mixins
from ..update import (
    RenamedUser,
)
from ..update import (
    SingleUpdate as SingleUpdateData,
)
from ..update import (
    Update as UpdateData,
)
from ..update import (
    UserUpdate as UserUpdateData,
)


class Update(BaseModel):
    added: dict[int, str] = Field(default_factory=dict)
    removed: dict[int, str] = Field(default_factory=dict)
    renamed: dict[int, tuple[str, str]] = Field(default_factory=dict)

    def _packed_change(self, change: ChangesType):
        if change == "renamed":
            return {
                uid: RenamedUser(old, new)
                for uid, (old, new) in self.renamed.items()
            }
        return getattr(self, change)

    def _lookup_in_renamed(self, username: str) -> SingleUpdateData:
        for uid, (old, new) in self.renamed.items():
            if username == old or username == new:
                return SingleUpdateData(
                    change="renamed",
                    user_id=uid,
                    username=RenamedUser(old, new),
                )
        return SingleUpdateData()

    @overload
    def pack_updates(
        self, username: str, changes: Iterable[ChangesType]
    ) -> SingleUpdateData: ...

    @overload
    def pack_updates(
        self, username: None, changes: Iterable[ChangesType]
    ) -> UpdateData: ...

    def pack_updates(self, username=None, changes=CHANGES):
        if username is None:
            return UpdateData(
                **{
                    change_type: self._packed_change(change_type)
                    for change_type in changes
                }
            )
        for change in changes:
            if change == "renamed":
                return self._lookup_in_renamed(username)
            change_dict: dict[int, str] = getattr(self, change)
            for uid, name in change_dict.items():
                if name == username:
                    return SingleUpdateData(
                        change=change, user_id=uid, username=name
                    )
        return SingleUpdateData()


class ChangelogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    followers: Update = Field(default_factory=Update)  # type: ignore[override]
    followings: Update = Field(default_factory=Update)  # type: ignore[override]

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime, _info):
        return timestamp.timestamp()

    def pack_updates(
        self,
        username: Optional[str] = None,
        lists: Iterable[ListsType] = LISTS,
        changes: Iterable[ChangesType] = CHANGES,
    ) -> UserUpdateData:
        return UserUpdateData(
            **{
                list_name: getattr(self, list_name).pack_updates(
                    username, changes
                )
                for list_name in lists
            }
        )


class User(mixins.User, mixins.Cached, BaseModel):
    subdir: ClassVar[str] = "state"
    followers: dict[int, str] = Field(default_factory=dict)
    followings: dict[int, str] = Field(default_factory=dict)
    changelog: list[ChangelogEntry] = Field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.followers or self.followings or self.changelog)

    def checkout(self, at: date, lists: Iterable[ListsType] = LISTS) -> Self:
        """Backtraces up to a specific point in time (specified by `at`) and
        recovers the state of followers/followings

        Note that the state returned does not include any updates that were performed
        that day, meaning those (if any) were reverted

        Args:
            at (date): The point to which history will be recovered,
                note that the result will include any updates that happened
                during that day
            lists (Iterable[ListsType]): The lists to recover,
                defaults to both followers and followings
        Returns:
            A new instance containing the state at the point in time specified
        """
        kwargs: dict[str, dict[int, str]] = {
            list_name: getattr(self, list_name).copy() for list_name in lists
        }
        changelog_count: int = len(self.changelog)

        for log in reversed(self.changelog):
            if log.timestamp.date() < at:
                break

            for list_name in lists:
                update: Update = getattr(log, list_name)
                state: dict[int, str] = kwargs[list_name]

                for uid in list(update.added.keys()):
                    del state[uid]

                state |= update.removed

                for uid, (old_name, _) in update.renamed.items():
                    state[uid] = old_name
            changelog_count -= 1

        return self.model_construct(
            None,
            **kwargs,
            changelog=deepcopy(self.changelog[:changelog_count]),
        )
    
    def reset(self, username: str, at: date) -> None:
        if not self.changelog:
            return
        updated = self.checkout(at)
        self.followers = updated.followers
        self.followings = updated.followings
        self.changelog = updated.changelog
        self.dump(username, UIDMap.get().uid_of(username))

    def dump_update(self, fetched_user: fetched.User) -> None:
        """Creates a new changelog entry by comparing the dynamically fetched state
        with the latest cached one. It will include users with added/removed/renamed updates
        and will proceed to back it up in a file

        Args:
            fetched_user (fetched.User): The dynamically fetched state to use (should not be empty)
            callback (Optional[OutputUpdateCallback]): An optional callback that will be called
                (if provided) for every list providing it with the list name as well as the changes
                as keyword arguments. Can be used for printing the result."""
        entry = ChangelogEntry()

        for list_name in LISTS:
            update: Update = getattr(entry, list_name)
            update.added = fetched_user.added_from(self, list_name)
            update.removed = fetched_user.removed_from(self, list_name)
            update.renamed = fetched_user.renamed_from_as_tuples(
                self, list_name
            )

        if fetched_user.follower_count != len(
            fetched_user.followers
        ) or fetched_user.following_count != len(fetched_user.followings):
            if (
                input(
                    "not all the requested users were fetched, should the result be cached regardless? (Y/n) "
                ).strip()
                != "Y"
            ):
                return

        self.followers = fetched_user.followers
        self.followings = fetched_user.followings
        self.changelog.append(entry)
        self.dump(fetched_user.username, fetched_user.id)

    def delete(self, username: str, record: date, hard: bool = False) -> bool:
        if not self.changelog:
            return False
        logs = reversed(self.changelog)
        selected: Optional[ChangelogEntry] = None
        prev: Optional[ChangelogEntry] = None
        current: ChangelogEntry = next(logs)
        delete_index: int = 0

        if current.timestamp.date() == record:
            selected = current

        for index, log in enumerate(logs, 1):
            prev, current = current, log

            if current.timestamp.date() != record:
                if selected is not None and current.timestamp.date() < record:
                    break
                continue

            if selected is None:
                selected = current
                delete_index = index
                continue

            from ...utils.renderers import DeletableLogEntriesRenderer

            options = [
                log for log in logs if log.timestamp.date() == record
            ]  # newest to oldest
            options.reverse()  # oldest to newest
            options.extend((log, selected))
            renderer = DeletableLogEntriesRenderer(
                ColoredOutput(stdout, "green")
            )  # rendered from newest to oldest
            renderer.render(options)

            selection_input = input(
                "Select the number of entry to delete "
                "(on anything else the operation is cancelled): "
            ).strip()
            if not selection_input.isdigit():
                return False
            selection = int(
                selection_input
            )  # selection is from newest to oldest (as rendered), starting from 1
            if not selection or selection > len(options):
                return False

            selected, prev = options[-selection : len(options) - selection + 2]
            delete_index += selection - 1
            break

        if selected is None:
            return False

        self.changelog.pop(-delete_index - 1)

        # no fixing operation is performed on hard deletes
        if hard:
            self.dump(username, UIDMap.get().uid_of(username))
            return True

        if prev is None:
            for list_name in LISTS:
                selected_list: Update = getattr(selected, list_name)
                self_list: dict[int, str] = getattr(self, list_name)

                for uid in selected_list.added.keys():
                    del self_list[uid]

                self_list |= selected_list.removed

                for uid, (old_name, _) in selected_list.renamed.items():
                    self_list[uid] = old_name
            self.dump(username, UIDMap.get().uid_of(username))
            return True

        for list_name in LISTS:
            prev_list: Update = getattr(prev, list_name)
            selected_list: Update = getattr(selected, list_name)

            updated_added = {  # exclude users removed and re-added
                key: prev_list.added[key]
                for key in prev_list.added.keys()
                - selected_list.removed.keys()
            } | {  # exclude users added and removed afterwards
                key: selected_list.added[key]
                for key in selected_list.added.keys()
                - prev_list.removed.keys()
            }
            updated_removed = {  # exclude users added and removed afterwards
                key: prev_list.removed[key]
                for key in prev_list.removed.keys()
                - selected_list.added.keys()
            } | {  # exclude users removed and re-added
                key: selected_list.removed[key]
                for key in selected_list.removed.keys()
                - prev_list.added.keys()
            }

            prev_list.added = updated_added
            prev_list.removed = updated_removed

            common_renamed_keys = (
                prev_list.renamed.keys() & selected_list.renamed.keys()
            )
            extra_renamed_keys = (
                selected_list.renamed.keys() - prev_list.renamed.keys()
            )

            prev_list.renamed |= {
                key: (selected_list.renamed[key][0], prev_list.renamed[key][1])
                for key in common_renamed_keys
            } | {key: selected_list.renamed[key] for key in extra_renamed_keys}

        self.dump(username, UIDMap.get().uid_of(username))
        return True
