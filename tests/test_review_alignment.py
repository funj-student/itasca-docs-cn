import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('review_translation_batch', ROOT / 'scripts/review_translation_batch.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class ReviewAlignmentChecks(unittest.TestCase):
    def test_empty_signatures_are_not_paired(self):
        en = [((), ()), ((), ()), ((), ())]
        zh = [((), ()), ((), ()), ((), ())]
        self.assertEqual(module.align_pairs(en, zh), [])

    def test_nonempty_matching_signature_is_paired(self):
        en = [((), ()), (('1e5',), ('zone.face.apply',)), ((), ())]
        zh = [((), ()), (('1e5',), ('zone.face.apply',)), ((), ())]
        self.assertEqual(module.align_pairs(en, zh), [(1, 1)])

    def test_signature_tokens_ignore_plain_prose(self):
        en_sig = module.signature_tokens('This sentence has no numbers or command names.')
        zh_sig = module.signature_tokens('这句话没有数字或命令名。')
        self.assertEqual(en_sig, ((), ()))
        self.assertEqual(zh_sig, ((), ()))

if __name__ == '__main__':
    unittest.main()
