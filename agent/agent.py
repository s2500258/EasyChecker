from threading import Event

from runner import run_agent_loop
from runtime_state import AgentRuntimeState


# Main entry point for the agent.
# Console entry point for the agent.
# The actual worker loop lives in runner.py so the same collection/send logic
# can also power the Windows GUI without duplicating behavior.
def run_agent() -> None:
    run_agent_loop(
        state=AgentRuntimeState(),
        stop_event=Event(),
        log=print,
    )


if __name__ == "__main__":
    run_agent()
