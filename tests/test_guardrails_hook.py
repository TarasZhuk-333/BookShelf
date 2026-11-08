"""Synthetic inputs only: no deletion commands are ever executed."""

import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'guardrails_hook', Path(__file__).parents[1] / 'scripts' / 'guardrails_hook.py')
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def event(command, cwd=r'C:\Users\user\BookShelf', tool='Bash'):
    return {'hook_event_name': 'PreToolUse', 'tool_name': tool,
            'cwd': cwd, 'tool_input': {'command': command}}


class GuardTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop('BOOKSHELF_GUARD_TEST_ROOT', None)

    def test_default_root_without_override(self):
        sample = event('rm C:/Users/user/BookShelf-KB/Decisions/note.md')
        self.assertEqual(hook.decision(sample)['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(hook.decision(event('rm C:/Temp/GuardTest/Decisions/test-adr.md')), {})

    def test_test_root_replaces_default(self):
        with patch.dict(os.environ, {'BOOKSHELF_GUARD_TEST_ROOT': 'C:/Temp/GuardTest/Decisions/'}):
            for command in (
                'Remove-Item -LiteralPath C:/Temp/GuardTest/Decisions/test-adr.md',
                'rm -rf C:/Temp/GuardTest',
                'rm C:/TEMP/GUARDTEST/DECISIONS/test-adr.md',
            ):
                with self.subTest(command=command):
                    output = hook.decision(event(command))['hookSpecificOutput']
                    self.assertEqual(output['permissionDecision'], 'deny')
            for command in (
                'rm C:/Users/user/BookShelf-KB/Decisions/note.md',
                'rm C:/Temp/GuardTest/Decisions-old/test-adr.md',
                'Get-Content C:/Temp/GuardTest/Decisions/test-adr.md',
            ):
                with self.subTest(command=command):
                    self.assertEqual(hook.decision(event(command)), {})

    def test_forbidden_shell_inputs(self):
        cases = [
            event(r'Remove-Item -LiteralPath "C:\Users\user\BookShelf-KB\Decisions\ADR-001 Technology Stack.md"'),
            event(r'del C:\Users\user\BookShelf-KB\Decisions\note.md'),
            event('rm -rf C:/Users/user/BookShelf-KB/Decisions'),
            event('rm -rf ../BookShelf-KB'),
            event('Remove-Item -Recurse C:/Users/user/BookShelf-KB'),
            event('rm Decisions/note.md', r'C:\Users\user\BookShelf-KB'),
            event('rm note.md', r'C:\Users\user\BookShelf-KB\Decisions'),
            event('rm ../Decisions/note.md', r'C:\Users\user\BookShelf-KB\Components'),
            event('rm C:/USERS/USER/BOOKSHELF-KB/DECISIONS/note.md'),
            event('rm C:/Users/user/BookShelf-KB/*'),
            event('rm C:/Users/user/BookShelf-KB/Decisions/note.md', tool='exec_command'),
        ]
        for sample in cases:
            with self.subTest(sample=sample):
                output = hook.decision(sample)['hookSpecificOutput']
                self.assertEqual(output['permissionDecision'], 'deny')
                self.assertEqual(output['hookEventName'], 'PreToolUse')

    def test_allowed_inputs(self):
        for command in (
            'pytest',
            'Get-Content C:/Users/user/BookShelf-KB/Decisions/note.md',
            'rm C:/Users/user/BookShelf-KB/Components/note.md',
            'rm C:/Users/user/BookShelf-KB/Decisions-old/note.md',
            'rm C:/Users/user/BookShelf-KB/Decisions/../Components/note.md',
        ):
            with self.subTest(command=command):
                self.assertEqual(hook.decision(event(command)), {})

    def test_patch_delete(self):
        sample = event('*** Begin Patch\n*** Delete File: C:/Users/user/BookShelf-KB/Decisions/note.md\n*** End Patch', tool='apply_patch')
        self.assertEqual(hook.decision(sample)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_mcp_delete(self):
        sample = event('', tool='mcp__filesystem__delete_file')
        sample['tool_input'] = {'path': 'C:/Users/user/BookShelf-KB/Decisions/note.md'}
        self.assertEqual(hook.decision(sample)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_other_event(self):
        sample = event('rm C:/Users/user/BookShelf-KB/Decisions/note.md')
        sample['hook_event_name'] = 'PostToolUse'
        self.assertEqual(hook.decision(sample), {})

    def test_stdin_stdout_protocol(self):
        for command, expected in [('pytest', {}), ('rm C:/Users/user/BookShelf-KB/Decisions/note.md', None)]:
            with patch('sys.stdin', io.StringIO(json.dumps(event(command)))), patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(hook.main(), 0)
                parsed = json.loads(output.getvalue())
                if expected is None:
                    self.assertEqual(parsed['hookSpecificOutput']['permissionDecision'], 'deny')
                else:
                    self.assertEqual(parsed, expected)

    def test_invalid_json(self):
        for value in ('{', '[]'):
            with patch('sys.stdin', io.StringIO(value)), patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(hook.main(), 2)


if __name__ == '__main__':
    unittest.main()
