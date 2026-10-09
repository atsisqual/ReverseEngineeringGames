import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RouteTests(unittest.TestCase):
    def run_route(self,name):
        cp=subprocess.run([sys.executable,str(ROOT/'portctl.py'),'route',name,'--json'],cwd=ROOT,text=True,capture_output=True,check=True)
        return json.loads(cp.stdout)
    def test_psx_alias_resolves_to_ps1(self):
        data=self.run_route('psx')
        self.assertEqual(data['platform'],'ps1')
        self.assertIn('retroarch-web',data['tools'])
    def test_ps2_prefers_play(self):
        data=self.run_route('ps2')
        self.assertEqual(data['status'],'official-experimental-browser')
        self.assertEqual(data['tools'][0],'play-ps2')
    def test_unknown_falls_back_to_other(self):
        data=self.run_route('mystery-console')
        self.assertEqual(data['platform'],'other')
        self.assertEqual(data['primary'],'research-first')
if __name__=='__main__': unittest.main()
