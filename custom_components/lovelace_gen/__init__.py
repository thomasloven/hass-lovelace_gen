import os
import logging
import json
import io
import time

import jinja2

from homeassistant.util.yaml import loader
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

jinja = jinja2.Environment(loader=jinja2.FileSystemLoader("/"))

def load_yaml(fname, args={}):
    try:
        stream = io.StringIO(jinja.get_template(fname).render(args))
        stream.name = fname
        return loader.yaml.load(stream, Loader=loader.SafeLineLoader) or {}
    except loader.yaml.YAMLError as exc:
        _LOGGER.error(str(exc))
        raise HomeAssistantError(exc)
    except UnicodeDecodeError as exc:
        _LOGGER.error("Unable to read file %s: %s", fname, exc)
        raise HomeAssistantError(exc)

def _include_yaml(ldr, node):
    fn, *args = node.value.split(' ', 1)
    fname = os.path.join(os.path.dirname(ldr.name), fn)
    if args:
        args = json.loads(args[0])
    return loader._add_reference(load_yaml(fname, args), ldr, node)

def _uncache_file(ldr, node):
    path = node.value
    timestamp = str(time.time())
    if '?' in path:
        return f"{path}&{timestamp}"
    return f"{path}?{timestamp}"

loader.load_yaml = load_yaml
loader.yaml.SafeLoader.add_constructor("!include", _include_yaml)
loader.yaml.SafeLoader.add_constructor("!file", _uncache_file)
