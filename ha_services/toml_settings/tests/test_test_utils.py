from pathlib import Path
from unittest import TestCase

from bx_py_utils.path import assert_is_dir, assert_is_file

from ha_services.cli.cli_app import SETTINGS_DIR_NAME, SETTINGS_FILE_NAME
from ha_services.example import DemoSettings
from ha_services.toml_settings.api import TomlSettings
from ha_services.toml_settings.test_utils.data_class_utils import (
    MockTomlSettings,
    replace_dataclass_values,
    replace_path_values,
)
from ha_services.toml_settings.tests.fixtures import ComplexExample, PathExample2


class TestUtilsTestCase(TestCase):
    def test_replace_dataclass_values(self):
        instance = ComplexExample()

        # Check before:
        self.assertEqual(instance.foo, 'bar')
        self.assertEqual(instance.sub_class_one.number, 123)
        self.assertEqual(instance.sub_class_two.something, 0.5)

        new_data = {
            'foo': 'NEW',
            'sub_class_two': {
                'something': 456,
            },
        }
        replace_dataclass_values(instance, data=new_data)

        # Check after:
        self.assertEqual(instance.foo, 'NEW')
        self.assertEqual(instance.sub_class_one.number, 123)  # unchanged?
        self.assertEqual(instance.sub_class_two.something, 456)

    def test_replace_path_values(self):
        instance = PathExample2()

        # Check before:
        self.assertEqual(instance.path, Path('/foo/baz'))
        self.assertEqual(instance.sub_path.path, Path('/foo/bar'))

        replace_path_values(instance)

        # Check after:
        self.assertEqual(instance.path, '/foo/baz')
        self.assertEqual(instance.sub_path.path, '/foo/bar')

    def test_toml_settings_mock(self):
        settings_overwrites = dict(
            systemd=dict(
                template_context=dict(
                    user='MockedUserName',
                    group='MockedUserName',
                )
            ),
        )
        with MockTomlSettings(
            SettingsDataclass=DemoSettings,
            settings_overwrites=settings_overwrites,
            dir_name=SETTINGS_DIR_NAME,
            file_name=SETTINGS_FILE_NAME,
            prefix='test_mock',
        ) as cm:
            self.assertIsInstance(cm, MockTomlSettings)
            self.assertIsInstance(cm.temp_path, Path)
            assert_is_dir(cm.temp_path)

            toml_settings = cm.toml_settings
            self.assertIsInstance(toml_settings, TomlSettings)
            assert_is_file(toml_settings.file_path)

            settings = toml_settings.settings_dataclass
            self.assertIsInstance(settings, DemoSettings)

            # Check some sample values:
            self.assertEqual(settings.systemd.service_slug, 'haservices_demo')
            self.assertEqual(settings.systemd.template_context.verbose_service_name, 'HaServices Demo')
            self.assertEqual(settings.systemd.template_context.user, 'MockedUserName')
            self.assertEqual(settings.systemd.template_context.group, 'MockedUserName')
            self.assertEqual(settings.systemd.template_context.work_dir, cm.temp_path)
            self.assertEqual(settings.app.device_name, 'ha-services-demo')

        self.assertFalse(cm.temp_path.exists())
