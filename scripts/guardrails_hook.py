"""Test PreToolUse guard; inspects input only and never executes commands.

Recognizes literal shell deletion commands, apply_patch deletions and deletion
MCP tools. Not a shell interpreter or a substitute for filesystem permissions:
encoded commands, variable-built paths, aliases and arbitrary programs may evade
this test guard. No filesystem reads, writes or path resolution through symlinks.
"""

import json
import ntpath
import os
import re
import sys


PROTECTED = r"C:\Users\user\BookShelf-KB\Decisions"
DELETE = re.compile(
    r"(?i)(?<![\w-])(?:remove-item|erase|del|rm|rmdir|rd|unlink|"
    r"delete_file|delete_directory|shutil\.rmtree|os\.remove|os\.unlink)"
    r"(?![\w-])"
)
TOKEN = re.compile(r'''"([^"]*)"|'([^']*)'|([^\s;,|&()]+)''')


def protected_target(value, cwd, recursive=False):
    """Match descendants; recursive removal of an ancestor is also forbidden."""
    path = value.strip().replace('/', '\\')
    if path.startswith('\\\\?\\'):
        path = path[4:]
    if not ntpath.isabs(path):
        path = ntpath.join(cwd, path)
    path = ntpath.normcase(ntpath.normpath(path)).rstrip('\\')
    root = os.environ.get('BOOKSHELF_GUARD_TEST_ROOT') or PROTECTED
    root = ntpath.normcase(ntpath.normpath(root)).rstrip('\\')
    # A wildcard may include Decisions or a protected descendant. Be conservative.
    if '*' in path or '?' in path:
        path = re.split(r'[*?]', path, maxsplit=1)[0].rstrip('\\')
        recursive = True
    return (path == root or path.startswith(root + '\\')
            or (recursive and bool(path) and root.startswith(path + '\\')))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def decision(event):
    if event.get('hook_event_name') != 'PreToolUse':
        return {}
    tool = event.get('tool_name', '')
    data = event.get('tool_input', {})
    cwd = event.get('cwd', r'C:\Users\user\BookShelf')
    if not isinstance(tool, str) or not isinstance(cwd, str):
        raise ValueError('tool_name and cwd must be strings')
    values = list(strings(data))
    forbidden = False
    for value in values:
        if tool in ('apply_patch', 'Edit', 'Write'):
            for target in re.findall(r'^\*\*\* Delete File: (.+)$', value, re.M):
                forbidden |= protected_target(target.strip(), cwd)
        if tool == 'Bash' or tool == 'exec_command':
            if DELETE.search(value):
                recursive = bool(re.search(r'(?i)-recurse\b|-[a-z]*r[a-z]*\b|/s\b|rmtree', value))
                for match in TOKEN.finditer(value):
                    token = next(part for part in match.groups() if part is not None)
                    forbidden |= protected_target(token, cwd, recursive)
        elif tool.startswith('mcp__') and re.search(r'(?i)delete|remove|unlink|rmdir', tool):
            forbidden |= protected_target(value, cwd, recursive=True)
    if not forbidden:
        return {}  # No permission grant: leave other controls intact.
    return {'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': (
            'BL-01: deletion in BOOKSHELF_GUARD_TEST_ROOT is forbidden.'
            if os.environ.get('BOOKSHELF_GUARD_TEST_ROOT') else
            'BL-01: deletion in BookShelf-KB/Decisions is forbidden.'
        ),
    }}


def main():
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('hook input must be an object')
        result = decision(event)
    except (ValueError, TypeError) as error:
        # Codex supports exit 2 with a blocking reason on stderr.
        print('Invalid hook input: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
