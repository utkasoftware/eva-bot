from __future__ import annotations
from asyncio import AbstractEventLoop, iscoroutinefunction
from asyncio import sleep as asleep
from typing import Any, Protocol

class StateMachineSyncer:

    """
    State Synchronizer from in-memory dict to DB.

    """


    def __init__(this,
        loop: AbstractEventLoop,
        fsm: "StateMachine",
        updater: StateMachineSyncer.StateUpdater,
        interval: int,  # seconds
        on_error: StateMachineSyncer.OnError
    ) -> None:

        this.__loop = loop
        this.__fsm  = fsm
        this.__updater  = updater
        this.__interval = interval
        this.__on_error = on_error
        this.__syncing = True

    def run(this) -> None:
        this.__loop.create_task(this._run_syncer_task())

    def stop(this) -> None:
        this.__syncing = False

    async def _syncer(this) -> Any:

        for key in await this.__fsm.iter_keys():
            state = await this.__fsm.get(key)
            await this.__updater(
                key,
                state.value
            )

    async def _run_syncer_task(this) -> None:
        while this.__syncing:
            if not iscoroutinefunction(this.__updater):
                raise TypeError(
                    "'{}' is not coroutine".format(this.__updater)
                )

            try:
                await asleep(this.__interval)  # сначала спим, чтобы не обновлять только что полученный кеш
                await this._syncer()
            except Exception as syncerex:
                this.__on_error(
                    this.__fsm.name,
                    syncerex
                )


    class OnError(Protocol):
        def __call__(this, memory_name: str, ex_trace: Exception
        ) -> None:
            """
            OnError handler

            """


    class StateUpdater(Protocol):
        async def __call__(this, state_for: int, state: int) -> None:
            """
            Database class state_update method protocol
            """
