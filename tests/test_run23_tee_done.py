"""tee_cmd writes logs/<label>.done -- ONE canonical completion signal.

Run 23's orchestrator waited on `[tee_cmd] <label> exit=` -- a line tee_cmd
prints to STDOUT only -- by grepping the LOG, which carries `EXIT=N`
instead. The waiter timed out; ~25 minutes of wall were lost to a completion
signal split across two streams. The `.done` file holds the exit code and
appears exactly when the child exits; a waiter polls os.path.exists of it
and nothing else.
"""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEE = os.path.join(ROOT, 'tests', 'stress', 'tee_cmd.py')


def _tee(td, label, *cmd):
    return subprocess.run(
        [sys.executable, '-X', 'utf8', TEE, '--workdir', td, label,
         '--', sys.executable, '-c', *cmd],
        capture_output=True, text=True, cwd=ROOT)


class TestTeeDone(unittest.TestCase):
    def test_done_carries_the_exit_code(self):
        with tempfile.TemporaryDirectory() as td:
            _tee(td, 'ok', 'print("hi")')
            _tee(td, 'bad', 'import sys; sys.exit(3)')
            self.assertEqual(
                open(os.path.join(td, 'logs', 'ok.done')).read().strip(), '0')
            self.assertEqual(
                open(os.path.join(td, 'logs', 'bad.done')).read().strip(),
                '3')

    def test_reused_label_gets_its_own_done(self):
        """Reused labels get numbered logs (lap semantics); the .done files
        must pair 1:1 with them or a waiter watches lap 1's marker while
        lap 2 runs."""
        with tempfile.TemporaryDirectory() as td:
            _tee(td, 'lap', 'pass')
            _tee(td, 'lap', 'import sys; sys.exit(2)')
            self.assertEqual(
                open(os.path.join(td, 'logs', 'lap.done')).read().strip(),
                '0')
            self.assertEqual(
                open(os.path.join(td, 'logs', 'lap.2.done')).read().strip(),
                '2')


if __name__ == '__main__':
    unittest.main(verbosity=1)
