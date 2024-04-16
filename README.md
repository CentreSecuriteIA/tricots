# TRICOT: Trace Interception and Collection Tool

TRICOT is a simple single-file tool to monitor and edit the messages sent to the openai api using monkey-patching.

TRICOT is meant to collect traces of LLM-agents and scaffoldings and to alter their behavior without needing to modify nor understand the codebase of the agent.

TRICOT was developped to enable monitoring as part of BELLS: Benchmarks for the Evaluation of LLM Supervisors.

## Installation

You can install and use TRICOT in one of two ways:
- Copy the [`tricot.py`](./src/tricot.py) file into your project and import it. That's it.
- OR Install it using pip: `pip install git+https://github.com/ddorn/tricot.git`

## Usage

This single file module is a monkey-patch for the openai api that enables:
- Logging of all calls to the openai api
- Modification of the messages sent to the api before sending them

TRICOT contains two main functions:
- `patch_openai(edit_call)`: Patches the openai api to add logging, with an optional function to edit the list of messages before sending them.
- `new_log_file(path)`: Sets the log file to use, should be before each individual run of the LLM-app to monitor.

### Example: Logging the runs of an agent asked to answer in French

```python
import tricot

agent = ...
tasks = ["task1", "task2", "task3"]

def edit_call(messages):
    # 1. We can do anything we want with the messages here, and it's fine to modify the list in place.
    # For example we can modify the system prompt to ask the model to always answer in French:
    messages[0]['content'] += "\n\nImportant: always answer in French."
    return messages

# 2. We patch the openai api to log all calls and edit the messages before sending them.
tricot.patch_openai(edit_call)

for task in tasks:
    # 3. We set the log file to use for this task.
    tricot.new_log_file(f"logs/{task}.log")
    # 4. We run the agent as usual.
    agent.run(task)
```

This example shows the main features of TRICOT:
1. Any user defined `edit_call` function can modify the messages before sending them, if needed.
2. The `patch_openai` needs to be called at least once to enables logging, with an optional `edit_call` function. `path_openai` can be called multiple times, especially if the `edit_call` function needs to change.
3. The `new_log_file` function should be called at least once, and before each independent run of the LLM-app/agent.
4. The agent can be run as usual, without any modification to its codebase.

Running this script with an otherwise defined agent will create three log files, `logs/task1.log`, `logs/task2.log`, and `logs/task3.log`, with the messages sent to the openai api, modified to ask the model to always answer in French.

### Structure of the log files

The log files are in the [jsonlines](http://jsonlines.org/) format, with one json-encoded API call per line. Each API call is a dictionary with the following structure:
```python
# One line of the log file = one API call
{
    "timestamp": "2021-09-01T12:34:56.789012",
    "messages": [
        {
            "role": "system or user or assistant",
            "content": "content of the first message",
        },
        ...
    ]
}
```

The last message in the `messages` field will always be the answer given by the model, so that `messages[:-1]` are messages sent to the API, and `messages[-1]` is the output of the API.

## Limitations

TRICOT is a simple tool with a few limitations, but should be easy to extend to fit your needs:
- It works only with the OpenAI API (albeit all versions of it)
- It requires the agent to be written in Python and that it is possible to add tricot to the runtime.
- It requires that the agent can be imported and run as a function call, i.e. it would not work with agents that can only be run from the command line...
    - ... in this case, TRICOT can still be used by editing the code of the agent to call the pathing function, anytime before running.

## Future work

Future improvement to TRICOT might include:
- Support for other APIs
- Support for changing the model used by the agent (e.g. to use Anthropic API on codebase written only for OpenAI API)
- Interactive visualization of the logs
- Interactive editing of the logs, to manually inspect and modify the messages sent to the API

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

TRICOT was developped by Diego Dorn, as part of the BELLS project, for the CeSIA — Centre pour la Sécurité de l'IA.
