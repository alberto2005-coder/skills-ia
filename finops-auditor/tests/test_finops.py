import unittest
import sys
import os

# Añadir la ruta absoluta de la carpeta scripts de este paquete específico
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.abspath(os.path.join(current_dir, '../scripts'))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from finops_analyzer import analyze_resources  # noqa: E402

class TestFinOpsAnalyzer(unittest.TestCase):
    
    def test_clean_infrastructure(self):
        data = {
            "resources": [
                {"id": "i-01234", "type": "compute", "monthly_cost": 100.0, "avg_cpu_utilization": 65},
                {"id": "vol-56789", "type": "storage", "monthly_cost": 50.0, "status": "attached", "utilization": 80}
            ]
        }
        result = analyze_resources(data)
        self.assertEqual(result["finops_score"], 100)
        self.assertEqual(result["total_estimated_waste"], 0.0)

    def test_waste_detection(self):
        data = {
            "resources": [
                {"id": "eip-dead", "type": "network", "monthly_cost": 10.0, "status": "unattached"},
                {"id": "i-over", "type": "compute", "monthly_cost": 200.0, "avg_cpu_utilization": 3}
            ]
        }
        result = analyze_resources(data)
        self.assertLess(result["finops_score"], 100)
        self.assertGreater(result["total_estimated_waste"], 0.0)
        self.assertEqual(len(result["findings"]), 2)

if __name__ == "__main__":
    unittest.main()