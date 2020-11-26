"""Universal test stuff."""
# pylint: disable=abstract-method
import os

from infopanel import driver, config, display

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))


def load_test_config():
    """Load a pre-packaged test config."""
    conf = config.load_config_yaml(os.path.join(TEST_ROOT, "test_config.yaml"))
    driver.apply_global_config(conf)
    return conf


class MockDisplay(display.Display):
    """A display mock."""

    @property
    def height(self):
        """Get the height."""
        return 32

    @property
    def width(self):
        """Get the width."""
        return 64
