"""Validate downloadable research artifacts against independently derived results."""
import csv
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from ear import studio


@unittest.skipUnless(shutil.which('node'), 'Node is only needed for client artifact checks')
class ReferenceArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='EAR reference artifacts ')
        cls.root = Path(cls.temp.name)
        script = r'''
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync(process.argv[1],'utf8');
const reference=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const start=html.indexOf('// The reference workflow is authored');
const end=html.indexOf('function pauseAnimations()',start);
if(start<0||end<0)throw Error('Missing reference workflow functions');
const downloads=[];
const context=vm.createContext({Blob,TextEncoder,Uint8Array,Uint32Array,DataView,
 atob,DATA:{reference},l:(en,zh)=>en,esc:s=>String(s),
 download:(blob,name)=>downloads.push({blob,name}),toast:()=>{}});
vm.runInContext(html.slice(start,end),context);
(async()=>{
 for(const mode of ['constant','decay'])for(const epsilon of [.05,.1,.2]){
  vm.runInContext(`demoGoal='${mode}';demoEpsilon=${epsilon};demoDownload('bundle')`,context);
  const {blob,name}=downloads.pop();
  if(blob.type!=='application/zip')throw Error('Incorrect bundle media type');
  fs.writeFileSync(require('node:path').join(process.argv[3],name),Buffer.from(await blob.arrayBuffer()));
 }
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        subprocess.run(['node', '-e', script, str(studio.TEMPLATE),
                        str(studio.TEMPLATE.parent / 'reference.json'), str(cls.root)],
                       capture_output=True, text=True, check=True, timeout=15)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_objectives_produce_correct_evidence_and_distinct_manuscripts(self):
        manuscripts = []
        for mode in ['constant', 'decay']:
            with self.subTest(mode=mode), zipfile.ZipFile(self.root / f'EAR-research-{mode}.zip') as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertEqual(set(bundle.namelist()), {
                    'README.md', 'RESEARCH_BRIEF.md', 'PROGRESS.md', 'proof.md',
                    'checks/trajectory.csv', 'paper/v1/main.md', 'REVIEW_FEEDBACK.md',
                    'paper/v2/main.md', 'paper/v2/main.tex', 'paper/v2/main.pdf',
                    'EVIDENCE_LEDGER.md', 'provenance.json', 'verify.py',
                })
                provenance = json.loads(bundle.read('provenance.json'))
                self.assertEqual(provenance['objective'], mode)
                self.assertEqual(provenance['model_calls'], 0)
                self.assertFalse(provenance['novel_research'])
                self.assertFalse(provenance['conference_acceptance'])
                self.assertEqual(provenance['review'], 'prepared_demonstration_feedback')
                rows = list(csv.DictReader(io.StringIO(bundle.read('checks/trajectory.csv').decode())))
                self.assertEqual(len(rows), 81)
                for k, row in enumerate(rows):
                    # Closed-form solution, independently of the browser recurrence.
                    x1 = (1.1 * .9 ** k - .1 if mode == 'constant' else
                          .9 ** k - .01 * sum(.9 ** (k - 1 - s) / (s + 1) for s in range(k)))
                    x2 = 1 if k == 0 else 0
                    self.assertAlmostEqual(float(row['x1']), x1, places=12)
                    self.assertEqual(float(row['x2']), x2)
                    self.assertAlmostEqual(float(row['norm']), math.hypot(x1, x2), places=12)
                    self.assertLessEqual(float(row['norm']), float(row['bound']) + 1e-12)
                self.assertTrue(bundle.read('paper/v2/main.pdf').startswith(b'%PDF-'))
                self.assertIn('INTENTIONALLY INCOMPLETE', bundle.read('paper/v1/main.md').decode())
                manuscript = bundle.read('paper/v2/main.md').decode()
                self.assertIn('No model calls', manuscript)
                self.assertIn('not a proof', manuscript)
                self.assertIn('0 < eta < 2 / L', manuscript)
                self.assertIn('||e[k]|| <= epsilon[k]', manuscript)
                self.assertIn('positive definite', bundle.read('paper/v2/main.tex').decode())
                manuscripts.append(manuscript)
        self.assertNotEqual(*manuscripts)

    def test_exported_check_runs_without_third_party_dependencies(self):
        for mode in ['constant', 'decay']:
            folder = self.root / mode
            folder.mkdir()
            with zipfile.ZipFile(self.root / f'EAR-research-{mode}.zip') as bundle:
                bundle.extractall(folder)
            result = subprocess.run([sys.executable, 'verify.py'], cwd=folder,
                                    capture_output=True, text=True, check=True, timeout=5)
            self.assertIn('Verified 81 trajectory states', result.stdout)

    def test_error_levels_change_every_exported_trajectory(self):
        for mode in ['constant', 'decay']:
            for epsilon in [.05, .1, .2]:
                suffix = '' if epsilon == .1 else f'-e{epsilon:.2f}'
                with self.subTest(mode=mode, epsilon=epsilon), zipfile.ZipFile(
                        self.root / f'EAR-research-{mode}{suffix}.zip') as bundle:
                    self.assertIsNone(bundle.testzip())
                    provenance = json.loads(bundle.read('provenance.json'))
                    self.assertEqual(provenance['error_level'], epsilon)
                    rows = list(csv.DictReader(io.StringIO(
                        bundle.read('checks/trajectory.csv').decode())))
                    for k, row in enumerate(rows):
                        # Solve the affine iteration independently in closed form.
                        x1 = ((1 + epsilon) * .9**k - epsilon if mode == 'constant'
                              else .9**k - .1 * epsilon * sum(
                                  .9**(k - 1 - s) / (s + 1) for s in range(k)))
                        self.assertAlmostEqual(float(row['x1']), x1, places=12)
                        self.assertAlmostEqual(float(row['norm']),
                                               math.hypot(x1, 1 if k == 0 else 0), places=12)
                    self.assertIn(f'{epsilon:.2f}', bundle.read('paper/v2/main.md').decode())
                    folder = self.root / f'{mode}{suffix}-verified'
                    folder.mkdir()
                    bundle.extractall(folder)
                result = subprocess.run([sys.executable, 'verify.py'], cwd=folder,
                                        capture_output=True, text=True, check=True, timeout=5)
                self.assertIn('Verified 81 trajectory states', result.stdout)


if __name__ == '__main__':
    unittest.main()
