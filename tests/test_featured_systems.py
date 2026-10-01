from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ['Vuln-Eval-Platform', 'Arborchive', 'IPI-Security-Vault', 'KaliMac', 'VulnArc']
ICONS = ['🛡️', '🌳', '💉', '🗡️', '🗂️']
NS = {'s': 'http://www.w3.org/2000/svg'}


class FeaturedSystemsTests(unittest.TestCase):
    def setUp(self):
        readme = (ROOT / 'README.md').read_text()
        self.section = readme.split('### Featured Systems\n', 1)[1].split('### Research Log', 1)[0]

    def test_featured_projects_have_ordered_numbers_and_icons(self):
        headings = re.findall(r'^#### (.+ / .+)$', self.section, re.MULTILINE)
        self.assertEqual(len(headings), len(PROJECTS))
        for number, (heading, project, icon) in enumerate(zip(headings, PROJECTS, ICONS), 1):
            with self.subTest(project=project):
                self.assertTrue(heading.startswith(icon + ' '))
                self.assertIn(f'`{number:02} / {project}`', heading)

    def test_new_project_summaries_match_their_roles(self):
        self.assertIn('A project-scoped Kali CLI for macOS.', self.section)
        self.assertIn('output and exit codes to the original terminal', self.section)
        self.assertIn('A repo-first workspace for human–AI vulnerability research.', self.section)
        self.assertIn('hypotheses, validation, disclosure, and reusable patterns', self.section)

    def test_project_links_and_more_system_icons(self):
        # KaliMac stays unlinked until its repository is publicly accessible.
        self.assertIn('#### 🗡️ `04 / KaliMac`', self.section)
        self.assertNotIn('https://github.com/L1ngSh1/KaliMac', self.section)
        for project in PROJECTS[:3] + PROJECTS[4:]:
            self.assertIn(f'(https://github.com/L1ngSh1/{project})', self.section)
        self.assertIn('- 🏴 [`ctf-lab`]', self.section)
        self.assertIn('- 📡 [`netwatch-cli`]', self.section)

    def test_responsive_indexes_match_readme_count_and_order(self):
        for name in ('projects.svg', 'projects-mobile.svg'):
            with self.subTest(asset=name):
                root = ET.parse(ROOT / 'assets' / name).getroot()
                labels = root.findall('.//s:text[@data-project]', NS)
                self.assertEqual([label.attrib['data-project'] for label in labels], PROJECTS)
                self.assertIn('05 SYSTEMS', [element.text for element in root.findall('.//s:text', NS)])
                description = root.find('s:desc', NS).text
                for project in PROJECTS:
                    self.assertIn(project, description)
                self.assertIsNone(root.find('.//s:image', NS))
                self.assertIsNone(root.find('.//s:script', NS))

    def test_responsive_picture_and_accessible_description(self):
        for name in ('projects.svg', 'projects-mobile.svg'):
            self.assertIn('assets/' + name, self.section)
            self.assertTrue((ROOT / 'assets' / name).is_file())
        self.assertIn('media="(max-width: 600px)"', self.section)
        self.assertIn('alt="Five featured systems:', self.section)

    def test_index_labels_stay_inside_viewboxes(self):
        for name in ('projects.svg', 'projects-mobile.svg'):
            root = ET.parse(ROOT / 'assets' / name).getroot()
            _, _, width, height = map(float, root.attrib['viewBox'].split())
            for label in root.findall('.//s:text[@data-project]', NS):
                self.assertGreater(float(label.attrib['x']), 0)
                self.assertLess(float(label.attrib['x']), width)
                self.assertGreater(float(label.attrib['y']), 0)
                self.assertLess(float(label.attrib['y']), height)


if __name__ == '__main__':
    unittest.main()
