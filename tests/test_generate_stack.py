import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('generate_stack',ROOT/'scripts/generate_stack.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
NS={'s':'http://www.w3.org/2000/svg'}

class StackTests(unittest.TestCase):
 def test_categories_and_inventory(self):
  self.assertEqual([len(items) for _,items in module.GROUPS],[5,6,9,4])
  labels=[label for _,items in module.GROUPS for label,_,_ in items]
  self.assertEqual(len(labels),len(set(labels)))
  self.assertIn('Kali Linux',labels)
  self.assertIn('Metasploit',labels)

 def test_generated_assets_are_current_and_self_contained(self):
  for mobile,name in [(False,'stack.svg'),(True,'stack-mobile.svg')]:
   with self.subTest(name=name):
    svg=module.generate(mobile)
    self.assertEqual(svg,(ROOT/'assets'/name).read_text())
    root=ET.fromstring(svg)
    self.assertEqual(root.attrib['viewBox'],'0 0 720 1340' if mobile else '0 0 1200 700')
    entries=[e.attrib['data-entry'] for e in root.iter() if 'data-entry' in e.attrib]
    self.assertEqual(entries,[i[0] for _,items in module.GROUPS for i in items])
    ids={e.attrib['id'] for e in root.iter() if 'id' in e.attrib}
    for e in root.iter():
     if 'href' in e.attrib:
      self.assertTrue(e.attrib['href'].startswith('#'))
      self.assertIn(e.attrib['href'][1:],ids)
    self.assertIsNone(root.find('.//s:image',NS))
    self.assertIsNone(root.find('.//s:script',NS))
    self.assertIsNotNone(root.find('s:desc',NS))

 def test_readme_picture_and_alt(self):
  readme=(ROOT/'README.md').read_text()
  section=readme.split('### Security & Engineering Stack\n',1)[1].split('### Featured Systems',1)[0]
  for token in ['assets/stack.svg','assets/stack-mobile.svg','Kali Linux','Metasploit']:
   self.assertIn(token,section)
  self.assertNotIn('img.shields.io',section)

 def test_featured_icons_have_no_caption_or_background_card(self):
  for mobile in (False,True):
   root=ET.fromstring(module.generate(mobile))
   featured=[e for e in root.iter() if 'data-featured' in e.attrib]
   self.assertEqual([e.attrib['data-featured'] for e in featured],module.FEATURED)
   self.assertEqual(root.findall('.//s:text[@class="feature"]',NS),[])
   for group in featured:
    self.assertIsNone(group.find('s:text',NS))
    self.assertIsNone(group.find('s:rect',NS))
    self.assertEqual(group.find('s:title',NS).text,group.attrib['aria-label'])
    self.assertEqual(group.find('s:use',NS).attrib['width'],'80')
   for key in module.FEATURED_ART.values():
    self.assertIsNotNone(root.find(f'.//s:symbol[@id="icon-featured-{key}"]',NS))

if __name__=='__main__':unittest.main()
