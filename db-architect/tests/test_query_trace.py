import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import query_trace  # noqa: E402

N_PLUS_ONE = '''
def pedidos_por_usuario(db, users):
    resultado = []
    for user in users:
        resultado.append(db.query(Order).filter_by(user_id=user.id).all())
    return resultado
'''

EAGER = '''
def pedidos_por_usuario(db):
    users = db.query(User).options(selectinload(User.orders)).all()
    for user in users:
        print(user.orders)
    return users
'''

NO_LOOP = '''
def un_pedido(db, order_id):
    return db.query(Order).get(order_id)
'''


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = query_trace.main(argv)
    return code, out.getvalue()


class TestQueryTrace(unittest.TestCase):

    def test_flags_query_inside_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repo.py"
            target.write_text(N_PLUS_ONE, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["findings"][0]["rule"], "consulta-en-bucle")
            self.assertIn("users", report["findings"][0]["message"])

    def test_eager_loading_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repo.py"
            target.write_text(EAGER, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_query_outside_loop_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repo.py"
            target.write_text(NO_LOOP, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_fail_on_controls_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repo.py"
            target.write_text(N_PLUS_ONE, encoding="utf-8")
            strict, _ = run(["--path", str(target), "--fail-on", "medium"])
            off, _ = run(["--path", str(target), "--fail-on", "none"])
            self.assertEqual((strict, off), (1, 0))

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe-esta-ruta"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
