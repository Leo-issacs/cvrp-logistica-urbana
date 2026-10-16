"""Pruebas del manejo de estados del solver y de la validez del modelo B.

Uso:  python -m unittest discover -s tests -v
La prueba con limite de tiempo e incumbente (~20 s) solo corre con CVRP_PRUEBAS_LENTAS=1.
"""
import math, os, sys, unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'src'))
import pulp
import resolver_cvrp_arcos as R

XY, Q_, CAP, DEP = R.leer(RAIZ / 'data' / 'instancia.txt')
D = R.matriz(XY)
OPT_LIBRE, OPT_TRES = 318.9894867478301, 339.1646737615703


class Clasificacion(unittest.TestCase):
    def test_tabla_de_estados(self):
        c = R.clasificar_estado
        self.assertEqual(c(pulp.LpStatusOptimal, pulp.LpSolutionOptimal)[0], 'optimo_probado')
        # PuLP dice 'Optimal' aunque CBC pare por tiempo: no es un certificado
        self.assertEqual(c(pulp.LpStatusOptimal, pulp.LpSolutionIntegerFeasible)[0], 'factible_sin_prueba')
        self.assertEqual(c(pulp.LpStatusInfeasible, pulp.LpSolutionInfeasible)[0], 'sin_solucion_factible')
        self.assertEqual(c(pulp.LpStatusNotSolved, pulp.LpSolutionNoSolutionFound)[0], 'sin_solucion_factible')
        self.assertEqual(c(pulp.LpStatusUnbounded, pulp.LpSolutionUnbounded)[0], 'fallo_solver')
        self.assertEqual(c(pulp.LpStatusUndefined, pulp.LpSolutionNoSolutionFound)[0], 'fallo_solver')


class Solver(unittest.TestCase):
    def test_optimo_probado_modelo_B(self):
        rutas, t = R.exacto(Q_, CAP, DEP, D, modelo="B")
        self.assertEqual(t['estado'], 'optimo_probado'); self.assertTrue(t['optimo_probado'])
        self.assertAlmostEqual(t['objetivo'], OPT_LIBRE, places=6)
        self.assertEqual((t['constraints'], t['sec']), (154, 0))
        self.assertAlmostEqual(sum(r['distancia'] for r in R.verificar(rutas, Q_, CAP, DEP, D)), OPT_LIBRE, places=6)
        self.assertAlmostEqual(t['total_s'], t['build_s'] + t['solve_s'] + t['reconstruct_s'], places=6)

    def test_tres_rutas_modelo_B(self):
        rutas, t = R.exacto(Q_, CAP, DEP, D, fixed_k=3, modelo='B')
        self.assertEqual((t['estado'], len(rutas)), ('optimo_probado', 3))
        self.assertAlmostEqual(t['objetivo'], OPT_TRES, places=6)

    def test_infactible(self):
        # con demanda 146 y Q = 50 hacen falta al menos 3 rutas
        rutas, t = R.exacto(Q_, CAP, DEP, D, fixed_k=2, exigir_optimo=False)
        self.assertEqual((t['estado'], rutas, t['objetivo']), ('sin_solucion_factible', None, None))
        with self.assertRaises(R.ResultadoNoOptimo) as cm:
            R.exacto(Q_, CAP, DEP, D, fixed_k=2)
        self.assertEqual(cm.exception.estado, 'sin_solucion_factible')

    def test_limite_sin_incumbente(self):
        rutas, t = R.exacto(Q_, CAP, DEP, D, fixed_k=3, limite=0.05, exigir_optimo=False, modelo='A')
        self.assertFalse(t['optimo_probado']); self.assertNotEqual(t['estado'], 'optimo_probado')
        if t['estado'] == 'sin_solucion_factible': self.assertIsNone(rutas)

    @unittest.skipUnless(os.environ.get('CVRP_PRUEBAS_LENTAS') == '1', 'prueba lenta (~20 s)')
    def test_limite_con_incumbente_no_es_optimo(self):
        rutas, t = R.exacto(Q_, CAP, DEP, D, fixed_k=3, limite=20, exigir_optimo=False, modelo='A')
        self.assertIn(t['estado'], ('factible_sin_prueba', 'optimo_probado'))
        if t['estado'] == 'factible_sin_prueba':
            self.assertFalse(t['optimo_probado']); self.assertGreaterEqual(t['objetivo'], OPT_TRES - 1e-6)
            self.assertEqual(R.verificar(rutas, Q_, CAP, DEP, D) is not None, True)
            with self.assertRaises(R.ResultadoNoOptimo): R.exacto(Q_, CAP, DEP, D, fixed_k=3, limite=1, modelo='A')

    def test_fallo_del_solver(self):
        with mock.patch.object(pulp.LpProblem, 'solve', side_effect=pulp.PulpSolverError('cbc no disponible')):
            rutas, t = R.exacto(Q_, CAP, DEP, D, exigir_optimo=False)
        self.assertEqual((t['estado'], rutas), ('fallo_solver', None))
        with mock.patch.object(pulp.LpProblem, 'solve', side_effect=OSError('sin ejecutable')):
            with self.assertRaises(R.ResultadoNoOptimo) as cm: R.exacto(Q_, CAP, DEP, D)
        self.assertEqual(cm.exception.estado, 'fallo_solver')

    def test_no_reconstruye_desde_valores_fraccionarios(self):
        A = [(1, 2), (2, 1)]
        for valor in (0.5, None, 0.999):
            x = {a: mock.Mock(value=mock.Mock(return_value=valor)) for a in A}
            with self.assertRaises(ValueError): R.reconstruir(x, A, [2], 1, 2)

    def test_modelo_B_exige_demandas_positivas(self):
        q = dict(Q_); q[2] = 0
        for m in 'BC':
            with self.assertRaises(ValueError): R.construir_modelo(q, CAP, DEP, D, m)
        R.construir_modelo(q, CAP, DEP, D, 'A')  # con subrutas explicitas si se admite


class Cotas(unittest.TestCase):
    def test_modelos_tienen_el_tamano_esperado(self):
        n = {m: len(R.construir_modelo(Q_, CAP, DEP, D, m)[0].constraints) for m in 'ABC'}
        self.assertEqual(n, {'A': 1167, 'B': 154, 'C': 264})

    def test_cotas_de_C_validas_en_toda_ruta_factible(self):
        import itertools as it
        C = sorted(set(Q_) - {DEP})
        for k in range(1, len(C) + 1):
            for S in it.combinations(C, k):
                if sum(Q_[i] for i in S) > CAP: continue
                for p in it.permutations(S):
                    r, rem = (DEP,) + p + (DEP,), sum(Q_[i] for i in p)
                    for i, j in zip(r, r[1:]):
                        self.assertTrue(Q_[j] <= rem <= CAP - Q_[i]); rem -= Q_[j]


if __name__ == '__main__':
    unittest.main()
