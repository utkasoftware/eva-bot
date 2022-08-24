from __future__ import annotations
from asyncio import AbstractEventLoop
from asyncio import get_event_loop
from enum import EnumMeta, IntEnum
from functools import partial, wraps
from typing import (
    Any,
    Callable,
    Coroutine,
    Iterable,
    NewType,
    NoReturn,
    Union
)


class StateMachine:

    State = NewType("State", IntEnum)
    StateId = NewType("StateId", int)
    UserId  = NewType("UserId", int)

    def __init__(this,
        name: str,
        states: EnumMeta,
        cold_cache: list[
            list[Union[UserId, StateId]]
        ] | None=None
        ) -> None:

        """
        name: The name for the current state machine. Required for exceptions logging.
        states: Instance of AbstractEnumMeta.
            The class itself should preferably inherit IntEnum and contain only int states.
        cold_cache: Cold cache from persistent database.
            Recommended for the correctness of the states after restarting the bot.

        """

        if not isinstance(states, EnumMeta):
            raise TypeError(
                (
                    "'states' class must be inherited from EnumMeta, "
                    "but got '{0}'".format(type(states).__name__)
                )
            )

        this.name = name
        this.states = states

        setattr(this.states, "_list", dict(
            this.states.__members__.items())
        )

        this._states_memory = this.Memory(name, this.states)
        if cold_cache: this.load_cc(cold_cache)
        this.Lock = this._states_memory.Lock

    async def set(this, user_id: UserId, state: State) -> None:
        this._states_memory.add(user_id, state)

    async def get(this, user_id: UserId) -> State:
        return this._states_memory.state_of(user_id)

    async def exists(this, user_id: UserId) -> bool:
        for key in this._states_memory.keys:
            if user_id == key:
                return True
        return False

    async def delete(this, user_id: UserId) -> None:
        this._states_memory.delete(user_id)

    async def get_keys(this) -> list[UserId]:
        return [k for k in this._states_memory.keys]

    async def iter_keys(this) -> Iterable:
        return this._states_memory.keys

    def load_cc(this, cache: list[list[Union[UserId, StateId]]]) -> None:
        for user in cache:
            this._states_memory.add(
                user[0],               # id
                this.states(user[1])   # state
            )

    @property
    def locked(this) -> bool:
        return this._states_memory._locked


    class Memory:

        def __init__(this, name: str, states: EnumMeta) -> None:
            this.name = name
            this._states = states
            this._locked = False
            this._memory: dict[StateMachine.UserId, StateMachine.StateId] = dict()
            this.Lock = partial(this.LockedMemory, this)

        def add(this,
            user_id: StateMachine.UserId,
            state: StateMachine.State
            ) -> None | NoReturn:

            if this._locked:
                raise this.MemoryIsLocked(this.name)

            this._safe_add(user_id, state)

        @property
        def keys(this) -> Iterable:
            yield from this._memory.keys()

        def state_of(this, user_id: StateMachine.UserId) -> StateMachine.State:
            state = this._memory.get(user_id)
            if state is None:
                # assume that zero is always used for the initial(default) state
                return this._states(0)

            return this._states(state)

        def _safe_add(this,
            user_id: StateMachine.UserId,
            state: StateMachine.State
            ) -> None:

            this._memory[user_id] = state.value

        def _lock(this) -> None:
            this._locked = True

        def _unlock(this) -> None:
            this._locked = False


        class LockedMemory:

            __slots__ = [
                "set", "get", "delete", "keys",
                "__lock", "__unlock"
            ]

            def __init__(this, parent: StateMachine.Memory) -> None:
                this.set = parent._safe_add
                this.get = parent.state_of
                this.delete = parent.delete
                this.keys = parent.keys
                this.__lock = parent._lock
                this.__unlock = parent._unlock

            def __enter__(this) -> StateMachine.Memory.LockedMemory:
                this.__lock()
                return this

            def __exit__(this, extype, exval, extraceb) -> None:
                this.__unlock()

            async def __aenter__(this) -> StateMachine.Memory.LockedMemory:
                this.__lock()

                this.set = this.__wrap_acontext__(this.set)
                this.get = this.__wrap_acontext__(this.get)
                this.delete = this.__wrap_acontext__(this.delete)

                return this

            async def __aexit__(this, aextype, aexval, aextraceb) -> None:
                this.__unlock()

            def __wrap_acontext__(this,
                _slot: Callable
                ) -> Callable[..., Coroutine]:
                @wraps(_slot)
                async def _aslot(this,
                    *args,
                    _loop: AbstractEventLoop | None = None,
                    **kwargs
                ) -> Any:
                    if not _loop:
                        _loop = get_event_loop()
                    cslot = partial(_slot, *args, **kwargs)
                    return await _loop.run_in_executor(None, cslot)
                return _aslot


        class MemoryIsLocked(Exception):
            def __init__(this, memory_name: str):
                this._msg = "'{0}' is currently locked.".format(memory_name)
                super().__init__(
                    this._msg.format(memory_name)
                )
