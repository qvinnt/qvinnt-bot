from aiogram.fsm.state import State
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import ShowMode, StartMode
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.kbd import Button, Start
from aiogram_dialog.widgets.kbd.button import OnClick
from aiogram_dialog.widgets.text import Text


class StartWithData(Start):
    def __init__(
        self,
        text: Text,
        id: str,  # noqa: A002
        state: State,
        data: dict | None = None,
        on_click: OnClick | None = None,
        show_mode: ShowMode | None = None,
        mode: StartMode = StartMode.NORMAL,
        when: WhenCondition = None,
        start_data_keys: list[str] | None = None,
        dialog_data_keys: list[str] | None = None,
    ) -> None:
        super().__init__(
            text=text,
            id=id,
            state=state,
            data=data,
            on_click=on_click,
            show_mode=show_mode,
            mode=mode,
            when=when,
        )
        self.start_data_keys = start_data_keys
        self.dialog_data_keys = dialog_data_keys

    async def _on_click(
        self,
        callback: CallbackQuery,
        button: Button,  # noqa: ARG002
        manager: DialogManager,
    ) -> None:
        if self.user_on_click:
            await self.user_on_click(callback, self, manager)

        data = {}

        if isinstance(manager.start_data, dict) and self.start_data_keys is not None:
            data.update({key: manager.start_data.get(key) for key in self.start_data_keys})

        if isinstance(manager.dialog_data, dict) and self.dialog_data_keys is not None:
            data.update({key: manager.dialog_data.get(key) for key in self.dialog_data_keys})

        if self.start_data:
            data.update(self.start_data)  # pyright: ignore[reportCallIssue, reportArgumentType]

        await manager.start(
            state=self.state,
            data=data,
            mode=self.mode,
            show_mode=self.show_mode,
        )
